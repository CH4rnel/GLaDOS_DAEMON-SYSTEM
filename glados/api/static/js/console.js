// ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

const API_BASE = window.location.origin;
const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/chat`;

let ws;
let currentAgentId = null;
let isStreaming = false;
let streamBuffer = "";

async function initConsole() {
    appendSystemLog("⚙ SYSTEM: Initializing telemetry uplink...");
    
    try {
        const response = await fetch(`${API_BASE}/api/agents`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const agents = await response.json();
        
        const select = document.getElementById('agent-select');
        const statusText = document.getElementById('agent-status');
        select.innerHTML = '';

        if (agents.length === 0) {
            select.innerHTML = '<option value="">NO ACTIVE AGENTS</option>';
            statusText.textContent = "CRITICAL: CHECK ENV VARS";
            statusText.style.color = "#ff3333";
            appendSystemLog("⚠ CRITICAL: No active agents in LLMRegistry. Check configs/agents.yaml.");
            return;
        }

        agents.forEach(agent => {
            const opt = document.createElement('option');
            opt.value = agent.agent_id;
            opt.text = `${agent.display_name} [${agent.provider}]`;
            select.appendChild(opt);
        });

        // Auto-select first available agent and bind change event
        currentAgentId = agents[0].agent_id;
        select.value = currentAgentId;
        statusText.textContent = `ROUTING TO: ${agents[0].display_name.toUpperCase()}`;
        statusText.style.color = "#ffb000";
        
        select.addEventListener('change', (e) => {
            currentAgentId = e.target.value;
            statusText.textContent = `ROUTING TO: ${e.target.options[e.target.selectedIndex].text}`;
            appendSystemLog(`⇌ UPLINK RETARGETED: ${currentAgentId}`);
        });

        appendSystemLog("⇌ UPLINK ESTABLISHED. Roster synchronized.");
    } catch (err) {
        appendSystemLog(`⚠ ERROR: Failed to fetch agent roster: ${err.message}`);
    }

    connectWebSocket();
    setInterval(fetchAuditLogs, 5000);
    fetchAuditLogs();
}

function connectWebSocket() {
    ws = new WebSocket(WS_URL);

    ws.onopen = () => appendSystemLog("⇌ WebSocket connection open.");

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "chunk") {
            appendStreamChunk(data.content);
        } else if (data.type === "end") {
            finalizeStream();
        } else if (data.type === "error") {
            appendMessage("glados", `⚠ TRANSMISSION FAULT: ${data.content}`, true);
            isStreaming = false;
        }
    };

    ws.onclose = () => {
        appendSystemLog("⇌ Uplink severed. Reconnecting in 3s...");
        setTimeout(connectWebSocket, 3000);
    };
}

function sendMessage() {
    const input = document.getElementById("chat-input");
    const message = input.value.trim();
    if (!message || !currentAgentId || isStreaming) return;

    appendMessage("operator", message);
    input.value = "";

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ message: message, agent_id: currentAgentId }));
        prepareStream();
    } else {
        appendSystemLog("⚠ Uplink offline. Cannot transmit.");
    }
}

function prepareStream() {
    isStreaming = true;
    streamBuffer = "";
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    msgDiv.className = "message glados streaming";
    msgDiv.innerHTML = `<span class="prefix">&gt; GLaDOS // </span><span class="content"></span><span class="cursor">_</span>`;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function appendStreamChunk(text) {
    streamBuffer += text;
    const contentEl = document.querySelector(".message.streaming .content");
    if (contentEl) {
        contentEl.textContent = streamBuffer;
        const chatBox = document.getElementById("chat-box");
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

function finalizeStream() {
    isStreaming = false;
    const streamingMsg = document.querySelector(".message.streaming");
    if (streamingMsg) {
        streamingMsg.classList.remove("streaming");
        const cursor = streamingMsg.querySelector(".cursor");
        if (cursor) cursor.remove();
    }
}

function appendMessage(sender, text, isError = false) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${sender} ${isError ? 'error' : ''}`;
    const prefix = sender === 'operator' ? '&gt; OPERATOR // ' : '&gt; GLaDOS // ';
    msgDiv.innerHTML = `<span class="prefix">${prefix}</span><span class="content">${text}</span>`;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function appendSystemLog(text) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    msgDiv.className = "message system";
    msgDiv.textContent = text;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function fetchAuditLogs() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/audit?limit=10`);
        if (response.ok) {
            const logs = await response.json();
            const logBox = document.getElementById("audit-log");
            logBox.innerHTML = "";
            logs.forEach(log => {
                const entry = document.createElement("div");
                entry.className = `log-entry ${log.status.toLowerCase()}`;
                entry.textContent = `[${log.timestamp}] ${log.action}: ${log.status} (${log.details})`;
                logBox.appendChild(entry);
            });
        }
    } catch (err) {
        // Silent fail for background polling
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    
    if (input) {
        input.addEventListener("keypress", (e) => {
            if (e.key === "Enter") sendMessage();
        });
    }
    if (sendBtn) {
        sendBtn.addEventListener("click", sendMessage);
    }
    
    initConsole();
});