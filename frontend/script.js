const loginContainer = document.getElementById('login-container');
const chatContainer = document.getElementById('chat-container');
const loginButton = document.getElementById('login-button');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const chatLog = document.getElementById('chat-log');
const userIdInput = document.getElementById('user-ad-id-input');

const API_URL = "http://localhost:8000";
let userAdId = null;

loginButton.addEventListener('click', () => {
    const id = parseInt(userIdInput.value, 10);
    if (id && !isNaN(id)) {
        userAdId = id;
        loginContainer.classList.add('hidden');
        chatContainer.classList.remove('hidden');
    } else {
        alert("Veuillez entrer un User AD ID valide.");
    }
});

sendButton.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

async function sendMessage() {
    const question = userInput.value.trim();
    if (!question || !userAdId) return;

    appendMessage(question, 'user');
    userInput.value = '';

    try {
        const response = await fetch(`${API_URL}/ask/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_ad_id: userAdId, question: question })
        });

        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }

        const data = await response.json();
        appendMessage(data.answer, 'bot', data.sources);
    } catch (error) {
        console.error("Erreur lors de l'envoi du message:", error);
        appendMessage("Désolé, une erreur est survenue.", 'bot');
    }
}

function appendMessage(text, sender, sources = null) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);

    const p = document.createElement('p');
    p.textContent = text;
    messageDiv.appendChild(p);

    // Ajouter les sources GLPI si disponibles
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.classList.add('sources');
        sourcesDiv.innerHTML = '<strong>📚 Sources GLPI:</strong>';
        
        const sourcesList = document.createElement('ul');
        sources.forEach(source => {
            const li = document.createElement('li');
            li.textContent = `${source.type} #${source.id}: ${source.title}`;
            li.style.fontSize = '0.85em';
            li.style.color = '#666';
            sourcesList.appendChild(li);
        });
        
        sourcesDiv.appendChild(sourcesList);
        messageDiv.appendChild(sourcesDiv);
    }

    chatLog.appendChild(messageDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
}