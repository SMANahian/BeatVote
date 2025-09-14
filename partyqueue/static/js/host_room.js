const queueEl = document.getElementById('queue');

// Render the queue with voting controls so the host can also
// participate in prioritising songs.
function renderQueue(queue) {
  queueEl.innerHTML = '';
  queue.forEach((s) => {
    const row = document.createElement('div');
    row.className = 'flex items-center gap-2 mb-2';

    const title = document.createElement('span');
    title.textContent = `${s.title} (score: ${s.score})`;

    const up = document.createElement('button');
    up.textContent = '▲';
    up.onclick = () => {
      socket.emit('queue:vote', { room_id: window.roomId, song_id: s._id, vote: 'like' });
    };

    const down = document.createElement('button');
    down.textContent = '▼';
    down.onclick = () => {
      socket.emit('queue:vote', { room_id: window.roomId, song_id: s._id, vote: 'dislike' });
    };

    row.appendChild(title);
    row.appendChild(up);
    row.appendChild(down);
    queueEl.appendChild(row);
  });
}

if (window.roomId) {
  fetch(`/api/rooms/${window.roomId}/queue`).then((r) => r.json()).then(renderQueue);
  socket.on('queue:updated', renderQueue);
}
