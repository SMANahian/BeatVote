const queueEl = document.getElementById('queue');

function renderQueue(queue) {
  queueEl.innerHTML = '';
  queue.forEach((s) => {
    const row = document.createElement('div');
    row.textContent = `${s.title} (score: ${s.score})`;
    queueEl.appendChild(row);
  });
}

if (window.roomId) {
  fetch(`/api/rooms/${window.roomId}/queue`).then((r) => r.json()).then(renderQueue);
  socket.on('queue:updated', renderQueue);
}
