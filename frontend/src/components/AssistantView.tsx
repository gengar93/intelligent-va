import { useEffect, useRef } from "react";
import type { FormEvent } from "react";
import ReactMarkdown from "react-markdown";

import { SendIcon, SparkIcon } from "../icons";
import type { ChatMessage, Customer, Order, ReasoningStep } from "../types";

import { OrderCard } from "./OrderCard";
import { ReasoningPanel } from "./ReasoningPanel";

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

function FollowUps({
  suggestions,
  disabled,
  onFollowUp,
}: {
  suggestions: string[];
  disabled: boolean;
  onFollowUp: (text: string) => void;
}) {
  if (suggestions.length === 0) return null;
  return (
    <>
      <div className="followup-label eyebrow">Suggested follow-ups</div>
      <div className="followups">
        {suggestions.map((suggestion) => (
          <button
            type="button"
            className="chip"
            key={suggestion}
            disabled={disabled}
            onClick={() => onFollowUp(suggestion)}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </>
  );
}

function AssistantTurnBody({
  reasoning,
  live,
  liveBuffer,
  answer,
  cards,
  status,
  onViewOrder,
}: {
  reasoning: ReasoningStep[];
  live: boolean;
  liveBuffer: string;
  answer: string | null;
  cards: Order[];
  status: string | null;
  onViewOrder: (orderId: string) => void;
}) {
  return (
    <div className="msg bot">
      <div className="col">
        <ReasoningPanel steps={reasoning} live={live} liveBuffer={liveBuffer} />
        {answer !== null && answer !== "" ? (
          <div className="bubble">
            <AssistantMarkdown>{answer}</AssistantMarkdown>
          </div>
        ) : null}
        {live && status ? (
          <div className="live-status" role="status">
            <span className="spinner" aria-hidden="true" />
            <span>{status}</span>
          </div>
        ) : null}
        {cards.map((order) => (
          <OrderCard key={order.order_id} order={order} onViewOrder={onViewOrder} />
        ))}
      </div>
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
  onDraftChange,
  onSend,
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
  onDraftChange: (value: string) => void;
  onSend: (message: string) => void;
  onViewOrder: (orderId: string) => void;
  onFollowUp: (text: string) => void;
}) {
  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const lastMessage = messages[messages.length - 1];

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
      <div className="chat">
        <div className="chat-body" aria-live="polite">
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
              <div className="msg user" key={message.id}>
                <div className="bubble">{message.content}</div>
              </div>
            ) : (
              <div key={message.id}>
                <AssistantTurnBody
                  reasoning={message.reasoning ?? []}
                  live={false}
                  liveBuffer=""
                  answer={message.content}
                  cards={message.cards ?? []}
                  status={null}
                  onViewOrder={onViewOrder}
                />
                {message === lastMessage && !liveTurn ? (
                  <FollowUps
                    suggestions={message.followUps ?? []}
                    disabled={isSending}
                    onFollowUp={onFollowUp}
                  />
                ) : null}
              </div>
            ),
          )}

          {liveTurn ? (
            <AssistantTurnBody
              reasoning={liveTurn.steps}
              live
              liveBuffer={liveTurn.buffer}
              answer={liveTurn.answer}
              cards={liveTurn.cards}
              status={currentStatus ?? "Understanding your question…"}
              onViewOrder={onViewOrder}
            />
          ) : null}

          <div ref={endOfMessagesRef} />
        </div>

        {error ? (
          <p className="inline-error chat-error" role="alert">
            {error}
          </p>
        ) : null}

        <form className="composer" onSubmit={handleSubmit}>
          <div className="field-wrap">
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
          </div>
          <button
            type="submit"
            className="send-btn"
            aria-label="Send message"
            disabled={isSending || !draft.trim()}
          >
            <SendIcon />
          </button>
        </form>
      </div>
    </div>
  );
}
