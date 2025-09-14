let player;
let currentSongId = null;

function onYouTubeIframeAPIReady() {
  player = new YT.Player('player');
}

async function checkQueue() {
  if (!window.roomId) return;
  const res = await fetch(`/api/rooms/${window.roomId}/queue`);
  const queue = await res.json();
  if (queue.length && queue[0]._id !== currentSongId) {
    currentSongId = queue[0]._id;
    if (player) {
      player.loadVideoById(queue[0].video_id);
    }
  }
}

if (window.roomId) {
  checkQueue();
  setInterval(checkQueue, 5000);
}
