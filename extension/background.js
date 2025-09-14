const SERVER_URL = "http://127.0.0.1:5000"; // Change if your server runs elsewhere

let playerTabId = null;
let ROOM_ID = null;

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
    let queue = data.queue;

    // If nothing is marked as current but the queue has songs, advance to next
    if (!currentId && queue.length > 0) {
      res = await fetch(`${SERVER_URL}/api/rooms/${ROOM_ID}/queue/next`, {
        method: "POST",
      });
      data = await res.json();
      currentId = data.current_song_id;
      queue = data.queue;
    }

    // No song to play, leave existing player tab until current video ends
    if (!currentId) {
      return;
    }

    const current = queue.find((s) => s._id === currentId);
    if (!current) return;

    const url = `https://www.youtube.com/watch?v=${current.video_id}`;
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
  }
});
