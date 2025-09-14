let player;
let currentSongId = null;
let currentVideoId = null;
const queueEl = document.getElementById('queue');
const toggleBtn = document.getElementById('use-extension');

let useExtension = true;
const storedPref = localStorage.getItem('useExtension');
if (storedPref !== null) {
  useExtension = storedPref === 'true';
} else {
  localStorage.setItem('useExtension', 'true');
}

function updatePlayerMode() {
  if (!toggleBtn) return;
  if (useExtension) {
    toggleBtn.textContent = 'Use Web Player';
    const playerEl = document.getElementById('player');
    if (playerEl) playerEl.style.display = 'none';
    if (player) {
      try {
        player.stopVideo();
      } catch (e) {
        // ignore
      }
    }
  } else {
    toggleBtn.textContent = 'Use Extension Player';
    const playerEl = document.getElementById('player');
    if (playerEl) playerEl.style.display = '';
    checkQueue();
  }
}

if (toggleBtn) {
  toggleBtn.addEventListener('click', () => {
    useExtension = !useExtension;
    localStorage.setItem('useExtension', useExtension.toString());
    updatePlayerMode();
  });
  updatePlayerMode();
}

function onYouTubeIframeAPIReady() {
  player = new YT.Player('player', {
    events: {
      onStateChange: onPlayerStateChange,
      onError: onPlayerError,
    },
  });
}

function onPlayerStateChange(event) {
  if (!useExtension && event.data === YT.PlayerState.ENDED) {
    fetch(`/api/rooms/${window.roomId}/queue/next`, { method: 'POST' })
      .then((r) => r.json())
      .then(renderQueue);
  }
}

function onPlayerError() {
  if (!useExtension) {
    fetch(`/api/rooms/${window.roomId}/queue/next`, { method: 'POST' })
      .then((r) => r.json())
      .then(renderQueue);
  }
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
    currentVideoId = nextSong.video_id;
    if (player && !useExtension) {
      player.loadVideoById(nextSong.video_id);
    }
  }
}

async function checkQueue() {
  if (!window.roomId) return;
  const res = await fetch(`/api/rooms/${window.roomId}/queue`);
  const data = await res.json();
  renderQueue(data);
  window.dispatchEvent(new Event('queue-updated'));
}

if (window.roomId) {
  checkQueue();
  setInterval(checkQueue, 5000);
}
