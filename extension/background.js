let serverUrl = "http://127.0.0.1:5000";
let roomId = null;
let hostToken = null;
let useExtension = true;

let playerTabId = null;
let currentVideoId = null;

function loadConfig() {
  return new Promise((resolve) => {
    chrome.storage.local.get(
      ["serverUrl", "roomId", "hostToken", "useExtension"],
      (res) => {
      serverUrl = (res.serverUrl || serverUrl).replace(/\/+$/, "");
      roomId = res.roomId || roomId;
      hostToken = res.hostToken || hostToken;
      useExtension = typeof res.useExtension === "boolean" ? res.useExtension : useExtension;
      resolve();
      }
    );
  });
}

function ensureHostTab() {
  if (!roomId) return;
  const hostPage = `${serverUrl}/${roomId}/host`;
  chrome.tabs.query({}, (tabs) => {
    const existing = tabs.find((t) => t.url === hostPage);
    if (!existing) {
      chrome.tabs.create({ url: hostPage, pinned: true });
      return;
    }
    if (!existing.pinned) {
      chrome.tabs.update(existing.id, { pinned: true });
    }
  });
}

async function apiFetch(path, init) {
  const headers = new Headers((init && init.headers) || {});
  if (hostToken) {
    headers.set("X-BeatVote-Host-Token", hostToken);
  }
  return fetch(`${serverUrl}${path}`, { ...(init || {}), headers });
}

async function ensurePlayback() {
  if (!roomId) return;
  if (!useExtension) {
    if (playerTabId != null) {
      chrome.tabs.remove(playerTabId);
      playerTabId = null;
      currentVideoId = null;
    }
    return;
  }
  try {
    // Fetch current queue state without mutating it
    let res = await apiFetch(`/api/rooms/${roomId}/queue`);
    let data = await res.json();
    let currentId = data.current_song_id;
    let queue = data.queue;

    // If nothing is marked as current but the queue has songs, advance to next
    if (!currentId && queue.length > 0) {
      if (!hostToken) return;
      res = await apiFetch(`/api/rooms/${roomId}/queue/next`, { method: "POST" });
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

    // Only create/update tab if video_id is different
    if (current.video_id !== currentVideoId) {
      currentVideoId = current.video_id;
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
    // If same video, do nothing (prevents reload loop)
  } catch (e) {
    console.error("Failed to ensure playback", e);
  }
}

async function advanceAndPlayNext() {
  if (!roomId || !hostToken) return;
  try {
    await apiFetch(`/api/rooms/${roomId}/queue/next`, { method: "POST" });
  } catch (e) {
    console.error("Failed to advance queue", e);
  }
  ensurePlayback();
}

async function init() {
  await loadConfig();
  if (!roomId) return;
  ensureHostTab();
  ensurePlayback();

  chrome.alarms.create("beatvote-tick", { periodInMinutes: 0.1 });
}

chrome.runtime.onInstalled.addListener(init);
chrome.runtime.onStartup.addListener(init);

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name !== "beatvote-tick") return;
  ensureHostTab();
  ensurePlayback();
});

chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.type === "video-ended") {
    if (sender.tab) {
      chrome.tabs.remove(sender.tab.id);
      if (sender.tab.id === playerTabId) {
        playerTabId = null;
      }
    }
    advanceAndPlayNext();
  } else if (msg.type === "queue-updated") {
    ensurePlayback();
  } else if (msg.type === "config-updated") {
    init();
  } else if (msg.type === "host-state") {
    useExtension = msg.useExtension !== false;
    ensurePlayback();
  }
});

chrome.tabs.onRemoved.addListener((tabId) => {
  if (tabId === playerTabId) {
    playerTabId = null;
    currentVideoId = null; // Reset when tab is closed
  }
});
