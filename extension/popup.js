document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('room');
  chrome.storage.local.get('roomId', (res) => {
    if (res.roomId) {
      input.value = res.roomId;
    }
  });
  document.getElementById('save').addEventListener('click', () => {
    chrome.storage.local.set({ roomId: input.value }, () => {
      chrome.runtime.sendMessage({ type: 'room-updated' });
    });
  });
});
