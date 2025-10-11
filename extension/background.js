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

function resolveCurrentSong(data) {
  if (!data) return null;
  let currentId = data.current_song_id;
  let currentSong = data.current_song;

  if (!currentId && currentSong) {
    currentId = currentSong._id;
  }

  if (!currentSong && currentId && Array.isArray(data.queue)) {
    currentSong = data.queue.find((s) => s._id === currentId);
  }

  if (!currentId && !currentSong) {
    currentSongId = null;
    return null;
  }

  if (!currentSong) {
    currentSongId = null;
    return null;
  }

  const nextSongId = currentSong._id || currentId;
  return { song: currentSong, id: nextSongId };
}

function openSongInPlayer(songEntry) {
  if (!songEntry) return false;
  const { song, id } = songEntry;
  const url = `https://www.youtube.com/watch?v=${song.video_id}`;

  if (playerTabId == null) {
    currentSongId = id;
    chrome.tabs.create({ url }, (tab) => {
      playerTabId = tab.id;
    });
    return true;
  }

  if (id !== currentSongId) {
    currentSongId = id;
    chrome.tabs.update(playerTabId, { url }, () => {
      if (chrome.runtime.lastError) {
        chrome.tabs.remove(playerTabId, () => {
          chrome.tabs.create({ url }, (tab) => {
            playerTabId = tab.id;
          });
        });
      }
    });
    return true;
  }

  // Already on the correct queue entry
  return true;
}

async function applyQueueSnapshot(data) {
  const songEntry = resolveCurrentSong(data);
  if (!songEntry) {
    return false;
  }
  return openSongInPlayer(songEntry);
}

async function ensurePlayback() {
  if (!ROOM_ID) return;
  try {
    let res = await fetch(`${SERVER_URL}/api/rooms/${ROOM_ID}/queue`);
    if (!res.ok) {
      throw new Error(`Queue fetch failed: ${res.status}`);
    }
    let data = await res.json();
    const started = await applyQueueSnapshot(data);
    if (started) return;

    if (Array.isArray(data.queue) && data.queue.length > 0) {
      res = await fetch(`${SERVER_URL}/api/rooms/${ROOM_ID}/queue/next`, {
        method: "POST",
      });
      if (!res.ok) {
        throw new Error(`Queue advance failed: ${res.status}`);
      }
      data = await res.json();
      await applyQueueSnapshot(data);
    }
  } catch (e) {
    console.error("Failed to ensure playback", e);
  }
}

async function advanceAndPlayNext() {
  if (!ROOM_ID) return;
  try {
    const res = await fetch(`${SERVER_URL}/api/rooms/${ROOM_ID}/queue/next`, {
      method: "POST",
    });
    if (!res.ok) {
      throw new Error(`Advance failed: ${res.status}`);
    }
    const data = await res.json();
    await applyQueueSnapshot(data);
  } catch (e) {
    console.error("Failed to advance queue", e);
    ensurePlayback();
  }
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
        currentSongId = null;
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
