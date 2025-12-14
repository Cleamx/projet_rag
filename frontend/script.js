// ============================================
// UNIVERSITÀ DI CORSICA - CAMPUS NUMÉRIQUE
// Assistant IA - Script JavaScript
// ============================================

// Configuration
const API_URL = "http://localhost:8000";
let userAdId = 1; // Utilisateur par défaut (déjà connecté via l'ENT)
let messageCounter = 0;

// DOM Elements
const chatLog = document.getElementById('chat-log');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const typingIndicator = document.getElementById('typing-indicator');
const toastContainer = document.getElementById('toast-container');

// ============================================
// Event Listeners
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = userInput.scrollHeight + 'px';
    });

    // Send message on button click
    sendButton.addEventListener('click', sendMessage);

    // Send message on Enter key (Shift+Enter for new line)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Quick action buttons
    document.addEventListener('click', (e) => {
        if (e.target.closest('.quick-btn')) {
            const question = e.target.closest('.quick-btn').dataset.question;
            userInput.value = question;
            sendMessage();
        }
    });
});

// ============================================
// Send Message
// ============================================
async function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message) return;

    // Clear input
    userInput.value = '';
    userInput.style.height = 'auto';

    // Remove welcome message if present
    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    // Add user message to chat
    addMessage(message, 'user');

    // Show typing indicator
    typingIndicator.classList.remove('hidden');

    try {
        const response = await fetch(`${API_URL}/ask/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_ad_id: userAdId,
                question: message
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Hide typing indicator
        typingIndicator.classList.add('hidden');

        // Add assistant response
        addMessage(data.answer, 'assistant', data.sources, data.response_id);

    } catch (error) {
        console.error('Error:', error);
        typingIndicator.classList.add('hidden');
        
        showToast('Une erreur est survenue. Veuillez réessayer.', 'error');
        
        addMessage(
            "Désolé, une erreur s'est produite. Veuillez réessayer.",
            'assistant'
        );
    }
}

// ============================================
// Add Message to Chat
// ============================================
function addMessage(text, sender, sources = null, responseId = null) {
    messageCounter++;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    messageDiv.id = `msg-${messageCounter}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;

    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = getCurrentTime();

    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);

    // Add sources if present (for assistant messages)
    if (sources && sources.length > 0) {
        const sourcesDiv = createSourcesElement(sources);
        messageDiv.appendChild(sourcesDiv);
    }

    // Add feedback buttons for assistant messages
    if (sender === 'assistant' && responseId) {
        const feedbackDiv = createFeedbackElement(responseId, messageCounter);
        messageDiv.appendChild(feedbackDiv);
    }

    chatLog.appendChild(messageDiv);

    // Scroll to bottom
    chatLog.scrollTop = chatLog.scrollHeight;

    // Animation
    messageDiv.style.animation = 'fadeIn 0.3s ease';
}

// ============================================
// Create Sources Element
// ============================================
function createSourcesElement(sources) {
    const sourcesContainer = document.createElement('div');
    sourcesContainer.className = 'sources';
    sourcesContainer.style.marginTop = '10px';
    sourcesContainer.style.padding = '10px';
    sourcesContainer.style.background = '#F5F5F5';
    sourcesContainer.style.borderRadius = '4px';
    sourcesContainer.style.fontSize = '13px';

    const header = document.createElement('div');
    header.innerHTML = '<strong><i class="fas fa-book"></i> Sources:</strong>';
    header.style.marginBottom = '8px';
    header.style.color = '#FF6600';

    const sourcesList = document.createElement('ul');
    sourcesList.style.listStyle = 'none';
    sourcesList.style.margin = '0';
    sourcesList.style.padding = '0';

    sources.forEach(source => {
        const li = document.createElement('li');
        // Afficher le titre de la source et son type
        const sourceText = source.title ? `${source.title} (${source.type})` : `Source ${source.id} (${source.type})`;
        li.innerHTML = `<i class="fas fa-file-alt" style="color: #FF6600; margin-right: 8px;"></i>${sourceText}`;
        li.style.padding = '4px 0';
        li.style.color = '#333333';
        sourcesList.appendChild(li);
    });

    sourcesContainer.appendChild(header);
    sourcesContainer.appendChild(sourcesList);

    return sourcesContainer;
}

// ============================================
// Create Feedback Element
// ============================================
function createFeedbackElement(responseId, messageId) {
    const feedbackContainer = document.createElement('div');
    feedbackContainer.className = 'feedback-container';
    feedbackContainer.id = `feedback-${messageId}`;
    feedbackContainer.style.marginTop = '12px';
    feedbackContainer.style.display = 'flex';
    feedbackContainer.style.alignItems = 'center';
    feedbackContainer.style.gap = '10px';

    const label = document.createElement('span');
    label.className = 'feedback-label';
    label.textContent = 'Cette réponse vous a-t-elle aidé ?';
    label.style.fontSize = '13px';
    label.style.color = '#666666';

    const positiveBtn = document.createElement('button');
    positiveBtn.className = 'feedback-btn positive';
    positiveBtn.innerHTML = '👍';
    positiveBtn.style.fontSize = '20px';
    positiveBtn.style.background = 'transparent';
    positiveBtn.style.border = 'none';
    positiveBtn.style.cursor = 'pointer';
    positiveBtn.style.padding = '5px 10px';
    positiveBtn.style.borderRadius = '4px';
    positiveBtn.style.transition = 'background 0.2s';
    positiveBtn.title = 'Bonne réponse';

    const negativeBtn = document.createElement('button');
    negativeBtn.className = 'feedback-btn negative';
    negativeBtn.innerHTML = '👎';
    negativeBtn.style.fontSize = '20px';
    negativeBtn.style.background = 'transparent';
    negativeBtn.style.border = 'none';
    negativeBtn.style.cursor = 'pointer';
    negativeBtn.style.padding = '5px 10px';
    negativeBtn.style.borderRadius = '4px';
    negativeBtn.style.transition = 'background 0.2s';
    negativeBtn.title = 'Mauvaise réponse';

    positiveBtn.addEventListener('click', () => handleFeedback(responseId, true, feedbackContainer));
    negativeBtn.addEventListener('click', () => handleFeedback(responseId, false, feedbackContainer));

    positiveBtn.addEventListener('mouseenter', () => {
        positiveBtn.style.background = 'rgba(16, 185, 129, 0.1)';
    });
    positiveBtn.addEventListener('mouseleave', () => {
        positiveBtn.style.background = 'transparent';
    });

    negativeBtn.addEventListener('mouseenter', () => {
        negativeBtn.style.background = 'rgba(239, 68, 68, 0.1)';
    });
    negativeBtn.addEventListener('mouseleave', () => {
        negativeBtn.style.background = 'transparent';
    });

    feedbackContainer.appendChild(label);
    feedbackContainer.appendChild(positiveBtn);
    feedbackContainer.appendChild(negativeBtn);

    return feedbackContainer;
}

// ============================================
// Handle Feedback
// ============================================
async function handleFeedback(responseId, isValid, container) {
    const buttons = container.querySelectorAll('.feedback-btn');
    buttons.forEach(btn => btn.disabled = true);

    try {
        const response = await fetch(`${API_URL}/feedback/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                response_id: responseId,
                is_valid: isValid
            })
        });

        if (!response.ok) {
            throw new Error('Erreur lors de l\'envoi du feedback');
        }

        // Hide buttons
        buttons.forEach(btn => btn.style.display = 'none');
        
        // Hide label
        const label = container.querySelector('.feedback-label');
        if (label) label.style.display = 'none';

        // Add thank you message
        const thanks = document.createElement('span');
        thanks.style.fontSize = '13px';
        thanks.style.color = '#10b981';
        thanks.style.fontWeight = '500';
        thanks.innerHTML = '<i class="fas fa-check"></i> Merci pour votre retour !';
        container.appendChild(thanks);

        showToast(
            isValid ? 'Merci ! Votre retour positif a été enregistré 😊' : 'Merci pour votre retour. Nous allons nous améliorer !',
            'success'
        );

    } catch (error) {
        console.error('Erreur feedback:', error);
        showToast('Erreur lors de l\'envoi du feedback', 'error');
        buttons.forEach(btn => btn.disabled = false);
    }
}

// ============================================
// Utility Functions
// ============================================
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('fr-FR', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = 'fa-info-circle';
    if (type === 'success') icon = 'fa-check-circle';
    if (type === 'error') icon = 'fa-exclamation-circle';

    toast.innerHTML = `
        <i class="fas ${icon}"></i>
        <span>${message}</span>
    `;

    toastContainer.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}