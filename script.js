// AI-Bridge JavaScript - REAL DUAL AGENT VERSION
// No fake messages - Only real Claude-A and Claude-B communication

// Global state for automated session
let automatedSession = {
    isRunning: false,
    currentIteration: 0,
    maxIterations: 10,
    messageDelay: 3000,
    conversationHistory: [],
    mode: 'specialized',
    roles: { 'claude-a': 'controller', 'claude-b': 'executor' },
    serverCount: 0
};

// Generate current timestamp
function generateTimestamp() {
    const now = new Date().toISOString();
    document.getElementById('current-timestamp').textContent = now;
    document.getElementById('system-time').textContent = now;
    return now;
}

// Update timestamp on page load
document.addEventListener('DOMContentLoaded', function() {
    generateTimestamp();
    setInterval(generateTimestamp, 60000); // Update every minute
    loadObjective();
    initializeRoleSystem();
    updateAgentTitles();
    startMessagePolling();
    // Default gating: auto-approve (policy: no prompts)
    try { setYesAll('claude-a', true); setYesAll('claude-b', true); } catch (e) {}
    fetchMetrics();
    setInterval(fetchMetrics, 2000);
});

// Save objective to localStorage
function saveObjective() {
    const objective = document.getElementById('objective').value;
    if (objective.trim() === '') {
        showNotification('Por favor escribe un objetivo', 'error');
        return;
    }
    
    localStorage.setItem('aibridge_objective', objective);
    showNotification('Objetivo guardado exitosamente', 'success');
}

// Load objective from localStorage
function loadObjective() {
    const savedObjective = localStorage.getItem('aibridge_objective');
    if (savedObjective) {
        document.getElementById('objective').value = savedObjective;
    }
}

// Copy text to clipboard
async function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    const text = element.value;
    
    if (text.trim() === '') {
        showNotification('No hay contenido para copiar', 'error');
        return;
    }
    
    try {
        await navigator.clipboard.writeText(text);
        showNotification('Mensaje copiado al portapapeles', 'success');
    } catch (err) {
        showNotification('Error al copiar al portapapeles', 'error');
    }
}

// Clear message
function clearMessage(elementId) {
    const element = document.getElementById(elementId);
    element.value = '';
    showNotification('Mensaje borrado', 'success');
}

// Load from file - REAL FILE LOADING
async function loadFromFile(filename, elementId) {
    try {
        const response = await fetch(`/messages/${filename}`);
        if (response.ok) {
            const content = await response.text();
            document.getElementById(elementId).value = content;
            showNotification(`Contenido cargado desde ${filename}`, 'success');
        } else {
            showNotification(`No se pudo cargar ${filename}`, 'error');
        }
    } catch (error) {
        showNotification('Error cargando archivo', 'error');
    }
}

// Copy protocol template
function copyTemplate() {
    const template = document.getElementById('protocol-template').textContent;
    navigator.clipboard.writeText(template).then(() => {
        showNotification('Plantilla copiada al portapapeles', 'success');
    });
}

// Create startup prompt
function createStartupPrompt() {
    const objective = document.getElementById('objective').value;
    
    if (objective.trim() === '') {
        showNotification('Primero define un objetivo', 'error');
        return;
    }
    
    const startupPrompt = `OBJETIVO: ${objective}

CONFIGURACION DUAL-AGENT:
- Claude-A (Controller): coordina y supervisa
- Claude-B (Executor): implementa y responde
- Workspace compartido: C:\\ai-bridge\\workspace\\
- Comunicacion via archivos: to_claude-b.txt / from_claude-b.txt

INSTRUCCIONES:
1. Define arquitectura y division de trabajo
2. Cada agente crea archivos en su especialidad
3. Revision cruzada y mejoras iterativas
4. Testing conjunto del sistema completo

FORMATO MENSAJES:
[TIMESTAMP]: ${generateTimestamp()}
[FROM]: Claude-A|Claude-B
[TO]: Claude-B|Claude-A
[ROLE]: Controller|Executor
[INTENT]: plan|design|code|review|test|done
[PAYLOAD]: (mensaje real)`;

    navigator.clipboard.writeText(startupPrompt).then(() => {
        showNotification('Prompt inicial copiado al portapapeles', 'success');
    });
}

// Open workspace
function openWorkspace() {
    showNotification('Workspace: C:\\ai-bridge\\workspace\\', 'success');
}

// View logs
function viewLogs() {
    pollForMessages();
    showNotification('Logs actualizados', 'success');
}

// Open project log in new tab for quick inspection
function openProjectLog() {
    window.open('/api/logs?tail=500', '_blank');
}

// Apply file bundle from pasted JSON
async function applyFileBundlePrompt(defaultBaseDir = 'prueba3') {
    try {
        const example = {
            base_dir: defaultBaseDir,
            files: [
                { path: 'README.md', content: '# Proyecto' },
                { path: 'src/app.py', content: 'print("hola")' }
            ]
        };
        const input = prompt('Pega JSON de bundle de archivos (se guardará bajo workspace/' + defaultBaseDir + '):', JSON.stringify(example, null, 2));
        if (!input) return;
        const payload = JSON.parse(input);
        const resp = await fetch('/api/apply_file_bundle', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        const data = await resp.json();
        if (data.success) {
            showNotification('Archivos creados: ' + (data.created?.length || 0), 'success');
        } else {
            showNotification('Error: ' + (data.error || 'fallo aplicando bundle'), 'error');
        }
    } catch (e) {
        showNotification('Error parseando/aplicando bundle: ' + e.message, 'error');
    }
}

// Gating: yes_all toggles
async function setYesAll(agent, value){
    try{
        await fetch('/api/set_yes_all', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({agent, value}) });
    }catch(e){ console.warn('setYesAll failed', e); }
}

// Start automated session - REAL VERSION
async function startAutomatedSession() {
    const objective = document.getElementById('objective').value.trim();
    if (!objective) {
        showNotification('Define un objetivo antes de iniciar', 'error');
        return;
    }

    // Get configuration
    automatedSession.mode = document.querySelector('input[name="interaction-mode"]:checked').value;
    automatedSession.roles['claude-a'] = document.getElementById('claude-role').value;
    automatedSession.roles['claude-b'] = document.getElementById('claude-b-role').value;
    automatedSession.maxIterations = parseInt(document.getElementById('max-iterations').value);
    automatedSession.messageDelay = parseInt(document.getElementById('message-delay').value) * 1000;
    
    // Reset session state
    automatedSession.isRunning = true;
    automatedSession.currentIteration = 0;
    automatedSession.conversationHistory = [];
    automatedSession.serverCount = 0;

    // Update UI
    document.getElementById('run-btn').style.display = 'none';
    document.getElementById('stop-btn').style.display = 'inline-block';
    document.getElementById('system-status').innerHTML = '[ACTIVE] Sesion en curso';

    // Start session via API
    try {
        const startResp = await fetch('/api/start_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                objective, 
                mode: automatedSession.mode, 
                roles: automatedSession.roles 
            })
        });
        if (!startResp.ok) throw new Error('No se pudo iniciar la sesión');
        
        addConversationMessage('system', '[SISTEMA]', 
            `Sesion automatizada iniciada REAL
Modo: ${automatedSession.mode}
Claude-A: ${automatedSession.roles['claude-a']}
Claude-B: ${automatedSession.roles['claude-b']}
Objetivo: ${objective}

Workspace: C:\\ai-bridge\\workspace\\
Messages: C:\\ai-bridge\\messages\\

Comunicacion real entre Claude-A y Claude-B iniciada.`);

        // Enviar primer mensaje (plan) de Claude-A -> Claude-B basado en el objetivo
        const initialPlan = `OBJETIVO: ${objective}\n\n[INTENT]: plan\n[PAYLOAD]:\nPor favor, analiza el objetivo y responde con:\n- division de tareas breve\n- primeros pasos para controller y executor\n- dudas si las hay`;
        try {
            const sendResp = await fetch('/api/send_message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sender: 'claude-a',
                    recipient: 'claude-b',
                    role: automatedSession.roles['claude-a'] || 'controller',
                    intent: 'plan',
                    last_seen: 'none',
                    content: initialPlan
                })
            });
            const sendJson = await sendResp.json();
            if (sendJson.success) {
                addConversationMessage('claude-a', getAgentDisplayName('claude-a'), initialPlan);
                showNotification('Primer mensaje enviado a Claude-B', 'success');
            }
        } catch (e) {
            console.error('No se pudo enviar el primer mensaje:', e);
        }

        showNotification('Sesion REAL automatizada iniciada', 'success');
        
    } catch (error) {
        showNotification('Error iniciando sesion: ' + error.message, 'error');
    }
}

// Stop automated session
function stopAutomatedSession() {
    automatedSession.isRunning = false;
    
    // Update UI
    document.getElementById('run-btn').style.display = 'inline-block';
    document.getElementById('stop-btn').style.display = 'none';
    document.getElementById('system-status').innerHTML = '[READY] Listo';
    
    addConversationMessage('system', '[SISTEMA]', 'Sesion automatizada detenida por el usuario.');
    showNotification('Sesion automatizada detenida', 'success');
}

// Send message - REAL VERSION
async function sendMessage(agent) {
    const messageElement = document.getElementById(agent + '-message');
    const message = messageElement.value.trim();
    
    if (!message) {
        showNotification('Escribe un mensaje primero', 'error');
        return;
    }
    
    try {
        // Send real message to peer server
        const response = await fetch('/api/send_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sender: agent === 'claude' ? 'claude-a' : 'claude-b',
                recipient: agent === 'claude' ? 'claude-b' : 'claude-a', 
                content: message,
                role: automatedSession.roles[agent === 'claude' ? 'claude-a' : 'claude-b'],
                intent: 'manual'
            })
        });
        
        const result = await response.json();
        if (result.success) {
            addConversationMessage(agent, getAgentDisplayName(agent), message);
            messageElement.value = '';
            showNotification(`Mensaje REAL enviado desde ${agent}`, 'success');
        } else {
            throw new Error(result.error || 'Failed to send message');
        }
    } catch (error) {
        showNotification('Error enviando mensaje: ' + error.message, 'error');
    }
}

// Poll for real messages
async function pollForMessages() {
    if (!automatedSession.isRunning) return;
    
    try {
        const response = await fetch('/api/messages');
        const result = await response.json();
        const total = result.count ?? (result.messages ? result.messages.length : 0);
        const prev = automatedSession.serverCount || 0;
        if (result.messages && total > prev) {
            const newMessages = result.messages.slice(prev);
            newMessages.forEach(msg => {
                if (msg.sender !== 'system') {
                    const senderKey = (msg.sender && msg.sender.indexOf('claude-a') !== -1) ? 'claude-a' : 'claude-b';
                    addConversationMessage(senderKey, getAgentDisplayName(senderKey), msg.content);
                }
            });
            automatedSession.serverCount = total;
        }
    } catch (error) {
        console.error('Error polling messages:', error);
    }
}

// Start message polling
function startMessagePolling() {
    setInterval(pollForMessages, 3000); // Poll every 3 seconds
}

// Fetch metrics for monitoring panel
async function fetchMetrics() {
    try {
        const resp = await fetch('/api/metrics');
        if (!resp.ok) return;
        const data = await resp.json();
        document.getElementById('metric-message-count').textContent = data.message_count ?? 0;
        document.getElementById('metric-mpm').textContent = data.messages_per_minute ?? 0;
        document.getElementById('metric-repeat-count').textContent = data.repeat_count ?? 0;
    } catch (e) {
        console.warn('metrics fetch failed', e);
    }
}

// Add message to conversation
function addConversationMessage(sender, senderName, content) {
    const conversationLog = document.getElementById('conversation-log');
    const timestamp = new Date().toISOString();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `conversation-message ${sender}`;
    
    const senderIcon = {
        'claude-a': '[A]',
        'claude-b': '[B]', 
        'system': '[SYS]'
    }[sender] || '[MSG]';
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="sender">${senderIcon} ${senderName}</span>
            <span class="timestamp">${timestamp}</span>
        </div>
        <div class="message-content">${content}</div>
    `;
    
    conversationLog.appendChild(messageDiv);
    scrollToBottom();
    
    // Store in history
    automatedSession.conversationHistory.push({ sender, senderName, content, timestamp });
}

// Helper functions
function getAgentDisplayName(agent) {
    if (agent.includes('claude-a') || agent === 'claude') {
        return `Claude-A (${automatedSession.roles['claude-a'] || 'Controller'})`;
    } else if (agent.includes('claude-b') || agent === 'codex') {
        return `Claude-B (${automatedSession.roles['claude-b'] || 'Executor'})`;
    }
    return agent;
}

// Clear conversation
function clearConversation() {
    const conversationLog = document.getElementById('conversation-log');
    conversationLog.innerHTML = `
        <div class="conversation-message system">
            <div class="message-header">
                <span class="sender">[SYS] Sistema</span>
                <span class="timestamp">${new Date().toISOString()}</span>
            </div>
            <div class="message-content">
                Conversacion limpiada. Sistema listo para nueva sesion Claude-A y Claude-B.
            </div>
        </div>
    `;
    
    automatedSession.conversationHistory = [];
    showNotification('Conversacion limpiada', 'success');
}

// Export conversation
function exportConversation() {
    if (automatedSession.conversationHistory.length === 0) {
        showNotification('No hay conversacion para exportar', 'error');
        return;
    }
    
    let exportText = `AI-Bridge Dual Agent Conversation Export\n`;
    exportText += `Generated: ${new Date().toISOString()}\n`;
    exportText += `Mode: ${automatedSession.mode}\n`;
    exportText += `Claude-A Role: ${automatedSession.roles['claude-a']}\n`;
    exportText += `Claude-B Role: ${automatedSession.roles['claude-b']}\n\n`;
    
    automatedSession.conversationHistory.forEach((msg, index) => {
        exportText += `Message ${index + 1}:\n`;
        exportText += `From: ${msg.senderName}\n`;
        exportText += `Time: ${msg.timestamp}\n`;
        exportText += `Content:\n${msg.content}\n\n`;
        exportText += '-'.repeat(50) + '\n\n';
    });
    
    // Create download
    const blob = new Blob([exportText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `aibridge-dual-agent-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification('Conversacion exportada', 'success');
}

// Scroll to bottom
function scrollToBottom() {
    const conversationLog = document.getElementById('conversation-log');
    conversationLog.scrollTop = conversationLog.scrollHeight;
}

// Role system management
function initializeRoleSystem() {
    document.getElementById('claude-role').addEventListener('change', updateAgentTitles);
    document.getElementById('claude-b-role').addEventListener('change', updateAgentTitles);
}

function updateAgentTitles() {
    const claudeARole = document.getElementById('claude-role').value;
    const claudeBRole = document.getElementById('claude-b-role').value;

    const roleNames = {
        controller: 'Controller',
        executor: 'Executor'
    };

    document.getElementById('claude-title').innerHTML = `[A] Claude-A (${roleNames[claudeARole]})`;
    document.getElementById('codex-title').innerHTML = `[B] Claude-B (${roleNames[claudeBRole]})`;
}

// Notification system
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">×</button>
    `;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#48bb78' : '#f56565'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        z-index: 1000;
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 400px;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 3000);
}
