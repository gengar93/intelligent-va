import type { ChatResponse, Customer, CustomerOrders } from "./types";

type ChatStreamEvent =
  | { type: "status"; message: string }
  | { type: "result"; conversation_id: string; answer: string }
  | { type: "error"; message: string };

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

export async function streamChatMessage(
  customerId: string,
  message: string,
  conversationId: string | null,
  onStatus: (message: string) => void,
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
    const event = JSON.parse(line) as ChatStreamEvent;
    if (event.type === "status") {
      onStatus(event.message);
    } else if (event.type === "error") {
      throw new Error(event.message);
    } else if (event.type === "result") {
      result = {
        conversation_id: event.conversation_id,
        answer: event.answer,
      };
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
