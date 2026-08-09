# Concept 02 — Premium service desk

A self-contained static prototype for a calm, professional customer-care workspace. Open `index.html` directly in a browser; no build step or dependencies are required.

## Design rationale

This concept treats customer support as a considered service interaction rather than an operations console. Editorial typography, warm neutral surfaces, restrained colour, and a narrow reading width make order information feel approachable without becoming casual. The Overview holds the customer identity and order count; the Assistant deliberately removes that large profile block so the conversation gets the full canvas.

The interface follows the operating system theme through `prefers-color-scheme`. Assistant answers include rendered bold emphasis, while the working state progresses through realistic, plain-language activities instead of exposing tool names or internal IDs.

## Strengths

- Distinct Overview and Assistant workspaces with accessible tabs.
- High readability and a premium service tone in light and dark modes.
- Useful activity feedback during the simulated assistant workflow.
- Responsive, keyboard-friendly, and dependency-free.

## Tradeoffs

- The editorial layout shows fewer orders at once than a dense admin dashboard.
- The warm visual language may be less suitable for brands that need a highly technical or utilitarian feel.
- Chat and activity are simulated locally; a production version would connect these states to streamed backend events.
