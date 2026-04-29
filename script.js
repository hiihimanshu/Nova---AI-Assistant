// ================= GLOBAL STATE =================
let currentTab = "chat";
let currentMode = "focus";
let isThinking = false;
let recognition = null;
let micActive = false;

// ================= ELEMENTS =================
const input = document.getElementById("text-input");
const micIcon = document.getElementById("mic-icon");
const sendIcon = document.getElementById("send-icon");
const actionBtn = document.getElementById("action-btn");
const chatHistory = document.getElementById("chatHistory");
const plusBtn = document.getElementById("plusBtn");
const toolsMenu = document.getElementById("toolsMenu");
const tabChat = document.getElementById("tab-chat");

// ================= CHAT MODES (UNCHANGED) =================
const chatModes = [
  { id: "focus", label: "Focus", icon: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2"/></svg>` },
  { id: "study", label: "Study", icon: `<svg viewBox="0 0 24 24"><path d="M4 6h16v12H4z"/><path d="M8 6v12"/></svg>` },
  { id: "build", label: "Build", icon: `<svg viewBox="0 0 24 24"><path d="M3 21h18"/><path d="M14 7l3 3-7 7H7v-3z"/></svg>` },
  { id: "action", label: "Action", icon: `<svg viewBox="0 0 24 24"><path d="M5 12h14"/><path d="M13 5l6 7-6 7"/></svg>` },
  { id: "deep_research", label: "Deep Research", icon: `<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>` }
];

// ================= MAIN CHAT LOGIC =================
function askNova() {
  // 🔥 IMMEDIATELY switch to chat state
  document.body.classList.add("chat-active");

  const hero = document.querySelector(".hero");
  if (hero && !hero.classList.contains("hidden")) {
    hero.classList.add("hidden");
  }

  if (isThinking) return;

  const text = input.value.trim();
  if (!text) return;

  stopListening();
  input.value = "";
  toggleIcons();

  addMessage(text, "user");
  fetchFromBackend(text);
}

// ================= BACKEND =================
async function fetchFromBackend(text) {
  console.log("Sending mode:", currentMode);
  isThinking = true;
  addMessage("NOVA is thinking…", "nova");

  try {
    const res = await fetch("http://127.0.0.1:8000/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: text,
        mode: currentMode,
        memory: []
      })
    });

    const data = await res.json();
    removeThinking();
   addMessage(formatResponse(String(data.answer)), "nova");


  } catch (err) {
    removeThinking();
    addMessage("⚠️ Connection error.", "nova");
  } finally {
    isThinking = false;
  }
}

// ================= UI HELPERS =================
function addMessage(text, type) {
  const div = document.createElement("div");
  div.className = `chat-message ${type}`;
  div.innerHTML = text.replace(/\n/g, "<br>");

  if (type === "nova") {
  const modeLabel = document.createElement("div");
  modeLabel.className = "mode-label";
  modeLabel.textContent = `Mode: ${currentMode.toUpperCase()}`;
  div.prepend(modeLabel);
}

  chatHistory.appendChild(div);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

// 🔥 FIX: THIS WAS MISSING (CAUSED EXECUTION STOP)
function removeThinking() {
  document.querySelectorAll(".chat-message.nova").forEach(msg => {
    if (msg.textContent.includes("thinking")) {
      msg.remove();
    }
  });
}

function formatResponse(text) {
  if (!text) return "";

  let formatted = text.trim();

  // ---------- Date / Time ----------
  if (
    formatted.includes("Today is") ||
    formatted.includes("Today's date") ||
    formatted.includes("The time is")
  ) {
    return (
      "🕒 Date & Time\n" +
      formatted.replace(/ · /g, "\n• ")
    );
  }

  // ---------- Split into sentences ----------
  const sentences = formatted.split(/(?<=\.)\s+/);

  // Short answers → no formatting
  if (sentences.length <= 2) {
    return formatted;
  }

  // ---------- Overview ----------
  let result = "📌 Overview\n";

  // First 2 sentences = overview paragraph
  result += sentences.slice(0, 2).join(" ") + "\n\n";

  // ---------- Career Highlights ----------
  result += "🏏 Career Highlights\n";

  const bulletKeywords = [
    "won",
    "holds",
    "record",
    "records",
    "captain",
    "highest",
    "most"
  ];

  for (let i = 2; i < sentences.length; i++) {
    const s = sentences[i].trim();

    // If sentence looks like an achievement → bullet
    if (bulletKeywords.some(k => s.toLowerCase().includes(k))) {
      result += "• " + s + "\n";
    } else {
      // Normal paragraph sentence
      result += s + "\n";
    }
  }

  return result.trim();
}



// ================= MIC =================
function startListening() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return alert("Browser does not support Speech Recognition");

  recognition = new SR();
  recognition.lang = "en-US";
  micActive = true;
  recognition.start();
  actionBtn.classList.add("listening");

  recognition.onresult = e => {
    if (!micActive) return;
    input.value = e.results[0][0].transcript;
    toggleIcons();
    askNova();
  };

  recognition.onend = stopListening;
  recognition.onerror = stopListening;
}

function stopListening() {
  micActive = false;
  if (recognition) {
    recognition.stop();
    recognition = null;
  }
  actionBtn.classList.remove("listening");
}

// ================= INPUT =================
function toggleIcons() {
  const hasText = input.value.trim().length > 0;
  micIcon.style.display = hasText ? "none" : "block";
  sendIcon.style.display = hasText ? "block" : "none";
}

actionBtn.onclick = () => {
  if (input.value.trim()) askNova();
  else startListening();
};

input.onkeydown = e => {
  if (e.key === "Enter") {
    e.preventDefault();
    askNova();
  }
};

input.oninput = toggleIcons;

setInterval(() => {
  document.title = "Mode: " + currentMode;
}, 500);

// ================= MODES MENU (UNCHANGED) =================
function renderChatModes() {
  toolsMenu.innerHTML = "";

  chatModes.forEach(m => {
    if (m.id === "deep_research") {
      const d = document.createElement("div");
      d.className = "menu-divider";
      toolsMenu.appendChild(d);
    }

    const item = document.createElement("div");
    item.innerHTML = `${m.icon}<span>${m.label}</span>`;
    if (m.id === currentMode) item.classList.add("active");

    item.onclick = () => {
      currentMode = m.id;

      console.log("Mode changed to:", currentMode); // debug

      toolsMenu.classList.add("hidden");
    };

    toolsMenu.appendChild(item);
  });
}

plusBtn.onclick = e => {
  e.stopPropagation();
  renderChatModes();
  toolsMenu.classList.toggle("hidden");
};

document.onclick = e => {
  if (!toolsMenu.contains(e.target) && e.target !== plusBtn) {
    toolsMenu.classList.add("hidden");
  }
};

if (tabChat) {
  tabChat.onclick = () => {
    currentTab = "chat";
    tabChat.classList.add("active");
  };
}
