import type { InvoiceStatus, Order, OrderStatus, TicketStatus } from "./types";

export const STATUS_LABELS: Record<OrderStatus, string> = {
  processing: "Processing",
  shipped: "Shipped",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

/** Maps an order status to the Atelier pill tone. */
export const STATUS_TONES: Record<OrderStatus, "ok" | "info" | "warn" | "stop"> = {
  processing: "info",
  shipped: "info",
  delivered: "ok",
  cancelled: "stop",
};

export const INVOICE_STATUS_LABELS: Record<InvoiceStatus, string> = {
  not_requested: "Not requested",
  queued: "Queued",
  in_progress: "In progress",
  available: "Available",
  failed: "Failed",
  cancelled: "Cancelled",
};

export const TICKET_STATUS_LABELS: Record<TicketStatus, string> = {
  queued: "Queued",
  in_progress: "In progress",
};

export function formatMoney(amountMinor: number, currency: string): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(amountMinor / 100);
}

export function formatDate(value: string | null, includeTime = false): string {
  if (!value) return "Not available";
  const parsedValue = value.includes("T") ? value : `${value}T00:00:00`;
  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    ...(includeTime ? { hour: "numeric", minute: "2-digit" } : {}),
  }).format(new Date(parsedValue));
}

export function itemCount(order: Order): number {
  return order.items.reduce((total, item) => total + item.quantity, 0);
}

export function deliveryLine(order: Order): string {
  if (order.status === "delivered") {
    return `Delivered ${formatDate(order.delivered_at)}`;
  }
  if (order.status === "cancelled") {
    return "No delivery scheduled";
  }
  return `Est. ${formatDate(order.estimated_delivery_date)}`;
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]!.toUpperCase())
    .join("");
}

export function formatElapsed(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${ms}ms`;
}
