const stateBadge = document.querySelector("#connection-state");
const waitingCount = document.querySelector("#waiting-count");
const calledCount = document.querySelector("#called-count");
const businessDate = document.querySelector("#business-date");
const waitingList = document.querySelector("#waiting-list");
const lastTicketNo = document.querySelector("#last-ticket-no");
const lastTicketMeta = document.querySelector("#last-ticket-meta");

function setConnectionState(text, className) {
  stateBadge.textContent = text;
  stateBadge.className = `status-pill ${className}`;
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
    item.innerHTML = "<strong>暂无</strong><span>等待客户取号</span><span></span>";
    waitingList.appendChild(item);
  }
}

async function refreshState() {
  const resp = await fetch("/api/state");
  renderState(await resp.json());
}

async function takeTicket(priority) {
  const resp = await fetch("/api/tickets", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({priority})
  });
  if (!resp.ok) {
    lastTicketNo.textContent = "--";
    lastTicketMeta.textContent = "取号失败，请重试";
    return;
  }
  const ticket = await resp.json();
  lastTicketNo.textContent = ticket.ticket_no;
  lastTicketMeta.textContent = `${ticket.priority_label} · ${new Date(ticket.created_at).toLocaleTimeString()}`;
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
    if (message.type === "queue_snapshot") {
      renderState(message.state);
    }
  });
}

document.querySelectorAll("[data-priority]").forEach(button => {
  button.addEventListener("click", () => takeTicket(button.dataset.priority));
});

refreshState();
connectWs();
