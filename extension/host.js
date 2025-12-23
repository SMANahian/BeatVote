function syncConfigFromHostPage(notifyType = "config-updated") {
  const el = document.getElementById("beatvote-extension-config");
  if (!el) {
    setTimeout(syncConfigFromHostPage, 800);
    return;
  }
  const roomId = el.dataset.roomId;
  const hostToken = el.dataset.hostToken;
  const serverUrl = el.dataset.serverUrl || window.location.origin;
  const useExtension = el.dataset.useExtension !== "false";
  if (!roomId || !hostToken) return;

  chrome.storage.local.set(
    {
      roomId,
      hostToken,
      serverUrl: serverUrl.replace(/\/+$/, ""),
      useExtension,
    },
    () => {
      chrome.runtime.sendMessage({ type: notifyType, useExtension });
    }
  );
}

window.addEventListener("queue-updated", () => {
  chrome.runtime.sendMessage({ type: "queue-updated" });
});

function attachButton() {
  const btn = document.getElementById("use-extension");
  if (!btn) {
    setTimeout(attachButton, 1000);
    return;
  }
  btn.addEventListener("click", () => {
    setTimeout(() => {
      syncConfigFromHostPage("host-state");
    }, 50);
  });
}

syncConfigFromHostPage("config-updated");
attachButton();
