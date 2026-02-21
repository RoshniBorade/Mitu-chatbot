// ============================================================
// MITU Chatbot - script.js  (Full enhanced version)
// Features: Typing indicator, Reactions, Search, Export, Voice
// ============================================================

let isSoundOn = true;
const synth = window.speechSynthesis;
let voices = [];

// ---------- Send Message ----------
function sendMessage() {
    var userInput = document.getElementById("user-input").value;
    var sessionInput = document.getElementById("current-session-id");
    var sessionId = sessionInput ? sessionInput.value : "";

    if (userInput.trim() === "") return;

    var chatBox = document.getElementById("chat-box");
    const userName = document.querySelector(".user-info strong").textContent || "User";

    // Append user message
    var userMessageDiv = document.createElement("div");
    userMessageDiv.className = "user-message message";
    userMessageDiv.innerHTML = `
        <div class="content">${escapeHtml(userInput)}</div>
        <div class="avatar"><img src="https://ui-avatars.com/api/?name=${encodeURIComponent(userName)}&background=random" alt="User"></div>
    `;
    chatBox.appendChild(userMessageDiv);
    document.getElementById("user-input").value = "";
    chatBox.scrollTop = chatBox.scrollHeight;

    // Show typing indicator
    const typingDiv = showTypingIndicator(chatBox);

    const csrfToken = document.getElementById("csrf_token").value;

    fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ message: userInput, session_id: sessionId })
    })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            removeTypingIndicator(typingDiv);

            if (!sessionId && data.session_id) {
                window.location.href = "/?session_id=" + data.session_id;
                return;
            }

            // Build bot message
            var botMessageDiv = document.createElement("div");
            botMessageDiv.className = "bot-message message";
            botMessageDiv.dataset.messageId = data.message_id || "";

            let messageContent = `
            <div class="avatar"><img src="/static/logo.png" alt="Bot"></div>
            <div class="message-wrapper">
                <div class="content">`;

            if (data.progress) {
                messageContent += `<div class="progress-text">${data.progress}</div>`;
                if (data.progress === "Opening Courses...") {
                    setTimeout(showCourses, 1000);
                }
            }

            messageContent += `${data.reply}`;

            if (data.buttons && data.buttons.length > 0) {
                messageContent += `<div class="quick-replies">`;
                data.buttons.forEach(btn => {
                    const safePayload = btn.payload.replace("'", "\\'");
                    messageContent += `<button class="quick-reply-btn" onclick="sendQuickReply('${safePayload}')">${btn.label}</button>`;
                });
                messageContent += `</div>`;
            }

            messageContent += `</div>
                <div class="reaction-bar">
                    <button class="reaction-btn" onclick="reactToMessage(this, 'like')" title="Helpful">👍</button>
                    <button class="reaction-btn" onclick="reactToMessage(this, 'dislike')" title="Not helpful">👎</button>
                </div>
            </div>`;

            botMessageDiv.innerHTML = messageContent;
            chatBox.appendChild(botMessageDiv);

            // Animate in
            botMessageDiv.style.opacity = "0";
            botMessageDiv.style.transform = "translateY(8px)";
            requestAnimationFrame(() => {
                botMessageDiv.style.transition = "opacity 0.3s ease, transform 0.3s ease";
                botMessageDiv.style.opacity = "1";
                botMessageDiv.style.transform = "translateY(0)";
            });

            chatBox.scrollTop = chatBox.scrollHeight;

            // Text-to-speech
            if (isSoundOn) {
                var tempDiv = document.createElement("div");
                tempDiv.innerHTML = data.reply;
                speakText(tempDiv.textContent || tempDiv.innerText || "");
            }
        })
        .catch(error => {
            removeTypingIndicator(typingDiv);
            console.error("Error:", error);
        });
}

// ---------- Typing Indicator ----------
function showTypingIndicator(chatBox) {
    const typingDiv = document.createElement("div");
    typingDiv.className = "bot-message message typing-message";
    typingDiv.id = "typing-indicator";
    typingDiv.innerHTML = `
        <div class="avatar"><img src="/static/logo.png" alt="Bot"></div>
        <div class="typing-bubble">
            <span></span><span></span><span></span>
        </div>
    `;
    chatBox.appendChild(typingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    return typingDiv;
}

function removeTypingIndicator(typingDiv) {
    if (typingDiv && typingDiv.parentNode) {
        typingDiv.parentNode.removeChild(typingDiv);
    }
}

// ---------- Message Reactions ----------
function reactToMessage(btn, type) {
    const bar = btn.closest(".reaction-bar");
    const allBtns = bar.querySelectorAll(".reaction-btn");

    // Toggle off if already active
    if (btn.classList.contains("active")) {
        btn.classList.remove("active");
        btn.classList.remove("animate-reaction");
        return;
    }

    // Reset all
    allBtns.forEach(b => {
        b.classList.remove("active", "animate-reaction");
    });

    // Activate clicked
    btn.classList.add("active", "animate-reaction");

    // Show toast feedback
    showToast(type === "like" ? "Thanks for the feedback! 😊" : "We'll work on improving that 🙏");

    // Optionally send feedback to backend (non-blocking)
    const csrfToken = document.getElementById("csrf_token").value;
    fetch("/react", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify({ reaction: type })
    }).catch(() => { }); // Silently fail if endpoint not ready
}

// ---------- Toast Notification ----------
function showToast(message) {
    let toast = document.getElementById("toast-notification");
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "toast-notification";
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2800);
}

// ---------- Chat Search (Session Filter) ----------
function filterSessions(query) {
    const wrappers = document.querySelectorAll("#session-list .session-wrapper");
    const q = query.toLowerCase().trim();
    wrappers.forEach(wrapper => {
        const title = wrapper.dataset.title || "";
        wrapper.style.display = title.includes(q) ? "flex" : "none";
    });
}

// ---------- Export Chat ----------
function showExportMenu() {
    const dropdown = document.getElementById("export-dropdown");
    dropdown.classList.toggle("visible");
    // Close when clicking elsewhere
    setTimeout(() => {
        document.addEventListener("click", function closeDropdown(e) {
            if (!e.target.closest("#export-btn") && !e.target.closest(".export-dropdown")) {
                dropdown.classList.remove("visible");
                document.removeEventListener("click", closeDropdown);
            }
        });
    }, 10);
}

function exportChat(format) {
    document.getElementById("export-dropdown").classList.remove("visible");
    const chatBox = document.getElementById("chat-box");
    const messages = chatBox.querySelectorAll(".message");

    if (messages.length === 0) {
        showToast("No messages to export!");
        return;
    }

    // Build text lines
    const lines = [];
    lines.push("=== MITU Chatbot - Chat Export ===");
    lines.push(`Exported: ${new Date().toLocaleString()}`);
    lines.push("=".repeat(40));
    lines.push("");

    messages.forEach(msg => {
        if (msg.id === "typing-indicator") return;
        const isUser = msg.classList.contains("user-message");
        const contentEl = msg.querySelector(".content");
        if (!contentEl) return;
        const text = contentEl.innerText.trim();
        if (!text) return;
        const prefix = isUser ? "You       " : "MITU Bot  ";
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        lines.push(`[${time}] ${prefix}: ${text}`);
    });

    const textContent = lines.join("\n");

    if (format === "text") {
        // Download as .txt
        const blob = new Blob([textContent], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `mitu-chat-${Date.now()}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        showToast("Chat exported as text! ✅");

    } else if (format === "pdf") {
        // Build a printable HTML window for PDF
        const printWindow = window.open("", "_blank");
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>MITU Chat Export</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 30px; color: #333; }
                    h1 { color: #4a90e2; font-size: 20px; border-bottom: 2px solid #4a90e2; padding-bottom: 10px; }
                    .meta { color: #888; font-size: 13px; margin-bottom: 20px; }
                    .msg { margin: 12px 0; padding: 10px 14px; border-radius: 10px; max-width: 80%; font-size: 14px; line-height: 1.5; }
                    .user { background: #4a90e2; color: white; margin-left: auto; text-align: right; }
                    .bot { background: #f0f0f0; color: #333; }
                    .sender { font-size: 11px; font-weight: bold; margin-bottom: 3px; }
                    .chat-area { display: flex; flex-direction: column; }
                </style>
            </head>
            <body>
                <h1>🤖 MITU Chatbot — Chat Export</h1>
                <div class="meta">Exported on: ${new Date().toLocaleString()}</div>
                <div class="chat-area">
        `);

        chatBox.querySelectorAll(".message").forEach(msg => {
            if (msg.id === "typing-indicator") return;
            const isUser = msg.classList.contains("user-message");
            const contentEl = msg.querySelector(".content");
            if (!contentEl) return;
            const text = contentEl.innerText.trim();
            if (!text) return;
            const cls = isUser ? "user" : "bot";
            const name = isUser ? "You" : "MITU Bot";
            printWindow.document.write(`
                <div class="msg ${cls}">
                    <div class="sender">${name}</div>
                    ${escapeHtml(text)}
                </div>
            `);
        });

        printWindow.document.write(`</div></body></html>`);
        printWindow.document.close();
        printWindow.focus();
        setTimeout(() => {
            printWindow.print();
        }, 500);
        showToast("PDF print dialog opened! 📄");
    }
}

// ---------- Helper: Escape HTML ----------
function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ---------- Quick Replies ----------
function sendQuickReply(payload) {
    const input = document.getElementById("user-input");
    input.value = payload;
    sendMessage();
}

// ---------- Enter key to send ----------
document.getElementById("user-input").addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});

// ---------- Voice Input (Web Speech API) ----------
const micBtn = document.getElementById("mic-btn");
const userInputEl = document.getElementById("user-input");

if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.lang = "en-US";
    recognition.interimResults = false;

    micBtn.addEventListener("click", () => {
        if (micBtn.classList.contains("active")) {
            recognition.stop();
        } else {
            recognition.start();
            showToast("🎙️ Listening...");
        }
    });

    recognition.onstart = () => {
        micBtn.classList.add("active");
        micBtn.title = "Stop listening";
    };

    recognition.onend = () => {
        micBtn.classList.remove("active");
        micBtn.title = "Voice Input";
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        userInputEl.value = transcript;
        showToast(`🎙️ Heard: "${transcript}"`);
        // Auto-send after recognizing voice
        setTimeout(sendMessage, 400);
    };

    recognition.onerror = (event) => {
        console.error("Speech recognition error", event.error);
        micBtn.classList.remove("active");
        if (event.error === "not-allowed") {
            showToast("Microphone permission denied ❌");
        } else {
            showToast("Voice input error: " + event.error);
        }
    };
} else {
    micBtn.style.display = "none";
    console.log("Web Speech API not supported in this browser.");
}

// ---------- Text-to-Speech ----------
const soundBtn = document.getElementById("sound-btn");

function populateVoices() {
    voices = synth.getVoices();
}

populateVoices();
if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = populateVoices;
}

function speakText(text) {
    if (synth.speaking) {
        synth.cancel();
        return;
    }
    if (text) {
        const utterance = new SpeechSynthesisUtterance(text);
        const preferredVoice = voices.find(v =>
            v.name.includes("Google US English") || v.name.includes("Google") || v.name.includes("Female")
        );
        if (preferredVoice) utterance.voice = preferredVoice;
        utterance.onerror = e => console.error("Speaking error", e);
        synth.speak(utterance);
    }
}

soundBtn.addEventListener("click", () => {
    isSoundOn = !isSoundOn;
    const icon = soundBtn.querySelector("i");
    if (isSoundOn) {
        icon.classList.replace("fa-volume-mute", "fa-volume-up");
        soundBtn.classList.add("active");
        showToast("🔊 Sound ON");
    } else {
        icon.classList.replace("fa-volume-up", "fa-volume-mute");
        soundBtn.classList.remove("active");
        synth.cancel();
        showToast("🔇 Sound OFF");
    }
});

// ---------- Scroll to bottom on load ----------
window.onload = function () {
    var chatBox = document.getElementById("chat-box");
    chatBox.scrollTop = chatBox.scrollHeight;
    populateCourses();
};

// ---------- Courses Data ----------
const courses = [
    {
        title: "Data Science & AI",
        category: "Advanced Technology",
        icon: "fas fa-brain",
        description: "Master the future with hands-on training in Data Science and Artificial Intelligence. Learn to transform businesses through data.",
        duration: "8 Weeks",
        syllabus: ["Intro to Data Science", "Machine Learning Algorithms", "Neural Networks & Deep Learning", "AI Ethics & Applications", "Real-world Projects"]
    },
    {
        title: "Python Programming",
        category: "Programming",
        icon: "fab fa-python",
        description: "From basics to system-level programming. The perfect foundation for automation and modern software development.",
        duration: "4 Weeks",
        syllabus: ["Python Basics & Syntax", "Control Structures", "Functional Programming", "File I/O & Modules", "System Programming with Python"]
    },
    {
        title: "Linux Administration",
        category: "Operating Systems",
        icon: "fab fa-linux",
        description: "Comprehensive training in Linux Essentials, Administration, and Kernel Programming. Become an open-source expert.",
        duration: "6 Weeks",
        syllabus: ["Linux Essentials", "User & Group Management", "System Administration", "Kernel Programming Basics", "Shell Scripting & Automation"]
    },
    {
        title: "Cloud Computing",
        category: "Cloud",
        icon: "fas fa-cloud",
        description: "Master Virtualization and OpenStack. Learn to manage and scale modern cloud infrastructures.",
        duration: "5 Weeks",
        syllabus: ["Cloud Fundamentals", "Virtualization Technologies", "OpenStack Architecture", "Cloud Storage & Security", "Managing Cloud Infrastructure"]
    },
    {
        title: "IoT & Raspberry Pi",
        category: "Hardware",
        icon: "fas fa-microchip",
        description: "Dive into hardware with Raspberry Pi and Arduino. Build smart connected systems for the modern age.",
        duration: "6 Weeks",
        syllabus: ["Electronic Fundamentals", "Raspberry Pi & Arduino Setup", "Sensors & Actuators", "IoT Protocols (MQTT/HTTP)", "End-to-End IoT Project"]
    },
    {
        title: "Full Stack Web Dev",
        category: "Web Computing",
        icon: "fas fa-code",
        description: "Master PHP, WordPress, and database management. Build responsive, professional websites from scratch.",
        duration: "8 Weeks",
        syllabus: ["HTML5 & CSS3 Essentials", "Responsive Design with Bootstrap", "PHP & MySQL Database", "CMS with WordPress", "Web Security Best Practices"]
    }
];

let selectedCourse = null;

function showCourses() {
    document.getElementById("main-chat-window").style.display = "none";
    document.getElementById("course-explorer").style.display = "flex";
}

function showChat() {
    document.getElementById("main-chat-window").style.display = "flex";
    document.getElementById("course-explorer").style.display = "none";
}

function populateCourses() {
    const grid = document.querySelector(".course-grid");
    if (!grid) return;

    grid.innerHTML = courses.map((course, index) => `
        <div class="course-card" onclick="openCourseModal(${index})">
            <div class="course-icon"><i class="${course.icon}"></i></div>
            <div class="course-category">${course.category}</div>
            <h4>${course.title}</h4>
            <p>${course.description}</p>
            <div class="course-footer">
                <span>View Details</span>
                <i class="fas fa-arrow-right"></i>
            </div>
        </div>
    `).join("");
}

function openCourseModal(index) {
    const course = courses[index];
    selectedCourse = course;

    document.getElementById("modal-icon").className = "course-icon " + course.icon;
    document.getElementById("modal-title").innerText = course.title;
    document.getElementById("modal-duration").innerText = course.duration;
    document.getElementById("modal-category").innerText = course.category;

    const syllabusList = document.getElementById("modal-syllabus");
    syllabusList.innerHTML = course.syllabus.map(item => `<li>${item}</li>`).join("");

    document.getElementById("course-modal").style.display = "flex";
}

function closeModal() {
    document.getElementById("course-modal").style.display = "none";
}

function askAboutSelectedCourse() {
    if (!selectedCourse) return;
    closeModal();
    showChat();
    const input = document.getElementById("user-input");
    input.value = "Tell me more about " + selectedCourse.title;
    sendMessage();
}

window.onclick = function (event) {
    const modal = document.getElementById("course-modal");
    if (event.target == modal) closeModal();
}

// ---------- Delete Session ----------
function deleteSession(event, sessionId) {
    event.stopPropagation();
    event.preventDefault();

    if (confirm("Are you sure you want to delete this chat session? This action cannot be undone.")) {
        const csrfToken = document.getElementById("csrf_token").value;
        fetch("/delete_session/" + sessionId, {
            method: "POST",
            headers: { "X-CSRFToken": csrfToken }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const currentSessionId = document.getElementById("current-session-id").value;
                    if (currentSessionId === sessionId) {
                        window.location.href = "/new_chat";
                    } else {
                        window.location.reload();
                    }
                } else {
                    alert("Error: " + (data.error || "Could not delete session"));
                }
            })
            .catch(error => {
                console.error("Error:", error);
                alert("Failed to connect to server.");
            });
    }
}
