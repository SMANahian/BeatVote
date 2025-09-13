const resultsEl = document.getElementById('results');
const queueEl = document.getElementById('queue');

if (document.getElementById('search-input')) {
  document.getElementById('search-input').addEventListener('change', async (e) => {
    const q = e.target.value;
    const res = await fetch(`/api/youtube/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    resultsEl.innerHTML = '';
    data.forEach(v => {
      const btn = document.createElement('button');
      btn.textContent = `Add ${v.title}`;
      btn.onclick = () => {
        socket.emit('queue:add', {room_id: window.roomId, video_id: v.video_id, title: v.title});
      };
      resultsEl.appendChild(btn);
    });
  });
}

socket.on('queue:updated', queue => {
  queueEl.innerHTML = '';
  queue.forEach(s => {
    const li = document.createElement('div');
    li.textContent = `${s.title} (score: ${s.score})`;
    queueEl.appendChild(li);
  });
});
