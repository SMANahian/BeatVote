const SERVER_URL = "http://127.0.0.1:5000"; // Change if your server runs elsewhere

let playerTabId = null;
let ROOM_ID = null;
let currentSongId = null; // Track the currently playing song entry

chrome.storage.local.get('roomId', (res) => {
  ROOM_ID = res.roomId;
  init();
});

function ensureHostTab() {
  if (!ROOM_ID) return;
  const hostPage = `${SERVER_URL}/${ROOM_ID}/host`;
  chrome.tabs.query({ url: `${SERVER_URL}/*` }, (tabs) => {
    const exists = tabs.some((t) => t.url === hostPage);
    if (!exists) {
      chrome.tabs.create({ url: hostPage, pinned: true });
    }
  });
}

async function ensurePlayback() {
  if (!ROOM_ID) return;
  try {
    // Fetch current queue state without mutating it
    let res = await fetch(`${SERVER_URL}/api/rooms/${ROOM_ID}/queue`);
    let data = await res.json();
    let currentId = data.current_song_id;
    let currentSong = data.current_song;
    if (!currentId && currentSong) {
      currentId = currentSong._id;
    }
    let queue = data.queue;

    // If nothing is marked as current but the queue has songs, advance to next
    if (!currentId && !currentSong && queue.length > 0) {
      res = await fetch(`${SERVER_URL}/api/rooms/${ROOM_ID}/queue/next`, {
        method: "POST",
      });
      data = await res.json();
      currentId = data.current_song_id;
      currentSong = data.current_song;
      queue = data.queue;
      if (!currentId && currentSong) {
        currentId = currentSong._id;
      }
    }

    // No song to play, leave existing player tab until current video ends
    if (!currentId && !currentSong) {
      currentSongId = null;
      return;
    }

    if (!currentSong && currentId) {
      currentSong = queue.find((s) => s._id === currentId);
    }

    if (!currentSong) return;

    const nextSongId = currentSong._id || currentId;
    const url = `https://www.youtube.com/watch?v=${currentSong.video_id}`;

    // Only create/update tab if the song entry is different
    if (nextSongId !== currentSongId) {
      currentSongId = nextSongId;
      if (playerTabId == null) {
        chrome.tabs.create({ url }, (tab) => {
          playerTabId = tab.id;
        });
      } else {
        chrome.tabs.update(playerTabId, { url }, () => {
          if (chrome.runtime.lastError) {
            chrome.tabs.remove(playerTabId, () => {
              chrome.tabs.create({ url }, (tab) => {
                playerTabId = tab.id;
              });
            });
          }
        });
      }
    }
    // If same song entry, do nothing (prevents reload loop)
  } catch (e) {
    console.error("Failed to ensure playback", e);
  }
}

async function advanceAndPlayNext() {
  if (!ROOM_ID) return;
  try {
    await fetch(`${SERVER_URL}/api/rooms/${ROOM_ID}/queue/next`, {
      method: "POST",
    });
  } catch (e) {
    console.error("Failed to advance queue", e);
  }
  ensurePlayback();
}

function init() {
  ensureHostTab();
  ensurePlayback();
}

chrome.runtime.onInstalled.addListener(init);
chrome.runtime.onStartup.addListener(init);

chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.type === "video-ended") {
    if (sender.tab) {
      chrome.tabs.remove(sender.tab.id);
      if (sender.tab.id === playerTabId) {
        playerTabId = null;
      }
    }
    advanceAndPlayNext();
  } else if (msg.type === "use-extension" || msg.type === "queue-updated") {
    ensurePlayback();
  } else if (msg.type === "room-updated") {
    chrome.storage.local.get('roomId', (res) => {
      ROOM_ID = res.roomId;
      init();
    });
  }
});

chrome.tabs.onRemoved.addListener((tabId) => {
  if (tabId === playerTabId) {
    playerTabId = null;
    currentSongId = null; // Reset when tab is closed
  }
});
