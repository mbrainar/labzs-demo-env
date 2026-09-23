function humanize(seconds) {
  if (seconds < 0) seconds = 0;
  seconds = Math.floor(seconds);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ${minutes % 60}m ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ${hours % 24}h ago`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function renderTable(devices) {
  const body = document.getElementById("device-table-body");
  if (!devices.length) {
    body.innerHTML = '<tr><td colspan="5" class="empty">No devices have checked in yet.</td></tr>';
    return;
  }
  body.innerHTML = devices
    .map((d) => `
      <tr>
        <td><span class="dot ${d.online ? "online" : "offline"}"></span></td>
        <td><a href="/device/${encodeURIComponent(d.hostname)}">${escapeHtml(d.hostname)}</a></td>
        <td>${escapeHtml(d.ip_address)}</td>
        <td>${escapeHtml(d.device_time || "")}</td>
        <td class="time-since" data-received="${d.received_at}">${d.time_since}</td>
      </tr>`)
    .join("");
}

function tickRelativeTimes() {
  document.querySelectorAll(".time-since").forEach((cell) => {
    const received = cell.getAttribute("data-received");
    if (!received) return;
    const seconds = (Date.now() - new Date(received).getTime()) / 1000;
    cell.textContent = humanize(seconds);
  });
}

async function refreshDevices() {
  try {
    const res = await fetch("/api/devices");
    if (!res.ok) return;
    const devices = await res.json();
    renderTable(devices);
  } catch (err) {
    console.error("Failed to refresh devices", err);
  }
}

setInterval(tickRelativeTimes, 1000);
setInterval(refreshDevices, 15000);
