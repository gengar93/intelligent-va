# UI concept comparison

These are dependency-free visual prototypes. They are intentionally separate from the React
application so the directions can be compared before any one of them becomes production code.
All chat responses and progress sequences are simulated.

## Shared requirements

Every concept includes:

- separate Overview and Assistant workspaces;
- customer identity and aggregate metrics only in Overview;
- automatic system light/dark appearance through `prefers-color-scheme`;
- rendered bold emphasis in assistant responses; and
- privacy-safe activity labels rather than internal tool names, arguments, or results.

## Concepts

### 1. Operations Console

[Open prototype](./01-operations-console/index.html) ·
[Read rationale](./01-operations-console/README.md)

A dense internal-tool direction with compact typography, square panels, thin dividers, and an
auditable activity rail. Its palette combines near-black surfaces, warm neutrals, and orange
accents from Service Desk. It feels the most like established operations software and makes
the best use of screen space without returning to the earlier blue treatment.

### 2. Service Desk

[Open prototype](./02-service-desk/index.html) ·
[Read rationale](./02-service-desk/README.md)

An editorial customer-care direction with a calmer reading width, restrained warm accents,
and conversation-first composition. It is the most approachable and polished, though it shows
fewer records at once than the denser concepts.

### 3. Command Center

[Open prototype](./03-command-center/index.html) ·
[Read rationale](./03-command-center/README.md)

A productivity-oriented interface with a navigation rail, keyboard shortcuts, numbered work
areas, and a persistent activity trace. It provides the clearest sense of system progress, but
its control-room character may be stronger than this product needs.

## Recommendation

The warm Operations Console is now the leading hybrid: it combines the most credible internal-
tool structure with the preferred Service Desk palette. The Command Center's more persistent
activity trace remains a useful optional element if greater workflow visibility is needed.

For the real React application, Markdown should be rendered with a maintained parser and a
restricted element set. Do not insert model output directly with `dangerouslySetInnerHTML`.
