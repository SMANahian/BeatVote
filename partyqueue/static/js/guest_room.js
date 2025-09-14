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
      fetch(`/api/rooms/${window.roomId}/queue/${s._id}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vote: 'like' })
      }).then(fetchQueue);
    };
    const down = document.createElement('button');
    down.textContent = '▼';
    down.onclick = () => {
      fetch(`/api/rooms/${window.roomId}/queue/${s._id}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vote: 'dislike' })
      }).then(fetchQueue);
    };
    row.appendChild(title);
    row.appendChild(up);
    row.appendChild(down);
    queueEl.appendChild(row);
  });
}

function fetchQueue() {
  fetch(`/api/rooms/${window.roomId}/queue`)
    .then((r) => r.json())
    .then((data) => renderQueue(data.queue));
}

if (window.roomId) {
  fetchQueue();
  setInterval(fetchQueue, 5000);
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
        fetch(`/api/rooms/${window.roomId}/queue/add`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ video_id: v.video_id, title: v.title })
        }).then(fetchQueue);
      };
      item.appendChild(thumb);
      item.appendChild(title);
      item.appendChild(btn);
      resultsEl.appendChild(item);
    });
  });
}
