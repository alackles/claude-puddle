// auth.js — login, register, logout, change-password fetch calls
import { state, showView, enterApp } from './app.js';

export function initAuth() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(btn => {
    btn.addEventListener('click', () => {
      tabs.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('form-login').classList.toggle('hidden', btn.dataset.tab !== 'login');
      document.getElementById('form-register').classList.toggle('hidden', btn.dataset.tab !== 'register');
    });
  });

  document.getElementById('form-login').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errEl = document.getElementById('login-error');
    errEl.textContent = '';

    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (res.ok) {
      state.user = await res.json();
      enterApp();
    } else {
      const data = await res.json();
      errEl.textContent = data.detail || 'Login failed';
    }
  });

  document.getElementById('form-register').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errEl = document.getElementById('reg-error');
    errEl.textContent = '';

    const body = {
      email: document.getElementById('reg-email').value,
      password: document.getElementById('reg-password').value,
      display_name: document.getElementById('reg-name').value,
      invite_code: document.getElementById('reg-invite').value,
    };

    const res = await fetch('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (res.ok) {
      // Re-fetch user info after registration
      const meRes = await fetch('/auth/me');
      if (meRes.ok) {
        state.user = await meRes.json();
        enterApp();
      }
    } else {
      const data = await res.json();
      errEl.textContent = data.detail || 'Registration failed';
    }
  });
}

export async function logout() {
  await fetch('/auth/logout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  location.reload();
}

export function initChangePassword() {
  const modal = document.getElementById('modal-change-password');
  document.getElementById('btn-change-password').addEventListener('click', () => {
    modal.classList.remove('hidden');
  });
  document.getElementById('btn-cancel-password').addEventListener('click', () => {
    modal.classList.add('hidden');
  });

  document.getElementById('form-change-password').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errEl = document.getElementById('cp-error');
    errEl.textContent = '';

    const res = await fetch('/auth/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        current_password: document.getElementById('cp-current').value,
        new_password: document.getElementById('cp-new').value,
      }),
    });

    if (res.ok) {
      modal.classList.add('hidden');
      document.getElementById('form-change-password').reset();
    } else {
      const data = await res.json();
      errEl.textContent = data.detail || 'Failed to update password';
    }
  });
}
