// Session ID stored in memory (clears on page refresh)
let currentSessionId = null;

// Get session ID (created by backend on first message)
function getSessionId() {
  return currentSessionId;
}

// Store session ID (in-memory only, not persistent)
function setSessionId(sessionId) {
  currentSessionId = sessionId;
}

// Start a new chat session (clears current conversation)
function newChat() {
  currentSessionId = null;
  const chatDiv = document.getElementById("chat");
  chatDiv.innerHTML = '<div class="empty-state"><p>Start a conversation by typing a message below.</p></div>';
}

function parseMessage(content) {
  // First escape HTML to prevent XSS
  let parsed = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  
  // Convert markdown bold **text** to <strong>text</strong> (process first)
  parsed = parsed.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  
  // Convert markdown italic *text* to <em>text</em> (process after bold to avoid conflicts)
  parsed = parsed.replace(/\*([^*]+?)\*/g, '<em>$1</em>');
  
  // Convert \n to <br> tags
  parsed = parsed.replace(/\\n/g, '<br>').replace(/\n/g, '<br>');
  
  return parsed;
}

function addMessage(content, type = 'assistant') {
  const chatDiv = document.getElementById("chat");
  
  // Remove empty state if present
  const emptyState = chatDiv.querySelector('.empty-state');
  if (emptyState) {
    emptyState.remove();
  }
  
  const messageDiv = document.createElement("div");
  messageDiv.className = `message message-${type}`;
  
  const label = type === 'user' ? 'You' : type === 'error' ? 'Error' : 'AI';
  
  // Parse content for AI messages (convert \n to line breaks)
  const parsedContent = type === 'assistant' ? parseMessage(content) : content.replace(/</g, '&lt;').replace(/>/g, '&gt;');
  
  messageDiv.innerHTML = `
    <div class="message-label">${label}</div>
    <div>${parsedContent}</div>
  `;
  
  chatDiv.appendChild(messageDiv);
  chatDiv.scrollTop = chatDiv.scrollHeight;
  
  return messageDiv;
}

function showLoading() {
  const chatDiv = document.getElementById("chat");
  const emptyState = chatDiv.querySelector('.empty-state');
  if (emptyState) {
    emptyState.remove();
  }
  
  const loadingDiv = document.createElement("div");
  loadingDiv.className = "loading";
  loadingDiv.id = "loading-indicator";
  loadingDiv.innerHTML = `
    <div class="spinner"></div>
    <span>AI is thinking...</span>
  `;
  
  chatDiv.appendChild(loadingDiv);
  chatDiv.scrollTop = chatDiv.scrollHeight;
}

function hideLoading() {
  const loadingDiv = document.getElementById("loading-indicator");
  if (loadingDiv) {
    loadingDiv.remove();
  }
}

async function sendOnEnter(event) {
  if (event.key === "Enter") {
    const input = event.target;
    const msg = input.value.trim();
    if (!msg) return;

    addMessage(msg, 'user');
    input.value = "";
    input.disabled = true;
    
    // Show loading indicator
    showLoading();

    try {
      const sessionId = getSessionId();
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: msg,
          session_id: sessionId 
        })
      });

      hideLoading();

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ error: `HTTP ${res.status}: ${res.statusText}` }));
        addMessage(errorData.error || 'An error occurred', 'error');
        return;
      }

      const data = await res.json();
      
      if (data.reply && data.reply.toLowerCase().includes('error')) {
        addMessage(data.reply, 'error');
      } else {
        addMessage(data.reply || 'No response received', 'assistant');
      }
      
      // Update session ID if it was created by backend
      if (data.session_id) {
        setSessionId(data.session_id);
      }
    } catch (err) {
      hideLoading();
      addMessage(`Network error: ${err.message}. Please check your connection and try again.`, 'error');
    } finally {
      input.disabled = false;
      input.focus();
    }
  }
}
