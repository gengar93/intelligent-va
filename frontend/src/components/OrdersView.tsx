import {
  deliveryLine,
  formatDate,
  formatMoney,
  INVOICE_STATUS_LABELS,
  itemCount,
} from "../format";
import { invoicePdfUrl } from "../api";
import {
  CancelIcon,
  CheckIcon,
  ChatIcon,
  ClockIcon,
  DownloadIcon,
  InvoiceDocIcon,
  OrdersIcon,
  TicketsIcon,
} from "../icons";
import type { CustomerOrders, Order, OrderStatus } from "../types";

import { ProductThumb } from "./shared";

const STEPS = ["Placed", "Processing", "Shipped", "Delivered"];

const STATUS_LABELS_A11Y: Record<OrderStatus, string> = {
  processing: "Processing",
  shipped: "Shipped",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

const STEP_INDEX: Record<OrderStatus, number> = {
  processing: 1,
  shipped: 2,
  delivered: 3,
  cancelled: -1,
};

function Stepper({ order }: { order: Order }) {
  if (order.status === "cancelled") {
    return (
      <div className="cancel-banner" role="status">
        <CancelIcon />
        This order was cancelled. No delivery scheduled.
      </div>
    );
  }
  const currentIndex = STEP_INDEX[order.status];
  return (
    <div className="stepper" aria-label="Order progress">
      {STEPS.map((label, index) => {
        const state = index < currentIndex ? "done" : index === currentIndex ? "current" : "";
        return (
          <div className="step-wrap" key={label}>
            <div className={`step ${state}`}>
              <div className="node" aria-hidden="true">
                {index < currentIndex ? <CheckIcon size={13} strokeWidth={2.6} /> : index + 1}
              </div>
              <div className="lbl">{label}</div>
            </div>
            {index < STEPS.length - 1 ? (
              <div className={`step-line ${index < currentIndex ? "filled" : ""}`} aria-hidden="true" />
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

function InvoiceFlag({ order }: { order: Order }) {
  const status = order.invoice_status;
  if (status === "available") {
    return (
      <span className="invoice-flag invoice-flag--ok">
        <CheckIcon size={14} strokeWidth={1.9} /> Invoice available
      </span>
    );
  }
  if (status === "queued" || status === "in_progress") {
    return (
      <span className="invoice-flag invoice-flag--warn">
        <ClockIcon /> Invoice {INVOICE_STATUS_LABELS[status].toLowerCase()}
      </span>
    );
  }
  return (
    <span className="invoice-flag invoice-flag--muted">
      <InvoiceDocIcon /> Invoice {INVOICE_STATUS_LABELS[status].toLowerCase()}
    </span>
  );
}

function OrderDetail({
  order,
  customerId,
  onGoToTickets,
  onGoToAssistant,
}: {
  order: Order;
  customerId: string;
  onGoToTickets: () => void;
  onGoToAssistant: () => void;
}) {
  const hasTicket = order.invoice_status === "queued" || order.invoice_status === "in_progress";
  const invoiceReady = order.invoice_status === "available";
  return (
    <section className="panel" aria-labelledby="order-detail-heading">
      <div className="panel-head">
        <h3 id="order-detail-heading">Order detail</h3>
        <InvoiceFlag order={order} />
      </div>
      <div className="detail-body">
        <div className="detail-top">
          <div>
            <h2 className="tnum">{order.order_id}</h2>
            <div className="placed">
              Placed {formatDate(order.placed_at)} · {deliveryLine(order)}
            </div>
          </div>
        </div>
        <Stepper order={order} />
        <div className="detail-grid">
          <div className="field">
            <div className="k">Payment</div>
            <div className="v tnum">{order.payment_method_display}</div>
          </div>
          <div className="field">
            <div className="k">Delivery</div>
            <div className="v">{deliveryLine(order)}</div>
          </div>
          <div className="field field--wide">
            <div className="k">Shipping address</div>
            <div className="v">{order.delivery_address}</div>
          </div>
        </div>
        <div className="items">
          {order.items.map((item) => (
            <div className="item" key={item.order_item_id}>
              <div className="item-ico" aria-hidden="true">
                <ProductThumb imageUrl={item.image_url} alt="" />
              </div>
              <div>
                <div className="nm">{item.product_name}</div>
                <div className="sku tnum">SKU {item.sku}</div>
              </div>
              <div>
                <div className="price tnum">{formatMoney(item.line_total_minor, order.currency)}</div>
                <div className="qty tnum">Qty {item.quantity}</div>
              </div>
            </div>
          ))}
          <div className="totals">
            <span className="k">Order total</span>
            <span className="v tnum">{formatMoney(order.total_minor, order.currency)}</span>
          </div>
          <div className="totals-pad" />
        </div>
        <div className="actions-row">
          {invoiceReady ? (
            <a
              className="btn btn-primary"
              href={invoicePdfUrl(customerId, order.order_id)}
              download
            >
              <DownloadIcon /> Download invoice
            </a>
          ) : hasTicket ? (
            <button type="button" className="btn btn-primary" onClick={onGoToTickets}>
              <TicketsIcon /> View invoice ticket
            </button>
          ) : null}
          <button type="button" className="btn btn-ghost" onClick={onGoToAssistant}>
            <ChatIcon /> Ask Order VA
          </button>
        </div>
      </div>
    </section>
  );
}

export function OrdersView({
  customerOrders,
  selectedOrderId,
  onSelectOrder,
  onGoToTickets,
  onGoToAssistant,
}: {
  customerOrders: CustomerOrders;
  selectedOrderId: string | null;
  onSelectOrder: (orderId: string) => void;
  onGoToTickets: () => void;
  onGoToAssistant: () => void;
}) {
  const { customer, orders } = customerOrders;
  const selectedOrder = orders.find((order) => order.order_id === selectedOrderId) ?? null;

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Orders &amp; Overview</span>
        <h1>
          Order history for <em>{customer.name}</em>
        </h1>
      </div>

      {orders.length === 0 ? (
        <div className="empty">
          <div className="ico" aria-hidden="true">
            <OrdersIcon />
          </div>
          <h3>No orders yet</h3>
          <p>{customer.name} hasn’t placed any orders. New orders will appear here.</p>
        </div>
      ) : (
        <>
          <div className="orders-grid">
            <section className="panel" aria-labelledby="orders-heading">
              <div className="panel-head">
                <h3 id="orders-heading">All orders</h3>
                <span className="eyebrow">
                  {orders.length} {orders.length === 1 ? "order" : "orders"}
                </span>
              </div>
              <div className="order-list">
                {orders.map((order) => {
                  const selected = order.order_id === selectedOrderId;
                  const description = order.items
                    .map((item) => (item.quantity > 1 ? `${item.quantity}× ` : "") + item.product_name)
                    .join(" + ");
                  return (
                    <button
                      type="button"
                      className="order-row"
                      key={order.order_id}
                      aria-current={selected}
                      onClick={() => onSelectOrder(order.order_id)}
                    >
                      <div className="order-thumb" aria-hidden="true">
                        <ProductThumb imageUrl={order.items[0]?.image_url ?? null} alt="" size={20} />
                      </div>
                      <div className="order-main">
                        <div className="id tnum">{order.order_id}</div>
                        <div className="desc">{description}</div>
                        <span className="sr-only">
                          {STATUS_LABELS_A11Y[order.status]}, {itemCount(order)} items, invoice{" "}
                          {INVOICE_STATUS_LABELS[order.invoice_status]}
                        </span>
                      </div>
                      <div className="order-right">
                        <div className="amt tnum">{formatMoney(order.total_minor, order.currency)}</div>
                        <div className="date">{formatDate(order.placed_at)}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>

            {selectedOrder ? (
              <OrderDetail
                order={selectedOrder}
                customerId={customer.customer_id}
                onGoToTickets={onGoToTickets}
                onGoToAssistant={onGoToAssistant}
              />
            ) : null}
          </div>
        </>
      )}
    </>
  );
}
