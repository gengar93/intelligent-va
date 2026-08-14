import { useState } from "react";

import { formatElapsed } from "../format";
import { ChevronRightIcon, ClockIcon, SparkIcon } from "../icons";
import type { ReasoningStep, ToolCallStep, ToolResultStep } from "../types";

function prettyJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2) ?? String(value);
  } catch {
    return String(value);
  }
}

function ToolCallBody({ step }: { step: ToolCallStep }) {
  const entries = Object.entries(step.arguments);
  return (
    <div className="tl-body">
      <div className="tl-call">
        <span className="fn">{step.name}</span>
        {"("}
        {entries.map(([key, value], index) => (
          <span key={key}>
            {index > 0 ? ", " : ""}
            <span className="arg">{key}</span>=
            <span className="str">{JSON.stringify(value)}</span>
          </span>
        ))}
        {")"}
      </div>
    </div>
  );
}

function ToolResultBody({ step }: { step: ToolResultStep }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="tl-body">
      <div className="tl-result-row">
        <button
          type="button"
          className="tl-expand"
          aria-expanded={expanded}
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? "Hide result" : "Show result"}
        </button>
        <span className="tl-result-chip">
          <ClockIcon size={12} strokeWidth={1.7} />
          {formatElapsed(step.elapsed_ms)}
        </span>
      </div>
      {expanded ? <pre className="code tl-json">{prettyJson(step.result)}</pre> : null}
    </div>
  );
}

function TimelineStep({ step }: { step: ReasoningStep }) {
  if (step.kind === "reasoning") {
    return (
      <div className="tl-step think">
        <div className="marker" aria-hidden="true" />
        <div className="tl-kind">Reasoning</div>
        <div className="tl-body">{step.text}</div>
      </div>
    );
  }
  if (step.kind === "tool_call") {
    return (
      <div className="tl-step tool">
        <div className="marker" aria-hidden="true" />
        <div className="tl-kind">Tool call · {step.name}</div>
        <ToolCallBody step={step} />
      </div>
    );
  }
  return (
    <div className="tl-step result">
      <div className="marker" aria-hidden="true" />
      <div className="tl-kind">Result</div>
      <ToolResultBody step={step} />
    </div>
  );
}

/**
 * Inline expandable "Show reasoning" timeline. Collapsed by default, including
 * while a turn is streaming (`live`) — the toggle stays clickable so the live
 * timeline (with the still-unclassified buffer) can be watched on demand.
 */
export function ReasoningPanel({
  steps,
  live = false,
  liveBuffer = "",
}: {
  steps: ReasoningStep[];
  live?: boolean;
  liveBuffer?: string;
}) {
  const [open, setOpen] = useState(false);
  const toolCalls = steps.filter((step) => step.kind === "tool_call").length;
  const summary =
    toolCalls === 0 ? "No tool calls" : toolCalls === 1 ? "1 tool call" : `${toolCalls} tool calls`;

  if (!live && steps.length === 0) return null;

  return (
    <div className="reasoning" data-open={open}>
      <button
        type="button"
        className="reasoning-toggle"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <span className="spark-ico" aria-hidden="true">
          <SparkIcon />
        </span>
        <span className="label-txt">
          <span className="main">{open ? "Hide reasoning" : "Show reasoning"}</span>
          <span className="meta">{live ? "Working on your request…" : summary}</span>
        </span>
        <span className="chev-r" aria-hidden="true">
          <ChevronRightIcon />
        </span>
      </button>
      {open ? (
        <div className="reasoning-panel">
          <div className="timeline">
            {steps.map((step, index) => (
              <TimelineStep key={index} step={step} />
            ))}
            {live && liveBuffer.trim() ? (
              <div className="tl-step think">
                <div className="marker" aria-hidden="true" />
                <div className="tl-kind">Thinking</div>
                <div className="tl-body tl-live">{liveBuffer}</div>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
