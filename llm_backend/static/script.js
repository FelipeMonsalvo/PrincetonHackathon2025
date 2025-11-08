async function sendOnEnter(event) {
  if (event.key === "Enter") {
    const input = event.target;
    const msg = input.value.trim();
    if (!msg) return;

    const chatDiv = document.getElementById("chat");
    chatDiv.innerHTML += `<p><b>You:</b> ${msg}</p>`;
    input.value = "";

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg })
      });

      const data = await res.json();
      chatDiv.innerHTML += `<p><b>AI:</b> ${data.reply}</p>`;
      chatDiv.scrollTop = chatDiv.scrollHeight;
    } catch (err) {
      chatDiv.innerHTML += `<p><b>Error:</b> ${err}</p>`;
    }
  }
}
