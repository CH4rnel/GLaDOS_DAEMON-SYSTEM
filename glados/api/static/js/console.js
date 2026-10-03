// ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

const API_BASE = window.location.origin;
const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/chat`;

let ws;
let currentAgentId = null;
let isStreaming = false;
let streamBuffer = "";
let availableAgents = [];

async function initConsole() {
    appendSystemLog("⚙ SYSTEM: Initializing telemetry uplink...");
    
    try {
        
        const response = await fetch(`${API_BASE}/api/v1/agents`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        availableAgents = await response.json();
        
        const select = document.getElementById('agent-select');
        const statusText = document.getElementById('agent-status');
        const activationPanel = document.getElementById('activation-panel');
        select.innerHTML = '';

        if (availableAgents.length === 0) {
            select.innerHTML = '<option value="">NO AGENTS CONFIGURED</option>';
            if (statusText) {
                statusText.textContent = "CRITICAL: CHECK CONFIGS";
                statusText.style.color = "#ff3333";
            }
            appendSystemLog("⚠ CRITICAL: No agents found. Check configs/agents.yaml.");
            return;
        }

        let firstActiveAgent = null;

        availableAgents.forEach(agent => {
            const opt = document.createElement('option');
            opt.value = agent.agent_id;
            const statusIcon = agent.is_active ? '🟢' : '🔴';
            const statusLabel = agent.is_active ? 'ONLINE' : 'OFFLINE (NO KEY)';
            opt.text = `${statusIcon} ${agent.display_name} [${agent.provider}] - ${statusLabel}`;
            opt.dataset.isActive = agent.is_active;
            
            if (!agent.is_active) {
                opt.style.color = "#888";
            } else if (!firstActiveAgent) {
                firstActiveAgent = agent;
            }
            
            select.appendChild(opt);
        });

        if (firstActiveAgent) {
            currentAgentId = firstActiveAgent.agent_id;
            select.value = currentAgentId;
            updateRoutingStatus();
            if (activationPanel) activationPanel.style.display = 'none';
        } else {
            if (statusText) {
                statusText.textContent = "NO AGENTS AVAILABLE (CHECK API KEYS)";
                statusText.style.color = "#ff3333";
            }
            if (activationPanel) activationPanel.style.display = 'none';
        }
        
        select.addEventListener('change', (e) => {
            currentAgentId = e.target.value;
            const selectedOpt = e.target.options[e.target.selectedIndex];
            const isActive = selectedOpt.dataset.isActive === 'true';
            
            updateRoutingStatus();
            
            if (activationPanel) {
                if (!isActive) {
                    activationPanel.style.display = 'block';
                    const keyInput = document.getElementById('api-key-input');
                    const statusEl = document.getElementById('activation-status');
                    if (keyInput) keyInput.value = '';
                    if (statusEl) {
                        statusEl.textContent = 'Enter API key to activate this agent.';
                        statusEl.style.color = "#ffb000";
                    }
                    if (keyInput) keyInput.focus();
                } else {
                    activationPanel.style.display = 'none';
                }
            }
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

function updateRoutingStatus() {
    const statusText = document.getElementById('agent-status');
    const agent = availableAgents.find(a => a.agent_id === currentAgentId);
    if (agent && statusText) {
        const statusLabel = agent.is_active ? 'ONLINE' : 'OFFLINE';
        statusText.textContent = `ROUTING TO: ${agent.display_name.toUpperCase()} [${agent.provider}] (${statusLabel})`;
        statusText.style.color = agent.is_active ? "#ffb000" : "#ff3333";
    }
}

async function activateCurrentAgent() {
    const apiKeyInput = document.getElementById('api-key-input');
    const statusEl = document.getElementById('activation-status');
    const apiKey = apiKeyInput ? apiKeyInput.value.trim() : '';

    if (!apiKey) {
        if (statusEl) {
            statusEl.textContent = "ERROR: API key cannot be empty";
            statusEl.style.color = "#ff3333";
        }
        return;
    }

    if (statusEl) {
        statusEl.textContent = "VALIDATING AND ESTABLISHING UPLINK...";
        statusEl.style.color = "#ffb000";
    }

    try {
        const response = await fetch(`${API_BASE}/api/v1/agents/${currentAgentId}/activate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey })
        });

        const data = await response.json();

        if (response.ok) {
            if (statusEl) {
                statusEl.textContent = "UPLINK ESTABLISHED SUCCESSFULLY";
                statusEl.style.color = "#00ff00";
            }
            
            const agent = availableAgents.find(a => a.agent_id === currentAgentId);
            if (agent) agent.is_active = true;
            
            const selectedOpt = document.querySelector(`#agent-select option[value="${currentAgentId}"]`);
            if (selectedOpt) {
                selectedOpt.dataset.isActive = 'true';
                selectedOpt.style.color = "";
                selectedOpt.text = `🟢 ${agent.display_name} [${agent.provider}] - ONLINE`;
            }

            setTimeout(() => {
                const activationPanel = document.getElementById('activation-panel');
                if (activationPanel) activationPanel.style.display = 'none';
                updateRoutingStatus();
            }, 1500);
            
            appendSystemLog(`✅ AGENT ACTIVATED: ${currentAgentId}`);
        } else {
            if (statusEl) {
                statusEl.textContent = `ERROR: ${data.detail || 'Activation failed'}`;
                statusEl.style.color = "#ff3333";
            }
            appendSystemLog(`⚠ ACTIVATION DENIED: ${currentAgentId} - ${data.detail}`);
        }
    } catch (err) {
        if (statusEl) {
            statusEl.textContent = "ERROR: Network failure during activation";
            statusEl.style.color = "#ff3333";
        }
        appendSystemLog(`⚠ ACTIVATION NETWORK ERROR: ${err.message}`);
    }
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
    const message = input ? input.value.trim() : "";
    if (!message || !currentAgentId || isStreaming) return;

    const agent = availableAgents.find(a => a.agent_id === currentAgentId);
    if (agent && !agent.is_active) {
        appendSystemLog(`⚠ TRANSMISSION BLOCKED: Agent ${currentAgentId} is not active. Activate it first.`);
        return;
    }

    appendMessage("operator", message);
    if (input) input.value = "";

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
            if (!logBox) return;
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
    const activateBtn = document.getElementById("activate-btn");
    
    if (input) {
        input.addEventListener("keypress", (e) => {
            if (e.key === "Enter") sendMessage();
        });
    }
    if (sendBtn) {
        sendBtn.addEventListener("click", sendMessage);
    }
    if (activateBtn) {
        activateBtn.addEventListener("click", activateCurrentAgent);
    }
    
    initConsole();
});