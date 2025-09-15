// Listen for song end event instead of queue update
window.addEventListener('song-ended', () => {
  chrome.runtime.sendMessage({ type: 'queue-updated' });
});

function attach() {
  const btn = document.getElementById('use-extension');
  if (!btn) {
    setTimeout(attach, 1000);
    return;
  }
  btn.addEventListener('click', () => {
    chrome.runtime.sendMessage({ type: 'use-extension' });
  });
}
attach();

// TODO: Make sure to dispatch a 'song-ended' event when the song actually finishes playing.
// If your player does not dispatch this event, you need to add it where the song ends.
