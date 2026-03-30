// chat.js — message send, streaming response reader, file attach, markdown render
import { state } from './app.js';
import { refreshConversationList, deleteCurrentConversation } from './conversations.js';

let pendingAttachment = null; // { filename, content }
let isStreaming = false;

export function initChat() {
  window.addEventListener('conversation:selected', (e) => loadConversation(e.detail.id));

  document.getElementById('btn-send').addEventListener('click', sendMessage);
  document.getElementById('message-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Auto-resize textarea
  document.getElementById('message-input').addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 160) + 'px';
  });

  // File attachment
  document.getElementById('file-input').addEventListener('change', handleFileSelect);
  document.getElementById('btn-remove-attachment').addEventListener('click', clearAttachment);

  document.getElementById('btn-delete-conversation').addEventListener('click', deleteCurrentConversation);

  document.getElementById('btn-export').addEventListener('click', exportConversation);

  document.getElementById('chat-title').addEventListener('click', startTitleEdit);
}

async function loadConversation(id) {
  const res = await fetch(`/conversations/${id}`);
  if (!res.ok) return;
  const data = await res.json();

  document.getElementById('chat-title').textContent = data.conversation.title;
  document.getElementById('chat-empty-state').classList.add('hidden');
  document.getElementById('chat-active').classList.remove('hidden');
  document.getElementById('truncation-notice').classList.add('hidden');

  const messagesEl = document.getElementById('messages');
  messagesEl.innerHTML = '';

  for (const msg of data.messages) {
    appendMessage(msg.role, msg.content, msg.attachment_filename);
  }

  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function sendMessage() {
  if (isStreaming) return;
  const input = document.getElementById('message-input');
  const content = input.value.trim();
  if (!content && !pendingAttachment) return;
  if (!state.conversationId) return;

  const body = { content };
  if (pendingAttachment) {
    body.attachment_filename = pendingAttachment.filename;
    body.attachment_content = pendingAttachment.content;
  }

  // Optimistically render user message
  appendMessage('user', content, pendingAttachment?.filename ?? null);
  input.value = '';
  input.style.height = 'auto';
  clearAttachment();

  // Disable send while streaming
  isStreaming = true;
  document.getElementById('btn-send').disabled = true;

  // Create placeholder assistant message
  const thinkingEl = appendThinkingIndicator();
  const messagesEl = document.getElementById('messages');
  messagesEl.scrollTop = messagesEl.scrollHeight;

  try {
    const res = await fetch(`/conversations/${state.conversationId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      thinkingEl.remove();
      appendMessage('assistant', 'Error: could not reach the server.');
      return;
    }

    // Read SSE stream
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let assistantEl = null;
    let toolIndicatorEl = null;
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop(); // keep incomplete event in buffer

      for (const part of parts) {
        const eventMatch = part.match(/^event: (\w+)/);
        const dataMatch = part.match(/\ndata: ([\s\S]*)/);
        if (!eventMatch || !dataMatch) continue;

        const eventType = eventMatch[1];
        const data = dataMatch[1];

        if (eventType === 'token') {
          // Remove tool indicator if present (new tokens mean tool call finished)
          if (toolIndicatorEl) {
            toolIndicatorEl.remove();
            toolIndicatorEl = null;
          }
          if (!assistantEl) {
            thinkingEl.remove();
            assistantEl = createMessageEl('assistant');
            messagesEl.appendChild(assistantEl);
          }
          assistantEl.dataset.raw = (assistantEl.dataset.raw || '') + data;
          renderMarkdown(assistantEl);
          messagesEl.scrollTop = messagesEl.scrollHeight;

        } else if (eventType === 'tool_start') {
          // thinkingEl may already be detached if text tokens preceded this tool call
          if (thinkingEl.isConnected) {
            thinkingEl.textContent = data;
          } else {
            toolIndicatorEl = appendThinkingIndicator();
            toolIndicatorEl.textContent = data;
          }

        } else if (eventType === 'truncated') {
          document.getElementById('truncation-notice').classList.remove('hidden');

        } else if (eventType === 'done') {
          // Clean up any lingering indicators
          if (toolIndicatorEl) { toolIndicatorEl.remove(); toolIndicatorEl = null; }
          if (thinkingEl.isConnected) thinkingEl.remove();
          if (!assistantEl) {
            // No tokens were streamed (tool used with no preamble text)
            assistantEl = createMessageEl('assistant');
            messagesEl.appendChild(assistantEl);
            assistantEl.dataset.raw = data;
          }
          // Re-render fully now that all text is accumulated
          renderMarkdown(assistantEl);
          messagesEl.scrollTop = messagesEl.scrollHeight;
          await refreshConversationList();

        } else if (eventType === 'error') {
          if (toolIndicatorEl) { toolIndicatorEl.remove(); toolIndicatorEl = null; }
          if (assistantEl) {
            assistantEl.textContent = `Error: ${data}`;
          } else {
            thinkingEl.textContent = `Error: ${data}`;
          }
        }
      }
    }
  } finally {
    isStreaming = false;
    document.getElementById('btn-send').disabled = false;
  }
}

function appendMessage(role, content, attachmentFilename = null) {
  const messagesEl = document.getElementById('messages');
  const el = createMessageEl(role);

  if (attachmentFilename) {
    const label = document.createElement('p');
    label.className = 'attachment-label';
    label.textContent = `📎 ${attachmentFilename}`;
    el.appendChild(label);
  }

  el.dataset.raw = content;
  renderMarkdown(el);
  messagesEl.appendChild(el);
  return el;
}

function createMessageEl(role) {
  const el = document.createElement('div');
  el.className = `message ${role}`;
  return el;
}

function appendThinkingIndicator() {
  const messagesEl = document.getElementById('messages');
  const el = document.createElement('div');
  el.className = 'message assistant thinking';
  el.textContent = 'Thinking…';
  messagesEl.appendChild(el);
  return el;
}

function renderMarkdown(el) {
  const raw = el.dataset.raw || '';
  // marked and hljs are loaded globally from vendored libs
  el.innerHTML = marked.parse(raw, { breaks: true });
  el.querySelectorAll('pre code').forEach(block => {
    hljs.highlightElement(block);
  });
}

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (ev) => {
    pendingAttachment = { filename: file.name, content: ev.target.result };
    document.getElementById('attachment-name').textContent = file.name;
    document.getElementById('attachment-preview').classList.remove('hidden');
  };
  reader.readAsText(file);
  e.target.value = ''; // reset so same file can be re-selected
}

function clearAttachment() {
  pendingAttachment = null;
  document.getElementById('attachment-preview').classList.add('hidden');
  document.getElementById('attachment-name').textContent = '';
}

function startTitleEdit() {
  if (!state.conversationId) return;
  const titleEl = document.getElementById('chat-title');
  const current = titleEl.textContent;

  const input = document.createElement('input');
  input.type = 'text';
  input.value = current;
  input.className = 'title-edit-input';
  titleEl.replaceWith(input);
  input.select();

  async function commit() {
    const newTitle = input.value.trim();
    const restored = document.createElement('h2');
    restored.id = 'chat-title';
    restored.addEventListener('click', startTitleEdit);

    if (newTitle && newTitle !== current) {
      const res = await fetch(`/conversations/${state.conversationId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle }),
      });
      restored.textContent = res.ok ? newTitle : current;
      if (res.ok) await refreshConversationList();
    } else {
      restored.textContent = current;
    }
    input.replaceWith(restored);
  }

  function cancel() {
    const restored = document.createElement('h2');
    restored.id = 'chat-title';
    restored.textContent = current;
    restored.addEventListener('click', startTitleEdit);
    input.replaceWith(restored);
  }

  input.addEventListener('blur', commit);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); input.blur(); }
    if (e.key === 'Escape') { input.removeEventListener('blur', commit); cancel(); }
  });
}

async function exportConversation() {
  if (!state.conversationId) return;
  const res = await fetch(`/conversations/${state.conversationId}/export`);
  if (!res.ok) return;

  const blob = await res.blob();
  const disposition = res.headers.get('content-disposition') || '';
  const match = disposition.match(/filename="([^"]+)"/);
  const filename = match ? match[1] : 'conversation.md';

  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
