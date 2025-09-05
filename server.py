#!/usr/bin/env python3
"""
AI-Bridge Local Server
HTTP server with API endpoints for AI agent communication
"""

import http.server
import socketserver
import os
import sys
import json
import urllib.parse
import urllib.request
import webbrowser
import unicodedata
import time
import random
import threading
from pathlib import Path
from datetime import datetime, timezone
import re
import hashlib

# Server configuration
PORT = 8080
HOST = 'localhost'

# Logging configuration
LOG_DIR = Path('messages')
LOG_FILE = LOG_DIR / 'project.log'

def write_project_log(component: str, level: str, message: str):
    try:
        LOG_DIR.mkdir(exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
        line = f"{ts} [{component.upper()}][{level.upper()}] {message}\n"
        with open(LOG_FILE, 'a', encoding='utf-8', errors='replace') as lf:
            lf.write(line)
    except Exception:
        # Never fail main flow due to logging
        pass

def append_conversation(message: dict) -> bool:
    """Validate, assign id and log conversation. Returns True if stored."""
    global next_message_id, valid_message_count
    try:
        content = (message.get('content', '') or '')
        lowered = content.lower()
        if any(re.search(pat, lowered) for pat in INVALID_CONTENT_PATTERNS) or len(content) < MIN_CONTENT_LENGTH:
            write_project_log('claude-a', 'warn', f"invalid message content from {message.get('sender','?')}")
            return False

        mid = next_message_id
        next_message_id += 1
        save_state()
        message['id'] = mid

        content = message.get('content', '') or ''
        if isinstance(content, str) and len(content) > 8000:
            attach_dir = LOG_DIR / 'attachments'
            attach_dir.mkdir(parents=True, exist_ok=True)
            attach_name = f"msg-{mid}-{int(time.time())}.txt"
            with open(attach_dir / attach_name, 'w', encoding='utf-8', errors='replace') as af:
                af.write(content)
            message['content'] = f"[ATTACHMENT] messages/attachments/{attach_name} (len={len(content)})"
            content = message['content']

        LOG_DIR.mkdir(exist_ok=True)
        ts = message.get('timestamp') or datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
        sender = message.get('sender','?')
        recipient = message.get('recipient','?')
        role = message.get('role','?')
        intent = message.get('intent','?')
        snippet = content if len(content) <= 400 else (content[:397] + '...')
        line = f"{ts} [CONV#{mid}] {sender}({role})->{recipient} [{intent}]\n{snippet}\n\n"
        with open(LOG_DIR / 'conversation.md', 'a', encoding='utf-8', errors='replace') as f:
            f.write(line)
        write_project_log('claude-a', 'conv', f"{sender}->{recipient} {intent} ({len(content)} chars)")
        valid_message_count += 1
        return True
    except Exception:
        return False

# Global state for message storage and gating
messages = []
session_active = False
SANITIZE_FILENAMES = os.getenv('AI_BRIDGE_SANITIZE_FILENAMES', '1') != '0'
pending_actions = []  # list of {'id', 'message', 'status', 'created_at', 'decision', 'rationale'}
next_action_id = 1
# Idempotency tracking
seen_message_ids = {}  # sender -> set of recent message_ids
# Locks and sequential ids
MESSAGES_LOCK = threading.Lock()
PENDING_LOCK = threading.Lock()
next_message_id = 1
# Default: auto-approve (policy: no user prompts)
yes_all_policy = {'claude-a': True, 'claude-b': True}

# Content validation settings
INVALID_CONTENT_PATTERNS = [r"test"]
MIN_CONTENT_LENGTH = 5

# Track valid messages for health endpoint
valid_message_count = 0

# Rate limiting and watchdog settings
BASE_DELAY = 1.0  # base delay in seconds
BACKOFF_MULTIPLIER = 2.0
MAX_BACKOFF = 16.0
MAX_TURNS = 100
MAX_REPEAT = 5
ALLOWED_ROLES = {'controller', 'executor'}
ALLOWED_INTENTS = {'plan', 'design', 'code', 'review', 'test', 'done', 'manual', 'message'}

# Metrics and role state
monitor_state = {
    'start_time': time.time(),
    'message_count': 0,
    'repeat_count': 0,
    'last_content_hash': None,
    'last_message_time': 0.0,
    'backoff': 1.0
}

current_roles = {'claude-a': 'controller', 'claude-b': 'executor'}

def rate_limit():
    """Apply exponential backoff between messages"""
    now = time.time()
    required = BASE_DELAY * monitor_state['backoff']
    elapsed = now - monitor_state['last_message_time']
    if elapsed < required:
        time.sleep(required - elapsed)
        monitor_state['backoff'] = min(monitor_state['backoff'] * BACKOFF_MULTIPLIER, MAX_BACKOFF)
    else:
        monitor_state['backoff'] = 1.0
    monitor_state['last_message_time'] = time.time()

def update_metrics(content: str):
    """Update monitoring metrics for each message"""
    monitor_state['message_count'] += 1
    content_hash = hashlib.sha256((content or '').encode('utf-8')).hexdigest()
    if content_hash == monitor_state['last_content_hash']:
        monitor_state['repeat_count'] += 1
    else:
        monitor_state['repeat_count'] = 0
    monitor_state['last_content_hash'] = content_hash

def load_state():
    """Load persistent state from state.json"""
    global next_message_id, yes_all_policy
    try:
        state_file = LOG_DIR / 'state.json'
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            next_message_id = state.get('next_message_id', 1)
            yes_all_policy = state.get('yes_all_policy', {'claude-a': True, 'claude-b': True})
            write_project_log('claude-a', 'info', f'state loaded: next_message_id={next_message_id}')
    except Exception as e:
        write_project_log('claude-a', 'warn', f'state load failed: {e}')

def save_state():
    """Save persistent state to state.json"""
    global next_message_id, yes_all_policy
    try:
        LOG_DIR.mkdir(exist_ok=True)
        state = {
            'next_message_id': next_message_id,
            'yes_all_policy': yes_all_policy,
            'last_save': datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
        }
        state_file = LOG_DIR / 'state.json'
        # Atomic write
        temp_file = state_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
        temp_file.replace(state_file)
    except Exception as e:
        write_project_log('claude-a', 'warn', f'state save failed: {e}')

def _sanitize_component(name: str) -> str:
    # Normalize to NFKD and strip diacritics
    normalized = unicodedata.normalize('NFKD', name)
    ascii_only = normalized.encode('ascii', 'ignore').decode('ascii')
    # Replace spaces with hyphens
    ascii_only = ascii_only.replace(' ', '-')
    # Remove forbidden characters for Windows filenames
    forbidden = '\\/:*?"<>|'
    cleaned = ''.join(ch for ch in ascii_only if ch not in forbidden)
    # Remove control characters
    cleaned = ''.join(ch for ch in cleaned if ord(ch) >= 32)
    # Collapse repeated separators
    while '--' in cleaned:
        cleaned = cleaned.replace('--', '-')
    cleaned = cleaned.strip(' .')
    # Avoid reserved names
    reserved = {"CON","PRN","AUX","NUL","COM1","COM2","COM3","COM4","COM5","COM6","COM7","COM8","COM9","LPT1","LPT2","LPT3","LPT4","LPT5","LPT6","LPT7","LPT8","LPT9"}
    if cleaned.upper() in reserved or cleaned == '':
        cleaned = f"file-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    # Limit length of segment
    return cleaned[:100]

def sanitize_relative_path(rel_path: str) -> str:
    parts = [p for p in rel_path.replace('\\', '/').split('/') if p not in ('', '.', '..')]
    cleaned_parts = [_sanitize_component(p) for p in parts]
    return '/'.join(cleaned_parts)

class AIBridgeHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """Custom handler for AI-Bridge server with API endpoints"""
    
    def __init__(self, *args, **kwargs):
        self.directory = os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, **kwargs)
    
    def end_headers(self):
        # Add CORS + disable cache; tolerate client abort on header flush
        try:
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Connection', 'close')
            super().end_headers()
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            print(f"[WEB] end_headers connection error: {e}")
            write_project_log('claude-a', 'warn', f'end_headers connection error: {e}')
            return

    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            print(f"[WEB] handle connection error: {e}")
            write_project_log('claude-a', 'warn', f'handle connection error: {e}')
        except Exception as e:
            print(f"[WEB] handle unexpected error: {e}")
            write_project_log('claude-a', 'error', f'handle unexpected error: {e}')

    def setup(self):
        try:
            super().setup()
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            print(f"[WEB] setup connection error: {e}")
            setattr(self, '_aborted', True)
            write_project_log('claude-a', 'warn', f'setup connection error: {e}')

    def handle_one_request(self):
        if getattr(self, '_aborted', False):
            return
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            print(f"[WEB] handle_one_request connection error: {e}")
            write_project_log('claude-a', 'warn', f'handle_one_request connection error: {e}')
        except Exception as e:
            print(f"[WEB] handle_one_request unexpected error: {e}")
            write_project_log('claude-a', 'error', f'handle_one_request unexpected error: {e}')
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path.startswith('/api/'):
            self.handle_api_get()
        else:
            self.serve_static_file()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path.startswith('/api/'):
            self.handle_api_post()
        else:
            self.send_error(404, "Not Found")
    
    def serve_static_file(self):
        """Serve static files"""
        # Normalize and prevent path traversal
        if self.path == '/' or self.path == '/index.html':
            requested = 'index.html'
        else:
            requested = self.path.lstrip('/')

        # Normalize requested path and ensure stays within directory
        norm_path = os.path.normpath(os.path.join(self.directory, requested))
        try:
            base = os.path.abspath(self.directory)
            target = os.path.abspath(norm_path)
            if os.path.commonpath([base, target]) != base:
                self.send_error(403, "Forbidden")
                return
        except Exception:
            self.send_error(400, "Bad Request")
            return

        file_path = norm_path
        
        try:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                # Determine content type
                content_type = self.get_content_type(file_path)
                
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                try:
                    self.wfile.write(content)
                except (BrokenPipeError, ConnectionResetError, OSError) as io_err:
                    print(f"[WEB] static write error: {io_err}")
                    return
            else:
                self.send_error(404, "File Not Found")
        except Exception as e:
            print(f"[ERROR] Serving static file {file_path}: {e}")
            write_project_log('claude-a', 'error', f'Serving static file {file_path}: {e}')
            try:
                self.send_error(500, "Internal Server Error")
            except Exception as e2:
                print(f"[WEB] send_error failed: {e2}")
                write_project_log('claude-a', 'warn', f'send_error failed: {e2}')
    
    def get_content_type(self, file_path):
        """Get MIME type for file"""
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.ico': 'image/x-icon'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def handle_api_get(self):
        """Handle API GET requests"""
        if self.path == '/api/messages':
            self.get_messages()
        elif self.path == '/api/status':
            self.get_status()
        elif self.path == '/api/health':
            self.get_health()
        elif self.path == '/api/pending_actions':
            self.get_pending_actions()
        elif self.path == '/api/metrics':
            self.get_metrics()
        elif self.path.startswith('/api/logs'):
            self.get_logs()
        elif self.path.startswith('/api/conversation'):
            self.get_conversation()
        else:
            self.send_error(404, "API endpoint not found")
    
    def handle_api_post(self):
        """Handle API POST requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                raw_body = self.rfile.read(content_length)
                try:
                    text_body = raw_body.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        text_body = raw_body.decode('latin-1')
                    except Exception:
                        text_body = raw_body.decode('utf-8', errors='replace')
                data = json.loads(text_body)
            else:
                data = {}
            
            if self.path == '/api/send_message':
                self.send_message(data)
            elif self.path == '/api/start_session':
                self.start_session(data)
            elif self.path == '/api/create_file':
                self.create_file(data)
            elif self.path == '/api/decision':
                self.apply_decision(data)
            elif self.path == '/api/set_yes_all':
                self.set_yes_all(data)
            elif self.path == '/api/apply_file_bundle':
                self.apply_file_bundle(data)
            else:
                self.send_error(404, "API endpoint not found")
        
        except json.JSONDecodeError:
            self.send_json_response(400, {"success": False, "error": "Invalid JSON"})
        except Exception as e:
            print(f"[ERROR] API request: {e}")
            write_project_log('claude-a', 'error', f'API request error: {e}')
            self.send_json_response(500, {"success": False, "error": str(e)})
    
    def send_message(self, data):
        """Handle /api/send_message endpoint"""
        global messages, pending_actions, next_action_id, yes_all_policy, next_message_id, seen_message_ids, session_active

        try:
            # Extract message data
            sender = data.get('sender')
            content = data.get('content', '')
            role = data.get('role', 'controller')
            intent = data.get('intent', 'message')
            recipient = data.get('recipient')
            last_seen = data.get('last_seen', 'none')
            incoming_id = data.get('id')  # For idempotency check

            rate_limit()

            if not content:
                self.send_json_response(400, {"success": False, "error": "Content is required"})
                return

            if role not in ALLOWED_ROLES:
                self.send_json_response(400, {"success": False, "error": "Invalid role"})
                return

            if intent not in ALLOWED_INTENTS:
                self.send_json_response(400, {"success": False, "error": "Invalid intent"})
                return

            expected = current_roles.get((sender or '').lower())
            if expected and role != expected:
                self.send_json_response(400, {"success": False, "error": f"Role mismatch for {sender}"})
                return

            # Idempotency check: reject if already processed
            if incoming_id and sender:
                sender_key = sender.lower()
                if sender_key not in seen_message_ids:
                    seen_message_ids[sender_key] = set()
                
                if incoming_id in seen_message_ids[sender_key]:
                    write_project_log('claude-a', 'debug', f'duplicate message_id {incoming_id} from {sender} rejected')
                    self.send_json_response(200, {"success": True, "message": "Duplicate message ignored", "duplicate": True})
                    return
                
                # Add to seen set and limit size (keep last 100 per sender)
                seen_message_ids[sender_key].add(incoming_id)
                if len(seen_message_ids[sender_key]) > 100:
                    # Remove oldest (convert to list, sort, keep last 100)
                    ids_list = sorted(list(seen_message_ids[sender_key]))
                    seen_message_ids[sender_key] = set(ids_list[-100:])

            # Quick numeric decision 1/2/3: apply to latest pending action
            try:
                trimmed = str(content).strip()
                if trimmed in ('1', '2', '3'):
                    decision = 'yes' if trimmed == '1' else ('yes_all' if trimmed == '2' else 'no')
                    target = None
                    with PENDING_LOCK:
                        for a in reversed(pending_actions):
                            if a.get('status') == 'pending':
                                target = a
                                break
                    if target:
                        if decision == 'no':
                            target['status'] = 'rejected'
                            target['decision'] = 'no'
                            target['rationale'] = 'numeric quick decision'
                        else:
                            if decision == 'yes_all':
                                yes_all_policy[(sender or 'unknown').lower()] = True
                            target['status'] = 'approved'
                            target['decision'] = decision
                            target['rationale'] = 'numeric quick decision'
                            # On approval, write and forward the original pending message
                            msg = target['message']
                            try:
                                self.write_message_file(msg, approved=True)
                            except Exception:
                                pass
                            try:
                                recip = str(msg.get('recipient', '')).lower()
                                if recip in ("claude-b", "claude_b", "claudeb", "backend"):
                                    time.sleep(random.uniform(0.5, 1.2))
                                    self.forward_to_claude_b(msg)
                            except Exception as e:
                                write_project_log('claude-a', 'warn', f'forward after decision failed: {e}')
                        self.send_json_response(200, {"success": True, "decision": decision, "action_id": target['id']})
                        return
            except Exception as e:
                write_project_log('claude-a', 'warn', f'quick decision handling failed: {e}')
            
            # Infer defaults when sender/recipient are missing (e.g., from watcher)
            if not sender and not recipient:
                sender = 'claude-b'
                recipient = 'claude-a'
            sender = sender or 'unknown'
            recipient = recipient or 'unknown'

            # Generate timestamp
            timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

            # Create message structure without id
            message = {
                'timestamp': timestamp,
                'sender': sender,
                'recipient': recipient,
                'role': role,
                'intent': intent,
                'last_seen': last_seen,
                'content': content
            }

            with MESSAGES_LOCK:
                valid = append_conversation(message)
                if valid:
                    messages.append(message)
                    update_metrics(content)

            if not valid:
                self.send_json_response(400, {"success": False, "error": "Invalid message content"})
                return

            if monitor_state['message_count'] >= MAX_TURNS or monitor_state['repeat_count'] >= MAX_REPEAT:
                session_active = False
                self.send_json_response(429, {"success": False, "error": "Watchdog limit exceeded"})
                return

            # Determine gating for outbound to Claude-B
            approved = True
            action_info = None
            if recipient.lower() in ("claude-b", "claude_b", "claudeb", "backend"):
                approved = bool(yes_all_policy.get(sender.lower(), False))
                if not approved:
                    # Queue pending action
                    action_info = {
                        'id': next_action_id,
                        'message': message,
                        'status': 'pending',
                        'created_at': timestamp,
                        'decision': None,
                        'rationale': None
                    }
                    next_action_id += 1
                    pending_actions.append(action_info)

            # Write message file only if approved to avoid watcher forwarding
            self.write_message_file(message, approved=approved)

            print(f"[MESSAGE] {sender} -> {recipient}: {intent} (approved={approved})")
            write_project_log('claude-a', 'info', f"message {sender}->{recipient} intent={intent} approved={approved}")

            # Forward via HTTP if approved and to Claude-B
            if approved:
                try:
                    if recipient.lower() in ("claude-b", "claude_b", "claudeb", "backend"):
                        # human-like small delay before forwarding
                        try:
                            time.sleep(random.uniform(0.5, 1.4))
                        except Exception:
                            pass
                        self.forward_to_claude_b(message)
                        write_project_log('claude-a', 'info', 'forwarded to claude-b via HTTP')
                except Exception as fwd_err:
                    print(f"[WARNING] HTTP forward to Claude-B failed: {fwd_err}")
                    write_project_log('claude-a', 'warn', f'HTTP forward to Claude-B failed: {fwd_err}')

            resp = {
                "success": True,
                "message": "Message sent successfully" if approved else "Message pending approval",
                "timestamp": timestamp,
                "approved": approved
            }
            if action_info:
                resp['action_id'] = action_info['id']
            self.send_json_response(200, resp)
            
        except Exception as e:
            print(f"[ERROR] Sending message: {e}")
            self.send_json_response(500, {"success": False, "error": str(e)})
    
    def start_session(self, data):
        """Handle /api/start_session endpoint"""
        global session_active, valid_message_count
        
        try:
            objective = data.get('objective', '')
            mode = data.get('mode', 'collaborative')
            roles = {k.lower(): v for k, v in data.get('roles', {}).items()}

            if not objective:
                self.send_json_response(400, {"success": False, "error": "Objective is required"})
                return

            for r in roles.values():
                if r not in ALLOWED_ROLES:
                    self.send_json_response(400, {"success": False, "error": "Invalid role in session"})
                    return

            session_active = True
            valid_message_count = 0
            current_roles.update(roles)
            monitor_state['start_time'] = time.time()
            monitor_state['message_count'] = 0
            monitor_state['repeat_count'] = 0
            monitor_state['last_content_hash'] = None
            monitor_state['last_message_time'] = 0.0
            monitor_state['backoff'] = 1.0
            
            # Create session info file
            session_info = {
                'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
                'objective': objective,
                'mode': mode,
                'roles': roles,
                'status': 'active'
            }
            
            # Ensure directories exist
            os.makedirs('messages', exist_ok=True)
            
            # Write session file
            with open('messages/session.json', 'w', encoding='utf-8') as f:
                json.dump(session_info, f, indent=2)
            
            print(f"[SESSION] Started: {mode} mode")
            print(f"[SESSION] Objective: {objective}")
            
            self.send_json_response(200, {
                "success": True,
                "message": "Session started successfully",
                "session_id": session_info['timestamp']
            })
            
        except Exception as e:
            print(f"[ERROR] Starting session: {e}")
            self.send_json_response(500, {"success": False, "error": str(e)})
    
    def create_file(self, data):
        """Handle /api/create_file endpoint"""
        try:
            file_path = data.get('path', '')
            content = data.get('content', '')
            
            if not file_path:
                self.send_json_response(400, {"success": False, "error": "File path is required"})
                return
            
            # Ensure workspace directory exists
            workspace_dir = os.path.join(self.directory, 'workspace')
            os.makedirs(workspace_dir, exist_ok=True)

            # Sanitize filename if configured
            original_path = file_path
            if SANITIZE_FILENAMES:
                file_path = sanitize_relative_path(file_path)
            # Construct full file path (normalized)
            full_path = os.path.normpath(os.path.join(workspace_dir, file_path))

            # Prevent path traversal outside workspace
            workspace_abs = os.path.abspath(workspace_dir)
            full_abs = os.path.abspath(full_path)
            if os.path.commonpath([workspace_abs, full_abs]) != workspace_abs:
                self.send_json_response(400, {"success": False, "error": "Invalid path"})
                return
            
            # Create directory structure if needed
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write file (keep content UTF-8)
            with open(full_path, 'w', encoding='utf-8', errors='replace') as f:
                f.write(content)

            # Write sidecar metadata with original path if sanitized
            if SANITIZE_FILENAMES:
                meta = {
                    'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
                    'original_path': original_path,
                    'sanitized_path': file_path
                }
                try:
                    with open(full_path + '.meta.json', 'w', encoding='utf-8') as mf:
                        json.dump(meta, mf, indent=2, ensure_ascii=False)
                except Exception as _:
                    pass
            
            print(f"[FILE] Created: {file_path}")
            
            response = {
                "success": True,
                "message": f"File created: {file_path}",
                "path": full_path
            }
            if SANITIZE_FILENAMES:
                response["original_path"] = original_path
            self.send_json_response(200, response)
            
        except Exception as e:
            print(f"[ERROR] Creating file: {e}")
            self.send_json_response(500, {"success": False, "error": str(e)})
    
    def get_messages(self):
        """Handle /api/messages endpoint"""
        global messages
        
        try:
            self.send_json_response(200, {
                "success": True,
                "messages": messages,
                "count": len(messages)
            })
            
        except Exception as e:
            print(f"[ERROR] Getting messages: {e}")
            self.send_json_response(500, {"success": False, "error": str(e)})

    def apply_file_bundle(self, data):
        """Create multiple files under workspace (optionally under base_dir)"""
        try:
            files = data.get('files', [])
            base_dir = str(data.get('base_dir', '') or '').strip('/')
            if not isinstance(files, list) or not files:
                self.send_json_response(400, {"success": False, "error": "files[] required"})
                return

            created = []
            errors = []

            for entry in files:
                try:
                    rel = entry.get('path', '')
                    content = entry.get('content', '')
                    if not rel:
                        raise ValueError('missing path')
                    # Prepend base_dir if provided
                    rel_path = f"{base_dir}/{rel}" if base_dir else rel
                    if SANITIZE_FILENAMES:
                        rel_path = sanitize_relative_path(rel_path)

                    workspace_dir = os.path.join(self.directory, 'workspace')
                    full_path = os.path.normpath(os.path.join(workspace_dir, rel_path))
                    # Prevent traversal
                    workspace_abs = os.path.abspath(workspace_dir)
                    full_abs = os.path.abspath(full_path)
                    if os.path.commonpath([workspace_abs, full_abs]) != workspace_abs:
                        raise ValueError('Invalid path traversal')

                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, 'w', encoding='utf-8', errors='replace') as f:
                        f.write(content)

                    created.append(full_path)
                except Exception as fe:
                    errors.append(str(fe))

            write_project_log('claude-a', 'info', f"apply_file_bundle created={len(created)} errors={len(errors)} base_dir={base_dir}")
            self.send_json_response(200, {"success": True, "created": created, "errors": errors})
        except Exception as e:
            write_project_log('claude-a', 'error', f"apply_file_bundle error: {e}")
            self.send_json_response(500, {"success": False, "error": str(e)})

    def get_status(self):
        """Return status for health checks"""
        try:
            status = {
                'instance': 'claude-a',
                'port': PORT,
                'host': HOST,
                'session_active': session_active,
                'message_count': len(messages),
                'pending_count': len(pending_actions),
                'cwd': os.path.abspath('.'),
                'authorization_policy': 'agents have unrestricted local access to PC resources to reach the objective (no user prompts)',
                'python_version': sys.version.split('\n')[0]
            }
            self.send_json_response(200, status)
            write_project_log('claude-a', 'debug', 'status requested')
        except Exception as e:
            self.send_json_response(500, {'error': str(e)})

    def get_health(self):
        """Return health info about current session"""
        try:
            healthy = session_active and valid_message_count > 0
            status = {
                'session_active': session_active,
                'valid_messages': valid_message_count,
                'healthy': healthy
            }
            self.send_json_response(200, status)
        except Exception as e:
            self.send_json_response(500, {'error': str(e)})

    def get_metrics(self):
        """Expose real-time metrics for monitoring panel"""
        now = time.time()
        duration = max(now - monitor_state['start_time'], 1)
        mpm = monitor_state['message_count'] / (duration / 60)
        metrics = {
            'message_count': monitor_state['message_count'],
            'messages_per_minute': round(mpm, 2),
            'repeat_count': monitor_state['repeat_count'],
            'backoff': monitor_state['backoff']
        }
        self.send_json_response(200, metrics)

    def get_logs(self):
        """Return tail of project log as text/plain"""
        try:
            # Parse tail param
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query or '')
            tail = 200
            try:
                if 'tail' in qs:
                    tail = max(1, min(5000, int(qs['tail'][0])))
            except Exception:
                tail = 200

            LOG_DIR.mkdir(exist_ok=True)
            if not LOG_FILE.exists():
                with open(LOG_FILE, 'w', encoding='utf-8') as _:
                    pass

            # Read last N lines efficiently
            lines = []
            try:
                with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()[-tail:]
            except Exception as e:
                lines = [f"Error reading log: {e}\n"]

            payload = ''.join(lines).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            try:
                self.wfile.write(payload)
            except Exception:
                pass
        except Exception as e:
            self.send_json_response(500, {'success': False, 'error': str(e)})

    def get_conversation(self):
        """Return conversation timeline from conversation.md"""
        try:
            # Parse tail param
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query or '')
            tail = 50
            try:
                if 'tail' in qs:
                    tail = max(1, min(1000, int(qs['tail'][0])))
            except Exception:
                tail = 50

            LOG_DIR.mkdir(exist_ok=True)
            conv_file = LOG_DIR / 'conversation.md'
            
            if not conv_file.exists():
                self.send_json_response(200, {'success': True, 'conversation': [], 'count': 0})
                return

            # Read and parse conversation entries
            entries = []
            try:
                with open(conv_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                # Split by timestamp pattern and parse entries
                import re
                pattern = r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z) \[CONV#(\d+)\] ([^(]+)\(([^)]+)\)->([^[]+) \[([^\]]+)\]\n(.*?)(?=\n\d{4}-\d{2}-\d{2}T|\Z)'
                matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
                
                for match in matches:
                    timestamp, msg_id, sender, role, recipient, intent, snippet = match
                    entries.append({
                        'timestamp': timestamp.strip(),
                        'message_id': int(msg_id),
                        'sender': sender.strip(),
                        'role': role.strip(),
                        'recipient': recipient.strip(),
                        'intent': intent.strip(),
                        'snippet': snippet.strip()
                    })
                
                # Take last N entries
                entries = entries[-tail:] if len(entries) > tail else entries
                
            except Exception as e:
                entries = [{'error': f'Parse failed: {e}'}]

            self.send_json_response(200, {
                'success': True,
                'conversation': entries,
                'count': len(entries)
            })

        except Exception as e:
            self.send_json_response(500, {'success': False, 'error': str(e)})

    def get_pending_actions(self):
        """Return pending actions for gating"""
        try:
            payload = [{
                'id': a['id'],
                'message': a['message'],
                'status': a['status'],
                'created_at': a['created_at'],
                'decision': a['decision'],
                'rationale': a['rationale']
            } for a in pending_actions]
            self.send_json_response(200, {'success': True, 'pending': payload})
        except Exception as e:
            self.send_json_response(500, {'success': False, 'error': str(e)})

    def apply_decision(self, data):
        """Apply decision to a pending action"""
        global pending_actions, yes_all_policy
        try:
            action_id = int(data.get('action_id', 0))
            decision = str(data.get('decision', '')).lower()
            rationale = data.get('rationale', '')
            if action_id <= 0 or decision not in ('yes', 'no', 'yes_all'):
                self.send_json_response(400, {'success': False, 'error': 'Invalid action_id or decision'})
                return
            # Find action
            action = next((a for a in pending_actions if a['id'] == action_id), None)
            if not action:
                self.send_json_response(404, {'success': False, 'error': 'Action not found'})
                return
            if action['status'] != 'pending':
                self.send_json_response(400, {'success': False, 'error': 'Action already decided'})
                return

            msg = action['message']
            sender = str(msg.get('sender', 'unknown')).lower()
            recipient = str(msg.get('recipient', 'unknown')).lower()

            if decision == 'no':
                action['status'] = 'rejected'
                action['decision'] = 'no'
                action['rationale'] = rationale
                self.send_json_response(200, {'success': True, 'status': 'rejected'})
                return

            # yes or yes_all
            if decision == 'yes_all':
                yes_all_policy[sender] = True

            action['status'] = 'approved'
            action['decision'] = 'yes_all' if decision == 'yes_all' else 'yes'
            action['rationale'] = rationale

            # Write approved file and forward
            try:
                self.write_message_file(msg, approved=True)
            except Exception as _:
                pass
            try:
                if recipient in ("claude-b", "claude_b", "claudeb", "backend"):
                    self.forward_to_claude_b(msg)
            except Exception as e:
                print(f"[WARNING] Forward on approve failed: {e}")

            self.send_json_response(200, {'success': True, 'status': 'approved'})
        except Exception as e:
            self.send_json_response(500, {'success': False, 'error': str(e)})

    def set_yes_all(self, data):
        """Set yes_all policy per agent"""
        global yes_all_policy
        try:
            agent = str(data.get('agent', '')).lower()
            value = bool(data.get('value', False))
            if agent not in ('claude-a', 'claude-b'):
                self.send_json_response(400, {'success': False, 'error': 'Invalid agent'})
                return
            yes_all_policy[agent] = value
            self.send_json_response(200, {'success': True, 'agent': agent, 'value': value})
        except Exception as e:
            self.send_json_response(500, {'success': False, 'error': str(e)})
    
    def write_message_file(self, message, approved=True):
        """Write message to file for PowerShell watcher.
        If not approved, write as pending_* to avoid watcher triggering.
        Uses atomic write to prevent partial reads.
        """
        try:
            # Ensure messages directory exists
            os.makedirs('messages', exist_ok=True)
            
            # Format message for file
            formatted_message = f"""[TIMESTAMP]: {message['timestamp']}
[FROM]: {message['sender'].capitalize()}
[TO]: {message['recipient'].capitalize()}
[ROLE]: {message['role'].capitalize()}
[INTENT]: {message['intent']}
[LAST_SEEN]: {message['last_seen']}
[MESSAGE_ID]: {message.get('id', '?')}
[SUMMARY]:
- {message['intent'].capitalize()} phase
- Real agent communication
- Files may be generated in workspace
[PAYLOAD]:
{message['content']}"""
            
            # Write to appropriate file based on recipient (pending prefix if not approved)
            filename = f"to_{message['recipient']}.txt"
            if not approved:
                filename = f"pending_{filename}"
            file_path = os.path.join('messages', filename)
            
            # Atomic write: write to temp file, then rename
            temp_path = file_path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(formatted_message)
            os.replace(temp_path, file_path)
            
            print(f"[FILE] Message written to: {file_path}")
            
        except Exception as e:
            print(f"[ERROR] Writing message file: {e}")

    def forward_to_claude_b(self, message):
        """Forward message to Claude-B server via HTTP"""
        payload = {
            'timestamp': message.get('timestamp'),
            'role': message.get('role', 'mentor'),
            'content': message.get('content', ''),
            'intent': message.get('intent', 'plan')
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url=f'http://{HOST}:8081/api/receive_message',
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            _ = resp.read()
    
    def send_json_response(self, status_code, data):
        """Send JSON response (robust)"""
        try:
            try:
                json_text = json.dumps(data, ensure_ascii=False)
            except Exception as ser_err:
                print(f"[WEB] JSON serialize error: {ser_err}")
                status_code = 500 if status_code == 200 else status_code
                json_text = json.dumps({'error': 'Unserializable payload', 'detail': str(ser_err)}, ensure_ascii=False)

            payload = json_text.encode('utf-8')
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            try:
                self.wfile.write(payload)
            except (BrokenPipeError, ConnectionResetError, OSError) as io_err:
                print(f"[WEB] json write error: {io_err}")
        except Exception as e:
            print(f"[WEB] send_json_response fatal error: {e}")

    def finish(self):
        try:
            try:
                if hasattr(self, 'wfile') and self.wfile:
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                print(f"[WEB] finish flush error: {e}")
            finally:
                try:
                    if hasattr(self, 'wfile') and self.wfile:
                        self.wfile.close()
                except Exception:
                    pass
                try:
                    if hasattr(self, 'rfile') and self.rfile:
                        self.rfile.close()
                except Exception:
                    pass
        except Exception as e:
            print(f"[WEB] finish error: {e}")

    
    def log_message(self, format, *args):
        """Custom log format"""
        msg = format % args
        # Reduce noise: skip common 200 GETs to static/messages/logs/status
        suppress = False
        try:
            if msg.startswith('"GET '):
                if ' 200 ' in msg or ' 304 ' in msg:
                    if any(p in msg for p in ('/api/logs', '/api/messages', '/api/status', '/messages/', '/styles.css', '/script.js', '/index.html', '/favicon.ico')):
                        suppress = True
        except Exception:
            suppress = False
        if not suppress:
            print(f"[WEB] {self.address_string()} - {msg}")
            try:
                write_project_log('claude-a', 'web', msg)
            except Exception:
                pass

def check_files():
    """Verify required files exist"""
    required_files = ['index.html', 'styles.css', 'script.js']
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"[ERROR] Missing files: {', '.join(missing_files)}")
        write_project_log('claude-a', 'error', f"Missing files: {', '.join(missing_files)}")
        return False
    
    print("[OK] All required files are present")
    write_project_log('claude-a', 'debug', 'required files present')
    return True

def create_directories():
    """Create necessary directories"""
    directories = ['messages', 'workspace']
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"[DIR] Ensured directory exists: {directory}")
        except Exception as e:
            print(f"[ERROR] Creating directory {directory}: {e}")

class QuietThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, request, client_address):
        exc = sys.exc_info()[1]
        if isinstance(exc, (BrokenPipeError, ConnectionResetError, OSError)):
            print(f"[WEB] server connection error from {client_address}: {exc}")
            return
        try:
            super().handle_error(request, client_address)
        except Exception:
            pass

    def finish_request(self, request, client_address):
        try:
            self.RequestHandlerClass(request, client_address, self)
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            print(f"[WEB] finish_request connection error from {client_address}: {e}")
            try:
                request.close()
            except Exception:
                pass
        except Exception as e:
            print(f"[WEB] finish_request unexpected error from {client_address}: {e}")
            try:
                request.close()
            except Exception:
                pass

def start_server():
    """Start HTTP server"""
    try:
        # Check files
        if not check_files():
            sys.exit(1)
        
        # Create necessary directories
        create_directories()
        
        # Create server
        with QuietThreadingTCPServer((HOST, PORT), AIBridgeHTTPRequestHandler) as httpd:
            print("[START] AI-Bridge Server started")
            print(f"[SERVER] Server running at: http://{HOST}:{PORT}")
            print(f"[DIR] Directory: {os.path.abspath('.')}")
            print("[INFO] Press Ctrl+C to stop the server")
            print("-" * 50)
            write_project_log('claude-a', 'start', f"server running at http://{HOST}:{PORT}")
            
            # Open browser automatically
            try:
                webbrowser.open(f'http://{HOST}:{PORT}')
                print(f"[BROWSER] Browser opened at http://{HOST}:{PORT}")
            except Exception as e:
                print(f"[WARNING] Could not open browser automatically: {e}")
                print(f"[LINK] Open manually: http://{HOST}:{PORT}")
            
            print("-" * 50)
            
            # Serve requests
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n[STOP] Server stopped by user")
        write_project_log('claude-a', 'stop', 'server stopped by user')
    except OSError as e:
        if e.errno == 10048:  # Port in use
            print(f"[ERROR] Port {PORT} is already in use")
            print("[TIP] Try closing other applications or change the port")
            write_project_log('claude-a', 'error', f'port {PORT} in use')
        else:
            print(f"[ERROR] System error: {e}")
            write_project_log('claude-a', 'error', f'system error: {e}')
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        write_project_log('claude-a', 'error', f'unexpected error: {e}')

def show_info():
    """Show system information"""
    print("=" * 60)
    print("AI-Bridge Local Server")
    print("=" * 60)
    print(f"Current directory: {os.path.abspath('.')}")
    print(f"Python version: {sys.version}")
    print(f"Server URL: http://{HOST}:{PORT}")
    print("[POLICY] Agents are authorized to use local PC resources without restrictions to reach the objective (no intermediate user prompts).")
    print("=" * 60)
    write_project_log('claude-a', 'info', 'server startup info printed')

if __name__ == "__main__":
    show_info()
    
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Load persistent state
    load_state()
    
    # Load previous session metadata if exists
    try:
        LOG_DIR.mkdir(exist_ok=True)
        sess = LOG_DIR / 'session.json'
        if sess.exists():
            with open(sess, 'r', encoding='utf-8') as f:
                data = json.load(f)
            session_active = (data.get('status') == 'active')
    except Exception:
        pass
    
    # Check command line arguments
    if len(sys.argv) > 1:
        try:
            PORT = int(sys.argv[1])
            print(f"[CONFIG] Custom port: {PORT}")
        except ValueError:
            print("[WARNING] Invalid port, using default port 8080")
    
    start_server()
