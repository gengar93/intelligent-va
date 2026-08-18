import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent } from "react";

import {
  fetchClosedTickets,
  fetchCustomerOrders,
  fetchCustomers,
  fetchModelOptions,
  fetchOpenTickets,
  generateInvoice,
  resetDemoDatabase,
  streamChatMessage,
} from "./api";
import { AssistantView } from "./components/AssistantView";
import type { LiveTurn } from "./components/AssistantView";
import { OrdersView } from "./components/OrdersView";
import { TicketsView } from "./components/TicketsView";
import { initials } from "./format";
import {
  ChatIcon,
  CheckIcon,
  ChevronDownIcon,
  CloseIcon,
  MenuIcon,
  MoonIcon,
  OrdersIcon,
  ResetIcon,
  SunIcon,
  TicketsIcon,
} from "./icons";
import type {
  ChatMessage,
  ClosedInvoiceTicket,
  Customer,
  CustomerOrders,
  InvoiceTicket,
  ModelOptions,
} from "./types";

type ActiveTab = "orders" | "tickets" | "assistant";
const TABS: ActiveTab[] = ["orders", "tickets", "assistant"];
const TAB_LABELS: Record<ActiveTab, string> = {
  orders: "Orders",
  tickets: "Tickets",
  assistant: "Order VA",
};
const AVATAR_CLASSES = ["av-1", "av-2", "av-3"];

function avatarClass(customerId: string, customers: Customer[]): string {
  const index = customers.findIndex((customer) => customer.customer_id === customerId);
  return AVATAR_CLASSES[(index >= 0 ? index : 0) % AVATAR_CLASSES.length];
}

function TabIcon({ tab }: { tab: ActiveTab }) {
  if (tab === "orders") return <OrdersIcon />;
  if (tab === "tickets") return <TicketsIcon />;
  return <ChatIcon />;
}

function LoadingState() {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <span>Loading customer records…</span>
    </div>
  );
}

export default function App() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [customerOrders, setCustomerOrders] = useState<CustomerOrders | null>(null);
  const [openTickets, setOpenTickets] = useState<InvoiceTicket[]>([]);
  const [closedTickets, setClosedTickets] = useState<ClosedInvoiceTicket[]>([]);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [isLoadingCustomers, setIsLoadingCustomers] = useState(true);
  const [isLoadingOrders, setIsLoadingOrders] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>("orders");

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [chatDraft, setChatDraft] = useState("");
  const [isSendingChat, setIsSendingChat] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [chatStatus, setChatStatus] = useState<string | null>(null);
  const [liveTurn, setLiveTurn] = useState<LiveTurn | null>(null);
  const liveTurnRef = useRef<LiveTurn | null>(null);
  const chatRequestRef = useRef<AbortController | null>(null);
  const [modelOptions, setModelOptions] = useState<ModelOptions | null>(null);
  const [selectedModelId, setSelectedModelId] = useState("");
  const [selectedRouteId, setSelectedRouteId] = useState("");

  const [generatingTicketId, setGeneratingTicketId] = useState<string | null>(null);
  const [ticketError, setTicketError] = useState<string | null>(null);
  const [isResettingDemo, setIsResettingDemo] = useState(false);

  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [switcherOpen, setSwitcherOpen] = useState(false);
  const switcherRef = useRef<HTMLDivElement>(null);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [mobileSwitcherOpen, setMobileSwitcherOpen] = useState(false);
  const mobileNavTriggerRef = useRef<HTMLButtonElement>(null);
  const mobileDrawerRef = useRef<HTMLElement>(null);

  const [toast, setToast] = useState<string | null>(null);
  const toastTimerRef = useRef<number | null>(null);

  const showToast = useCallback((message: string) => {
    setToast(message);
    if (toastTimerRef.current !== null) window.clearTimeout(toastTimerRef.current);
    toastTimerRef.current = window.setTimeout(() => setToast(null), 3200);
  }, []);

  const closeMobileNav = useCallback(() => {
    setMobileSwitcherOpen(false);
    setMobileNavOpen(false);
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    if (!switcherOpen) return;
    function handleClick(event: MouseEvent) {
      if (!switcherRef.current?.contains(event.target as Node)) {
        setSwitcherOpen(false);
      }
    }
    document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, [switcherOpen]);

  useEffect(() => {
    if (!mobileNavOpen) return;

    const trigger = mobileNavTriggerRef.current;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.requestAnimationFrame(() => {
      mobileDrawerRef.current?.querySelector<HTMLButtonElement>("button")?.focus();
    });

    function handleKeyDown(event: globalThis.KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        closeMobileNav();
        return;
      }
      if (event.key !== "Tab" || !mobileDrawerRef.current) return;

      const focusable = Array.from(
        mobileDrawerRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
        ),
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
      trigger?.focus();
    };
  }, [closeMobileNav, mobileNavOpen]);

  useEffect(() => {
    const mobileQuery = window.matchMedia("(max-width: 620px)");
    function handleViewportChange(event: MediaQueryListEvent) {
      if (!event.matches) {
        setMobileNavOpen(false);
        setMobileSwitcherOpen(false);
      }
    }
    mobileQuery.addEventListener("change", handleViewportChange);
    return () => mobileQuery.removeEventListener("change", handleViewportChange);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchCustomers(controller.signal)
      .then((result) => {
        setCustomers(result);
        if (result.length > 0) {
          setIsLoadingOrders(true);
          setSelectedCustomerId(result[0].customer_id);
        }
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof Error && requestError.name !== "AbortError") {
          setError("We couldn’t load the customer list. Check that the API is running.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoadingCustomers(false);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchModelOptions(controller.signal)
      .then((result) => {
        const defaultModel =
          result.models.find((model) => model.id === result.default_model) ?? result.models[0];
        setModelOptions(result);
        if (defaultModel) {
          setSelectedModelId(defaultModel.id);
          setSelectedRouteId(defaultModel.default_route);
        }
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof Error && requestError.name !== "AbortError") {
          setModelOptions(null);
        }
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!selectedCustomerId) return;
    const controller = new AbortController();
    Promise.all([
      fetchCustomerOrders(selectedCustomerId, controller.signal),
      fetchOpenTickets(selectedCustomerId, controller.signal),
      fetchClosedTickets(selectedCustomerId, controller.signal),
    ])
      .then(([ordersResult, ticketsResult, closedResult]) => {
        setCustomerOrders(ordersResult);
        setOpenTickets(ticketsResult);
        setClosedTickets(closedResult);
        setSelectedOrderId(ordersResult.orders[0]?.order_id ?? null);
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof Error && requestError.name !== "AbortError") {
          setError("We couldn’t load this customer’s orders. Please try again.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoadingOrders(false);
      });
    return () => controller.abort();
  }, [selectedCustomerId]);

  const selectedCustomer = useMemo(
    () => customers.find((customer) => customer.customer_id === selectedCustomerId) ?? null,
    [customers, selectedCustomerId],
  );

  const selectedModel = useMemo(
    () => modelOptions?.models.find((model) => model.id === selectedModelId) ?? null,
    [modelOptions, selectedModelId],
  );

  const updateLive = useCallback((updater: (turn: LiveTurn) => LiveTurn) => {
    const current = liveTurnRef.current;
    if (!current) return;
    const next = updater(current);
    liveTurnRef.current = next;
    setLiveTurn(next);
  }, []);

  function clearLiveTurn() {
    liveTurnRef.current = null;
    setLiveTurn(null);
  }

  function resetConversation() {
    setChatMessages([]);
    setConversationId(null);
    setChatDraft("");
    setChatError(null);
    setChatStatus(null);
    setIsSendingChat(false);
    clearLiveTurn();
  }

  function handleModelChange(modelId: string) {
    const model = modelOptions?.models.find((option) => option.id === modelId);
    if (!model || model.id === selectedModelId || isSendingChat) return;
    resetConversation();
    setSelectedModelId(model.id);
    setSelectedRouteId(model.default_route);
    showToast(`New conversation with ${model.label}`);
  }

  function handleRouteChange(routeId: string) {
    const route = selectedModel?.routes.find((option) => option.id === routeId);
    if (!route || route.id === selectedRouteId || isSendingChat) return;
    resetConversation();
    setSelectedRouteId(route.id);
    showToast(`New conversation using ${route.label}`);
  }

  function handleCustomerChange(customerId: string) {
    if (customerId === selectedCustomerId || generatingTicketId !== null) return;
    chatRequestRef.current?.abort();
    chatRequestRef.current = null;
    setSelectedCustomerId(customerId);
    setIsLoadingOrders(true);
    setError(null);
    setCustomerOrders(null);
    setOpenTickets([]);
    setClosedTickets([]);
    setSelectedOrderId(null);
    setGeneratingTicketId(null);
    setTicketError(null);
    resetConversation();
  }

  function handleTabKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    const currentIndex = TABS.indexOf(activeTab);
    const offset = event.key === "ArrowRight" ? 1 : -1;
    const nextTab = TABS[(currentIndex + offset + TABS.length) % TABS.length];
    setActiveTab(nextTab);
    document.getElementById(`${nextTab}-tab`)?.focus();
  }

  function handleViewOrder(orderId: string) {
    setSelectedOrderId(orderId);
    setActiveTab("orders");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function refreshWorkspace(signal?: AbortSignal) {
    const [ordersResult, ticketsResult, closedResult] = await Promise.all([
      fetchCustomerOrders(selectedCustomerId, signal),
      fetchOpenTickets(selectedCustomerId, signal),
      fetchClosedTickets(selectedCustomerId, signal),
    ]);
    setCustomerOrders(ordersResult);
    setOpenTickets(ticketsResult);
    setClosedTickets(closedResult);
  }

  async function handleGenerateInvoice(ticket: InvoiceTicket) {
    if (!selectedCustomerId || generatingTicketId) return;
    setGeneratingTicketId(ticket.ticket_id);
    setTicketError(null);

    try {
      const result = await generateInvoice(selectedCustomerId, ticket.ticket_id);
      showToast(`${result.invoice.invoice_number} generated for ${result.invoice.order_id}`);
      try {
        await refreshWorkspace();
      } catch {
        setTicketError("The invoice was generated, but the workspace could not be refreshed.");
      }
    } catch {
      setTicketError("The invoice could not be generated. Please try again.");
    } finally {
      setGeneratingTicketId(null);
    }
  }

  async function handleResetDemoData() {
    if (isResettingDemo || generatingTicketId !== null) return;
    const confirmed = window.confirm(
      "Reset all demo data? Generated invoices, ticket changes, and conversations will be removed.",
    );
    if (!confirmed) return;

    setIsResettingDemo(true);
    closeMobileNav();
    chatRequestRef.current?.abort();
    chatRequestRef.current = null;

    try {
      await resetDemoDatabase();
      resetConversation();
      setActiveTab("orders");
      setError(null);
      setTicketError(null);
      setGeneratingTicketId(null);
      setCustomerOrders(null);
      setOpenTickets([]);
      setClosedTickets([]);
      setSelectedOrderId(null);
      setSelectedCustomerId("");
      setCustomers([]);
      setIsLoadingCustomers(true);

      const result = await fetchCustomers();
      setCustomers(result);
      if (result.length > 0) {
        setIsLoadingOrders(true);
        setSelectedCustomerId(result[0].customer_id);
      }
      showToast("Demo data restored");
    } catch {
      setError("The demo data could not be reset. Please try again.");
    } finally {
      setIsLoadingCustomers(false);
      setIsResettingDemo(false);
    }
  }

  async function sendChatMessage(message: string) {
    const trimmed = message.trim();
    if (!trimmed || !selectedCustomerId || isSendingChat) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };
    const controller = new AbortController();
    chatRequestRef.current = controller;
    setChatMessages((current) => [...current, userMessage]);
    setChatDraft("");
    setChatError(null);
    setChatStatus("Understanding your question…");
    setIsSendingChat(true);
    const initialTurn: LiveTurn = {
      steps: [],
      buffer: "",
      answer: null,
      cards: [],
      followUps: [],
    };
    liveTurnRef.current = initialTurn;
    setLiveTurn(initialTurn);

    try {
      const response = await streamChatMessage(
        selectedCustomerId,
        trimmed,
        conversationId,
        selectedModelId,
        selectedRouteId,
        {
          onStatus: (status) => setChatStatus(status),
          onDelta: (content) =>
            updateLive((turn) => ({ ...turn, buffer: turn.buffer + content })),
          onSegment: (kind) =>
            updateLive((turn) => {
              const text = turn.buffer;
              if (!text.trim()) return { ...turn, buffer: "" };
              if (kind === "reasoning") {
                return {
                  ...turn,
                  buffer: "",
                  steps: [...turn.steps, { kind: "reasoning", text: text.trim() }],
                };
              }
              return { ...turn, buffer: "", answer: text.trim() };
            }),
          onToolCall: (step) =>
            updateLive((turn) => ({ ...turn, steps: [...turn.steps, step] })),
          onToolResult: (step) =>
            updateLive((turn) => ({ ...turn, steps: [...turn.steps, step] })),
          onCards: (orders) => updateLive((turn) => ({ ...turn, cards: orders })),
          onFollowUps: (suggestions) =>
            updateLive((turn) => ({ ...turn, followUps: suggestions })),
        },
        controller.signal,
      );

      const finishedTurn = liveTurnRef.current;
      setConversationId(response.conversation_id);
      setChatMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.answer,
          reasoning: finishedTurn?.steps ?? [],
          cards: finishedTurn?.cards ?? [],
          followUps: finishedTurn?.followUps ?? [],
        },
      ]);
      clearLiveTurn();

      try {
        await refreshWorkspace(controller.signal);
      } catch (refreshError) {
        if (refreshError instanceof Error && refreshError.name !== "AbortError") {
          setError("The assistant responded, but the customer record could not be refreshed.");
        }
      }
    } catch (requestError) {
      if (requestError instanceof Error && requestError.name !== "AbortError") {
        setChatMessages((current) => current.filter((item) => item.id !== userMessage.id));
        clearLiveTurn();
        setChatError("The assistant couldn’t respond. Please try sending your message again.");
        setChatDraft(trimmed);
      }
    } finally {
      if (chatRequestRef.current === controller) {
        chatRequestRef.current = null;
        setIsSendingChat(false);
        setChatStatus(null);
        if (liveTurnRef.current) clearLiveTurn();
      }
    }
  }

  const isLoading = isLoadingCustomers || isLoadingOrders;

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-inner">
          <button
            ref={mobileNavTriggerRef}
            type="button"
            className="icon-btn mobile-nav-trigger"
            aria-label="Open navigation menu"
            aria-expanded={mobileNavOpen}
            aria-controls="mobile-navigation"
            onClick={() => setMobileNavOpen(true)}
          >
            <MenuIcon />
          </button>

          <div className="brand">
            <div className="brand-name">Order VA</div>
          </div>

          <nav className="tabs desktop-tabs" role="tablist" aria-label="Console sections">
            {TABS.map((tab) => (
              <button
                key={tab}
                id={`${tab}-tab`}
                type="button"
                className="tab"
                role="tab"
                aria-selected={activeTab === tab}
                aria-controls={`view-${tab}`}
                tabIndex={activeTab === tab ? 0 : -1}
                onClick={() => setActiveTab(tab)}
                onKeyDown={handleTabKeyDown}
              >
                <TabIcon tab={tab} />
                <span className="lbl">{TAB_LABELS[tab]}</span>
                {tab === "tickets" && openTickets.length > 0 ? (
                  <span className="count">{openTickets.length}</span>
                ) : null}
              </button>
            ))}
          </nav>

          <div className="topbar-spacer" />

          <button
            type="button"
            className="icon-btn desktop-reset-button"
            title="Reset demo data"
            aria-label="Reset demo data"
            disabled={isResettingDemo || generatingTicketId !== null}
            onClick={handleResetDemoData}
          >
            <ResetIcon />
          </button>

          <button
            type="button"
            className="icon-btn desktop-theme-toggle"
            aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
            onClick={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
          >
            {theme === "dark" ? <MoonIcon /> : <SunIcon />}
          </button>

          <div className="switcher desktop-switcher" ref={switcherRef}>
            <button
              type="button"
              className="switcher-btn"
              aria-haspopup="true"
              aria-expanded={switcherOpen}
              disabled={isLoadingCustomers || customers.length === 0}
              onClick={() => setSwitcherOpen((open) => !open)}
            >
              <span
                className={`avatar ${avatarClass(selectedCustomerId, customers)}`}
                aria-hidden="true"
              >
                {selectedCustomer ? initials(selectedCustomer.name) : "··"}
              </span>
              <span className="switcher-meta">
                <span className="nm">{selectedCustomer?.name ?? "Loading…"}</span>
                <span className="id">{selectedCustomer?.customer_id ?? ""}</span>
              </span>
              <span className="chev" aria-hidden="true">
                <ChevronDownIcon />
              </span>
            </button>
            {switcherOpen ? (
              <div className="menu" role="menu" aria-label="Switch customer">
                <div className="menu-label eyebrow">Viewing as customer</div>
                {customers.map((customer) => (
                  <button
                    key={customer.customer_id}
                    type="button"
                    role="menuitem"
                    className="menu-item"
                    aria-current={customer.customer_id === selectedCustomerId}
                    disabled={generatingTicketId !== null}
                    onClick={() => {
                      setSwitcherOpen(false);
                      handleCustomerChange(customer.customer_id);
                    }}
                  >
                    <span
                      className={`avatar ${avatarClass(customer.customer_id, customers)}`}
                      aria-hidden="true"
                    >
                      {initials(customer.name)}
                    </span>
                    <span>
                      <span className="nm">{customer.name}</span>
                      <span className="id">{customer.customer_id} · {customer.email}</span>
                    </span>
                    <span className="tick" aria-hidden="true">
                      <CheckIcon />
                    </span>
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      </header>

      {mobileNavOpen ? (
        <div className="mobile-drawer-layer">
          <button
            type="button"
            className="mobile-drawer-backdrop"
            aria-label="Close navigation menu"
            onClick={closeMobileNav}
          />
          <aside
            id="mobile-navigation"
            ref={mobileDrawerRef}
            className="mobile-drawer"
            role="dialog"
            aria-modal="true"
            aria-labelledby="mobile-navigation-title"
          >
            <div className="mobile-drawer-head">
              <h2 id="mobile-navigation-title">Order VA</h2>
              <button
                type="button"
                className="icon-btn"
                aria-label="Close navigation menu"
                onClick={closeMobileNav}
              >
                <CloseIcon />
              </button>
            </div>

            <nav className="mobile-drawer-nav" aria-label="Console sections">
              {TABS.map((tab) => (
                <button
                  key={tab}
                  type="button"
                  className="mobile-drawer-nav-item"
                  aria-current={activeTab === tab ? "page" : undefined}
                  onClick={() => {
                    setActiveTab(tab);
                    closeMobileNav();
                  }}
                >
                  <TabIcon tab={tab} />
                  <span>{TAB_LABELS[tab]}</span>
                  {tab === "tickets" && openTickets.length > 0 ? (
                    <span className="count">{openTickets.length}</span>
                  ) : null}
                </button>
              ))}
            </nav>

            <div className="mobile-drawer-footer">
              <button
                type="button"
                className="mobile-setting-btn"
                onClick={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
              >
                <span className="mobile-setting-icon" aria-hidden="true">
                  {theme === "dark" ? <MoonIcon /> : <SunIcon />}
                </span>
                <span>
                  <span className="mobile-setting-label">Appearance</span>
                  <span className="mobile-setting-value">
                    {theme === "dark" ? "Dark mode" : "Light mode"}
                  </span>
                </span>
              </button>

              <button
                type="button"
                className="mobile-setting-btn mobile-reset-btn"
                disabled={isResettingDemo || generatingTicketId !== null}
                onClick={handleResetDemoData}
              >
                <span className="mobile-setting-icon" aria-hidden="true">
                  <ResetIcon />
                </span>
                <span>
                  <span className="mobile-setting-label">
                    {isResettingDemo ? "Resetting demo data…" : "Reset demo data"}
                  </span>
                  <span className="mobile-setting-value">Restore the original records</span>
                </span>
              </button>

              <div className="mobile-customer-switcher">
                <div className="eyebrow">Viewing as customer</div>
                {mobileSwitcherOpen ? (
                  <div className="mobile-customer-menu" role="menu" aria-label="Switch customer">
                    {customers.map((customer) => (
                      <button
                        key={customer.customer_id}
                        type="button"
                        role="menuitem"
                        className="menu-item"
                        aria-current={customer.customer_id === selectedCustomerId}
                        disabled={generatingTicketId !== null}
                        onClick={() => {
                          closeMobileNav();
                          handleCustomerChange(customer.customer_id);
                        }}
                      >
                        <span
                          className={`avatar ${avatarClass(customer.customer_id, customers)}`}
                          aria-hidden="true"
                        >
                          {initials(customer.name)}
                        </span>
                        <span className="mobile-customer-copy">
                          <span className="nm">{customer.name}</span>
                          <span className="id">{customer.customer_id} · {customer.email}</span>
                        </span>
                        <span className="tick" aria-hidden="true">
                          <CheckIcon />
                        </span>
                      </button>
                    ))}
                  </div>
                ) : null}
                <button
                  type="button"
                  className="mobile-customer-btn"
                  aria-haspopup="menu"
                  aria-expanded={mobileSwitcherOpen}
                  disabled={isLoadingCustomers || customers.length === 0}
                  onClick={() => setMobileSwitcherOpen((open) => !open)}
                >
                  <span
                    className={`avatar ${avatarClass(selectedCustomerId, customers)}`}
                    aria-hidden="true"
                  >
                    {selectedCustomer ? initials(selectedCustomer.name) : "··"}
                  </span>
                  <span className="mobile-customer-copy">
                    <span className="nm">{selectedCustomer?.name ?? "Loading…"}</span>
                    <span className="id">{selectedCustomer?.customer_id ?? ""}</span>
                  </span>
                  <span className="chev" aria-hidden="true">
                    <ChevronDownIcon />
                  </span>
                </button>
              </div>
            </div>
          </aside>
        </div>
      ) : null}

      <main className={activeTab === "assistant" ? "main--full" : undefined}>
        {error ? (
          <div className="inline-error page-error" role="alert">
            {error}
          </div>
        ) : null}
        {isLoading ? <LoadingState /> : null}

        {!isLoading && customerOrders && selectedCustomer ? (
          <>
            <section
              className="view"
              id="view-orders"
              role="tabpanel"
              aria-labelledby="orders-tab"
              hidden={activeTab !== "orders"}
            >
              <OrdersView
                customerOrders={customerOrders}
                selectedOrderId={selectedOrderId}
                onSelectOrder={setSelectedOrderId}
                onGoToTickets={() => setActiveTab("tickets")}
                onGoToAssistant={() => setActiveTab("assistant")}
              />
            </section>
            <section
              className="view"
              id="view-tickets"
              role="tabpanel"
              aria-labelledby="tickets-tab"
              hidden={activeTab !== "tickets"}
            >
              <TicketsView
                customerName={customerOrders.customer.name}
                tickets={openTickets}
                closedTickets={closedTickets}
                generatingTicketId={generatingTicketId}
                error={ticketError}
                onGenerate={handleGenerateInvoice}
              />
            </section>
            <section
              className="view"
              id="view-assistant"
              role="tabpanel"
              aria-labelledby="assistant-tab"
              hidden={activeTab !== "assistant"}
            >
              <AssistantView
                customer={customerOrders.customer}
                messages={chatMessages}
                liveTurn={liveTurn}
                draft={chatDraft}
                isSending={isSendingChat}
                currentStatus={chatStatus}
                error={chatError}
                modelOptions={modelOptions}
                selectedModelId={selectedModelId}
                selectedRouteId={selectedRouteId}
                onDraftChange={setChatDraft}
                onSend={sendChatMessage}
                onNewConversation={resetConversation}
                onModelChange={handleModelChange}
                onRouteChange={handleRouteChange}
                onViewOrder={handleViewOrder}
                onFollowUp={sendChatMessage}
              />
            </section>
          </>
        ) : null}
      </main>

      <div className={`toast ${toast ? "show" : ""}`} role="status" aria-live="polite">
        <div className="tick-ico" aria-hidden="true">
          <CheckIcon size={13} strokeWidth={2.6} />
        </div>
        <span>{toast ?? ""}</span>
      </div>
    </div>
  );
}
