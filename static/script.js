function sendMessage() {
    var userInput = document.getElementById("user-input").value;
    if (userInput.trim() === "") return;

    var chatBox = document.getElementById("chat-box");

    // Create user message element
    var userMessageDiv = document.createElement("div");
    userMessageDiv.className = "user-message message";
    userMessageDiv.innerHTML = `
        <div class="content">${userInput}</div>
        <div class="avatar"><img src="https://ui-avatars.com/api/?name=User&background=random" alt="User"></div>
    `;
    chatBox.appendChild(userMessageDiv);

    // Clear input field
    document.getElementById("user-input").value = "";

    // Scroll to bottom
    chatBox.scrollTop = chatBox.scrollHeight;

    // Send request to Flask backend
    fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: userInput })
    })
        .then(response => response.json())
        .then(data => {
            // Create bot message element
            var botMessageDiv = document.createElement("div");
            botMessageDiv.className = "bot-message message";
            botMessageDiv.innerHTML = `
            <div class="avatar"><img src="/static/logo.png" alt="Bot"></div>
            <div class="content">${data.reply}</div>
        `;
            chatBox.appendChild(botMessageDiv);

            // Scroll to bottom
            chatBox.scrollTop = chatBox.scrollHeight;

            // Speak response if sound is on
            if (isSoundOn) {
                speakText(data.reply);
            }
        })
        .catch(error => {
            console.error("Error:", error);
        });
}

// Allow sending message with Enter key
document.getElementById("user-input").addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});

// Voice Input Implementation
const micBtn = document.getElementById("mic-btn");
const userInput = document.getElementById("user-input");

if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = false; // Stop after one sentence
    recognition.lang = "en-US";
    recognition.interimResults = false;

    micBtn.addEventListener("click", () => {
        if (micBtn.classList.contains("active")) {
            recognition.stop();
        } else {
            recognition.start();
        }
    });

    recognition.onstart = () => {
        micBtn.classList.add("active");
    };

    recognition.onend = () => {
        micBtn.classList.remove("active");
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        userInput.value = transcript;
        // Optional: Auto-send the message
        // sendMessage(); 
    };

    recognition.onerror = (event) => {
        console.error("Speech recognition error", event.error);
        micBtn.classList.remove("active");
    };
} else {
    micBtn.style.display = "none"; // Hide button if not supported
    console.log("Web Speech API not supported in this browser.");
}

// Text-to-Speech Implementation
const soundBtn = document.getElementById("sound-btn");
let isSoundOn = true;
const synth = window.speechSynthesis;
let voices = [];

function populateVoices() {
    voices = synth.getVoices();
}

populateVoices();
if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = populateVoices;
}

function speakText(text) {
    if (synth.speaking) {
        console.error("Already speaking...");
        return;
    }
    if (text !== "") {
        const speakText = new SpeechSynthesisUtterance(text);

        // Select voice (Try to find Google US English or a female voice)
        const preferredVoice = voices.find(voice =>
            voice.name.includes("Google US English") ||
            voice.name.includes("Google") ||
            voice.name.includes("Female")
        );

        if (preferredVoice) {
            speakText.voice = preferredVoice;
        }

        speakText.onend = e => {
            console.log("Finished speaking...");
        };

        speakText.onerror = e => {
            console.error("Speaking error");
        };

        synth.speak(speakText);
    }
}

soundBtn.addEventListener("click", () => {
    isSoundOn = !isSoundOn;
    const icon = soundBtn.querySelector("i");
    if (isSoundOn) {
        icon.classList.remove("fa-volume-mute");
        icon.classList.add("fa-volume-up");
        soundBtn.classList.add("active");
    } else {
        icon.classList.remove("fa-volume-up");
        icon.classList.add("fa-volume-mute");
        soundBtn.classList.remove("active");
        synth.cancel(); // Stop speaking if muted
    }
});
