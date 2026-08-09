# Command Center concept

A dependency-free UI mockup for a professional order-support workspace. Open `index.html` directly in a browser.

## Design rationale

This concept borrows from operations software rather than consumer chat products: a compact navigation rail, numbered work areas, dense record inspection, square geometry, and a visible activity trace. Overview and Assistant are deliberately separate workspaces. Customer identity, email, and order counts appear only in Overview; the Assistant keeps customer context private and focuses on the task.

The interface automatically follows the operating system’s light or dark appearance with `prefers-color-scheme`. Assistant messages render a small safe subset of Markdown (`**bold**`), demonstrated in the initial response. Submitting a message drives a realistic staged activity sequence before returning a mock grounded answer.

## Strengths

- Efficient, information-dense layout suited to support and operations teams.
- Live progress is explicit without exposing tool names, IDs, or raw tool output.
- Working customer selector, order inspector, workspace navigation, keyboard shortcuts, chat simulation, and clear action.
- Responsive layout and reduced-motion support.

## Tradeoffs

- The command-center aesthetic is more utilitarian than welcoming.
- The activity rail uses extra horizontal space on large screens, though it moves above the conversation on narrower screens.
- This static prototype intentionally mocks chat timing and supports only bold Markdown; production should use backend stream events and a vetted Markdown renderer.
