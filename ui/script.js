const messagesContainer = document.getElementById('messages');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const toolInvocationsList = document.getElementById('toolInvocationsList');
const leftSidebar = document.getElementById('leftSidebar');
const rightSidebar = document.getElementById('rightSidebar');
const toggleLeftSidebar = document.getElementById('toggleLeftSidebar');
const toggleRightSidebar = document.getElementById('toggleRightSidebar');
const newChatBtn = document.getElementById('newChatBtn');

let messages = [];
let toolInvocations = [];
let isStreaming = false;

// Sidebar toggle for mobile
toggleLeftSidebar.addEventListener('click', () => {
    leftSidebar.classList.toggle('hidden');
});

toggleRightSidebar.addEventListener('click', () => {
    rightSidebar.classList.toggle('hidden');
});

// New chat button
newChatBtn.addEventListener('click', () => {
    messages = [];
    toolInvocations = [];
    messagesContainer.innerHTML = `
        <div class="max-w-3xl mx-auto">
            <div class="text-center py-24">
                <h2 class="text-4xl font-bold mb-3" style="color: var(--text-primary)">Deep Insights Copilot</h2>
                <p class="text-lg" style="color: var(--text-secondary)">How can I help you today?</p>
            </div>
        </div>
    `;
    renderToolInvocations();
});

// Auto-resize textarea
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 200) + 'px';
});

// Handle form submission
chatForm.addEventListener('submit', async function(e) {
    e.preventDefault(); // Prevent page refresh
    e.stopPropagation(); // Stop event bubbling
    
    console.log('=== Form Submitted ===');
    
    const content = messageInput.value.trim();
    
    if (!content) {
        console.log('Empty message, ignoring');
        return;
    }

    console.log('User message:', content);

    // Add user message
    addMessage('user', content);
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Disable input
    messageInput.disabled = true;
    sendButton.disabled = true;

    try {
        await simulateAIResponse(content);
    } catch (error) {
        console.error('=== Critical Error in Form Submission ===');
        console.error('Error:', error);
        console.error('Stack:', error.stack);
        
        // Add error message
        addMessage('assistant', '❌ Critical error occurred. Check browser console for details.');
    } finally {
        // Always re-enable input
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
        console.log('=== Form Processing Complete ===');
    }
});

function addMessage(role, content) {
    messages.push({ role, content, timestamp: new Date() });
    renderMessages();
}

function renderMessages() {
    if (messages.length === 1) {
        messagesContainer.innerHTML = '<div class="max-w-3xl mx-auto"></div>';
    }

    const container = messagesContainer.querySelector('.max-w-3xl');
    container.innerHTML = messages.map((msg, index) => {
        const isLastMessage = index === messages.length - 1;
        const showCursor = isStreaming && isLastMessage && msg.role === 'assistant';
        
        return `
            <div class="${msg.role === 'user' ? 'message-user' : 'message-ai'} px-6 py-8">
                <div class="max-w-3xl mx-auto flex gap-6">
                    <div class="flex-shrink-0">
                        <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold" style="background: ${msg.role === 'user' ? 'var(--accent)' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'}; color: white">
                            ${msg.role === 'user' ? 'U' : 'AI'}
                        </div>
                    </div>
                    <div class="flex-1 pt-1 whitespace-pre-wrap ${showCursor ? 'streaming-cursor' : ''}" style="color: var(--text-primary); line-height: 1.7">${escapeHtml(msg.content)}</div>
                </div>
            </div>
        `;
    }).join('');

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addToolInvocation(toolName, params, result, duration) {
    toolInvocations.push({
        toolName,
        params,
        result,
        duration,
        timestamp: new Date()
    });
    renderToolInvocations();
}

function renderToolInvocations() {
    const totalInvocations = document.getElementById('totalInvocations');
    const sessionInvocations = document.getElementById('sessionInvocations');
    
    totalInvocations.textContent = toolInvocations.length;
    sessionInvocations.textContent = toolInvocations.length;

    if (toolInvocations.length === 0) {
        toolInvocationsList.innerHTML = `
            <div class="text-sm text-center py-12" style="color: var(--text-secondary)">
                No tool invocations yet
            </div>
        `;
        return;
    }

    toolInvocationsList.innerHTML = toolInvocations.map((inv, index) => `
        <div class="tool-card rounded-xl p-4 fade-in max-h-[400px]">
            <div class="flex items-center justify-between mb-3">
                <span class="font-semibold text-sm" style="color: var(--text-primary)">${escapeHtml(inv.toolName)}</span>
                <span class="text-xs px-2 py-1 rounded" style="background: var(--bg-hover); color: var(--text-secondary)">${inv.duration}</span>
            </div>
            <div class="text-xs mb-3" style="color: var(--text-secondary)">
                <div class="font-medium mb-1.5" style="color: var(--text-secondary)">Parameters</div>
                <pre class="p-2.5 rounded-lg overflow-x-auto" style="background: var(--bg-primary); color: var(--text-secondary); font-size: 11px">${escapeHtml(JSON.stringify(inv.params, null, 2))}</pre>
            </div>
            <div class="text-xs" style="color: var(--text-secondary)">
                <div class="font-medium mb-1.5" style="color: var(--text-secondary)">Result</div>
                <div class="p-2.5 rounded-lg max-h-32 overflow-auto" style="background: var(--bg-primary); color: var(--text-secondary)">${escapeHtml(inv.result)}</div>
            </div>
            <div class="text-xs mt-3 pt-3 border-t" style="color: #555; border-color: var(--border-color)">
                ${inv.timestamp.toLocaleTimeString()}
            </div>
        </div>
    `).reverse().join('');
}

async function simulateAIResponse(userMessage) {
    try {
        // Call real backend API with streaming
        const response = await fetch('http://localhost:8001/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                conversation_id: `conv_${Date.now()}`,
                question: userMessage,
                stream: true,
                user_id: "user_001"
            })
        });

        if (!response.ok) {
            throw new Error('Failed to get response from server');
        }

        // Handle streaming response
        await handleStreamingResponse(response);

    } catch (error) {
        console.error('Error calling backend:', error);
        
        // Fallback to demo mode if backend is not available
        await simulateDemoResponse(userMessage);
    }
}

async function handleStreamingResponse(response) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    let streamedContent = '';
    let buffer = ''; // Buffer for incomplete chunks
    
    // Add initial assistant message placeholder
    const messageIndex = messages.length;
    addMessage('assistant', '');
    
    // Start streaming
    isStreaming = true;
    
    try {
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
                console.log('Stream completed successfully');
                break;
            }
            
            // Decode the chunk and add to buffer
            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;
            
            // Split by newlines
            const lines = buffer.split('\n');
            
            // Keep the last incomplete line in buffer
            buffer = lines.pop() || '';
            
            // Process each complete line
            for (const line of lines) {
                // Skip empty lines
                if (!line.trim()) continue;
                
                if (line.startsWith('data: ')) {
                    try {
                        const jsonStr = line.slice(6).trim(); // Remove 'data: ' prefix
                        
                        // Skip empty data
                        if (!jsonStr) continue;
                        
                        // console.log('Parsing SSE:', jsonStr.substring(0, 100)); // Debug log (truncated)
                        
                        const data = JSON.parse(jsonStr);
                        
                        if (data.type === 'status') {
                            console.log('Status:', data.content);
                            
                        } else if (data.type === 'text') {
                            // Append text chunk
                            streamedContent += data.content;
                            
                            // Update the message in real-time
                            messages[messageIndex].content = streamedContent;
                            renderMessages();
                            
                        } else if (data.type === 'tool_call') {
                            console.log('Tool call received:', data.data?.tool_name);
                            
                            // Extract tool invocation data properly
                            const toolData = data.data || {};
                            const toolName = toolData.tool_name || 'unknown';
                            const params = toolData.parameters || {};
                            const resultData = toolData.result || {};
                            const executionTimeMs = resultData.execution_time_ms || 0;
                            const error = toolData.error || null;
                            
                            // Format result for display
                            let resultDisplay;
                            if (resultData.success) {
                                // If successful, show the actual result
                                resultDisplay = JSON.stringify(resultData.result || resultData, null, 2);
                            } else {
                                resultDisplay = resultData.error || 'No result';
                            }
                            
                            // Add tool invocation to sidebar
                            addToolInvocation(
                                toolName,
                                params,
                                resultDisplay,
                                `${executionTimeMs}ms`,
                                error
                            );
                            
                        } 
                        // for debugging
                        // else if (data.type === 'done') {
                        //     console.log('Response metadata:', data.data);
                        // }
                        
                    } catch (e) {
                        console.error('JSON Parse Error:', e);
                        console.error('Problematic line:', line);
                        // Don't break - continue processing other lines
                    }
                }
            }
        }
        
        // Check if we got any content
        if (!streamedContent.trim()) {
            console.warn('No content received from stream');
            messages[messageIndex].content = 'No response received. Please try again.';
            renderMessages();
        }
        
    } catch (error) {
        console.error('Stream reading error:', error);
        console.error('Error stack:', error.stack);
        
        // Update message with error
        if (streamedContent.trim()) {
            messages[messageIndex].content = streamedContent + '\n\n[Stream interrupted]';
        } else {
            messages[messageIndex].content = 'Error: Failed to receive response. Check console for details.';
        }
        renderMessages();
    } finally {
        // Always stop streaming and re-render
        isStreaming = false;
        renderMessages();
        console.log('Stream handling complete');
    }
}

async function simulateDemoResponse(userMessage) {
    // Demo mode fallback with simulated streaming
    const tools = ['kb.search', 'sql.query', 'kpi.top_root_causes'];
    const randomTool = tools[Math.floor(Math.random() * tools.length)];
    
    // Add tool invocation
    addToolInvocation(
        randomTool,
        { query: userMessage.substring(0, 50) },
        'Success: Retrieved relevant information (DEMO MODE)',
        Math.floor(Math.random() * 500 + 100)
    );

    const demoResponses = [
        "I currently do not have access to that specific data. My capabilities are focused on customer support ticket analysis, root cause identification, and customer behavior insights.",
        "Based on the available data, I can help you analyze customer tickets, identify patterns, and provide insights into support operations.",
        "To answer this question accurately, I would need access to the relevant database tables. However, I can help you construct the SQL query needed to retrieve this information.",
        "Let me search through the knowledge base for relevant information about this topic."
    ];

    const fullResponse = demoResponses[Math.floor(Math.random() * demoResponses.length)] + 
        "\n\n⚠️ Running in DEMO MODE - Connect to backend for real insights. Check the connection status indicators in the header.";

    // Simulate streaming effect
    const messageIndex = messages.length;
    addMessage('assistant', '');
    
    isStreaming = true;
    let currentText = '';
    const words = fullResponse.split(' ');
    
    for (let i = 0; i < words.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 50 + Math.random() * 50));
        currentText += (i > 0 ? ' ' : '') + words[i];
        messages[messageIndex].content = currentText;
        renderMessages();
    }
    
    isStreaming = false;
    renderMessages();
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Handle Enter key (submit) and Shift+Enter (new line)
messageInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

// Connection status checking
async function checkConnectionStatus() {
    const fastapiStatus = document.getElementById('fastapiStatus');
    const mcpStatus = document.getElementById('mcpStatus');
    
    // Check FastAPI on port 8001
    try {
        const fastapiResponse = await fetch('http://localhost:8001/health');
        updateStatusIndicator(fastapiStatus, fastapiResponse.ok);
    } catch (error) {
        updateStatusIndicator(fastapiStatus, false);
    }

    // Check MCP on port 8000
    try {
        const mcpResponse = await fetch('http://localhost:8000/health');
        updateStatusIndicator(mcpStatus, mcpResponse.ok);
    } catch {
        updateStatusIndicator(mcpStatus, false);
    }
}

function updateStatusIndicator(element, isConnected) {
    const dot = element.querySelector('.w-2');
    if (isConnected) {
        dot.className = 'w-2 h-2 rounded-full bg-green-500';
    } else {
        dot.className = 'w-2 h-2 rounded-full bg-red-500';
    }
}

// Check connection on load and periodically
checkConnectionStatus();
setInterval(checkConnectionStatus, 7000); // Check every 7 seconds