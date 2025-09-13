let player;
function onYouTubeIframeAPIReady() {
  player = new YT.Player('player');
}

socket.on('player:play', data => {
  if (player) {
    player.loadVideoById(data.video_id);
  }
});
