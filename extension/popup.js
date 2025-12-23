document.addEventListener('DOMContentLoaded', () => {
  const roomEl = document.getElementById('room');
  const serverEl = document.getElementById('server');
  const tokenEl = document.getElementById('token');
  const statusEl = document.getElementById('status');

  const setStatus = (text, ok = false) => {
    statusEl.textContent = text || '';
    statusEl.classList.toggle('ok', ok);
  };

  const normalizeServerUrl = (raw) => (raw || '').trim().replace(/\/+$/, '');

  chrome.storage.local.get(['serverUrl', 'roomId', 'hostToken'], (res) => {
    serverEl.value = res.serverUrl || 'http://127.0.0.1:5000';
    roomEl.value = res.roomId || '';
    tokenEl.value = res.hostToken || '';
  });

  document.getElementById('save').addEventListener('click', () => {
    const serverUrl = normalizeServerUrl(serverEl.value);
    const roomId = (roomEl.value || '').trim();
    const hostToken = (tokenEl.value || '').trim();

    if (!serverUrl.startsWith('http')) {
      setStatus('Server URL must start with http:// or https://');
      return;
    }
    if (!roomId) {
      setStatus('Room ID is required');
      return;
    }
    if (!hostToken) {
      setStatus('Host Token is required for auto-advance');
      return;
    }

    chrome.storage.local.set({ serverUrl, roomId, hostToken }, () => {
      chrome.runtime.sendMessage({ type: 'config-updated' });
      setStatus('Saved', true);
    });
  });

  document.getElementById('openHost').addEventListener('click', () => {
    const serverUrl = normalizeServerUrl(serverEl.value);
    const roomId = (roomEl.value || '').trim();
    if (!serverUrl.startsWith('http') || !roomId) {
      setStatus('Set Server URL and Room ID first');
      return;
    }
    const url = `${serverUrl}/${roomId}/host`;
    chrome.tabs.create({ url, pinned: true });
  });
});
