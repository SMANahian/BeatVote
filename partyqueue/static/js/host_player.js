let player;
let currentSongId = null;
const queueEl = document.getElementById('queue');

function onYouTubeIframeAPIReady() {
  player = new YT.Player('player', {
    events: {
      onStateChange: onPlayerStateChange,
      onError: onPlayerError,
    },
  });
}

function onPlayerStateChange(event) {
  if (event.data === YT.PlayerState.ENDED) {
    fetch(`/api/rooms/${window.roomId}/queue/next`, { method: 'POST' })
      .then((r) => r.json())
      .then(renderQueue);
  }
}

function onPlayerError(event) {
  fetch(`/api/rooms/${window.roomId}/queue/next`, { method: 'POST' })
    .then((r) => r.json())
    .then(renderQueue);
}

function renderQueue(data) {
  const queue = data.queue;
  queueEl.innerHTML = '';
  queue.forEach((s) => {
    const li = document.createElement('li');
    li.className = 'mb-2';
    const title = document.createElement('span');
    title.textContent = `${s.title} (score: ${s.score})`;
    const playBtn = document.createElement('button');
    playBtn.textContent = 'Play';
    playBtn.onclick = () => {
      fetch(`/api/rooms/${window.roomId}/queue/${s._id}/play`, { method: 'POST' }).then(checkQueue);
    };
    const removeBtn = document.createElement('button');
    removeBtn.textContent = 'Remove';
    removeBtn.onclick = () => {
      fetch(`/api/rooms/${window.roomId}/queue/${s._id}/remove`, { method: 'POST' }).then(checkQueue);
    };
    li.appendChild(title);
    li.appendChild(playBtn);
    li.appendChild(removeBtn);
    queueEl.appendChild(li);
  });

  let nextSong = queue[0];
  if (data.current_song_id) {
    const found = queue.find((s) => s._id === data.current_song_id);
    if (found) {
      nextSong = found;
    }
  }
  if (nextSong && nextSong._id !== currentSongId) {
    currentSongId = nextSong._id;
    if (player) {
      player.loadVideoById(nextSong.video_id);
    }
  }
}

async function checkQueue() {
  if (!window.roomId) return;
  const res = await fetch(`/api/rooms/${window.roomId}/queue`);
  const data = await res.json();
  renderQueue(data);
}

if (window.roomId) {
  checkQueue();
  setInterval(checkQueue, 5000);
}
