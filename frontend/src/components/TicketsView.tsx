import { formatDate, formatMoney, TICKET_STATUS_LABELS } from "../format";
import { CircleCheckIcon, InvoiceDocIcon } from "../icons";
import type { ClosedInvoiceTicket, ClosedTicketStatus, InvoiceTicket } from "../types";

import { StatusPill } from "./shared";

const CLOSED_STATUS_LABELS: Record<ClosedTicketStatus, string> = {
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};

const CLOSED_STATUS_TONES: Record<ClosedTicketStatus, "ok" | "stop" | "info"> = {
  completed: "ok",
  failed: "stop",
  cancelled: "info",
};

export function TicketsView({
  customerName,
  tickets,
  closedTickets,
  generatingTicketId,
  error,
  onGenerate,
}: {
  customerName: string;
  tickets: InvoiceTicket[];
  closedTickets: ClosedInvoiceTicket[];
  generatingTicketId: string | null;
  error: string | null;
  onGenerate: (ticket: InvoiceTicket) => void;
}) {
  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Invoice Tickets</span>
        <h1>
          Open invoice <em>requests</em>
        </h1>
      </div>

      {error ? (
        <p className="inline-error" role="alert">
          {error}
        </p>
      ) : null}

      {tickets.length === 0 ? (
        <div className="empty">
          <div className="ico" aria-hidden="true">
            <CircleCheckIcon />
          </div>
          <h3>No open tickets</h3>
          <p>
            {customerName} has no invoice requests waiting. New requests raised from an order will
            appear here.
          </p>
        </div>
      ) : (
        <div className="tickets-grid">
          {tickets.map((ticket) => {
            const isGenerating = generatingTicketId === ticket.ticket_id;
            return (
              <article className="ticket-card" key={ticket.ticket_id}>
                <div className="corner" aria-hidden="true" />
                <div className="ticket-head">
                  <div>
                    <div className="tid tnum">{ticket.ticket_id}</div>
                    <div className="for">
                      Invoice for order <strong className="tnum">{ticket.order_id}</strong>
                    </div>
                  </div>
                  <StatusPill
                    tone={ticket.status === "in_progress" ? "info" : "warn"}
                    label={TICKET_STATUS_LABELS[ticket.status]}
                  />
                </div>
                <div className="ticket-meta">
                  <div>
                    <div className="k">Requested</div>
                    <div className="v">{formatDate(ticket.created_at)}</div>
                  </div>
                  <div>
                    <div className="k">Items</div>
                    <div className="v tnum">{ticket.item_count}</div>
                  </div>
                  <div>
                    <div className="k">Order total</div>
                    <div className="v tnum">{formatMoney(ticket.total_minor, ticket.currency)}</div>
                  </div>
                  <div>
                    <div className="k">Updated</div>
                    <div className="v">{formatDate(ticket.updated_at)}</div>
                  </div>
                </div>
                <div className="ticket-foot">
                  <span className="note">Completes the ticket and attaches the invoice</span>
                  <button
                    type="button"
                    className="btn btn-primary btn-sm"
                    disabled={generatingTicketId !== null}
                    onClick={() => onGenerate(ticket)}
                  >
                    {isGenerating ? "Generating…" : "Generate Invoice"}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}

      <section className="ticket-history" aria-labelledby="ticket-history-heading">
        <div className="section-head">
          <span className="eyebrow" id="ticket-history-heading">
            Ticket History
          </span>
          <span className="section-count tnum">{closedTickets.length}</span>
        </div>
        {closedTickets.length === 0 ? (
          <p className="history-empty">
            No completed, failed, or cancelled tickets yet for {customerName}.
          </p>
        ) : (
          <ul className="history-list">
            {closedTickets.map((ticket) => (
              <li className="history-row" key={ticket.ticket_id}>
                <div className="history-main">
                  <div className="history-id">
                    <span className="tid tnum">{ticket.ticket_id}</span>
                    <StatusPill
                      tone={CLOSED_STATUS_TONES[ticket.status]}
                      label={CLOSED_STATUS_LABELS[ticket.status]}
                    />
                  </div>
                  <div className="history-desc">
                    Invoice for order <strong className="tnum">{ticket.order_id}</strong>
                    <span className="dot" aria-hidden="true">
                      ·
                    </span>
                    <span className="tnum">
                      {formatMoney(ticket.total_minor, ticket.currency)}
                    </span>
                  </div>
                  {ticket.status === "completed" && ticket.invoice_number ? (
                    <div className="history-note ok-note">
                      <InvoiceDocIcon size={13} strokeWidth={1.8} />
                      {ticket.invoice_number}
                    </div>
                  ) : null}
                  {ticket.status === "failed" && ticket.failure_reason ? (
                    <div className="history-note fail-note">{ticket.failure_reason}</div>
                  ) : null}
                </div>
                <div className="history-when">
                  <div className="k">{ticket.status === "completed" ? "Completed" : "Updated"}</div>
                  <div className="v">
                    {formatDate(ticket.completed_at ?? ticket.updated_at)}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
