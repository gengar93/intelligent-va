import type { ChatResponse, Customer, CustomerOrders } from "./types";

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

export async function sendChatMessage(
  customerId: string,
  message: string,
  conversationId: string | null,
  signal?: AbortSignal,
): Promise<ChatResponse> {
  const response = await fetch("/api/chat", {
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

  return response.json() as Promise<ChatResponse>;
}
