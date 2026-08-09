# Operations Console

A self-contained, dependency-free mockup for a compact customer-order workspace. Open `index.html` directly in a browser.

## Design rationale

The concept borrows from internal support and operations software: thin borders, dense tables, compact typography, and persistent context controls. Its near-black, warm-neutral, and orange palette is adapted from the Service Desk concept while retaining the Operations Console structure. Overview and Assistant are equal workspace tabs. Customer identity and aggregate order metrics appear only in Overview; Assistant receives only the application-controlled customer ID.

The Assistant includes a visible activity rail that reports real categories of work—understanding, product matching, order retrieval, and answer preparation. The conversation demonstrates rendered emphasis for important facts rather than exposing raw Markdown markers. The palette follows the operating system automatically through `prefers-color-scheme`.

## Strengths

- Efficient for repeated, information-dense support work.
- Clear separation between customer records and conversational help.
- Status activity feels auditable without exposing internal tool arguments or results.
- Responsive and usable without a build step or external assets.

## Tradeoffs

- The utilitarian visual language feels less warm than a consumer-facing product.
- The activity rail uses valuable horizontal space on desktop.
- Dense tables require horizontal scrolling on narrow phones.
- Interactions and answers are simulated; this is a visual prototype, not an API integration.
