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
  chatDiv.innerHTML = "<p><i>New conversation started</i></p>";
}

async function sendOnEnter(event) {
  if (event.key === "Enter") {
    const input = event.target;
    const msg = input.value.trim();
    if (!msg) return;

    const chatDiv = document.getElementById("chat");
    chatDiv.innerHTML += `<p><b>You:</b> ${msg}</p>`;
    input.value = "";
    input.disabled = true; // Disable input while waiting for response

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

      const data = await res.json();
      chatDiv.innerHTML += `<p><b>AI:</b> ${data.reply}</p>`;
      chatDiv.scrollTop = chatDiv.scrollHeight;
      
      // Update session ID if it was created by backend
      if (data.session_id) {
        setSessionId(data.session_id);
      }
    } catch (err) {
      chatDiv.innerHTML += `<p><b>Error:</b> ${err.message}</p>`;
    } finally {
      input.disabled = false; // Re-enable input
      input.focus(); // Focus back on input
    }
  }
}
