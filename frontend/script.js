const API_BASE = "http://localhost:8000";

let sessionId = null;
let sessions = [];
let currentMode = "chat";
let quizState = null;
let quizCompleted = false;
let quizGenerating = false;

async function ensureSession() {
    const res = await fetch(`${API_BASE}/sessions/new`, { method: "POST" });
    const data = await res.json();
    sessionId = data.session_id;
    loadSessions();
}

async function loadSessions() {
    const res = await fetch(`${API_BASE}/sessions`);
    const data = await res.json();
    sessions = (data.sessions || []).slice().reverse();
    renderSessionList();
}

function getSessionId(obj) {
    if (typeof obj === "string") return obj;
    return obj.id || obj.session_id;
}

function getSessionTitle(obj) {
    if (obj.title && obj.title.trim() !== "") return obj.title;
    return "New Chat";
}

function renderSessionList() {
    const list = document.getElementById("session-list");
    list.innerHTML = "";
    sessions.forEach(s => {
        const id = getSessionId(s);
        const item = document.createElement("div");
        item.classList.add("session-item");
        if (id === sessionId) item.classList.add("active");

        const titleSpan = document.createElement("span");
        titleSpan.classList.add("session-title");
        titleSpan.innerText = getSessionTitle(s);

        const delBtn = document.createElement("button");
        delBtn.classList.add("delete-session-btn");
        delBtn.innerText = "×";
        delBtn.onclick = e => {
            e.stopPropagation();
            deleteSession(id);
        };

        item.onclick = () => openSession(id);
        item.appendChild(titleSpan);
        item.appendChild(delBtn);
        list.appendChild(item);
    });
}

async function openSession(id) {
    if (!id) return;
    sessionId = id;
    const res = await fetch(`${API_BASE}/sessions/${id}`);
    const data = await res.json();
    const box = document.getElementById("chat-box");
    box.innerHTML = "";
    const msgs = data.messages || [];
    msgs.forEach(m => addMessage(m.text, m.role));
    renderSessionList();
}

async function newChat() {
    const res = await fetch(`${API_BASE}/sessions/new`, { method: "POST" });
    const data = await res.json();
    sessionId = data.session_id;
    document.getElementById("chat-box").innerHTML = "";
    loadSessions();
}

async function deleteSession(id) {
    const ok = window.confirm("Delete this chat?");
    if (!ok) return;
    await fetch(`${API_BASE}/sessions/${id}`, { method: "DELETE" });
    await loadSessions();
    const box = document.getElementById("chat-box");
    if (!sessions.length) {
        sessionId = null;
        box.innerHTML = "";
        return;
    }
    if (id === sessionId) {
        const first = sessions[0];
        const newId = getSessionId(first);
        sessionId = newId;
        box.innerHTML = "";
        await openSession(newId);
    }
}

function addMessage(text, sender) {
    const box = document.getElementById("chat-box");
    const msg = document.createElement("div");
    msg.classList.add("message", sender);
    msg.innerText = text;
    box.appendChild(msg);
    box.scrollTop = box.scrollHeight;
}

function showLoadingBubble() {
    const box = document.getElementById("chat-box");
    const bubble = document.createElement("div");
    bubble.id = "loading-bubble";
    bubble.classList.add("loading-bubble");
    bubble.innerHTML = `
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
    `;
    box.appendChild(bubble);
    box.scrollTop = box.scrollHeight;
}

function removeLoadingBubble() {
    const bubble = document.getElementById("loading-bubble");
    if (bubble) bubble.remove();
}

async function sendMessage() {
    if (currentMode !== "chat") return;
    const input = document.getElementById("chat-input");
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, "user");
    input.value = "";
    showLoadingBubble();

    const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: text })
    });

    const data = await res.json();
    removeLoadingBubble();
    addMessage(data.response, "assistant");
    loadSessions();
}


function switchToChat() {
    currentMode = "chat";
    document.getElementById("tab-chat").classList.add("active");
    document.getElementById("tab-quiz").classList.remove("active");
    document.getElementById("tab-review").classList.remove("active");
    document.getElementById("chat-view").classList.remove("hidden");
    document.getElementById("quiz-view").classList.add("hidden");
    document.getElementById("review-view").classList.add("hidden");
    document.getElementById("chat-input-area").style.display = "flex";
}

function switchToQuiz() {
    currentMode = "quiz";
    document.getElementById("tab-chat").classList.remove("active");
    document.getElementById("tab-quiz").classList.add("active");
    document.getElementById("tab-review").classList.remove("active");
    document.getElementById("chat-view").classList.add("hidden");
    document.getElementById("quiz-view").classList.remove("hidden");
    document.getElementById("review-view").classList.add("hidden");
    document.getElementById("chat-input-area").style.display = "none";

    if (quizGenerating) {
        document.getElementById("quiz-start-screen").classList.add("hidden");
        document.getElementById("quiz-loading").classList.remove("hidden");
        document.getElementById("quiz-container").classList.add("hidden");
    }

    else if (quizCompleted || quizState) {
        document.getElementById("quiz-start-screen").classList.add("hidden");
        document.getElementById("quiz-loading").classList.add("hidden");
        document.getElementById("quiz-container").classList.remove("hidden");

    } else {
        document.getElementById("quiz-start-screen").classList.remove("hidden");
        document.getElementById("quiz-loading").classList.add("hidden");
        document.getElementById("quiz-container").classList.add("hidden");
    }
}

async function generateQuiz() {
    if (quizGenerating) return;
    quizGenerating = true;
    quizCompleted = false;

    document.getElementById("quiz-start-screen").classList.add("hidden");

    const loadingDiv = document.getElementById("quiz-loading");
    loadingDiv.classList.remove("hidden");
    
    try {
        loadingDiv.innerHTML = `
            <div class="loading-spinner"></div>
            <p>Building your profile...</p>
            <p style="font-size: 14px; color: #888;">Analyzing your learning progress</p>
        `;
        
        const profileRes = await fetch(`${API_BASE}/quiz/prepare`, { method: "POST" });
        const profileData = await profileRes.json();
        
        loadingDiv.innerHTML = `
            <div class="loading-spinner"></div>
            <p>Generating questions...</p>
            <p style="font-size: 14px; color: #888;">Creating personalized quiz for you</p>
        `;
        
        const quizRes = await fetch(`${API_BASE}/quiz/generate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(profileData)
        });
        const data = await quizRes.json();

        loadingDiv.classList.add("hidden");
        document.getElementById("quiz-container").classList.remove("hidden");

        quizState = {
            progress: data.progress,
            text: data.text
        };

        renderQuizText(quizState);

    } catch (err) {
        console.error(err);
        loadingDiv.innerHTML = `
            <p style="color: red;">Failed to generate quiz.</p>
            <button onclick="generateQuiz()" class="quiz-main-btn">Retry</button>
        `;
    } finally {
        quizGenerating = false;
    }
}

function clearFeedbackCards() {
    document.getElementById("quiz-feedback-list").innerHTML = "";
}

function clearQuizUI() {
    document.getElementById("quiz-progress").innerHTML = "";
    document.getElementById("quiz-question").innerHTML = "";
    clearFeedbackCards();
}

function renderFeedbackCard(data) {
    const list = document.getElementById("quiz-feedback-list");

    const card = document.createElement("div");
    card.classList.add("quiz-card");
    card.innerText = data.feedback;
    
    if (data.explanation && data.explanation.trim() !== "") {
        card.innerHTML += `<br><br><em>Explanation: ${data.explanation}</em>`;
    }

    if (data.done) {
        quizCompleted = true;
        quizState = null;
        
        const score = document.createElement("div");
        score.innerText = `Final Score: ${data.final_score}/${data.total} (${data.accuracy.toFixed(0)}%)`;
        card.appendChild(document.createElement("br"));
        card.appendChild(score);

        const btn = document.createElement("button");
        btn.innerText = "Next Quiz";
        btn.className = "quiz-main-btn";
        btn.onclick = async () => {
            quizCompleted = false;
            document.getElementById("quiz-container").classList.add("hidden");
            clearQuizUI();
            
            document.getElementById("quiz-loading").classList.remove("hidden");

            await generateQuiz();
        };

        card.appendChild(btn);

    } else {
        const btn = document.createElement("button");
        btn.innerText = "Next Question";
        btn.className = "quiz-main-btn";
        btn.onclick = async () => {
            clearFeedbackCards();
            await loadNextQuiz();
        };
        card.appendChild(btn);
    }

    list.appendChild(card);
}

function renderQuizText(data) {
    clearFeedbackCards();

    document.getElementById("quiz-progress").innerText = data.progress;
    document.getElementById("quiz-question").innerText = data.text;

    document.querySelectorAll(".quiz-choice-btn").forEach(btn => {
        btn.classList.remove("hidden");
    });

    document.getElementById("quiz-choices").classList.remove("hidden");
    
    quizState = data;
}

function renderQuizResponse(data) {
    document.querySelectorAll(".quiz-choice-btn").forEach(btn => {
        btn.classList.add("hidden");
    });
    renderFeedbackCard(data);
}

async function loadNextQuiz() {
    const res = await fetch(`${API_BASE}/quiz/next`);
    const data = await res.json();
    quizState = data;
    renderQuizText(data);
}

async function answerQuiz(choice) {
    const res = await fetch(`${API_BASE}/quiz/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ choice: Number(choice) })
    });
    const data = await res.json();
    renderQuizResponse(data);
}

function switchToReview() {
    currentMode = "review";
    document.getElementById("tab-chat").classList.remove("active");
    document.getElementById("tab-quiz").classList.remove("active");
    document.getElementById("tab-review").classList.add("active");
    document.getElementById("chat-view").classList.add("hidden");
    document.getElementById("quiz-view").classList.add("hidden");
    document.getElementById("review-view").classList.remove("hidden");
    document.getElementById("chat-input-area").style.display = "none";
    
    loadQuizHistory();
}

async function loadQuizHistory() {
    const res = await fetch(`${API_BASE}/quiz/history`);
    const data = await res.json();
    renderQuizHistory(data.history);
}


function renderQuizHistory(history) {
    const list = document.getElementById("review-list");
    list.innerHTML = "";
    
    if (!history || history.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <p>No quiz history yet.</p>
                <p style="font-size: 16px; color: #aaa; margin-top: -20px;">Take your first quiz to see your progress here!</p>
                <button onclick="document.getElementById('tab-quiz').click()">Start Your First Quiz</button>
            </div>
        `;
        return;
    }

    const reversedHistory = [...history].reverse();
    
    reversedHistory.forEach((session, idx) => {
        const card = document.createElement("div");
        card.classList.add("quiz-card");
        
        const date = new Date(session.timestamp).toLocaleString();
        const total = session.questions.length;
        const correct = session.questions.filter(q => q.is_correct).length;
        const accuracy = ((correct / total) * 100).toFixed(0);
        
        let emoji = "🎯";
        
        card.innerHTML = `
            <h3>${emoji} Quiz ${history.length - idx}</h3>
            <p style="color: #888; font-size: 14px; margin-top: -5px;">${date}</p>
            <p><strong style="font-size: 24px; color: ${accuracy >= 70 ? '#0ea37f' : '#ff6b6b'};">${correct}/${total}</strong> <span style="color: #888;">(${accuracy}%)</span></p>
            <button class="quiz-main-btn" onclick="showQuizDetails(${idx})">View Details</button>
        `;
        
        list.appendChild(card);
    });
}

function showQuizDetails(idx) {
    fetch(`${API_BASE}/quiz/history`)
        .then(res => res.json())
        .then(data => {
            const history = data.history.reverse();
            const session = history[idx];
            
            const list = document.getElementById("review-list");
            list.innerHTML = "";
            
            const backBtn = document.createElement("button");
            backBtn.className = "quiz-main-btn";
            backBtn.innerText = "← Back";
            backBtn.onclick = loadQuizHistory;
            list.appendChild(backBtn);
            
            session.questions.forEach((q, i) => {
                const card = document.createElement("div");
                card.classList.add("quiz-card");
                
                const status = q.is_correct ? "✓ Correct" : "✗ Incorrect";
                const statusColor = q.is_correct ? "green" : "red";
                
                card.innerHTML = `
                    <h3 style="color: ${statusColor}">Q${i+1}: ${status}</h3>
                    <p><strong>${q.question}</strong></p>
                    <ol>
                        ${q.choices.map((choice, ci) => {
                            let style = "";
                            if (ci === q.correct) style = "color: green; font-weight: bold;";
                            else if (ci === q.user_answer && !q.is_correct) style = "color: red;";
                            return `<li style="${style}">${choice}</li>`;
                        }).join("")}
                    </ol>
                    ${q.explanation ? `<p><em>Explanation: ${q.explanation}</em></p>` : ""}
                `;
                
                list.appendChild(card);
            });

            document.querySelector('.main').scrollTop = 0;
        });
}

window.addEventListener('beforeunload', () => {
    if (navigator.sendBeacon) {
        navigator.sendBeacon(`${API_BASE}/profile/invalidate`);
    }
});


document.getElementById("quiz-generate-btn").addEventListener("click", generateQuiz);

document.getElementById("send-btn").addEventListener("click", sendMessage);
document.getElementById("chat-input").addEventListener("keydown", e => {
    if (e.key === "Enter") sendMessage();
});
document.getElementById("new-chat-btn").addEventListener("click", newChat);
document.getElementById("tab-chat").addEventListener("click", switchToChat);
document.getElementById("tab-quiz").addEventListener("click", switchToQuiz);
document.getElementById("tab-review").addEventListener("click", switchToReview);

document.querySelectorAll(".quiz-choice-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const choice = btn.getAttribute("data-choice");
        answerQuiz(choice);
    });
});

ensureSession();
