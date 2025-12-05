// ============================================
// GLPI Assistant - Modern Frontend JavaScript
// ============================================

// DOM Elements
const loginPage = document.getElementById('login-page');
const chatPage = document.getElementById('chat-page');
const ticketsPage = document.getElementById('tickets-page');
const knowledgePage = document.getElementById('knowledge-page');
const statsPage = document.getElementById('stats-page');

const loginButton = document.getElementById('login-button');
const logoutButton = document.getElementById('logout-btn');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const chatLog = document.getElementById('chat-log');
const userIdInput = document.getElementById('user-ad-id-input');
const navUser = document.getElementById('nav-user');
const userName = document.getElementById('user-name');
const typingIndicator = document.getElementById('typing-indicator');
const newChatBtn = document.getElementById('new-chat-btn');
const toastContainer = document.getElementById('toast-container');

// Configuration
const API_URL = "http://localhost:8000";
let userAdId = null;
let messageCounter = 0;

// ============================================
// Navigation
// ============================================
const navLinks = document.querySelectorAll('.nav-link');
const pages = {
    chat: chatPage,
    tickets: ticketsPage,
    knowledge: knowledgePage,
    stats: statsPage
};

navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = link.dataset.page;
        
        // Update active nav link
        navLinks.forEach(l => l.classList.remove('active'));
        link.classList.add('active');
        
        // Show corresponding page
        Object.values(pages).forEach(p => p.classList.add('hidden'));
        if (pages[page]) {
            pages[page].classList.remove('hidden');
        }
    });
});

// ============================================
// Authentication
// ============================================
loginButton.addEventListener('click', handleLogin);
userIdInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleLogin();
});

function handleLogin() {
    const id = parseInt(userIdInput.value, 10);
    if (id && !isNaN(id)) {
        userAdId = id;
        loginPage.classList.add('hidden');
        chatPage.classList.remove('hidden');
        navUser.classList.remove('hidden');
        userName.textContent = `Utilisateur #${id}`;
        showToast('Connexion réussie !', 'success');
        
        // Focus on input
        setTimeout(() => userInput.focus(), 300);
    } else {
        showToast('Veuillez entrer un User AD ID valide.', 'error');
        userIdInput.classList.add('shake');
        setTimeout(() => userIdInput.classList.remove('shake'), 500);
    }
}

logoutButton.addEventListener('click', () => {
    userAdId = null;
    navUser.classList.add('hidden');
    chatPage.classList.add('hidden');
    loginPage.classList.remove('hidden');
    chatLog.innerHTML = getWelcomeMessageHTML();
    userIdInput.value = '';
    showToast('Déconnexion réussie', 'success');
});

// ============================================
// Chat Functionality
// ============================================
sendButton.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Auto-resize textarea
userInput.addEventListener('input', () => {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 150) + 'px';
    sendButton.disabled = !userInput.value.trim();
});

// Quick actions and suggestion chips
document.querySelectorAll('.quick-btn, .chip').forEach(btn => {
    btn.addEventListener('click', () => {
        const question = btn.dataset.question;
        if (question) {
            userInput.value = question;
            userInput.dispatchEvent(new Event('input'));
            sendMessage();
        }
    });
});

// New chat button
newChatBtn.addEventListener('click', () => {
    chatLog.innerHTML = getWelcomeMessageHTML();
    messageCounter = 0;
    showToast('Nouvelle conversation démarrée', 'success');
});

async function sendMessage() {
    const question = userInput.value.trim();
    if (!question || !userAdId) return;

    // Remove welcome message if present
    const welcomeMsg = chatLog.querySelector('.welcome-message');
    if (welcomeMsg) welcomeMsg.remove();

    appendMessage(question, 'user');
    userInput.value = '';
    userInput.style.height = 'auto';
    sendButton.disabled = true;

    // Show typing indicator
    typingIndicator.classList.remove('hidden');
    chatLog.scrollTop = chatLog.scrollHeight;

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
        typingIndicator.classList.add('hidden');
        appendMessage(data.answer, 'bot', data.sources, data.response_id);
    } catch (error) {
        console.error("Erreur lors de l'envoi du message:", error);
        typingIndicator.classList.add('hidden');
        appendMessage("Désolé, une erreur est survenue. Veuillez réessayer.", 'bot');
        showToast('Erreur de connexion au serveur', 'error');
    }
}

function appendMessage(text, sender, sources = null, responseId = null) {
    messageCounter++;
    const messageId = `msg-${messageCounter}`;
    const time = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);
    messageDiv.id = messageId;

    let html = `
        <div class="message-content">
            ${formatMessage(text)}
        </div>
        <div class="message-time">${time}</div>
    `;

    // Add sources for bot messages
    if (sender === 'bot' && sources && sources.length > 0) {
        html += `
            <div class="sources">
                <div class="sources-header">
                    <i class="fas fa-book-open"></i>
                    <span>Sources GLPI</span>
                </div>
                <ul>
                    ${sources.map(source => `
                        <li>
                            <i class="fas fa-file-alt"></i>
                            <span>${source.type} #${source.id}: ${source.title}</span>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    // Add feedback for bot messages
    if (sender === 'bot' && responseId) {
        html += `
            <div class="feedback-container" id="feedback-${messageId}">
                <span class="feedback-label">Cette réponse vous a-t-elle aidé ?</span>
                <button class="feedback-btn positive" data-rating="positive" data-response-id="${responseId}" data-message-id="${messageId}" title="Bonne réponse">
                    👍
                </button>
                <button class="feedback-btn negative" data-rating="negative" data-response-id="${responseId}" data-message-id="${messageId}" title="Mauvaise réponse">
                    👎
                </button>
            </div>
        `;
    }

    messageDiv.innerHTML = html;
    chatLog.appendChild(messageDiv);

    // Add feedback event listeners
    if (sender === 'bot') {
        const feedbackBtns = messageDiv.querySelectorAll('.feedback-btn');
        feedbackBtns.forEach(btn => {
            btn.addEventListener('click', () => handleFeedback(btn));
        });
    }

    chatLog.scrollTop = chatLog.scrollHeight;
}

function formatMessage(text) {
    // Simple formatting: convert newlines to <br>
    return text.replace(/\n/g, '<br>');
}

async function handleFeedback(button) {
    const messageId = button.dataset.messageId;
    const responseId = button.dataset.responseId;
    const rating = button.dataset.rating;
    const container = document.getElementById(`feedback-${messageId}`);
    const isValid = rating === 'positive';
    
    // Désactiver les boutons pendant l'envoi
    const allBtns = container.querySelectorAll('.feedback-btn');
    allBtns.forEach(btn => btn.disabled = true);
    
    try {
        // Envoyer le feedback au serveur
        const response = await fetch(`${API_URL}/feedback/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                response_id: parseInt(responseId),
                is_valid: isValid
            })
        });
        
        if (!response.ok) {
            throw new Error('Erreur lors de l\'envoi du feedback');
        }
        
        // Masquer les boutons non sélectionnés
        allBtns.forEach(btn => {
            if (btn === button) {
                btn.classList.add('selected');
            } else {
                btn.style.display = 'none';
            }
        });
        
        // Ajouter le message de remerciement
        const thanks = document.createElement('span');
        thanks.classList.add('feedback-thanks');
        thanks.innerHTML = '<i class="fas fa-check"></i> Merci pour votre retour !';
        container.appendChild(thanks);
        
        // Masquer le label
        container.querySelector('.feedback-label').style.display = 'none';
        
        // Afficher le toast
        const messages = {
            positive: 'Merci ! Votre retour positif a été enregistré 😊',
            negative: 'Merci pour votre retour. Nous allons nous améliorer !'
        };
        showToast(messages[rating], 'success');
        
    } catch (error) {
        console.error('Erreur feedback:', error);
        showToast('Erreur lors de l\'envoi du feedback', 'error');
        // Réactiver les boutons en cas d'erreur
        allBtns.forEach(btn => btn.disabled = false);
    }
}

function getWelcomeMessageHTML() {
    return `
        <div class="welcome-message">
            <div class="welcome-icon">
                <i class="fas fa-hand-wave"></i>
            </div>
            <h3>Bonjour ! Je suis votre assistant GLPI</h3>
            <p>Je peux vous aider avec vos questions concernant le support informatique, 
               les tickets GLPI et la documentation technique.</p>
            <div class="quick-actions">
                <button class="quick-btn" data-question="Quels sont mes tickets ouverts ?">
                    <i class="fas fa-folder-open"></i>
                    Mes tickets ouverts
                </button>
                <button class="quick-btn" data-question="Comment puis-je créer un nouveau ticket ?">
                    <i class="fas fa-plus"></i>
                    Créer un ticket
                </button>
                <button class="quick-btn" data-question="Rechercher dans la base de connaissances">
                    <i class="fas fa-search"></i>
                    Rechercher
                </button>
            </div>
        </div>
    `;
}

// ============================================
// Toast Notifications
// ============================================
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.classList.add('toast', type);
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle'
    };
    
    toast.innerHTML = `
        <i class="fas ${icons[type]}"></i>
        <span>${message}</span>
    `;
    
    toastContainer.appendChild(toast);
    
    // Remove after 4 seconds
    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ============================================
// Initialization
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Add shake animation CSS
    const style = document.createElement('style');
    style.textContent = `
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            20%, 60% { transform: translateX(-5px); }
            40%, 80% { transform: translateX(5px); }
        }
        .shake { animation: shake 0.5s ease; }
    `;
    document.head.appendChild(style);
    
    // Re-attach quick-btn listeners after DOM is ready
    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const question = btn.dataset.question;
            if (question && userAdId) {
                userInput.value = question;
                userInput.dispatchEvent(new Event('input'));
                sendMessage();
            }
        });
    });
});