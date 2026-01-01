const textarea = document.querySelector('textarea[name="user_input"]');
const form = document.querySelector('form.input-area');
const toggle = document.getElementById('theme-toggle');
const root = document.documentElement;
const typingIndicator = document.getElementById('typing-indicator');

function scrollToBottom() {
  const content = document.getElementById('content');
  if (content) {
    content.scrollTop = content.scrollHeight;
  }
}

function showTyping() {
  typingIndicator.style.display = 'flex';
  scrollToBottom();
}

if (textarea) {
  textarea.addEventListener('keydown', (event) => {
    if (!event.shiftKey && event.key === 'Enter') {
      event.preventDefault();
      showTyping();
      form.submit();
    }
  });
}

document.querySelectorAll('.qr-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    textarea.value = btn.textContent;
    showTyping();
    form.submit();
  });
});

toggle.addEventListener('change', () => {
  if (toggle.checked) {
    root.classList.add('dark-mode');
    localStorage.setItem('theme', 'dark');
  } else {
    root.classList.remove('dark-mode');
    localStorage.setItem('theme', 'light');
  }
});

const saved = localStorage.getItem('theme');
if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
  root.classList.add('dark-mode');
  toggle.checked = true;
}

window.addEventListener('load', scrollToBottom);
