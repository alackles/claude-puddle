// sharing.js — share button handler; instructor shared-conversations view
import { state, showView } from './app.js';
import { logout } from './auth.js';

export function initSharing() {
  document.getElementById('btn-logout').addEventListener('click', logout);
  document.getElementById('btn-shared-logout')?.addEventListener('click', logout);

  document.getElementById('btn-share').addEventListener('click', async () => {
    if (!state.conversationId) return;

    const res = await fetch(`/conversations/${state.conversationId}/share`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    if (res.ok) {
      document.getElementById('btn-share').textContent = '✓ Shared';
      document.getElementById('btn-share').disabled = true;
    }
  });

  document.getElementById('btn-shared-view')?.addEventListener('click', () => {
    showView('shared');
    document.getElementById('shared-user-name').textContent = state.user.display_name;
    loadSharedConversations();
  });

  document.getElementById('btn-back-to-chat')?.addEventListener('click', () => {
    showView('chat');
  });
}

async function loadSharedConversations() {
  const res = await fetch('/shared');
  if (!res.ok) return;
  const conversations = await res.json();

  const list = document.getElementById('shared-conversation-list');
  list.innerHTML = '';

  for (const conv of conversations) {
    const li = document.createElement('li');
    li.textContent = `${conv.title} — ${conv.owner_display_name}`;
    li.dataset.id = conv.id;
    li.addEventListener('click', () => loadSharedConversation(conv));
    list.appendChild(li);
  }
}

async function loadSharedConversation(conv) {
  document.querySelectorAll('#shared-conversation-list li').forEach(li => {
    li.classList.toggle('active', parseInt(li.dataset.id) === conv.id);
  });

  const res = await fetch(`/conversations/${conv.id}`);
  if (!res.ok) return;
  const data = await res.json();

  document.getElementById('shared-chat-title').textContent = data.conversation.title;
  document.getElementById('shared-chat-owner').textContent =
    `${conv.owner_display_name} (${conv.owner_email})`;

  document.getElementById('shared-empty-state').classList.add('hidden');
  document.getElementById('shared-chat-active').classList.remove('hidden');

  const messagesEl = document.getElementById('shared-messages');
  messagesEl.innerHTML = '';

  for (const msg of data.messages) {
    const el = document.createElement('div');
    el.className = `message ${msg.role}`;

    if (msg.attachment_filename) {
      const label = document.createElement('p');
      label.className = 'attachment-label';
      label.textContent = `📎 ${msg.attachment_filename}`;
      el.appendChild(label);
    }

    el.dataset.raw = msg.content;
    el.innerHTML += marked.parse(msg.content, { breaks: true });
    el.querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));

    messagesEl.appendChild(el);
  }

  messagesEl.scrollTop = messagesEl.scrollHeight;
}
