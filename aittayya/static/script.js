// static/script.js

document.addEventListener('DOMContentLoaded', () => {

    // --- DOM ELEMENT REFERENCES ---
    const contentViewer = document.getElementById('content-viewer');
    const backToHomeButton = document.getElementById('back-to-home');
    const chatOpener = document.getElementById('chat-opener');
    const openChatPrompt = document.getElementById('open-chat-prompt');
    const chatWindow = document.getElementById('chat-window');
    const chatCloser = document.getElementById('chat-closer');
    const chatBox = document.getElementById('chat-box');
    const messageForm = document.getElementById('message-form');
    const userInput = document.getElementById('user-input');
    const typingIndicator = document.getElementById('typing-indicator');

    // Store the original home content (the temple image)
    const originalHomeContent = contentViewer.innerHTML;

    // --- INITIALIZATION ---
    // Trigger the new user flow on page load to get the welcome message.
    sendMessageToServer(""); 

    // --- EVENT LISTENERS ---
    chatOpener.addEventListener('click', () => toggleChatWindow(true));
    openChatPrompt.addEventListener('click', () => toggleChatWindow(true));
    chatCloser.addEventListener('click', () => toggleChatWindow(false));
    messageForm.addEventListener('submit', handleFormSubmit);
    chatBox.addEventListener('click', handleChatBoxClick);
    backToHomeButton.addEventListener('click', restoreHomeView);

    // --- FUNCTIONS ---
    
    function restoreHomeView() {
        contentViewer.innerHTML = originalHomeContent;
        // IMPORTANT: Re-attach the button to the restored content so it can be found again
        contentViewer.appendChild(backToHomeButton);
        backToHomeButton.classList.remove('visible');
    }

    function toggleChatWindow(show) {
        chatWindow.classList.toggle('visible', show);
        if (show) userInput.focus();
    }

    function handleFormSubmit(event) {
        event.preventDefault();
        const question = userInput.value.trim();
        if (!question) return;
        addMessage(question, 'user');
        userInput.value = '';
        sendMessageToServer(question);
    }
    
    function handleChatBoxClick(event) {
        const target = event.target;
        
        // Handle embeddable links that open inside the page
        const embedLink = target.closest('a[data-embed="true"]');
        if (embedLink) {
            event.preventDefault(); 
            loadContentInIframe(embedLink.href);
            return;
        }
        
        // Let the browser handle regular links (like target="_blank")
        const regularLink = target.closest('a:not([data-embed="true"])');
        if (regularLink) { return; }

        // Handle chat buttons
        const chatButton = target.closest('.chat-button');
        if (chatButton) {
            event.preventDefault();
            const payload = chatButton.dataset.payload;
            const buttonText = chatButton.textContent.trim();
            addMessage(buttonText, 'user');
            const buttonContainer = chatButton.closest('.button-container');
            if (buttonContainer) {
                buttonContainer.querySelectorAll('.chat-button').forEach(btn => btn.disabled = true);
            }
            sendMessageToServer(payload);
        }
    }

    function loadContentInIframe(url) {
        contentViewer.innerHTML = ''; // Clear previous content
        
        const iframe = document.createElement('iframe');
        iframe.src = url;
        iframe.setAttribute('allowfullscreen', '');
        iframe.setAttribute('loading', 'lazy');
        iframe.setAttribute('referrerpolicy', 'no-referrer-when-downgrade');
        
        contentViewer.appendChild(backToHomeButton);
        contentViewer.appendChild(iframe);

        // Make the back button visible and scroll the main page to the top
        backToHomeButton.classList.add('visible');
        window.scrollTo({ top: 0, behavior: 'smooth' });
        
        toggleChatWindow(false); // Hide chat to show the map clearly
    }

    async function sendMessageToServer(message) {
        const isInitialMessage = message === "";
        toggleInput(false);
        if (!isInitialMessage) showTypingIndicator(true);

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    question: message, 
                    user_id: USER_ID,
                    // Send a flag for the initial call
                    input_type: isInitialMessage ? 'start_command' : 'text' 
                })
            });
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            
            const data = await response.json();
            
            if (!isInitialMessage) showTypingIndicator(false);
            addMessage(data.text, 'bot', data.buttons);

        } catch (error) {
            console.error('Error fetching bot response:', error);
            if (!isInitialMessage) showTypingIndicator(false);
            addMessage('Sorry, I encountered a communication error. Please try again.', 'bot');
        } finally {
            toggleInput(true);
        }
    }
    
    function addMessage(text, sender, buttons = []) {
        if (!text) return;

        const shouldScroll = isChatScrolledToBottom();
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        const bubbleElement = document.createElement('div');
        bubbleElement.classList.add('bubble');
        const textElement = document.createElement('div');
        textElement.innerHTML = text; 
        bubbleElement.appendChild(textElement);
        if (buttons && buttons.length > 0) {
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'button-container';
            buttons.forEach(btnData => {
                const button = document.createElement('button');
                button.className = 'chat-button';
                button.textContent = btnData.text;
                button.dataset.payload = btnData.payload;
                buttonContainer.appendChild(button);
            });
            bubbleElement.appendChild(buttonContainer);
        }
        messageElement.appendChild(bubbleElement);
        chatBox.insertBefore(messageElement, typingIndicator);
        
        if (shouldScroll) {
            scrollChatToBottom();
        }
    }

    function showTypingIndicator(show) {
        const shouldScroll = isChatScrolledToBottom();
        typingIndicator.classList.toggle('visible', show); 
        if (show && shouldScroll) {
            scrollChatToBottom();
        }
    }

    function toggleInput(enabled) {
        userInput.disabled = !enabled;
        sendButton.disabled = !enabled;
        if (enabled) userInput.focus();
    }

    function isChatScrolledToBottom() {
        const threshold = 15;
        return chatBox.scrollHeight - chatBox.clientHeight <= chatBox.scrollTop + threshold;
    }

    function scrollChatToBottom() {
        chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' });
    }
});