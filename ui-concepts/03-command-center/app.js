const customers = {
  "CUS-001": {
    name: "Aarav Sharma",
    email: "aarav.sharma@example.test",
    orders: [
      { id: "ORD-1042", status: "Shipped", placed: "4 Aug 2026", delivery: "11 Aug 2026", payment: "Visa ending in 1842", address: "22 Lakeview Apartments, Koramangala, Bengaluru 560034", total: "₹7,498", items: [{ name: "NoiseBeat H100 Headphones", sku: "NB-H100-BLK", qty: 1, total: "₹7,498" }] },
      { id: "ORD-1038", status: "Cancelled", placed: "28 Jul 2026", delivery: "Cancelled", payment: "Visa ending in 1842", address: "22 Lakeview Apartments, Koramangala, Bengaluru 560034", total: "₹4,299", items: [{ name: "BrewPro Coffee Maker", sku: "BP-CM20-SLV", qty: 1, total: "₹4,299" }] }
    ]
  },
  "CUS-002": {
    name: "Meera Iyer",
    email: "meera.iyer@example.test",
    orders: [
      { id: "ORD-1087", status: "Processing", placed: "7 Aug 2026", delivery: "12 Aug 2026", payment: "UPI account", address: "8 Palm Grove, Adyar, Chennai 600020", total: "₹3,398", items: [{ name: "UrbanTrail Backpack", sku: "UT-BP45-GRN", qty: 1, total: "₹2,499" }, { name: "SteelSip Bottle", sku: "SS-B750-BLU", qty: 1, total: "₹899" }] },
      { id: "ORD-1095", status: "Delivered", placed: "1 Aug 2026", delivery: "8 Aug 2026 at 3:42 pm", payment: "UPI account", address: "8 Palm Grove, Adyar, Chennai 600020", total: "₹5,199", items: [{ name: "HomeChef Mixer", sku: "HC-MIX-750", qty: 1, total: "₹5,199" }] }
    ]
  },
  "CUS-003": {
    name: "Kabir Khan",
    email: "kabir.khan@example.test",
    orders: [
      { id: "ORD-1064", status: "Delivered", placed: "26 Jul 2026", delivery: "3 Aug 2026 at 1:15 pm", payment: "Mastercard ending in 7710", address: "51 Crescent Residency, Bandra West, Mumbai 400050", total: "₹6,398", items: [{ name: "NorthPeak Rain Jacket", sku: "NP-RJ-L-NVY", qty: 2, total: "₹6,398" }] }
    ]
  }
};

const select = document.querySelector("#customer-select");
const table = document.querySelector("#order-table");
const detail = document.querySelector("#order-detail");
const statusTag = document.querySelector("#detail-status");
let selectedCustomerId = "CUS-001";
let selectedOrderId = "ORD-1042";

Object.entries(customers).forEach(([id, customer]) => {
  const option = document.createElement("option");
  option.value = id;
  option.textContent = customer.name;
  select.append(option);
});

function initials(name) { return name.split(" ").map((part) => part[0]).join(""); }
function numericAmount(value) { return Number(value.replace(/[^0-9]/g, "")); }

function renderOverview() {
  const customer = customers[selectedCustomerId];
  const active = customer.orders.filter((order) => !["Delivered", "Cancelled"].includes(order.status)).length;
  const lifetime = customer.orders.reduce((sum, order) => sum + numericAmount(order.total), 0);
  document.querySelector("#customer-initials").textContent = initials(customer.name);
  document.querySelector("#customer-name").textContent = customer.name;
  const email = document.querySelector("#customer-email");
  email.textContent = customer.email;
  email.href = `mailto:${customer.email}`;
  document.querySelector("#metric-orders").textContent = customer.orders.length;
  document.querySelector("#metric-active").textContent = active;
  document.querySelector("#metric-value").textContent = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(lifetime);

  table.replaceChildren(...customer.orders.map((order) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `order-entry${order.id === selectedOrderId ? " is-selected" : ""}`;
    button.innerHTML = `<strong>${order.id}</strong><small>${order.placed} · ${order.status}</small><span class="amount">${order.total}</span>`;
    button.addEventListener("click", () => { selectedOrderId = order.id; renderOverview(); });
    return button;
  }));

  const order = customer.orders.find((item) => item.id === selectedOrderId) || customer.orders[0];
  selectedOrderId = order.id;
  statusTag.textContent = order.status;
  statusTag.className = `status-tag${order.status === "Cancelled" ? " cancelled" : ""}`;
  detail.innerHTML = `<div class="order-detail-content">
    <div class="detail-order-line"><h3>${order.id}</h3><span>Placed ${order.placed}</span></div>
    <div class="fact-grid">
      <div class="fact"><span>${order.status === "Delivered" ? "Delivered" : "Estimated delivery"}</span><strong>${order.delivery}</strong></div>
      <div class="fact"><span>Payment</span><strong>${order.payment}</strong></div>
      <div class="fact"><span>Delivery address</span><strong>${order.address}</strong></div>
      <div class="fact"><span>Order total</span><strong>${order.total}</strong></div>
    </div>
    <div class="line-items"><h4>Line items</h4>${order.items.map((item) => `<div class="line-item"><div><strong>${item.name}</strong><small>${item.sku} · Qty ${item.qty}</small></div><strong>${item.total}</strong></div>`).join("")}</div>
  </div>`;
}

select.addEventListener("change", () => {
  selectedCustomerId = select.value;
  selectedOrderId = customers[selectedCustomerId].orders[0].id;
  renderOverview();
});

function showView(viewName) {
  document.querySelectorAll(".view").forEach((view) => { view.hidden = view.id !== `${viewName}-view`; });
  document.querySelectorAll(".rail-action").forEach((button) => {
    const active = button.dataset.view === viewName;
    button.classList.toggle("is-active", active);
    active ? button.setAttribute("aria-current", "page") : button.removeAttribute("aria-current");
  });
  const overview = viewName === "overview";
  document.querySelector("#view-title").textContent = overview ? "Customer overview" : "Assistant workspace";
  document.querySelector("#customer-switcher").hidden = !overview;
  const command = document.querySelector("#command-button");
  command.querySelector("span").textContent = overview ? "Jump to assistant" : "Return to overview";
  command.querySelector("kbd").textContent = overview ? "⌘ J" : "⌘ O";
}

document.querySelectorAll(".rail-action").forEach((button) => button.addEventListener("click", () => showView(button.dataset.view)));
document.querySelector("#command-button").addEventListener("click", () => showView(document.querySelector("#overview-view").hidden ? "overview" : "assistant"));
document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "j") { event.preventDefault(); showView("assistant"); }
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "o") { event.preventDefault(); showView("overview"); }
});

const chatForm = document.querySelector("#chat-form");
const chatInput = document.querySelector("#chat-input");
const sendButton = document.querySelector("#send-button");
const messages = document.querySelector("#messages");
const activityPanel = document.querySelector(".activity-panel");
const activityList = document.querySelector("#activity-list");
const stages = [
  ["Question understood", "Intent and date context identified"],
  ["Orders fetched", "Recent customer records checked"],
  ["Matching products found", "Order items compared with the question"],
  ["Answer prepared", "Response grounded in order data"]
];

function addMessage(role, content) {
  const article = document.createElement("article");
  article.className = `message message-${role}`;
  const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const label = role === "assistant" ? '<span class="assistant-mark">N</span> Order assistant' : "You";
  article.innerHTML = `<div class="message-meta">${label}<time>${now}</time></div><div class="message-body"></div>`;
  const body = article.querySelector(".message-body");
  // Tiny, safe Markdown subset for the prototype: only **bold** is supported.
  content.split(/(\*\*[^*]+\*\*)/g).filter(Boolean).forEach((part) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      const strong = document.createElement("strong");
      strong.textContent = part.slice(2, -2);
      body.append(strong);
    } else body.append(document.createTextNode(part));
  });
  messages.append(article);
  article.scrollIntoView({ behavior: "smooth", block: "end" });
}

function resetActivity() {
  activityList.replaceChildren(...stages.map(([title, note]) => {
    const li = document.createElement("li");
    li.innerHTML = `<span></span><div><strong>${title}</strong><small>${note}</small></div>`;
    return li;
  }));
}

const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = chatInput.value.trim();
  if (!question) return;
  addMessage("user", question);
  chatInput.value = "";
  sendButton.disabled = true;
  activityPanel.classList.add("is-working");
  resetActivity();
  const items = [...activityList.children];
  for (let index = 0; index < items.length; index += 1) {
    if (index > 0) items[index - 1].className = "is-complete";
    items[index].className = "is-active";
    await wait(620);
  }
  items.at(-1).className = "is-complete";
  activityPanel.classList.remove("is-working");
  addMessage("assistant", "Order **ORD-1042 is expected to arrive on 11 Aug 2026**. Its current status is **shipped**.");
  sendButton.disabled = false;
  chatInput.focus();
});

document.querySelector("#clear-chat").addEventListener("click", () => {
  messages.replaceChildren();
  resetActivity();
  chatInput.focus();
});

renderOverview();
