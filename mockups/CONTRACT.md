# Chat stream contract — v2 (Concept A build)

`POST /api/chat/stream` — body
`{customer_id, message, conversation_id | null, model_id?, route_id?}`. Omitted model and
route values use the defaults in `config/models.toml`.
Response: NDJSON, one JSON event per line. Event order within a turn:

```
status* → [segment cycle]* → cards → follow_ups → result
where a segment cycle = delta* → segment(reasoning) → (tool_call → status → tool_result)+
final cycle          = delta* → segment(answer)
```

## Events

| type | payload | meaning |
|---|---|---|
| `status` | `{message: str}` | Canned progress line ("Fetching your orders…"). Unchanged from v1. |
| `delta` | `{content: str}` | Streamed text of the CURRENT segment. The client appends to a live buffer. Classification arrives at segment end. |
| `segment` | `{kind: "reasoning" \| "answer"}` | Closes the current streamed buffer. `reasoning` → move buffer into the reasoning timeline as a step (it preceded tool calls). `answer` → buffer is the final visible reply. Empty buffers may be closed too; ignore those. |
| `tool_call` | `{id: str, name: str, arguments: object}` | A real tool invocation. `arguments` is the parsed JSON object (`{"_raw": "..."} ` if unparseable). |
| `tool_result` | `{id: str, name: str, result: any, elapsed_ms: int}` | The tool's actual return value (JSON) + measured duration. `id` matches the tool_call. |
| `cards` | `{orders: OrderRead[]}` | Full order payloads (same shape as `/api/customers/{id}/orders` entries, incl. `items[].image_url`) hydrated from the DB for orders the assistant discussed. May be empty. Render as order cards under the answer. |
| `follow_ups` | `{suggestions: str[]}` | 0–4 short plain-text follow-up questions. Render as text-only chips; clicking sends the text as the next user message. |
| `result` | `{conversation_id: str, answer: str}` | Turn complete. `answer` is the cleaned final text (metadata block already stripped) — replace the streamed answer buffer with it. |
| `error` | `{message: str}` | Terminal failure. |

Client rules:
- Maintain one live text buffer; `segment` tells you where it lands.
- Steps for the reasoning timeline arrive interleaved: reasoning segments, tool_call,
  tool_result (statuses optional to show). Persist the collected steps with the finished
  assistant message so "Show reasoning" works after the turn ends.
- Unknown event types must be ignored (forward compatibility).
- `/api/chat` (non-streaming) still returns `{conversation_id, answer}` (answer cleaned).

## REST changes

- `OrderItemRead` gains `image_url: string | null` — a site-relative path like
  `/products/headphones.svg`, served from `frontend/public/products/`. All other REST
  order and ticket endpoints are unchanged.
- `GET /api/model-options` returns the safe model and route IDs and labels for selectors. It
  deliberately omits upstream model slugs and provider-routing configuration.
- `/api/chat` accepts the same optional `model_id` and `route_id` fields as the streaming
  endpoint. A conversation remains bound to the model and route with which it started.

## Product image assets

`frontend/public/products/` contains one SVG per seed product, referenced by seed data:
headphones.svg, coffee-maker.svg, backpack.svg, bottle.svg, mixer.svg, jacket.svg.
Style: consistent thin-line illustrations on transparent background, stroke currentColor
or warm neutral (#8a7f74), so they sit on the Atelier cream card background.

## Frontend behaviors

- Customer switch aborts in-flight chat, resets conversation, reloads orders + tickets.
- The composer footer owns New conversation, the model selector, any conditional route
  selector, and Send. The title bar does not duplicate New conversation.
- Model options are loaded from `GET /api/model-options`; the frontend does not hardcode the
  catalog. A route selector appears only when the selected model has multiple routes.
- Changing model or route clears the transcript, starts a fresh backend conversation, and
  shows a confirmation toast. Selection controls are disabled during a streamed turn.
- After a chat turn or invoice generation, refresh orders + tickets.
- Enter submits, Shift+Enter newline. Errors restore the draft.

## Product decisions locked in

- Lifetime value = sum over non-cancelled orders only.
- Order-card actions: "View order" (jump to Orders tab with that order selected). No
  Track order / Email invoice anywhere. Invoice state shown as a status line on the card.
- Follow-up chips: text only, no icons.
- The composer has no microphone or voice controls.
- Reasoning UI: inline expandable "Show reasoning" per assistant message (Concept A style),
  showing reasoning notes, tool calls with args, and results as expandable JSON.
