const PARTICLE_COUNT = 20;
const MIN_PARTICLE_SIZE = 50;
const MAX_PARTICLE_SIZE = 250;
const MIN_ANIMATION_DURATION = 20;
const MAX_ANIMATION_DURATION = 50;
const MAX_DELAY = 5;

function createParticles() {
    try {
        const container = document.getElementById('particles');
        if (!container) {
            console.error('Elemento de partículas não encontrado');
            return;
        }

        container.innerHTML = '';
        
        const fragment = document.createDocumentFragment();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        for (let i = 0; i < PARTICLE_COUNT; i++) {
            const particle = document.createElement('div');
            particle.classList.add('particle');
            
            const size = Math.floor(Math.random() * (MAX_PARTICLE_SIZE - MIN_PARTICLE_SIZE)) + MIN_PARTICLE_SIZE;
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            
            const posX = Math.random() * viewportWidth;
            const posY = Math.random() * viewportHeight;
            
            particle.style.position = 'absolute';
            particle.style.left = `${posX}px`;
            particle.style.top = `${posY}px`;
            
            const duration = Math.floor(Math.random() * (MAX_ANIMATION_DURATION - MIN_ANIMATION_DURATION)) + MIN_ANIMATION_DURATION;
            particle.style.animationDuration = `${duration}s`;
            
            const angle = Math.random() * 360;
            const distance = 1000 + Math.random() * 500;
            
            const animationName = `float-${i}`;
            const keyframes = `
                @keyframes ${animationName} {
                    0% {
                        transform: translate(0, 0) rotate(0deg);
                        opacity: 0.8;
                    }
                    100% {
                        transform: translate(${Math.cos(angle) * distance}px, ${Math.sin(angle) * distance}px) rotate(360deg);
                        opacity: 0;
                    }
                }
            `;
            
            const style = document.createElement('style');
            style.textContent = keyframes;
            document.head.appendChild(style);
            
            particle.style.animationName = animationName;
            
            const delay = Math.random() * MAX_DELAY;
            particle.style.animationDelay = `${delay}s`;
            
            fragment.appendChild(particle);
        }
        
        container.appendChild(fragment);
        
    } catch (error) {
        console.error('Erro ao criar partículas:', error);
    }
}

function togglePasswordVisibility() {
    try {
        const passwordField = document.getElementById('token');
        if (!passwordField) {
            console.error('Campo de token não encontrado');
            return;
        }

        const toggleButton = document.getElementById('togglePassword');
        if (!toggleButton) {
            console.error('Botão de toggle não encontrado');
            return;
        }

        const icon = toggleButton.querySelector('i');
        if (!icon) {
            console.error('Ícone não encontrado');
            return;
        }

        if (passwordField.type === 'password') {
            passwordField.type = 'text';
            icon.classList.replace('fa-eye', 'fa-eye-slash');
            toggleButton.setAttribute('aria-label', 'Ocultar token');
        } else {
            passwordField.type = 'password';
            icon.classList.replace('fa-eye-slash', 'fa-eye');
            toggleButton.setAttribute('aria-label', 'Mostrar token');
        }
        
    } catch (error) {
        console.error('Erro ao alternar visibilidade:', error);
    }
}

function animateFormElements() {
    try {
        const formElements = document.querySelectorAll(
            '.login-header, .input-group, .remember-forgot, .login-button, .divider, .social-login, .help-links'
        );
        
        if (!formElements.length) {
            console.warn('Nenhum elemento de formulário encontrado para animação');
            return;
        }
        
        formElements.forEach((el, index) => {
            el.classList.add('fade-in-up');
            el.style.animationDelay = `${0.1 * (index + 1)}s`;
        });
        
    } catch (error) {
        console.error('Erro ao animar elementos:', error);
    }
}

function initializeApp() {
    try {
        createParticles();
        
        const toggleButton = document.getElementById('togglePassword');
        if (toggleButton) {
            toggleButton.addEventListener('click', togglePasswordVisibility);
            toggleButton.setAttribute('aria-label', 'Mostrar token');
        }
        
        animateFormElements();
        
        const loginForm = document.querySelector('.login-box');
        if (loginForm) {
            loginForm.addEventListener('submit', function(event) {
                const tokenField = document.getElementById('token');
                if (tokenField && tokenField.value.trim() === '') {
                    event.preventDefault();
                    showError('Por favor, insira um token válido');
                }
            });
        }
        
    } catch (error) {
        console.error('Erro durante a inicialização:', error);
    }
}

function showError(message) {
    try {
        const existingError = document.querySelector('.error-message');
        if (existingError) existingError.remove();
        
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        errorElement.setAttribute('role', 'alert');
        errorElement.setAttribute('aria-live', 'assertive');
        
        const tokenContainer = document.querySelector('.password-container');
        if (tokenContainer) {
            tokenContainer.parentNode.insertBefore(errorElement, tokenContainer.nextSibling);
            
            setTimeout(() => {
                if (errorElement.parentNode) {
                    errorElement.parentNode.removeChild(errorElement);
                }
            }, 5000);
        }
        
    } catch (error) {
        console.error('Erro ao mostrar mensagem de erro:', error);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}

window.addEventListener('beforeunload', () => {
    const toggleButton = document.getElementById('togglePassword');
    if (toggleButton) {
        toggleButton.removeEventListener('click', togglePasswordVisibility);
    }
    
    const loginForm = document.querySelector('.login-box');
    if (loginForm) {
        loginForm.removeEventListener('submit', loginForm._submitHandler);
    }
});