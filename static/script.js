function sendMessage() {
    var userInput = document.getElementById("user-input").value;
    var sessionInput = document.getElementById("current-session-id");
    var sessionId = sessionInput ? sessionInput.value : "";

    if (userInput.trim() === "") return;

    var chatBox = document.getElementById("chat-box");

    // Get username from the DOM
    const userName = document.querySelector(".user-info strong").textContent || "User";

    // Create user message element
    var userMessageDiv = document.createElement("div");
    userMessageDiv.className = "user-message message";
    userMessageDiv.innerHTML = `
        <div class="content">${userInput}</div>
        <div class="avatar"><img src="https://ui-avatars.com/api/?name=${encodeURIComponent(userName)}&background=random" alt="User"></div>
    `;
    chatBox.appendChild(userMessageDiv);

    // Clear input field
    document.getElementById("user-input").value = "";

    // Scroll to bottom
    chatBox.scrollTop = chatBox.scrollHeight;

    const csrfToken = document.getElementById("csrf_token").value;

    // Send request to Flask backend
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
            // Check if this was a new session and we need to reload to show it in sidebar
            if (!sessionId && data.session_id) {
                window.location.href = "/?session_id=" + data.session_id;
                return;
            }
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

// Scroll to bottom on load
window.onload = function () {
    var chatBox = document.getElementById("chat-box");
    chatBox.scrollTop = chatBox.scrollHeight;
    populateCourses();
};

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

// Close modal when clicking outside of it
window.onclick = function (event) {
    const modal = document.getElementById("course-modal");
    if (event.target == modal) {
        closeModal();
    }
}
// function to delete session
function deleteSession(event, sessionId) {
    // Prevent the parent link click (which would switch to that session)
    event.stopPropagation();
    event.preventDefault();

    if (confirm("Are you sure you want to delete this chat session? This action cannot be undone.")) {
        const csrfToken = document.getElementById("csrf_token").value;
        fetch("/delete_session/" + sessionId, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // If the deleted session was the current one, go to new chat
                    const currentSessionId = document.getElementById("current-session-id").value;
                    if (currentSessionId === sessionId) {
                        window.location.href = "/new_chat";
                    } else {
                        // Otherwise just reload to update sidebar
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
