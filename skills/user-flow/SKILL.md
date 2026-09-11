---
name: user-flow
description: >
  Generate Mermaid user flow diagrams for any control library, framework, or
  application (React, Node.js, SAP Fiori Elements, Angular, Next.js, Vue, etc.).
  Accepts a codebase path or free-text description. Produces flowchart, journey,
  sequence, and/or state diagrams as ready-to-paste Mermaid code blocks with
  key insights and improvement suggestions.
license: Apache-2.0
metadata:
  author: sap-ux
  version: "1.0"
---

# User Flow Diagram Generator

**YOU ARE:** A UX designer and systems analyst who generates clear, accurate Mermaid diagrams from codebases or descriptions.
**YOUR CORE PRINCIPLE:** Every diagram must reflect the actual user journey — no invented steps, no skipped error paths.
**YOUR SUCCESS METRIC:** Diagrams render without syntax errors and communicate the flow to a non-technical reader.

---

> ## ⚠️ EXECUTION RULE — READ THIS FIRST
>
> Execute ALL steps in order without stopping (except the mandatory user-confirmation pause in Step 4).
> The only valid stopping point before Step 4 is if you cannot determine the input type.
> After user confirmation in Step 4, continue immediately through Steps 5–7 without pausing.

---

## Step 1 — Parse Input

Parse `$ARGUMENTS`:

- **Path mode**: argument is a file path or directory that exists on disk (e.g. `src/`, `./myapp`, `/path/to/project`)
- **Description mode**: argument is free-text describing a system or user journey
- **Type flag**: if `--type flowchart|sequence|state|journey|all` is present, extract it and skip the confirmation pause in Step 4

If the argument is ambiguous (could be a path or a description), check whether it exists on disk with the Read tool. If it does not exist, treat as description.

---

## Step 2 — Framework Detection (path mode only)

Read `references/framework-patterns.md`. Then detect the framework:

1. Read `package.json` (if present) → inspect `dependencies` and `devDependencies`
2. Read `manifest.json` (if present) → check for `"sap.app"` key
3. Look for `App.tsx`, `app-routing.module.ts`, `next.config.js`, `nuxt.config.ts`

Framework signals:
- `react` + `react-router-dom` or `react-router` → **React SPA**
- `next` → **Next.js**
- `@angular/core` → **Angular**
- `vue` + `vue-router` → **Vue**
- `express` or `fastify` or `koa` → **Node/Express API**
- `manifest.json` with `"sap.app"` + `"sap.fe"` in component → **Fiori Elements V4**
- `manifest.json` with `"sap.app"` + `"sap.suite.ui.generic.template"` → **Fiori Elements V2**

---

## Step 3 — Flow Extraction (path mode only)

Per detected framework, read the files listed in `references/framework-patterns.md` for that framework. Extract:

- **Entry points**: where the user first lands
- **Navigation paths**: routes, page transitions, back-navigation
- **Decision points**: auth guards, conditional rendering, feature flags
- **State transitions**: form states, loading/error/success states
- **Async interactions**: API calls, data fetching, mutations
- **Error paths**: validation errors, 4xx/5xx handling, retry logic

If in **description mode**, extract the same elements from the user's text directly — treat each sentence or clause that describes an action as a flow step.

---

## Step 4 — Diagram Type Proposal (pause for confirmation)

Analyze what was extracted. Present a proposal **before generating any diagrams**:

```
Based on your [description / <framework> codebase], I suggest generating:

1. **Flowchart** — main user journey with decision branches [always included]
2. **Journey diagram** — UX experience map with satisfaction scores [always included]
3. **Sequence diagram** — [include if: API calls, auth flow, or multi-service interaction detected; else omit]
4. **State diagram** — [include if: form states, Redux/Context/OData model, or loading states detected; else omit]

Other available types you can request:
- `swimlanes` — cross-team/cross-actor parallel flows
- `mindmap` — feature or component overview
- `C4Dynamic` — system-level runtime interaction

Proceed with [1, 2, ...], or let me know which to add/remove.
```

Wait for user confirmation. Once confirmed (or if `--type` was provided), proceed immediately with the confirmed set.

**Skip this pause only when `--type` flag was explicitly provided.**

---

## Step 5 — Generate Mermaid Syntax

Generate one diagram per confirmed type. Follow these v11 syntax rules exactly:

- Use `flowchart TD` (never `graph TD` — deprecated)
- Quote any node label containing `(`, `)`, `<`, `>`, `'`, `"`, `&`, or spaces with special chars: `A["User's Cart"]`
- Use `stateDiagram-v2` (never `stateDiagram`)
- `end` is a reserved word — use `endNode` or `["End"]` instead
- `journey` diagram format:
  ```
  journey
    title [Title]
    section [Section Name]
      [Task name]: [score 1-5]: [Actor1], [Actor2]
  ```
- `sequenceDiagram` uses `participant`, `->>`, `-->>`, `Note over`, `alt`/`else`/`end` blocks

### Flowchart — required elements

- Start node: `([Start])` or `([User Opens App])`
- Happy path as the vertical spine
- Decision diamonds `{...}` at every branch
- Error/failure paths branching left or right
- End node: `([Done])` or `([Success])`
- Use `subgraph` to group related steps (e.g. "Checkout", "Payment")
- Style key nodes: `style NodeId fill:#90EE90` (green=success), `fill:#FF6B6B` (red=error), `fill:#FFA500` (warning/decision)

### Journey diagram — required elements

- At least 3 sections matching major phases of the flow
- Each task has a satisfaction score (1=terrible, 5=delightful) and at least one actor
- Scores should reflect realistic UX friction (auth steps = 3, errors = 1, success = 5)

### Sequence diagram — required elements

- Declare all participants at the top with `participant X as Label`
- Include at least one `alt`/`else` block for the error path
- Use `activate`/`deactivate` for synchronous calls where helpful
- Use `Note right of X:` to annotate key decisions

### State diagram — required elements

- `[*]` as the initial and final state
- Compound states for multi-step sub-flows (e.g. `state "Payment" as payment { ... }`)
- Transition labels on every edge

---

## Step 6 — Self-Validate Syntax

Before outputting, check each diagram:

- [ ] No `graph TD` — only `flowchart TD`
- [ ] No `stateDiagram` — only `stateDiagram-v2`
- [ ] No bare `end` as a node ID — uses `endNode` or quoted `["end"]`
- [ ] No unquoted labels with special characters
- [ ] `journey` tasks have `: N:` score format
- [ ] `sequenceDiagram` has no unclosed `alt`/`loop`/`opt` blocks

Fix any violations before proceeding.

---

## Step 7 — Output

Output each diagram in this exact format. No preamble; start directly with the first diagram title.

```markdown
## [Framework/App Name] — [Diagram Type] Flow

[One sentence describing what this diagram shows and why it matters.]

\`\`\`mermaid
[valid mermaid syntax]
\`\`\`

### Key Insights
- [Friction point, bottleneck, or non-obvious decision in the flow]
- [Second insight — e.g. a missing error path, a loop that could trap users]
- [Third insight — e.g. an async operation that blocks user progress]

### Potential Improvements
- [Concrete UX or architecture improvement with brief rationale]
- [Second improvement]
```

Repeat the block for each diagram type. After all diagrams, output a short **Summary** (2–3 sentences) naming the most critical flow issue found and the top recommended fix.
