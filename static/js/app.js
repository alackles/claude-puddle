// app.js — router/view switching, session state
import { initAuth } from './auth.js';
import { initConversations } from './conversations.js';
import { initChat } from './chat.js';
import { initSharing } from './sharing.js';

export const state = {
  user: null,        // { id, email, display_name, is_instructor }
  conversationId: null,
};

export function showView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
  document.getElementById(`view-${name}`).classList.remove('hidden');
}

async function boot() {
  // Try to restore session
  try {
    const res = await fetch('/auth/me');
    if (res.ok) {
      state.user = await res.json();
    }
  } catch (_) {
    // network error — stay on auth view
  }

  if (state.user) {
    enterApp();
  } else {
    showView('auth');
    initAuth();
  }
}

export function enterApp() {
  showView('chat');
  document.getElementById('user-display-name').textContent = state.user.display_name;

  if (state.user.is_instructor) {
    document.getElementById('btn-shared-view').classList.remove('hidden');
  }

  initConversations();
  initChat();
  initSharing();
}

boot();
