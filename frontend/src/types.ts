export type OrderStatus = "processing" | "shipped" | "delivered" | "cancelled";
export type InvoiceStatus =
  | "not_requested"
  | "queued"
  | "in_progress"
  | "available"
  | "failed"
  | "cancelled";
export type TicketStatus = "queued" | "in_progress";

export interface Customer {
  customer_id: string;
  name: string;
  email: string;
}

export interface OrderItem {
  order_item_id: string;
  product_id: string;
  sku: string;
  product_name: string;
  description: string | null;
  quantity: number;
  unit_price_minor: number;
  line_total_minor: number;
}

export interface Order {
  order_id: string;
  status: OrderStatus;
  placed_at: string;
  estimated_delivery_date: string | null;
  delivered_at: string | null;
  currency: string;
  delivery_address: string;
  payment_method_display: string;
  total_minor: number;
  invoice_status: InvoiceStatus;
  items: OrderItem[];
}

export interface CustomerOrders {
  customer: Customer;
  orders: Order[];
}

export interface InvoiceTicket {
  ticket_id: string;
  order_id: string;
  status: TicketStatus;
  created_at: string;
  updated_at: string;
  order_status: OrderStatus;
  currency: string;
  item_count: number;
  total_minor: number;
}

export interface InvoiceGeneration {
  state: "available";
  created: boolean;
  invoice: {
    invoice_id: string;
    invoice_number: string;
    order_id: string;
    issued_at: string;
    document_url: string;
  };
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  conversation_id: string;
  answer: string;
}
