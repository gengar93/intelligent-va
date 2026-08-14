import { useEffect, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import ReactMarkdown from "react-markdown";

import { formatElapsed } from "../format";
import { ChevronRightIcon, PlusIcon, SendIcon, SparkIcon } from "../icons";
import type {
  ChatMessage,
  Customer,
  ModelOptions,
  Order,
  ReasoningStep,
  ToolCallStep,
  ToolResultStep,
} from "../types";

import { OrderCard } from "./OrderCard";

const MARKDOWN_ELEMENTS = ["p", "strong", "em", "ul", "ol", "li", "code", "br"];

/** The in-flight assistant turn, updated live as stream events arrive. */
export interface LiveTurn {
  steps: ReasoningStep[];
  buffer: string;
  answer: string | null;
  cards: Order[];
  followUps: string[];
}

function AssistantMarkdown({ children }: { children: string }) {
  return (
    <ReactMarkdown allowedElements={MARKDOWN_ELEMENTS} skipHtml unwrapDisallowed>
      {children}
    </ReactMarkdown>
  );
}

function prettyJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2) ?? String(value);
  } catch {
    return String(value);
  }
}

/** One tool invocation: the call and (when finished) its result, as a compact expandable row. */
function ToolRow({ call, result }: { call: ToolCallStep; result: ToolResultStep | undefined }) {
  const [expanded, setExpanded] = useState(false);
  const entries = Object.entries(call.arguments);
  const running = result === undefined;
  return (
    <div className="tool-row">
      <button
        type="button"
        className="tool-head"
        aria-expanded={expanded}
        disabled={running}
        onClick={() => setExpanded((value) => !value)}
      >
        <span className={`tool-chev ${expanded ? "open" : ""}`} aria-hidden="true">
          <ChevronRightIcon size={13} />
        </span>
        <code className="tool-call">
          <span className="fn">{call.name}</span>
          {"("}
          {entries.map(([key, value], index) => (
            <span key={key}>
              {index > 0 ? ", " : ""}
              <span className="arg">{key}</span>=<span className="str">{JSON.stringify(value)}</span>
            </span>
          ))}
          {")"}
        </code>
        {running ? (
          <span className="spinner spinner--sm" aria-label="Running" />
        ) : (
          <span className="tool-time tnum">{formatElapsed(result.elapsed_ms)}</span>
        )}
      </button>
      {expanded && result !== undefined ? (
        <pre className="code tool-json">{prettyJson(result.result)}</pre>
      ) : null}
    </div>
  );
}

/** Collapsed-by-default disclosure wrapping a finished turn's trace. */
function TraceDisclosure({ steps }: { steps: ReasoningStep[] }) {
  const [open, setOpen] = useState(false);
  const toolCalls = steps.filter((step) => step.kind === "tool_call").length;
  if (steps.length === 0) return null;
  const label =
    toolCalls === 0
      ? "Reasoning"
      : `Reasoning · ${toolCalls} tool ${toolCalls === 1 ? "call" : "calls"}`;
  return (
    <div className="trace">
      <button
        type="button"
        className="trace-toggle"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <span className={`tool-chev ${open ? "open" : ""}`} aria-hidden="true">
          <ChevronRightIcon size={13} />
        </span>
        {label}
      </button>
      {open ? (
        <div className="trace-body">
          <TurnSteps steps={steps} />
        </div>
      ) : null}
    </div>
  );
}

/** Interleaves narration and tool rows in the order they streamed. */
function TurnSteps({ steps }: { steps: ReasoningStep[] }) {
  const items: ReactNode[] = [];
  steps.forEach((step, index) => {
    if (step.kind === "reasoning") {
      items.push(
        <div className="turn-think" key={index}>
          <AssistantMarkdown>{step.text}</AssistantMarkdown>
        </div>,
      );
    } else if (step.kind === "tool_call") {
      const result = steps.find(
        (candidate): candidate is ToolResultStep =>
          candidate.kind === "tool_result" && candidate.id === step.id,
      );
      items.push(<ToolRow key={index} call={step} result={result} />);
    }
    // tool_result steps render inside their ToolRow.
  });
  return <>{items}</>;
}

function AssistantTurn({
  steps,
  live,
  liveBuffer,
  answer,
  cards,
  status,
  customerId,
  onViewOrder,
}: {
  steps: ReasoningStep[];
  live: boolean;
  liveBuffer: string;
  answer: string | null;
  cards: Order[];
  status: string | null;
  customerId: string;
  onViewOrder: (orderId: string) => void;
}) {
  const hasAnswer = answer !== null && answer !== "";
  return (
    <div className="turn">
      {live ? <TurnSteps steps={steps} /> : <TraceDisclosure steps={steps} />}
      {live && liveBuffer.trim() ? (
        <div className="turn-answer">
          <AssistantMarkdown>{liveBuffer}</AssistantMarkdown>
        </div>
      ) : null}
      {hasAnswer ? (
        <div className="turn-answer">
          <AssistantMarkdown>{answer}</AssistantMarkdown>
        </div>
      ) : null}
      {live && status && !hasAnswer && !liveBuffer.trim() ? (
        <div className="live-status" role="status">
          <span className="spinner" aria-hidden="true" />
          <span>{status}</span>
        </div>
      ) : null}
      {cards.map((order) => (
        <OrderCard
          key={order.order_id}
          order={order}
          customerId={customerId}
          onViewOrder={onViewOrder}
        />
      ))}
    </div>
  );
}

export function AssistantView({
  customer,
  messages,
  liveTurn,
  draft,
  isSending,
  currentStatus,
  error,
  modelOptions,
  selectedModelId,
  selectedRouteId,
  onDraftChange,
  onSend,
  onNewConversation,
  onModelChange,
  onRouteChange,
  onViewOrder,
  onFollowUp,
}: {
  customer: Customer;
  messages: ChatMessage[];
  liveTurn: LiveTurn | null;
  draft: string;
  isSending: boolean;
  currentStatus: string | null;
  error: string | null;
  modelOptions: ModelOptions | null;
  selectedModelId: string;
  selectedRouteId: string;
  onDraftChange: (value: string) => void;
  onSend: (message: string) => void;
  onNewConversation: () => void;
  onModelChange: (modelId: string) => void;
  onRouteChange: (routeId: string) => void;
  onViewOrder: (orderId: string) => void;
  onFollowUp: (text: string) => void;
}) {
  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const lastMessage = messages[messages.length - 1];
  const selectedModel =
    modelOptions?.models.find((model) => model.id === selectedModelId) ?? null;

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, liveTurn, isSending]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = draft.trim();
    if (message) onSend(message);
  }

  return (
    <div className="assistant">
      <div className="chat-scroll">
        <div className="chat-col" aria-live="polite">
          {messages.length === 0 && !liveTurn ? (
            <div className="chat-empty">
              <div className="ico" aria-hidden="true">
                <SparkIcon />
              </div>
              <h3>Hello, {customer.name}</h3>
              <p>Ask about an order, invoice, or delivery to get started.</p>
            </div>
          ) : null}

          {messages.map((message) =>
            message.role === "user" ? (
              <div className="msg-user" key={message.id}>
                <div className="bubble">{message.content}</div>
              </div>
            ) : (
              <div key={message.id}>
                <AssistantTurn
                  steps={message.reasoning ?? []}
                  live={false}
                  liveBuffer=""
                  answer={message.content}
                  cards={message.cards ?? []}
                  status={null}
                  customerId={customer.customer_id}
                  onViewOrder={onViewOrder}
                />
                {message === lastMessage && !liveTurn && (message.followUps?.length ?? 0) > 0 ? (
                  <div className="followups">
                    {message.followUps?.map((suggestion) => (
                      <button
                        type="button"
                        className="chip"
                        key={suggestion}
                        disabled={isSending}
                        onClick={() => onFollowUp(suggestion)}
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
            ),
          )}

          {liveTurn ? (
            <AssistantTurn
              steps={liveTurn.steps}
              live
              liveBuffer={liveTurn.buffer}
              answer={liveTurn.answer}
              cards={liveTurn.cards}
              status={currentStatus ?? "Understanding your question…"}
              customerId={customer.customer_id}
              onViewOrder={onViewOrder}
            />
          ) : null}

          <div ref={endOfMessagesRef} />
        </div>
      </div>

      <div className="composer-wrap">
        {error ? (
          <p className="inline-error chat-error" role="alert">
            {error}
          </p>
        ) : null}
        <form className="composer" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="chat-message">
            Ask about an order
          </label>
          <textarea
            id="chat-message"
            rows={1}
            value={draft}
            placeholder="Ask about an order, invoice, or delivery…"
            disabled={isSending}
            onChange={(event) => onDraftChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
              }
            }}
          />
          <div className="composer-actions">
            <button
              type="button"
              className="composer-new-chat"
              title="New conversation"
              aria-label="New conversation"
              disabled={(messages.length === 0 && !liveTurn) || isSending}
              onClick={onNewConversation}
            >
              <PlusIcon />
            </button>

            <div className="composer-controls">
              <label className="sr-only" htmlFor="chat-model">
                Model
              </label>
              <select
                id="chat-model"
                className="composer-select model-select"
                value={selectedModelId}
                disabled={isSending || !modelOptions || modelOptions.models.length === 0}
                onChange={(event) => onModelChange(event.target.value)}
              >
                {!selectedModelId ? <option value="">Default model</option> : null}
                {modelOptions?.models.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.label}
                  </option>
                ))}
              </select>

              {selectedModel && selectedModel.routes.length > 1 ? (
                <>
                  <label className="sr-only" htmlFor="chat-route">
                    Provider route
                  </label>
                  <select
                    id="chat-route"
                    className="composer-select route-select"
                    value={selectedRouteId}
                    disabled={isSending}
                    onChange={(event) => onRouteChange(event.target.value)}
                  >
                    {selectedModel.routes.map((route) => (
                      <option key={route.id} value={route.id}>
                        {route.label}
                      </option>
                    ))}
                  </select>
                </>
              ) : null}

              <button
                type="submit"
                className="send-btn"
                aria-label="Send message"
                disabled={isSending || !draft.trim()}
              >
                <SendIcon size={16} />
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
