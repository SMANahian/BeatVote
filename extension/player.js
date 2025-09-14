function attach() {
  const video = document.querySelector('video');
  if (!video) {
    setTimeout(attach, 1000);
    return;
  }
  video.addEventListener('ended', () => {
    chrome.runtime.sendMessage({ type: 'video-ended' });
  });
}
attach();
