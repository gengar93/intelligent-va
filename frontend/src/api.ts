import type {
  ChatResponse,
  ChatStreamCallbacks,
  ClosedInvoiceTicket,
  Customer,
  CustomerOrders,
  InvoiceGeneration,
  InvoiceTicket,
  Order,
  SegmentKind,
} from "./types";

interface RawStreamEvent {
  type?: string;
  message?: string;
  content?: string;
  kind?: string;
  id?: string;
  name?: string;
  arguments?: unknown;
  result?: unknown;
  elapsed_ms?: number;
  orders?: Order[];
  suggestions?: string[];
  conversation_id?: string;
  answer?: string;
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function fetchCustomers(signal?: AbortSignal): Promise<Customer[]> {
  return getJson<Customer[]>("/api/customers", signal);
}

export function fetchCustomerOrders(
  customerId: string,
  signal?: AbortSignal,
): Promise<CustomerOrders> {
  return getJson<CustomerOrders>(`/api/customers/${customerId}/orders`, signal);
}

export function fetchOpenTickets(
  customerId: string,
  signal?: AbortSignal,
): Promise<InvoiceTicket[]> {
  return getJson<InvoiceTicket[]>(`/api/customers/${customerId}/tickets`, signal);
}

export function fetchClosedTickets(
  customerId: string,
  signal?: AbortSignal,
): Promise<ClosedInvoiceTicket[]> {
  return getJson<ClosedInvoiceTicket[]>(
    `/api/customers/${customerId}/tickets/closed`,
    signal,
  );
}

export async function generateInvoice(
  customerId: string,
  ticketId: string,
): Promise<InvoiceGeneration> {
  const response = await fetch(
    `/api/customers/${customerId}/tickets/${ticketId}/generate-invoice`,
    { method: "POST" },
  );
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json() as Promise<InvoiceGeneration>;
}

function asObject(value: unknown): Record<string, unknown> {
  if (value !== null && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return { _raw: value };
}

/**
 * Streams a chat turn over the v2 NDJSON contract, dispatching every event
 * through the provided callbacks. Unknown event types are ignored.
 */
export async function streamChatMessage(
  customerId: string,
  message: string,
  conversationId: string | null,
  callbacks: ChatStreamCallbacks,
  signal?: AbortSignal,
): Promise<ChatResponse> {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      customer_id: customerId,
      message,
      conversation_id: conversationId,
    }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  if (!response.body) {
    throw new Error("Streaming response is unavailable");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: ChatResponse | null = null;

  function handleLine(line: string) {
    if (!line.trim()) return;
    let event: RawStreamEvent;
    try {
      event = JSON.parse(line) as RawStreamEvent;
    } catch {
      return; // skip malformed lines
    }

    switch (event.type) {
      case "status":
        if (typeof event.message === "string") callbacks.onStatus?.(event.message);
        break;
      case "delta":
        if (typeof event.content === "string") callbacks.onDelta?.(event.content);
        break;
      case "segment":
        if (event.kind === "reasoning" || event.kind === "answer") {
          callbacks.onSegment?.(event.kind as SegmentKind);
        }
        break;
      case "tool_call":
        callbacks.onToolCall?.({
          kind: "tool_call",
          id: String(event.id ?? ""),
          name: String(event.name ?? "tool"),
          arguments: asObject(event.arguments),
        });
        break;
      case "tool_result":
        callbacks.onToolResult?.({
          kind: "tool_result",
          id: String(event.id ?? ""),
          name: String(event.name ?? "tool"),
          result: event.result,
          elapsed_ms: typeof event.elapsed_ms === "number" ? event.elapsed_ms : 0,
        });
        break;
      case "cards":
        callbacks.onCards?.(Array.isArray(event.orders) ? event.orders : []);
        break;
      case "follow_ups":
        callbacks.onFollowUps?.(
          Array.isArray(event.suggestions)
            ? event.suggestions.filter((item): item is string => typeof item === "string")
            : [],
        );
        break;
      case "result":
        result = {
          conversation_id: String(event.conversation_id ?? ""),
          answer: String(event.answer ?? ""),
        };
        break;
      case "error":
        throw new Error(event.message ?? "The assistant reported an error");
      default:
        // Unknown event types must be ignored (forward compatibility).
        break;
    }
  }

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    lines.forEach(handleLine);
    if (done) break;
  }
  handleLine(buffer);

  if (!result) {
    throw new Error("The stream ended without an answer");
  }
  return result;
}
