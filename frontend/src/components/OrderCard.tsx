import { deliveryLine, formatDate, formatMoney, INVOICE_STATUS_LABELS } from "../format";
import { InvoiceDocIcon, ReceiptIcon, TruckIcon } from "../icons";
import type { InvoiceStatus, Order } from "../types";

import { ProductThumb } from "./shared";

const INVOICE_TONE_CLASS: Record<InvoiceStatus, string> = {
  not_requested: "rv--muted",
  queued: "rv--warn",
  in_progress: "rv--warn",
  available: "rv--ok",
  failed: "rv--stop",
  cancelled: "rv--stop",
};

/** Receipt-style order card rendered under assistant messages. */
export function OrderCard({
  order,
  onViewOrder,
}: {
  order: Order;
  onViewOrder: (orderId: string) => void;
}) {
  return (
    <article className="receipt" aria-label={`Order ${order.order_id}`}>
      <div className="receipt-head">
        <div>
          <div className="r-id">
            <span className="badge-ico" aria-hidden="true">
              <ReceiptIcon />
            </span>
            {order.order_id}
          </div>
          <div className="r-sub">
            Placed {formatDate(order.placed_at)} · {order.payment_method_display}
          </div>
        </div>
      </div>
      <div className="receipt-items">
        {order.items.map((item) => (
          <div className="r-item" key={item.order_item_id}>
            <div className="r-ico" aria-hidden="true">
              <ProductThumb imageUrl={item.image_url} alt="" />
            </div>
            <div>
              <div className="r-nm">{item.product_name}</div>
              <div className="r-q">Qty {item.quantity}</div>
            </div>
            <div className="r-price tnum">{formatMoney(item.line_total_minor, order.currency)}</div>
          </div>
        ))}
      </div>
      <div className="receipt-rows">
        <div className="r-row">
          <span className="rk">
            <TruckIcon /> Delivery
          </span>
          <span className="rv">{deliveryLine(order)}</span>
        </div>
        <div className="r-row">
          <span className="rk">
            <InvoiceDocIcon size={13} strokeWidth={1.7} /> Invoice
          </span>
          <span className={`rv ${INVOICE_TONE_CLASS[order.invoice_status]}`}>
            {INVOICE_STATUS_LABELS[order.invoice_status]}
          </span>
        </div>
      </div>
      <div className="receipt-total">
        <span className="tk">Order total</span>
        <span className="tv tnum">{formatMoney(order.total_minor, order.currency)}</span>
      </div>
      <div className="receipt-actions">
        <button type="button" className="btn btn-ghost btn-sm" onClick={() => onViewOrder(order.order_id)}>
          View order
        </button>
      </div>
    </article>
  );
}
