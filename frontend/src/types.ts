export type OrderStatus = "processing" | "shipped" | "delivered" | "cancelled";

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
  items: OrderItem[];
}

export interface CustomerOrders {
  customer: Customer;
  orders: Order[];
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
