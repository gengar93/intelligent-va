import { useEffect, useMemo, useState } from "react";

import { fetchCustomerOrders, fetchCustomers } from "./api";
import type { Customer, CustomerOrders, Order, OrderStatus } from "./types";

const STATUS_LABELS: Record<OrderStatus, string> = {
  processing: "Processing",
  shipped: "Shipped",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

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
      <span className="loading-state__mark" aria-hidden="true" />
      <span>Loading order data…</span>
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
    <section className="order-list-panel" aria-labelledby="orders-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Order history</p>
          <h2 id="orders-heading">Orders</h2>
        </div>
        <span className="count-label">{orders.length}</span>
      </div>

      <div className="order-list">
        {orders.map((order) => (
          <button
            className={`order-row ${selectedOrderId === order.order_id ? "order-row--selected" : ""}`}
            key={order.order_id}
            type="button"
            onClick={() => onSelect(order.order_id)}
            aria-pressed={selectedOrderId === order.order_id}
          >
            <span className="order-row__topline">
              <strong>{order.order_id}</strong>
              <StatusBadge status={order.status} />
            </span>
            <span className="order-row__meta">
              <span>{formatDate(order.placed_at)}</span>
              <span aria-hidden="true">·</span>
              <span>
                {itemCount(order)} {itemCount(order) === 1 ? "item" : "items"}
              </span>
            </span>
            <span className="order-row__bottomline">
              <span>{formatMoney(order.total_minor, order.currency)}</span>
              <span className="order-row__arrow" aria-hidden="true">
                →
              </span>
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
    <section className="order-detail-panel" aria-labelledby="order-detail-heading">
      <div className="detail-header">
        <div>
          <p className="eyebrow">Selected order</p>
          <h2 id="order-detail-heading">{order.order_id}</h2>
          <p className="detail-header__date">Placed {formatDate(order.placed_at)}</p>
        </div>
        <StatusBadge status={order.status} />
      </div>

      <div className="detail-facts">
        <div className="detail-fact">
          <span>{deliveryLabel}</span>
          <strong>{deliveryValue}</strong>
        </div>
        <div className="detail-fact">
          <span>Payment</span>
          <strong>{order.payment_method_display}</strong>
        </div>
        <div className="detail-fact detail-fact--address">
          <span>Delivery address</span>
          <strong>{order.delivery_address}</strong>
        </div>
      </div>

      <div className="items-section">
        <div className="items-section__heading">
          <h3>Items</h3>
          <span>
            {itemCount(order)} {itemCount(order) === 1 ? "item" : "items"}
          </span>
        </div>

        <div className="items-table-wrap">
          <table className="items-table">
            <thead>
              <tr>
                <th scope="col">Product</th>
                <th scope="col">Qty</th>
                <th scope="col">Unit price</th>
                <th scope="col">Total</th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((item) => (
                <tr key={item.order_item_id}>
                  <td>
                    <strong>{item.product_name}</strong>
                    <span>{item.sku}</span>
                  </td>
                  <td>{item.quantity}</td>
                  <td>{formatMoney(item.unit_price_minor, order.currency)}</td>
                  <td>{formatMoney(item.line_total_minor, order.currency)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="order-total">
          <span>Order total</span>
          <strong>{formatMoney(order.total_minor, order.currency)}</strong>
        </div>
      </div>
    </section>
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

  const deliveredCount =
    customerOrders?.orders.filter((order) => order.status === "delivered").length ?? 0;
  const activeCount =
    customerOrders?.orders.filter((order) =>
      (["processing", "shipped"] as OrderStatus[]).includes(order.status),
    ).length ?? 0;

  function handleCustomerChange(customerId: string) {
    setSelectedCustomerId(customerId);
    setIsLoadingOrders(true);
    setError(null);
    setCustomerOrders(null);
    setSelectedOrderId(null);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand__mark" aria-hidden="true">
            OS
          </span>
          <div>
            <strong>Order Support</strong>
            <span>Demo workspace</span>
          </div>
        </div>
        <span className="read-only-label">Read-only</span>
      </header>

      <main>
        <section className="page-intro">
          <div>
            <p className="eyebrow">Customer overview</p>
            <h1>Orders at a glance</h1>
            <p>Review a customer’s order history and delivery details in one place.</p>
          </div>

          <label className="customer-select">
            <span>Viewing customer</span>
            <select
              value={selectedCustomerId}
              onChange={(event) => handleCustomerChange(event.target.value)}
              disabled={isLoadingCustomers || customers.length === 0}
            >
              {customers.map((customer) => (
                <option key={customer.customer_id} value={customer.customer_id}>
                  {customer.name} · {customer.customer_id}
                </option>
              ))}
            </select>
          </label>
        </section>

        {error ? (
          <div className="error-state" role="alert">
            <strong>Unable to load data</strong>
            <span>{error}</span>
          </div>
        ) : null}

        {isLoadingCustomers || isLoadingOrders ? <LoadingState /> : null}

        {!isLoadingCustomers && !isLoadingOrders && customerOrders ? (
          <>
            <section className="customer-strip" aria-label="Customer summary">
              <div className="customer-identity">
                <span className="customer-avatar" aria-hidden="true">
                  {customerOrders.customer.name
                    .split(" ")
                    .map((part) => part[0])
                    .join("")}
                </span>
                <div>
                  <strong>{customerOrders.customer.name}</strong>
                  <span>{customerOrders.customer.email}</span>
                </div>
              </div>
              <dl className="summary-stats">
                <div>
                  <dt>Total orders</dt>
                  <dd>{customerOrders.orders.length}</dd>
                </div>
                <div>
                  <dt>Active</dt>
                  <dd>{activeCount}</dd>
                </div>
                <div>
                  <dt>Delivered</dt>
                  <dd>{deliveredCount}</dd>
                </div>
              </dl>
            </section>

            {customerOrders.orders.length > 0 && selectedOrder ? (
              <div className="dashboard-grid">
                <OrderList
                  orders={customerOrders.orders}
                  selectedOrderId={selectedOrderId}
                  onSelect={setSelectedOrderId}
                />
                <OrderDetails order={selectedOrder} />
              </div>
            ) : (
              <div className="empty-state">
                <strong>No orders yet</strong>
                <span>This customer does not have any orders to display.</span>
              </div>
            )}
          </>
        ) : null}
      </main>

      <footer>
        Fictional data for demonstration purposes. <span aria-hidden="true">•</span> No changes
        can be made from this dashboard
      </footer>
    </div>
  );
}
