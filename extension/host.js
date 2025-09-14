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
