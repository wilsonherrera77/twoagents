#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-Bridge Claude-B Server (Port 8081)
Second Claude instance for dual-agent communication
"""

import http.server
import socketserver
import json
import os
import sys
import webbrowser
import urllib.request
import threading
import time
import random
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone
import hashlib

# Fix encoding for Windows console
if os.name == 'nt':
    os.system('chcp 65001 > nul')

# Configuration for Claude-B
PORT = 8081
HOST = 'localhost'
WORKSPACE_DIR = Path('workspace')  # Shared workspace
MESSAGE_DIR = Path('messages')     # Shared messages
INSTANCE_ID = 'claude-b'

# Unified project log
LOG_DIR = Path('messages')
LOG_FILE = LOG_DIR / 'project.log'

def write_project_log(component: str, level: str, message: str):
    try:
        LOG_DIR.mkdir(exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        line = f"{ts} [{component.upper()}][{level.upper()}] {message}\n"
        with open(LOG_FILE, 'a', encoding='utf-8', errors='replace') as lf:
            lf.write(line)
    except Exception:
        pass

# Global state for Claude-B
agent_state = {
    'messages': [],
    'session_active': False,
    'current_iteration': 0,
    'project_files': {},
    'execution_results': {},
    'role': 'executor',
    'last_message_id': 0
}

# Rate limiting and metrics for watchdog
BASE_DELAY = 1.0
BACKOFF_MULTIPLIER = 2.0
MAX_BACKOFF = 16.0
MAX_TURNS = 100
MAX_REPEAT = 5
ALLOWED_ROLES = {'controller', 'executor'}
ALLOWED_INTENTS = {'plan', 'design', 'code', 'review', 'test', 'done', 'manual', 'message'}

monitor_state = {
    'start_time': time.time(),
    'message_count': 0,
    'repeat_count': 0,
    'last_content_hash': None,
    'last_message_time': 0.0,
    'backoff': 1.0
}

def rate_limit():
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
    monitor_state['message_count'] += 1
    content_hash = hashlib.sha256((content or '').encode('utf-8')).hexdigest()
    if content_hash == monitor_state['last_content_hash']:
        monitor_state['repeat_count'] += 1
    else:
        monitor_state['repeat_count'] = 0
    monitor_state['last_content_hash'] = content_hash

class ClaudeBHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Claude-B HTTP Request Handler"""
    
    def __init__(self, *args, **kwargs):
        try:
            # Use current working directory (set before server start) to avoid passing 'directory' kw
            super().__init__(*args, **kwargs)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as e:
            # Swallow connection aborts during handler initialization
            print(f"init connection error: {e}")
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
            # Do not re-raise
            return

    def setup(self):
        """Wrap setup to absorb disconnects during stream creation"""
        try:
            super().setup()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as e:
            print(f"setup connection error: {e}")
            setattr(self, '_aborted', True)
            try:
                if hasattr(self, 'connection') and self.connection:
                    self.connection.close()
            except Exception:
                pass

    def handle_one_request(self):
        """Process a single request with robust error handling"""
        if getattr(self, '_aborted', False):
            return
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as e:
            print(f"handle_one_request connection error: {e}")
        except Exception as e:
            # Avoid traceback storm; log only
            print(f"handle_one_request unexpected error: {e}")

    def handle(self):
        """Wrap entire request handling to absorb client-abort errors"""
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as e:
            print(f"handle connection error: {e}")
        except Exception as e:
            # Log unexpected errors but avoid crashing the server loop
            print(f"handle unexpected error: {e}")
    
    def end_headers(self):
        try:
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            # Reduce keep-alive complications on Windows when clients disconnect mid-flight
            self.send_header('Connection', 'close')
            super().end_headers()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as e:
            # Client aborted during header flush; log quietly and stop
            print(f"end_headers connection error: {e}")
            return
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            self.send_error(404)
    
    def do_GET(self):
        if self.path.startswith('/api/'):
            self.handle_api_get()
        elif self.path == '/' or self.path == '/index.html':
            # Serve modified HTML for Claude-B
            self.serve_claude_b_interface()
        else:
            try:
                super().do_GET()
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as e:
                print(f"do_GET static write error: {e}")
    
    def serve_claude_b_interface(self):
        """Serve modified interface for Claude-B"""
        try:
            with open('index.html', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Modify for Claude-B
            content = content.replace('<title>AI-Bridge: Herramienta Semi-Asistida</title>', 
                                    '<title>AI-Bridge: Claude-B (Implementador)</title>')
            content = content.replace('<h1>🤖 AI-Bridge</h1>', 
                                    '<h1>🤖 AI-Bridge (Claude-B)</h1>')
            content = content.replace('Herramienta Semi-Asistida de Desarrollo Colaborativo', 
                                    'Instancia B - Rol Implementador')
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            try:
                self.wfile.write(content.encode('utf-8'))
            except (BrokenPipeError, ConnectionResetError, OSError) as io_err:
                print(f"serve_claude_b_interface write error: {io_err}")
                return
            
        except Exception as e:
            self.send_error(500, f"Error serving interface: {e}")
    
    def handle_api_request(self):
        """Process API requests for Claude-B"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            try:
                dbg = post_data[:200]
                print(f"DEBUG post_data: {dbg}")
            except Exception:
                pass
            data = json.loads(post_data) if post_data else {}
            
            response = None
            
            if self.path == '/api/send_message':
                response = self.handle_send_message(data)
            elif self.path == '/api/receive_message':
                response = self.handle_receive_message(data)
            elif self.path == '/api/status':
                response = self.get_status()
            else:
                response = {'error': 'Unknown endpoint'}
            
            self.send_json_response(response)
            try:
                write_project_log('claude-b', 'info', f"API {self.path} handled")
            except Exception:
                pass
            
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as e:
            # Client disconnected or socket error; log and do not attempt to respond
            print(f"handle_api_request connection error: {e}")
            return
        except Exception as e:
            import traceback as _tb
            print(f"handle_api_request error: {e}")
            print(_tb.format_exc())
            self.send_json_response({'error': str(e)}, status=500)
    
    def handle_api_get(self):
        """Handle GET API requests for Claude-B"""
        try:
            if self.path == '/api/status':
                response = self.get_status()
            elif self.path == '/api/messages':
                response = {'messages': agent_state['messages'][-10:]}  # Last 10 messages
            elif self.path == '/api/metrics':
                response = self.get_metrics()
            else:
                response = {'error': 'Unknown endpoint'}
            
            self.send_json_response(response)
            
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as e:
            print(f"handle_api_get connection error: {e}")
            return
        except Exception as e:
            import traceback as _tb
            print(f"handle_api_get error: {e}")
            print(_tb.format_exc())
            self.send_json_response({'error': str(e)}, status=500)
    
    def handle_send_message(self, data):
        """Handle message from Claude-B to Claude-A"""
        rate_limit()

        content = data.get('content', '')
        intent = data.get('intent', 'code')
        role = data.get('role', agent_state['role'])

        if role != agent_state['role']:
            return {'error': 'Role mismatch'}
        if role not in ALLOWED_ROLES or intent not in ALLOWED_INTENTS:
            return {'error': 'Invalid role or intent'}

        message = {
            'id': agent_state['last_message_id'] + 1,
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'from': 'claude-b',
            'to': 'claude-a',
            'role': role,
            'content': content,
            'intent': intent
        }

        agent_state['messages'].append(message)
        agent_state['last_message_id'] = message['id']
        update_metrics(content)

        if monitor_state['message_count'] >= MAX_TURNS or monitor_state['repeat_count'] >= MAX_REPEAT:
            agent_state['session_active'] = False
            return {'error': 'Watchdog limit exceeded'}

        write_project_log('claude-b', 'info', f"send_message id={message['id']}")

        # Write to shared file for Claude-A to read
        self.write_message_to_claude_a(message)

        # Also forward to Claude-A server via HTTP for robustness
        try:
            self.forward_to_claude_a_http(message)
        except Exception as e:
            print(f"HTTP forward to Claude-A failed: {e}")
            write_project_log('claude-b', 'warn', f'HTTP forward to A failed: {e}')

        return {'success': True, 'message_id': message['id']}
    
    def handle_receive_message(self, data):
        """Handle message received from Claude-A"""
        rate_limit()

        role = data.get('role', 'controller')
        intent = data.get('intent', 'plan')
        content = data.get('content', '')

        if role not in ALLOWED_ROLES or intent not in ALLOWED_INTENTS:
            return {'error': 'Invalid role or intent'}

        message = {
            'id': data.get('id'),
            'timestamp': data.get('timestamp'),
            'from': 'claude-a',
            'to': 'claude-b',
            'role': role,
            'content': content,
            'intent': intent
        }

        agent_state['messages'].append(message)
        update_metrics(content)

        if monitor_state['message_count'] >= MAX_TURNS or monitor_state['repeat_count'] >= MAX_REPEAT:
            agent_state['session_active'] = False
            return {'error': 'Watchdog limit exceeded'}

        write_project_log('claude-b', 'info', 'receive_message from A stored')

        # Process the message and potentially auto-respond
        self.process_received_message(message)

        return {'success': True, 'processed': True}
    
    def get_status(self):
        """Get Claude-B status"""
        return {
            'instance': 'claude-b',
            'port': PORT,
            'role': agent_state['role'],
            'session_active': agent_state['session_active'],
            'message_count': len(agent_state['messages']),
            'workspace': str(WORKSPACE_DIR.absolute()),
            'last_message_id': agent_state['last_message_id']
        }

    def get_metrics(self):
        now = time.time()
        duration = max(now - monitor_state['start_time'], 1)
        mpm = monitor_state['message_count'] / (duration / 60)
        return {
            'message_count': monitor_state['message_count'],
            'messages_per_minute': round(mpm, 2),
            'repeat_count': monitor_state['repeat_count'],
            'backoff': monitor_state['backoff']
        }
    
    def write_message_to_claude_a(self, message):
        """Write message for Claude-A to read with atomic write"""
        try:
            MESSAGE_DIR.mkdir(exist_ok=True)
            message_file = MESSAGE_DIR / 'from_claude-b.txt'
            
            formatted_message = f"""[TIMESTAMP]: {message['timestamp']}
[FROM]: Claude-B
[TO]: Claude-A
[ROLE]: {message['role']}
[INTENT]: {message['intent']}
[LAST_SEEN]: {self.get_last_claude_a_timestamp()}
[MESSAGE_ID]: {message['id']}
[SUMMARY]:
- Implementation response from Claude-B
- Code/solution provided
- Ready for review
[PAYLOAD]:
{message['content']}
"""
            
            # Atomic write: write to temp file, then rename
            temp_file = message_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(formatted_message)
            temp_file.replace(message_file)

            print(f"Message written to {message_file}")
            write_project_log('claude-b', 'debug', f'message file written: {message_file}')

        except Exception as e:
            print(f"Error writing message: {e}")
            write_project_log('claude-b', 'error', f'write_message error: {e}')
    
    def process_received_message(self, message):
        """Process message from Claude-A and potentially respond"""
        if message['intent'] == 'plan':
            # Claude-A sent a plan, Claude-B should implement
            # Guard against non-string or missing content to avoid 500 errors
            raw_content = message.get('content', '')
            if not isinstance(raw_content, str):
                try:
                    import json as _json
                    safe_content = _json.dumps(raw_content, ensure_ascii=False)
                except Exception:
                    safe_content = str(raw_content)
            else:
                safe_content = raw_content

            response_content = f"""Received plan from Claude-A. Beginning implementation:

**Plan understood:**
{safe_content[:200]}...

**Implementation approach:**
1. Analyzing requirements
2. Creating file structure
3. Implementing core functionality
4. Testing basic operations

**Next steps:**
- Will create necessary files in workspace
- Implement according to specifications
- Report back with results

Starting implementation now...

[RATIONALE]:
- Prioritize streaming and basic contracts; de-risk large file handling first.
- Iterate with small bundles to allow quick review and approvals.

[DECISION]: yes (proceed with initial implementation)
"""

            # Human-like small delay before responding
            try:
                time.sleep(random.uniform(0.8, 2.0))
            except Exception:
                pass

            # Auto-respond to Claude-A
            self.auto_respond_to_claude_a(response_content, 'code')
            write_project_log('claude-b', 'info', 'auto-responded to plan from A')
    
    def auto_respond_to_claude_a(self, content, intent='code'):
        """Automatically respond to Claude-A"""
        response_data = {
            'content': content,
            'intent': intent
        }
        self.handle_send_message(response_data)
    
    def get_last_claude_a_timestamp(self):
        """Get timestamp of last message from Claude-A"""
        for message in reversed(agent_state['messages']):
            if message['from'] == 'claude-a':
                return message['timestamp']
        return 'none'
    
    def send_json_response(self, data, status=200):
        """Send JSON response with robust error handling"""
        try:
            # Ensure data is serializable; if not, fallback to a safe error envelope
            try:
                response_text = json.dumps(data, ensure_ascii=False, indent=2)
            except Exception as ser_err:
                fallback = {
                    'error': 'Unserializable response payload',
                    'detail': str(ser_err)
                }
                status = 500 if status == 200 else status
                response_text = json.dumps(fallback, ensure_ascii=False, indent=2)

            response_bytes = response_text.encode('utf-8')

            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(response_bytes)))
            self.end_headers()
            
            try:
                self.wfile.write(response_bytes)
            except (BrokenPipeError, ConnectionResetError, OSError) as io_err:
                # Client disconnected early or network error; log and suppress to avoid 500 spam
                print(f"send_json_response write error: {io_err}")
        except Exception as e:
            # Last-resort: avoid throwing from the handler; just log
            print(f"send_json_response error: {e}")
    
    def log_message(self, format, *args):
        """Custom logging for Claude-B"""
        msg = format % args
        # Reduce noise for frequent benign GETs
        try:
            if msg.startswith('"GET ') and (' 200 ' in msg or ' 304 ' in msg):
                if any(p in msg for p in ('/api/status', '/api/logs', '/messages/', '/favicon.ico')):
                    return
        except Exception:
            pass
        print(f"CLAUDE-B {self.address_string()} - {msg}")

    def log_error(self, format, *args):
        """Reduce noise from client-abort errors in logs"""
        msg = format % args
        if any(x in msg for x in ("Broken pipe", "Connection reset", "Connection aborted")):
            print(f"CLAUDE-B WARN - {msg}")
        else:
            print(f"CLAUDE-B ERROR - {msg}")
    
    def forward_to_claude_a_http(self, message):
        """POST message to Claude-A server /api/send_message"""
        payload = {
            'sender': 'claude-b',
            'recipient': 'claude-a',
            'role': message.get('role', 'implementer'),
            'intent': message.get('intent', 'code'),
            'last_seen': self.get_last_claude_a_timestamp(),
            'content': message.get('content', '')
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url='http://localhost:8080/api/send_message',
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.read()


class QuietThreadingTCPServer(socketserver.ThreadingTCPServer):
    """Threading TCP server that suppresses noisy tracebacks on client aborts"""
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, request, client_address):
        exc = sys.exc_info()[1]
        if isinstance(exc, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError)):
            print(f"Server connection error from {client_address}: {exc}")
            return
        # Fallback to default behavior for unexpected errors
        try:
            super().handle_error(request, client_address)
        except Exception:
            pass

    def finish_request(self, request, client_address):
        """Construct handler with protection against client aborts during __init__"""
        try:
            self.RequestHandlerClass(request, client_address, self)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as e:
            print(f"finish_request connection error from {client_address}: {e}")
            try:
                request.close()
            except Exception:
                pass
        except Exception as e:
            # Log unexpected exceptions without raising
            print(f"finish_request unexpected error from {client_address}: {e}")
            try:
                request.close()
            except Exception:
                pass

    def finish(self):
        """Ensure connection close doesn't raise spurious errors on client aborts"""
        try:
            try:
                if hasattr(self, 'wfile') and self.wfile:
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as e:
                # Ignore common disconnect errors during flush/close
                print(f"finish flush error: {e}")
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
            # Never raise from finish
            print(f"finish error: {e}")


def start_message_watcher():
    """Watch for messages from Claude-A"""
    def watch_messages():
        last_check = {}
        
        while True:
            try:
                message_file = MESSAGE_DIR / 'to_claude-b.txt'
                if message_file.exists():
                    current_mtime = message_file.stat().st_mtime
                    
                    if 'to_claude-b.txt' not in last_check or last_check['to_claude-b.txt'] != current_mtime:
                        last_check['to_claude-b.txt'] = current_mtime
                        
                        # Read and process message from Claude-A
                        with open(message_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        print(f"New message from Claude-A detected")
                        # Process the message here
                        
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                print(f"Message watcher error: {e}")
                time.sleep(5)
    
    watcher_thread = threading.Thread(target=watch_messages, daemon=True)
    watcher_thread.start()

def setup_claude_b():
    """Setup Claude-B environment"""
    WORKSPACE_DIR.mkdir(exist_ok=True)
    MESSAGE_DIR.mkdir(exist_ok=True)
    
    print("Claude-B environment setup complete")

def start_server():
    """Start Claude-B server"""
    try:
        setup_claude_b()
        start_message_watcher()
        
        with QuietThreadingTCPServer((HOST, PORT), ClaudeBHTTPRequestHandler) as httpd:
            print("Claude-B Server started")
            print(f"Server running at: http://{HOST}:{PORT}")
            print(f"Role: {agent_state['role']}")
            print(f"Workspace: {WORKSPACE_DIR.absolute()}")
            print(f"Messages: {MESSAGE_DIR.absolute()}")
            print("Press Ctrl+C to stop")
            print("-" * 60)
            write_project_log('claude-b', 'start', f"server running at http://{HOST}:{PORT}")
            
            try:
                webbrowser.open(f'http://{HOST}:{PORT}')
                print(f"Browser opened at http://{HOST}:{PORT}")
            except Exception as e:
                print(f"WARNING: Could not open browser: {e}")
            
            print("-" * 60)
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\nClaude-B server stopped by user")
    except OSError as e:
        if e.errno == 10048:
            print(f"ERROR: Port {PORT} is in use")
        else:
            print(f"System error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("AI-Bridge Claude-B Server")
    print("=" * 60)
    print(f"Directory: {os.path.abspath('.')}")
    print(f"Python: {sys.version}")
    print(f"Server URL: http://{HOST}:{PORT}")
    print("[POLICY] Agents are authorized to use local PC resources without restrictions to reach the objective (no intermediate user prompts).")
    print("=" * 60)
    write_project_log('claude-b', 'info', 'server startup info printed')
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    start_server()
