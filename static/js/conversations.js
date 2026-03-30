// conversations.js — sidebar: list, create, delete, load conversations
import { state } from './app.js';

let onSelectCallback = null;

export function initConversations(onSelect) {
  onSelectCallback = onSelect;

  const modal = document.getElementById('modal-new-conversation');
  const form = document.getElementById('form-new-conversation');
  const titleInput = document.getElementById('new-conv-title');
  const btnCancel = document.getElementById('btn-cancel-new-conversation');

  document.getElementById('btn-new-conversation').addEventListener('click', () => {
    titleInput.value = '';
    modal.classList.remove('hidden');
    titleInput.focus();
  });

  btnCancel.addEventListener('click', () => {
    modal.classList.add('hidden');
  });

  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.add('hidden');
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = titleInput.value.trim();
    if (!title) return;

    modal.classList.add('hidden');

    const res = await fetch('/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    });

    if (res.ok) {
      const conv = await res.json();
      await refreshConversationList();
      selectConversation(conv.id);
    }
  });

  refreshConversationList();
}

export async function refreshConversationList() {
  const res = await fetch('/conversations');
  if (!res.ok) return;
  const conversations = await res.json();

  const list = document.getElementById('conversation-list');
  list.innerHTML = '';

  for (const conv of conversations) {
    const li = document.createElement('li');
    li.textContent = conv.title;
    li.dataset.id = conv.id;
    if (conv.id === state.conversationId) li.classList.add('active');
    li.addEventListener('click', () => selectConversation(conv.id));
    list.appendChild(li);
  }
}

export function selectConversation(id) {
  state.conversationId = id;

  document.querySelectorAll('#conversation-list li').forEach(li => {
    li.classList.toggle('active', parseInt(li.dataset.id) === id);
  });

  if (onSelectCallback) onSelectCallback(id);

  // Trigger chat load via custom event (chat.js listens)
  window.dispatchEvent(new CustomEvent('conversation:selected', { detail: { id } }));
}

export async function deleteCurrentConversation() {
  if (!state.conversationId) return;
  if (!confirm('Delete this conversation? This cannot be undone.')) return;

  const res = await fetch(`/conversations/${state.conversationId}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
  });

  if (res.ok) {
    state.conversationId = null;
    document.getElementById('chat-active').classList.add('hidden');
    document.getElementById('chat-empty-state').classList.remove('hidden');
    await refreshConversationList();
  }
}
