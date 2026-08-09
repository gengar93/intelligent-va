const customers = {
  "CUS-001": {
    name: "Aarav Sharma", email: "aarav.sharma@example.test", value: "₹11,797.00",
    orders: [
      { id: "ORD-1042", status: "shipped", date: "4 Aug 2026", placed: "Placed 4 Aug 2026, 2:20 pm", total: "₹7,498.00", delivery: "11 Aug 2026", payment: "Visa ending in 1842", address: "22 Lakeview Apartments, Koramangala, Bengaluru 560034", items: [{ name: "NoiseBeat H100 Headphones", sku: "NB-H100-BLK", qty: 1, price: "₹7,498.00", total: "₹7,498.00" }] },
      { id: "ORD-1038", status: "cancelled", date: "28 Jul 2026", placed: "Placed 28 Jul 2026, 10:05 am", total: "₹4,299.00", delivery: "Cancelled", payment: "Visa ending in 1842", address: "22 Lakeview Apartments, Koramangala, Bengaluru 560034", items: [{ name: "BrewPro Coffee Maker", sku: "BP-CM20-SLV", qty: 1, price: "₹4,299.00", total: "₹4,299.00" }] }
    ]
  },
  "CUS-002": {
    name: "Meera Iyer", email: "meera.iyer@example.test", value: "₹8,597.00",
    orders: [
      { id: "ORD-1087", status: "processing", date: "7 Aug 2026", placed: "Placed 7 Aug 2026, 9:15 am", total: "₹3,398.00", delivery: "12 Aug 2026", payment: "UPI account", address: "8 Palm Grove, Adyar, Chennai 600020", items: [{ name: "UrbanTrail Backpack", sku: "UT-BP45-GRN", qty: 1, price: "₹2,499.00", total: "₹2,499.00" }, { name: "SteelSip Bottle", sku: "SS-B750-BLU", qty: 1, price: "₹899.00", total: "₹899.00" }] },
      { id: "ORD-1095", status: "delivered", date: "1 Aug 2026", placed: "Placed 1 Aug 2026, 12:30 pm", total: "₹5,199.00", delivery: "Delivered 8 Aug 2026", payment: "UPI account", address: "8 Palm Grove, Adyar, Chennai 600020", items: [{ name: "HomeChef Mixer", sku: "HC-MIX-750", qty: 1, price: "₹5,199.00", total: "₹5,199.00" }] }
    ]
  },
  "CUS-003": {
    name: "Kabir Khan", email: "kabir.khan@example.test", value: "₹6,398.00",
    orders: [{ id: "ORD-1064", status: "delivered", date: "26 Jul 2026", placed: "Placed 26 Jul 2026, 11:10 am", total: "₹6,398.00", delivery: "Delivered 3 Aug 2026", payment: "Mastercard ending in 7710", address: "51 Crescent Residency, Bandra West, Mumbai 400050", items: [{ name: "NorthPeak Rain Jacket", sku: "NP-RJ-L-NVY", qty: 2, price: "₹3,199.00", total: "₹6,398.00" }] }]
  }
};

const $ = (selector) => document.querySelector(selector);
let selectedCustomer = "CUS-001";
let demoGeneration = 0;

function titleCase(value) { return value[0].toUpperCase() + value.slice(1); }

function renderOrder(order) {
  $("#record-title").textContent = order.id;
  $("#record-date").textContent = order.placed;
  $("#record-status").textContent = titleCase(order.status);
  $("#record-status").className = `status status--${order.status}`;
  $("#delivery-date").textContent = order.delivery;
  $("#payment").textContent = order.payment;
  $("#address").textContent = order.address;
  $("#item-summary").textContent = `${order.items.reduce((n, item) => n + item.qty, 0)} ${order.items.length === 1 ? "item" : "items"}`;
  $("#line-items-body").innerHTML = order.items.map(item => `<tr><td><strong>${item.name}</strong></td><td>${item.sku}</td><td>${item.qty}</td><td>${item.price}</td><td>${item.total}</td></tr>`).join("");
  $("#order-total").textContent = order.total;
  document.querySelectorAll(".order-row").forEach(row => row.classList.toggle("is-active", row.dataset.order === order.id));
}

function renderCustomer(id) {
  selectedCustomer = id;
  const customer = customers[id];
  $("#customer-name").textContent = customer.name;
  $("#customer-email").textContent = customer.email;
  $("#customer-email").href = `mailto:${customer.email}`;
  $("#order-count").textContent = customer.orders.length;
  $("#open-count").textContent = customer.orders.filter(order => ["processing", "shipped"].includes(order.status)).length;
  $("#lifetime-value").textContent = customer.value;
  $("#order-list").innerHTML = customer.orders.map((order, index) => `
    <button type="button" class="order-row${index === 0 ? " is-active" : ""}" data-order="${order.id}">
      <strong>${order.id}</strong><span class="status status--${order.status}">${titleCase(order.status)}</span>
      <span class="order-row__date">${order.date}</span><span class="order-row__items">${order.items.length} ${order.items.length === 1 ? "line item" : "line items"}</span>
      <span></span><span class="order-row__total">${order.total}</span>
    </button>`).join("");
  document.querySelectorAll(".order-row").forEach(row => row.addEventListener("click", () => renderOrder(customer.orders.find(order => order.id === row.dataset.order))));
  renderOrder(customer.orders[0]);
  resetChat();
}

document.querySelectorAll(".tab").forEach(tab => tab.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach(item => { item.classList.remove("is-active"); item.setAttribute("aria-selected", "false"); });
  tab.classList.add("is-active"); tab.setAttribute("aria-selected", "true");
  document.querySelectorAll(".view").forEach(view => { view.hidden = view.id !== tab.dataset.tab; });
}));

$("#customer").addEventListener("change", event => renderCustomer(event.target.value));

function resetChat() {
  demoGeneration += 1;
  const welcome = document.createElement("div");
  welcome.className = "conversation-empty";
  const mark = document.createElement("span");
  mark.setAttribute("aria-hidden", "true");
  mark.textContent = "OD";
  const heading = document.createElement("strong");
  heading.textContent = `Hello, ${customers[selectedCustomer].name}`;
  const guidance = document.createElement("p");
  guidance.textContent = "Type your order question below to get started.";
  welcome.append(mark, heading, guidance);
  $("#messages").replaceChildren(welcome);
  $("#activity-log").innerHTML = `<li><span>·</span><div><strong>No active request</strong><small>Submit a question to begin</small></div></li>`;
  $("#activity-inline").hidden = true;
  $("#send").disabled = false;
}

function addMessage(role, body) {
  $(".conversation-empty")?.remove();
  const article = document.createElement("article");
  article.className = `message message--${role}`;
  article.innerHTML = `<div class="message__meta">${role === "user" ? "You" : "Order assistant"} <time>now</time></div><div class="message__body">${body}</div>`;
  $("#messages").append(article);
  article.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function runDemo(question) {
  const generation = ++demoGeneration;
  const steps = [
    ["Understanding question", "Understanding your question…"],
    ["Searching recent orders", "Looking for matching products…"],
    ["Reading order details", "Fetching order details…"],
    ["Preparing response", "Preparing your answer…"]
  ];
  $("#activity-log").innerHTML = "";
  $("#activity-inline").hidden = false;
  $("#send").disabled = true;

  for (let i = 0; i < steps.length; i += 1) {
    $("#activity-text").textContent = steps[i][1];
    const li = document.createElement("li");
    li.className = "is-active";
    li.innerHTML = `<span>•</span><div><strong>${steps[i][0]}</strong><small>In progress</small></div>`;
    $("#activity-log").append(li);
    await delay(520);
    if (generation !== demoGeneration) return;
    li.className = "is-complete";
    li.innerHTML = `<span>✓</span><div><strong>${steps[i][0]}</strong><small>Completed</small></div>`;
  }

  if (generation !== demoGeneration) return;
  const firstOrder = customers[selectedCustomer].orders[0];
  addMessage("assistant", `The most recent order is <strong>${firstOrder.id}</strong>. Its current status is <strong>${titleCase(firstOrder.status)}</strong>, and the order total is <strong>${firstOrder.total}</strong>.`);
  $("#activity-inline").hidden = true;
  $("#send").disabled = false;
  $("#message").focus();
}

$("#chat-form").addEventListener("submit", event => {
  event.preventDefault();
  const input = $("#message");
  const value = input.value.trim();
  if (!value || $("#send").disabled) return;
  addMessage("user", value.replace(/[<>]/g, ""));
  input.value = "";
  runDemo(value);
});

$("#message").addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); $("#chat-form").requestSubmit(); }
});
$("#new-chat").addEventListener("click", resetChat);

renderCustomer(selectedCustomer);
