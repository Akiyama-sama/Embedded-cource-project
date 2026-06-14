const stationId = window.STATION_ID;
const stateBadge = document.querySelector("#connection-state");
const waitingCount = document.querySelector("#waiting-count");
const calledCount = document.querySelector("#called-count");
const businessDate = document.querySelector("#business-date");
const waitingList = document.querySelector("#waiting-list");
const currentTicketNo = document.querySelector("#current-ticket-no");
const currentAnnouncement = document.querySelector("#current-announcement");

function setConnectionState(text, className) {
  stateBadge.textContent = text;
  stateBadge.className = `status-pill ${className}`;
}

function speak(text) {
  if (!("speechSynthesis" in window)) {
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "zh-CN";
  utterance.rate = 0.9;
  window.speechSynthesis.speak(utterance);
}

function renderCall(call, shouldSpeak) {
  currentTicketNo.textContent = call.ticket_no;
  currentAnnouncement.textContent = call.announcement_text;
  if (shouldSpeak) {
    speak(call.announcement_text);
  }
}

function renderState(state) {
  businessDate.textContent = state.business_date;
  waitingCount.textContent = state.waiting_count;
  calledCount.textContent = state.called_count;
  waitingList.innerHTML = "";
  for (const ticket of state.waiting_tickets) {
    const item = document.createElement("li");
    item.innerHTML = `<strong>${ticket.ticket_no}</strong><span>${ticket.priority_label}</span><span>${new Date(ticket.created_at).toLocaleTimeString()}</span>`;
    waitingList.appendChild(item);
  }
  if (state.waiting_tickets.length === 0) {
    const item = document.createElement("li");
    item.innerHTML = "<strong>暂无</strong><span>没有等待客户</span><span></span>";
    waitingList.appendChild(item);
  }
  if (state.last_calls[stationId]) {
    renderCall(state.last_calls[stationId], false);
  }
}

async function refreshState() {
  const resp = await fetch("/api/state");
  renderState(await resp.json());
}

async function stationPost(action) {
  const resp = await fetch(`/api/stations/${stationId}/${action}`, {method: "POST"});
  if (!resp.ok) {
    currentTicketNo.textContent = "--";
    currentAnnouncement.textContent = "当前没有可呼叫号码";
    return;
  }
  renderCall(await resp.json(), true);
}

function connectWs() {
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${location.host}/ws`);
  socket.addEventListener("open", () => setConnectionState("已连接", "online"));
  socket.addEventListener("close", () => {
    setConnectionState("已断开", "offline");
    setTimeout(connectWs, 1500);
  });
  socket.addEventListener("message", event => {
    const message = JSON.parse(event.data);
    if (message.type !== "queue_snapshot") {
      return;
    }
    renderState(message.state);
    if ((message.event === "ticket_called" || message.event === "call_repeated") && message.payload.station_id === stationId) {
      renderCall(message.payload, false);
    }
  });
}

document.querySelector("#call-next-btn").addEventListener("click", () => stationPost("next"));
document.querySelector("#repeat-call-btn").addEventListener("click", () => stationPost("repeat"));

refreshState();
connectWs();
