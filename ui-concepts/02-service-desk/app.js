const customers = {
  "CUS-001": {
    name: "Aarav Sharma",
    email: "aarav.sharma@example.test",
    orders: [
      { id: "ORD-1042", product: "NoiseBeat H100 Headphones", total: "₹7,498", date: "4 Aug 2026", status: "Shipped", delivery: "11 Aug 2026", payment: "Visa ending in 1842", address: "22 Lakeview Apartments<br>Koramangala, Bengaluru 560034" },
      { id: "ORD-1038", product: "BrewPro Coffee Maker", total: "₹4,299", date: "28 Jul 2026", status: "Cancelled", delivery: "2 Aug 2026", payment: "Visa ending in 1842", address: "22 Lakeview Apartments<br>Koramangala, Bengaluru 560034" }
    ]
  },
  "CUS-002": {
    name: "Meera Iyer",
    email: "meera.iyer@example.test",
    orders: [
      { id: "ORD-1087", product: "UrbanTrail Backpack + SteelSip Bottle", total: "₹3,398", date: "7 Aug 2026", status: "Processing", delivery: "12 Aug 2026", payment: "UPI account", address: "8 Palm Grove<br>Adyar, Chennai 600020" },
      { id: "ORD-1095", product: "HomeChef Mixer", total: "₹5,199", date: "1 Aug 2026", status: "Delivered", delivery: "8 Aug 2026", payment: "UPI account", address: "8 Palm Grove<br>Adyar, Chennai 600020" }
    ]
  },
  "CUS-003": {
    name: "Kabir Khan",
    email: "kabir.khan@example.test",
    orders: [
      { id: "ORD-1064", product: "NorthPeak Rain Jacket × 2", total: "₹6,398", date: "26 Jul 2026", status: "Delivered", delivery: "3 Aug 2026", payment: "Mastercard ending in 7710", address: "51 Crescent Residency<br>Bandra West, Mumbai 400050" }
    ]
  }
};

const tabs = [...document.querySelectorAll(".tab")];
const panels = { overview: document.querySelector("#overview-panel"), assistant: document.querySelector("#assistant-panel") };
const select = document.querySelector("#customer-select");
const ordersList = document.querySelector("#orders-list");
const conversation = document.querySelector("#conversation");
const activity = document.querySelector("#activity");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#chat-input");

function setTab(name) {
  tabs.forEach((tab) => {
    const active = tab.dataset.tab === name;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
  });
  Object.entries(panels).forEach(([key, panel]) => { panel.hidden = key !== name; });
}

tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => setTab(tab.dataset.tab));
  tab.addEventListener("keydown", (event) => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    const offset = event.key === 'ArrowRight' ? 1 : -1;
    const next = tabs[(index + offset + tabs.length) % tabs.length];
    setTab(next.dataset.tab);
    next.focus();
  });
});

function statusClass(status) { return `status--${status.toLowerCase()}`; }

function showDetail(order) {
  document.querySelector("#detail-heading").textContent = order.id;
  const status = document.querySelector("#detail-status");
  status.textContent = order.status;
  status.className = `status ${statusClass(order.status)}`;
  document.querySelector("#detail-product").textContent = order.product;
  document.querySelector("#detail-total").textContent = order.total;
  document.querySelector("#detail-delivery").textContent = order.delivery;
  document.querySelector("#detail-payment").textContent = order.payment;
  document.querySelector("#detail-address").innerHTML = order.address;
  [...ordersList.children].forEach((row) => row.classList.toggle("is-selected", row.dataset.order === order.id));
}

function renderCustomer(id, resetConversation = true) {
  const customer = customers[id];
  document.querySelector("#customer-name").textContent = customer.name;
  document.querySelector("#customer-email").textContent = customer.email;
  document.querySelector("#order-count").textContent = customer.orders.length;
  ordersList.replaceChildren();
  customer.orders.forEach((order, index) => {
    const row = document.createElement("button");
    row.type = "button";
    row.className = `order-row${index === 0 ? " is-selected" : ""}`;
    row.dataset.order = order.id;
    row.innerHTML = `<span><span class="order-row__product">${order.product}</span><span class="order-row__id">${order.id} · ${order.status}</span></span><span class="order-row__amount">${order.total}</span><span class="order-row__date">${order.date}</span>`;
    row.addEventListener("click", () => showDetail(order));
    ordersList.append(row);
  });
  showDetail(customer.orders[0]);
  if (resetConversation) resetChat();
}

select.addEventListener("change", () => renderCustomer(select.value));

function addMessage(role, html) {
  const wrapper = document.createElement("div");
  wrapper.className = `message message--${role}`;
  if (role === "user") {
    wrapper.innerHTML = `<div class="message__label">You</div><div class="message__bubble"></div>`;
  } else {
    wrapper.innerHTML = `<div class="assistant-avatar" aria-hidden="true">N</div><div><div class="message__label">Northstar assistant</div><div class="message__bubble message__bubble--assistant"></div></div>`;
  }
  wrapper.querySelector(".message__bubble").innerHTML = html;
  conversation.append(wrapper);
  wrapper.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function escapeHtml(value) {
  const node = document.createElement("div");
  node.textContent = value;
  return node.innerHTML;
}

const stages = [
  ["Understanding your question", "Reviewing the conversation context…"],
  ["Looking for matching products", "Checking recent purchases on this account…"],
  ["Fetching order details", "Confirming status, price, and delivery information…"],
  ["Preparing your answer", "Turning the order record into a clear response…"]
];

async function simulateReply(question) {
  activity.hidden = false;
  form.querySelector("button").disabled = true;
  for (const [title, detail] of stages) {
    document.querySelector("#activity-title").textContent = title;
    document.querySelector("#activity-detail").textContent = detail;
    await new Promise((resolve) => setTimeout(resolve, 720));
  }
  activity.hidden = true;
  form.querySelector("button").disabled = false;
  const current = customers[select.value].orders[0];
  const response = question.toLowerCase().includes("arriv") || question.toLowerCase().includes("deliver")
    ? `Your most recent order is expected to arrive by <strong>${current.delivery}</strong>. Its current status is <strong>${current.status}</strong>.`
    : `I found your most recent purchase: <strong>${current.product}</strong> for <strong>${current.total}</strong>. It is part of order <strong>${current.id}</strong>.`;
  addMessage("assistant", response);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question || form.querySelector("button").disabled) return;
  addMessage("user", escapeHtml(question));
  input.value = "";
  await simulateReply(question);
  input.focus();
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
});

function resetChat() {
  conversation.innerHTML = "";
  activity.hidden = true;
  addMessage("assistant", "Hello. I can help with order status, delivery dates, products, and payments. What would you like to know?");
}

document.querySelector("#new-chat").addEventListener("click", resetChat);

renderCustomer(select.value, false);
