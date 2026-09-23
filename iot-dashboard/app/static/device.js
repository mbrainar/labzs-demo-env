// Close the Actions menu when clicking anywhere outside it.
document.addEventListener("click", (e) => {
  document.querySelectorAll("details.actions[open]").forEach((d) => {
    if (!d.contains(e.target)) d.removeAttribute("open");
  });
});

// navigator.clipboard is unavailable on plain-http origins, so fall back to execCommand.
function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text);
  }
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.select();
  try {
    document.execCommand("copy");
  } finally {
    document.body.removeChild(ta);
  }
  return Promise.resolve();
}

// Copy actions. For the ssh:// link the navigation still proceeds; the copied
// command is the fallback for machines with no registered ssh:// handler.
document.querySelectorAll(".js-copy").forEach((el) => {
  el.addEventListener("click", () => {
    const text = el.getAttribute("data-copy");
    const isSsh = text.startsWith("ssh ");
    copyText(text)
      .then(() => {
        const note = document.getElementById("action-note");
        note.textContent = isSsh
          ? `Copied "${text}" to clipboard. If no SSH client opened, paste it into a terminal.`
          : `Copied "${text}" to clipboard.`;
        note.hidden = false;
      })
      .catch(() => {});
    el.closest("details").removeAttribute("open");
  });
});

// Destructive actions: show a confirmation dialog, then POST to the action's URL.
const dialog = document.getElementById("confirm-dialog");
const confirmForm = document.getElementById("confirm-form");

document.querySelectorAll("[data-confirm]").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.getElementById("confirm-title").textContent = btn.dataset.title;
    document.getElementById("confirm-message").textContent = btn.dataset.message;
    document.getElementById("confirm-submit").textContent = btn.dataset.confirmLabel;
    confirmForm.action = btn.dataset.url;
    btn.closest("details").removeAttribute("open");
    dialog.showModal();
  });
});

document.getElementById("confirm-cancel").addEventListener("click", () => dialog.close());
