const resultsEl = document.getElementById('results');
const queueEl = document.getElementById('queue');

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

if (document.getElementById('search-input')) {
  document.getElementById('search-input').addEventListener('change', async (e) => {
    const q = e.target.value;
    const res = await fetch(`/api/youtube/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    resultsEl.innerHTML = '';
    data.forEach((v) => {
      const item = document.createElement('div');
      item.className = 'flex items-center gap-2 mb-2';
      const thumb = document.createElement('img');
      const t = (v.thumbnails.medium && v.thumbnails.medium.url) ||
                (v.thumbnails.default && v.thumbnails.default.url);
      if (t) {
        thumb.src = t;
        thumb.alt = v.title;
      }
      const title = document.createElement('span');
      title.textContent = v.title;
      const btn = document.createElement('button');
      btn.textContent = 'Add';
      btn.onclick = () => {
        socket.emit('queue:add', { room_id: window.roomId, video_id: v.video_id, title: v.title });
      };
      item.appendChild(thumb);
      item.appendChild(title);
      item.appendChild(btn);
      resultsEl.appendChild(item);
    });
  });
}
