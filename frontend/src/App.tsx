import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import ReactMarkdown from "react-markdown";

import { fetchCustomerOrders, fetchCustomers, streamChatMessage } from "./api";
import type { ChatMessage, Customer, CustomerOrders, Order, OrderStatus } from "./types";

const STATUS_LABELS: Record<OrderStatus, string> = {
  processing: "Processing",
  shipped: "Shipped",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

const MARKDOWN_ELEMENTS = ["p", "strong", "em", "ul", "ol", "li", "code", "br"];

function formatMoney(amountMinor: number, currency: string): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(amountMinor / 100);
}

function formatDate(value: string | null, includeTime = false): string {
  if (!value) return "Not available";
  const parsedValue = value.includes("T") ? value : `${value}T00:00:00`;
  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    ...(includeTime ? { hour: "numeric", minute: "2-digit" } : {}),
  }).format(new Date(parsedValue));
}

function itemCount(order: Order): number {
  return order.items.reduce((total, item) => total + item.quantity, 0);
}

function StatusBadge({ status }: { status: OrderStatus }) {
  return <span className={`status status--${status}`}>{STATUS_LABELS[status]}</span>;
}

function LoadingState() {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <span>Loading customer records…</span>
    </div>
  );
}

function OrderList({
  orders,
  selectedOrderId,
  onSelect,
}: {
  orders: Order[];
  selectedOrderId: string | null;
  onSelect: (orderId: string) => void;
}) {
  return (
    <section className="panel orders-panel" aria-labelledby="orders-heading">
      <div className="panel-header">
        <div>
          <span className="label">ORDER HISTORY</span>
          <h2 id="orders-heading">Recent orders</h2>
        </div>
        <span className="count-label">{orders.length}</span>
      </div>
      <div className="order-list">
        {orders.map((order) => (
          <button
            className={`order-row ${selectedOrderId === order.order_id ? "is-active" : ""}`}
            key={order.order_id}
            type="button"
            onClick={() => onSelect(order.order_id)}
            aria-pressed={selectedOrderId === order.order_id}
          >
            <strong>{order.order_id}</strong>
            <StatusBadge status={order.status} />
            <span className="order-row__date">{formatDate(order.placed_at)}</span>
            <span className="order-row__items">
              {itemCount(order)} {itemCount(order) === 1 ? "item" : "items"}
            </span>
            <span />
            <span className="order-row__total">
              {formatMoney(order.total_minor, order.currency)}
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}

function OrderDetails({ order }: { order: Order }) {
  const deliveryLabel = order.status === "delivered" ? "Delivered" : "Estimated delivery";
  const deliveryValue =
    order.status === "delivered"
      ? formatDate(order.delivered_at, true)
      : formatDate(order.estimated_delivery_date);

  return (
    <section className="panel order-details" aria-labelledby="order-detail-heading">
      <div className="record-header">
        <div>
          <span className="label">SELECTED ORDER</span>
          <h2 id="order-detail-heading">{order.order_id}</h2>
          <span className="muted">Placed {formatDate(order.placed_at, true)}</span>
        </div>
        <StatusBadge status={order.status} />
      </div>

      <dl className="fact-grid">
        <div>
          <dt>{deliveryLabel}</dt>
          <dd>{deliveryValue}</dd>
        </div>
        <div>
          <dt>Payment</dt>
          <dd>{order.payment_method_display}</dd>
        </div>
        <div className="fact-grid__wide">
          <dt>Delivery address</dt>
          <dd>{order.delivery_address}</dd>
        </div>
      </dl>

      <div className="line-items">
        <div className="line-items__head">
          <strong>Line items</strong>
          <span>
            {itemCount(order)} {itemCount(order) === 1 ? "item" : "items"}
          </span>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th scope="col">Product</th>
                <th scope="col">SKU</th>
                <th scope="col">Qty</th>
                <th scope="col">Unit price</th>
                <th scope="col">Total</th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((item) => (
                <tr key={item.order_item_id}>
                  <td><strong>{item.product_name}</strong></td>
                  <td>{item.sku}</td>
                  <td>{item.quantity}</td>
                  <td>{formatMoney(item.unit_price_minor, order.currency)}</td>
                  <td>{formatMoney(item.line_total_minor, order.currency)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan={4}>Order total</td>
                <td>{formatMoney(order.total_minor, order.currency)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </section>
  );
}

function AssistantMarkdown({ children }: { children: string }) {
  return (
    <ReactMarkdown
      allowedElements={MARKDOWN_ELEMENTS}
      skipHtml
      unwrapDisallowed
    >
      {children}
    </ReactMarkdown>
  );
}

function ChatPanel({
  customerName,
  messages,
  activities,
  draft,
  isSending,
  currentStatus,
  error,
  onDraftChange,
  onSubmit,
  onNewConversation,
}: {
  customerName: string;
  messages: ChatMessage[];
  activities: string[];
  draft: string;
  isSending: boolean;
  currentStatus: string | null;
  error: string | null;
  onDraftChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onNewConversation: () => void;
}) {
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, isSending]);

  return (
    <div className="chat-view">
      <div className="chat-toolbar">
        <h1>Order assistant</h1>
        <button
          className="secondary-button"
          type="button"
          onClick={onNewConversation}
          disabled={messages.length === 0 || isSending}
        >
          New conversation
        </button>
      </div>

      <div className="assistant-layout">
        <section className="conversation" aria-label="Conversation">
          <div className="messages" aria-live="polite">
            {messages.length === 0 ? (
              <div className="conversation-empty">
                <span aria-hidden="true">SC</span>
                <strong>Hello, {customerName}</strong>
                <p>Type your order question below to get started.</p>
              </div>
            ) : null}

            {messages.map((message) => (
              <article className={`message message--${message.role}`} key={message.id}>
                <div className="message__meta">
                  {message.role === "user" ? "You" : "Order assistant"}
                </div>
                <div className="message__body">
                  {message.role === "assistant" ? (
                    <AssistantMarkdown>{message.content}</AssistantMarkdown>
                  ) : (
                    <p>{message.content}</p>
                  )}
                </div>
              </article>
            ))}

            <div ref={endOfMessagesRef} />
          </div>

          {isSending ? (
            <div className="activity-inline" role="status">
              <span className="spinner" aria-hidden="true" />
              <span>{currentStatus ?? "Understanding your question…"}</span>
            </div>
          ) : null}

          {error ? <p className="chat-error" role="alert">{error}</p> : null}

          <form className="composer" onSubmit={onSubmit}>
            <label className="sr-only" htmlFor="chat-message">Ask about an order</label>
            <textarea
              id="chat-message"
              rows={2}
              value={draft}
              onChange={(event) => onDraftChange(event.target.value)}
              placeholder="Ask about order status, items, delivery, or payment…"
              disabled={isSending}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
            />
            <div className="composer__footer">
              <button type="submit" disabled={isSending || !draft.trim()}>
                {isSending ? "Working" : "Send"} <kbd>↵</kbd>
              </button>
            </div>
          </form>
        </section>

        <aside className="activity-panel" aria-labelledby="activity-title">
          <header>
            <span className="label">CURRENT REQUEST</span>
            <h2 id="activity-title">Activity</h2>
          </header>
          <ol className="activity-log">
            {activities.length === 0 ? (
              <li>
                <span>·</span>
                <div><strong>No active request</strong><small>Submit a question to begin</small></div>
              </li>
            ) : activities.map((activity, index) => {
              const active = isSending && index === activities.length - 1;
              return (
                <li className={active ? "is-active" : "is-complete"} key={`${activity}-${index}`}>
                  <span>{active ? "•" : "✓"}</span>
                  <div>
                    <strong>{activity.replace(/…$/, "")}</strong>
                    <small>{active ? "In progress" : "Completed"}</small>
                  </div>
                </li>
              );
            })}
          </ol>
        </aside>
      </div>
    </div>
  );
}

export default function App() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [customerOrders, setCustomerOrders] = useState<CustomerOrders | null>(null);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [isLoadingCustomers, setIsLoadingCustomers] = useState(true);
  const [isLoadingOrders, setIsLoadingOrders] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [chatDraft, setChatDraft] = useState("");
  const [isSendingChat, setIsSendingChat] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [chatStatus, setChatStatus] = useState<string | null>(null);
  const [chatActivities, setChatActivities] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<"overview" | "assistant">("overview");
  const chatRequestRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchCustomers(controller.signal)
      .then((result) => {
        setCustomers(result);
        if (result.length > 0) {
          setIsLoadingOrders(true);
          setSelectedCustomerId(result[0].customer_id);
        }
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof Error && requestError.name !== "AbortError") {
          setError("We couldn’t load the customer list. Check that the API is running.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoadingCustomers(false);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!selectedCustomerId) return;
    const controller = new AbortController();
    fetchCustomerOrders(selectedCustomerId, controller.signal)
      .then((result) => {
        setCustomerOrders(result);
        setSelectedOrderId(result.orders[0]?.order_id ?? null);
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof Error && requestError.name !== "AbortError") {
          setError("We couldn’t load this customer’s orders. Please try again.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoadingOrders(false);
      });
    return () => controller.abort();
  }, [selectedCustomerId]);

  const selectedOrder = useMemo(
    () => customerOrders?.orders.find((order) => order.order_id === selectedOrderId) ?? null,
    [customerOrders, selectedOrderId],
  );

  const openCount = customerOrders?.orders.filter((order) =>
    (["processing", "shipped"] as OrderStatus[]).includes(order.status),
  ).length ?? 0;
  const totalValue = customerOrders?.orders.reduce((sum, order) => sum + order.total_minor, 0) ?? 0;
  const currency = customerOrders?.orders[0]?.currency ?? "INR";

  function resetConversation() {
    setChatMessages([]);
    setConversationId(null);
    setChatDraft("");
    setChatError(null);
    setChatStatus(null);
    setChatActivities([]);
    setIsSendingChat(false);
  }

  function handleCustomerChange(customerId: string) {
    chatRequestRef.current?.abort();
    setSelectedCustomerId(customerId);
    setIsLoadingOrders(true);
    setError(null);
    setCustomerOrders(null);
    setSelectedOrderId(null);
    resetConversation();
  }

  function handleTabKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    const nextTab = activeTab === "overview" ? "assistant" : "overview";
    setActiveTab(nextTab);
    document.getElementById(`${nextTab}-tab`)?.focus();
  }

  async function handleChatSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = chatDraft.trim();
    if (!message || !selectedCustomerId || isSendingChat) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: message,
    };
    const assistantMessageId = crypto.randomUUID();
    const controller = new AbortController();
    chatRequestRef.current = controller;
    setChatMessages((current) => [...current, userMessage]);
    setChatDraft("");
    setChatError(null);
    setChatActivities([]);
    setChatStatus("Understanding your question…");
    setIsSendingChat(true);

    try {
      const response = await streamChatMessage(
        selectedCustomerId,
        message,
        conversationId,
        (status) => {
          setChatStatus(status);
          setChatActivities((current) =>
            current[current.length - 1] === status ? current : [...current, status],
          );
        },
        (content) => {
          setChatMessages((current) => {
            const existing = current.find((item) => item.id === assistantMessageId);
            if (!existing) {
              return [
                ...current,
                { id: assistantMessageId, role: "assistant", content },
              ];
            }
            return current.map((item) =>
              item.id === assistantMessageId
                ? { ...item, content: item.content + content }
                : item,
            );
          });
        },
        controller.signal,
      );
      setConversationId(response.conversation_id);
      setChatMessages((current) => {
        const existing = current.find((item) => item.id === assistantMessageId);
        if (!existing) {
          return [
            ...current,
            { id: assistantMessageId, role: "assistant", content: response.answer },
          ];
        }
        return current.map((item) =>
          item.id === assistantMessageId ? { ...item, content: response.answer } : item,
        );
      });
    } catch (requestError) {
      if (requestError instanceof Error && requestError.name !== "AbortError") {
        setChatMessages((current) =>
          current.filter(
            (item) => item.id !== userMessage.id && item.id !== assistantMessageId,
          ),
        );
        setChatActivities([]);
        setChatError("The assistant couldn’t respond. Please try sending your message again.");
        setChatDraft(message);
      }
    } finally {
      if (chatRequestRef.current === controller) {
        chatRequestRef.current = null;
        setIsSendingChat(false);
        setChatStatus(null);
      }
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand__mark" aria-hidden="true">SC</span>
          <strong>Support Console</strong>
        </div>
        <div className="topbar__context">
          <label htmlFor="customer-select">Customer</label>
          <select
            id="customer-select"
            aria-label="Select customer"
            value={selectedCustomerId}
            onChange={(event) => handleCustomerChange(event.target.value)}
            disabled={isLoadingCustomers || customers.length === 0}
          >
            {customers.map((customer) => (
              <option key={customer.customer_id} value={customer.customer_id}>
                {customer.customer_id}
              </option>
            ))}
          </select>
        </div>
      </header>

      {customerOrders ? (
        <div className="tabs" role="tablist" aria-label="Customer workspace">
          <button
            id="overview-tab"
            className={`tab ${activeTab === "overview" ? "is-active" : ""}`}
            type="button"
            role="tab"
            aria-selected={activeTab === "overview"}
            aria-controls="overview-panel"
            tabIndex={activeTab === "overview" ? 0 : -1}
            onClick={() => setActiveTab("overview")}
            onKeyDown={handleTabKeyDown}
          >Overview</button>
          <button
            id="assistant-tab"
            className={`tab ${activeTab === "assistant" ? "is-active" : ""}`}
            type="button"
            role="tab"
            aria-selected={activeTab === "assistant"}
            aria-controls="assistant-panel"
            tabIndex={activeTab === "assistant" ? 0 : -1}
            onClick={() => setActiveTab("assistant")}
            onKeyDown={handleTabKeyDown}
          >Assistant</button>
        </div>
      ) : null}

      <main>
        {error ? (
          <div className="error-state" role="alert">
            <strong>Unable to load data</strong><span>{error}</span>
          </div>
        ) : null}
        {isLoadingCustomers || isLoadingOrders ? <LoadingState /> : null}

        {!isLoadingCustomers && !isLoadingOrders && customerOrders ? (
          activeTab === "overview" ? (
            <section id="overview-panel" role="tabpanel" aria-labelledby="overview-tab">
              <div className="customer-strip">
                <div>
                  <span className="label">CUSTOMER RECORD</span>
                  <h1>{customerOrders.customer.name}</h1>
                  <a href={`mailto:${customerOrders.customer.email}`}>
                    {customerOrders.customer.email}
                  </a>
                </div>
                <dl className="metrics">
                  <div><dt>Orders</dt><dd>{customerOrders.orders.length}</dd></div>
                  <div><dt>Open</dt><dd>{openCount}</dd></div>
                  <div><dt>Total value</dt><dd>{formatMoney(totalValue, currency)}</dd></div>
                </dl>
              </div>

              {customerOrders.orders.length > 0 && selectedOrder ? (
                <div className="workspace-grid">
                  <OrderList
                    orders={customerOrders.orders}
                    selectedOrderId={selectedOrderId}
                    onSelect={setSelectedOrderId}
                  />
                  <OrderDetails order={selectedOrder} />
                </div>
              ) : (
                <div className="empty-state"><strong>No orders yet</strong></div>
              )}
            </section>
          ) : (
            <section id="assistant-panel" role="tabpanel" aria-labelledby="assistant-tab">
              <ChatPanel
                customerName={customerOrders.customer.name}
                messages={chatMessages}
                activities={chatActivities}
                draft={chatDraft}
                isSending={isSendingChat}
                currentStatus={chatStatus}
                error={chatError}
                onDraftChange={setChatDraft}
                onSubmit={handleChatSubmit}
                onNewConversation={resetConversation}
              />
            </section>
          )
        ) : null}
      </main>
    </div>
  );
}
