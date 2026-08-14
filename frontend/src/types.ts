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
  image_url: string | null;
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

export type ClosedTicketStatus = "completed" | "failed" | "cancelled";

export interface ClosedInvoiceTicket {
  ticket_id: string;
  order_id: string;
  status: ClosedTicketStatus;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  failure_reason: string | null;
  order_status: OrderStatus;
  currency: string;
  item_count: number;
  total_minor: number;
  invoice_number: string | null;
  document_url: string | null;
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

/* ---- Chat stream contract v2 ---- */

export type SegmentKind = "reasoning" | "answer";

export interface ReasoningTextStep {
  kind: "reasoning";
  text: string;
}

export interface ToolCallStep {
  kind: "tool_call";
  id: string;
  name: string;
  arguments: Record<string, unknown>;
}

export interface ToolResultStep {
  kind: "tool_result";
  id: string;
  name: string;
  result: unknown;
  elapsed_ms: number;
}

export type ReasoningStep = ReasoningTextStep | ToolCallStep | ToolResultStep;

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  reasoning?: ReasoningStep[];
  cards?: Order[];
  followUps?: string[];
}

export interface ChatResponse {
  conversation_id: string;
  answer: string;
}

export interface ChatStreamCallbacks {
  onStatus?: (message: string) => void;
  onDelta?: (content: string) => void;
  onSegment?: (kind: SegmentKind) => void;
  onToolCall?: (step: ToolCallStep) => void;
  onToolResult?: (step: ToolResultStep) => void;
  onCards?: (orders: Order[]) => void;
  onFollowUps?: (suggestions: string[]) => void;
}
