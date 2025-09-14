let player;
let pendingVideoId = null;

// Load the YouTube IFrame API dynamically so that the callback is
// defined before the script requests it. This avoids situations where
// the API loads before our handler is ready, leaving `player`
// undefined and preventing videos from playing on the host's player.
const tag = document.createElement('script');
tag.src = 'https://www.youtube.com/iframe_api';
document.head.appendChild(tag);

window.onYouTubeIframeAPIReady = function () {
  player = new YT.Player('player', {
    events: {
      onReady: () => {
        if (pendingVideoId) {
          player.loadVideoById(pendingVideoId);
          pendingVideoId = null;
        }
      },
    },
  });
};

socket.on('player:play', (data) => {
  if (player) {
    player.loadVideoById(data.video_id);
  } else {
    // Player is not ready yet; remember the video id so it can be
    // loaded once the API is initialised.
    pendingVideoId = data.video_id;
  }
});
