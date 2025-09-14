const SERVER_URL = "http://localhost:5000"; // Change if your server runs elsewhere

let playerTabId = null;
let ROOM_ID = null;

chrome.storage.local.get('roomId', (res) => {
  ROOM_ID = res.roomId;
  init();
});

function ensureHostTab() {
  if (!ROOM_ID) return;
  const hostPage = `${SERVER_URL}/rooms/${ROOM_ID}/host`;
  chrome.tabs.query({ url: `${SERVER_URL}/*` }, (tabs) => {
    const exists = tabs.some((t) => t.url === hostPage);
    if (!exists) {
      chrome.tabs.create({ url: hostPage, pinned: true });
    }
  });
}

async function playNext() {
  if (!ROOM_ID) return;
  try {
    const res = await fetch(
      `${SERVER_URL}/api/rooms/${ROOM_ID}/queue/next`,
      { method: "POST" }
    );
    const data = await res.json();
    const currentId = data.current_song_id;
    if (!currentId) {
      if (playerTabId != null) {
        chrome.tabs.remove(playerTabId);
        playerTabId = null;
      }
      return;
    }
    const current = data.queue.find((s) => s._id === currentId);
    if (!current) {
      return;
    }
    const url = `https://www.youtube.com/watch?v=${current.video_id}`;
    if (playerTabId == null) {
      chrome.tabs.create({ url }, (tab) => {
        playerTabId = tab.id;
      });
    } else {
      chrome.tabs.update(playerTabId, { url }, () => {
        if (chrome.runtime.lastError) {
          chrome.tabs.create({ url }, (tab) => {
            playerTabId = tab.id;
          });
        }
      });
    }
  } catch (e) {
    console.error("Failed to play next song", e);
  }
}

function init() {
  ensureHostTab();
  playNext();
}

chrome.runtime.onInstalled.addListener(init);
chrome.runtime.onStartup.addListener(init);

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === "video-ended" || msg.type === "use-extension") {
    playNext();
  } else if (msg.type === 'room-updated') {
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
