---
name: scaffold-fiori-ai-bridge
description: >
  Make a UI5 or Fiori app / library control AI-callable. Generates the JS bridge and
  all YAML files needed for Joule Frontend Actions (sap.das.webclient registration,
  scenario + function YAMLs, deploy.sh) and/or Chrome WebMCP tools
  (navigator.modelContext.registerTool). Works for Fiori Elements apps (List Report,
  Object Page), freestyle UI5 apps, and reusable library controls.
  Keywords: joule frontend actions, webmcp, joule bridge, joule-bridge.js,
  webmcp-bridge.js, frontend_action_name, sap.das.webclient, registerBridgeCallbacks,
  navigator.modelContext, registerTool, joule YAML, capability.sapdas.yaml,
  scenario yaml, function yaml, UI5 bridge, Fiori AI.
whenToUse: >
  Use this skill when you want Joule or a WebMCP-enabled AI model to call JavaScript
  running inside a live Fiori/UI5 app or control — reading data, applying filters,
  navigating pages, editing fields, or pressing buttons on the user's behalf.
---

## How to use this skill — prompts and tips

### Starter prompts (copy and adapt)

**App → Joule Frontend Actions + YAML:**
> "Scaffold Joule Frontend Actions for my product management app. I want Joule to filter the list, navigate to a product, and edit fields on the object page."

**App → WebMCP only:**
> "Add WebMCP tools to my Fiori app so a Chrome AI can filter the table and read the current row."

**Library control → WebMCP:**
> "Add WebMCP tools for the `sap.suite.ui.commons.Timeline` control. Put the bridge in the demokit sample."

**Existing Joule bridge → extend it:**
> "I already have a joule-bridge.js. Add a `submitOrder` Frontend Action for the new Submit button on the object page."

**Both consumers at once:**
> "Wire my app for both Joule and WebMCP. Joule gets the full YAML stack; WebMCP gets a companion bridge file in the app."

### Tips for best results

- **Name the intent, not just the control.** "I want Joule to filter by status and navigate to detail" gives better tool designs than "expose the SmartFilterBar".
- **Point to a demokit/test file early.** The skill will ask — having the path ready saves several turns.
- **Know roughly which page you want covered.** List Report only? Object Page only? Both? The skill asks, but a hint upfront speeds discovery.
- **For library controls**, the skill uses dynamic registry discovery — no hard-coded IDs needed. Just name the control class (`sap.m.FeedInput`, `sap.suite.ui.commons.Timeline`, etc.).
- **Security:** write operations (edit, save, submit, delete) get extra scrutiny. Have a view on whether Joule should confirm before executing.

### What this skill produces

| Target | Output files |
|---|---|
| Joule | `webapp/joule-bridge.js`, `joule/<app>/capability.sapdas.yaml`, `scenarios/frontend_action/<action>.yaml` × N, `functions/frontend_action/<action>.yaml` × N, `deploy.sh` |
| WebMCP | `webmcp-bridge.js` (location confirmed with you) |
| Both | All of the above |

---

You are helping a UI5 or Fiori Elements developer expose their app's capabilities as Joule Frontend Actions (SAP's production mechanism for Joule to call JS running in the browser) and optionally as Chrome WebMCP tools.

Follow these steps **in order**. Do not skip steps. Do not generate any code until Step 3.

---

## STEP 0 — Detect Joule environment

Scan the project root for signs of existing Joule configuration:
- `joule/` folder anywhere in the tree
- Any file named `capability.sapdas.yaml`, `da.sapdas.yaml`, or matching `*.sapdas.yaml`
- `joule` referenced in `package.json` scripts, `.joulerc`, or any `deploy.sh`

**If found**: note the existing namespace and `joule/` base path — use as defaults later.

**If not found**: inform the developer before continuing:

```
⚠ No Joule configuration detected in this project.

Joule Frontend Actions require three things beyond the JS bridge:
  1. Scenario + Function YAML files (this skill generates them)
  2. A Joule-enabled SAP BTP tenant with the capability deployed
  3. The Joule CLI to push YAMLs:  joule deploy joule --compile -n <name>

How would you like to proceed?
  a) Full setup — generate JS bridge + all YAML files + deployment instructions
  b) JS bridge only — skip YAML for now (I'll add Joule YAML later)
  c) WebMCP only — Chrome browser-native, no Joule integration
  d) I have a Joule folder elsewhere — let me give you the path

Wait for their answer before continuing. If (d), ask for the path.
```

---

## STEP 1 — Ask three setup questions

Ask these before reading any code:

**Q0 — Target type** (REQUIRED — changes discovery strategy downstream)
- "App — I'm in a UI5 or Fiori Elements application. Discover actual control IDs from views/controllers."
- "Library control — I'm working on a reusable UI5 control or library. Use dynamic registry discovery, not hard-coded IDs. Bridge goes in the test/demokit folder, not webapp/."

If the developer picks **Library control**, skip Steps 2's view/controller/manifest reads and instead:
- Read the control's `.js` source for its metadata block (properties, aggregations, events, public methods)
- Read any renderer or util file for rendered DOM patterns
- Read the demokit/test HTML to understand how the control is instantiated and what IDs are used in samples
- Output bridge to `test/.../demokit/<ControlName>-webmcp-bridge.js` (not `webapp/`)
- Skip all YAML generation (library controls have no Joule namespace of their own)

**Before starting analysis**, ask:
> "Can you point me to the demokit sample, test HTML, or any usage example for this control?
> Even a file path or folder name helps me find how it's instantiated faster.
> (If you're not sure, I'll search — but a pointer saves several turns.)"

Wait for the response before reading any files. If they provide a path, start there. If not, run a broad search for `<ControlName>` across the project.

**Q1 — Target consumer** (default: Joule with YAML)
- "Joule (JS bridge + YAML deployed via joule CLI)"
- "WebMCP only (Chrome experimental, JS only, no YAML needed)"
- "Both Joule and WebMCP"
- "Just the JS bridge for now"

**If the developer picks WebMCP only or Both**, ask immediately as a follow-up:

> "Where would you like the WebMCP registration to live?
>
>   a) **Demokit / test page only** *(recommended)* — a standalone `<ControlName>-webmcp-bridge.js`
>      loaded from the demokit HTML. No impact on the production library or app bundle.
>      Best for: exploring the control's AI surface, demos, developer testing.
>
>   b) **Alongside the control source** — a companion file in `src/.../` that consumers
>      can optionally load. Bridge registers on page load if WebMCP is available.
>      Best for: library teams who want to ship AI tooling as part of the control package.
>
>   c) **Embedded in the control's own JS** — registration added directly to the control's
>      `init()` or module body, guarded by `if (navigator.modelContext)`.
>      Best for: tightly coupling AI tooling to the control lifecycle.
>      ⚠ Adds a runtime browser-API check to every control instance — weigh carefully.
>
>   d) **In the consuming app** — `webapp/webmcp-bridge.js` loaded from the app's
>      `Component.js` or `index.html`. App-specific, app-controlled.
>      Best for: production apps that want to expose specific controls to an AI assistant.
>
> My suggestion: **(a) demokit** for library controls, **(d) consuming app** for app-specific use.
> The production control stays clean; teams that want AI tooling opt in explicitly."

Wait for their answer — it determines both the file path and the loading mechanism generated in Step 3.

**Q2 — Tool granularity** (default: semantic)
- "Semantic / intent-based tools (recommended) — e.g. 'filterByStatus', 'navigateToOrder'. Survives refactors."
- "Control-level tools — one tool per UI5 control ID. Brittle but granular."

Explain the trade-off if they ask.

---

## STEP 2 — Analyse the application (read-only)

Read these files **in parallel** (use parallel tool calls):
- `webapp/manifest.json` — namespace, routes, Fiori Elements page types (`sap.fe.templates.*`), OData service names
- `webapp/Component.js` (or `Component.ts`) — lifecycle hooks, existing bridge registrations
- `webapp/controller/*.js` and `webapp/controller/*.ts` — public methods, `onPress*`, `on*` handlers, any existing action methods
- `webapp/view/*.xml` — SmartFilterBar, SmartTable, SmartForm controls, toolbar action buttons, entity bindings
- `webapp/model/*.js` (if exists) — OData `read()`, `create()`, `update()`, `callFunction()` patterns
- `webapp/localService/metadata.xml` or any `*metadata.xml` — entity types, navigation properties, function imports
- Any existing `joule-bridge.js` or `webmcp-bridge.js`

**Detect Fiori Elements pages** from manifest targets:
- `sap.fe.templates.ListReport` → List Report
- `sap.fe.templates.ObjectPage` → Object Page
- `sap.fe.templates.AnalyticalListPage` → Analytical List Page

**Classify every discovered capability**:

| Category | Examples | Default |
|---|---|---|
| Navigation | route changes, drill-down to Object Page | ✓ include |
| Read/Query | table rows, filter state, field values, OData read | ✓ include |
| Write/Action | form field edit, OData CUD, toolbar button click | ✓ include (flag writes) |
| UI state | tab selection, dialog open/close, scroll | offer — user decides |
| Private/Internal | `_` prefix methods, framework private APIs | ⚠ exclude by default |
| Sensitive | auth, tokens, personal/financial data methods | ⚠ warn prominently |

---

## STEP 2b — Interactive tool discovery (MANDATORY GATE)

**No code is generated until the developer confirms the final tool list.**

### Phase 1 — Present grouped candidates

**This format is mandatory — do not use a flat list or markdown table.** Group by page/route:

```
📋 Here's what I found in your app that could become Joule Frontend Actions:

─── List Report: <EntitySetName> ────────────────────────────────
  ✓ filterByStatus      Filter the list by status field
  ✓ searchByCriteria    Apply filter bar values and trigger search
  ✓ getVisibleRows      Return currently visible rows as JSON
  ✓ navigateToDetail    Open the detail page for a selected row
  ⚠ _refreshInternal   Private method — excluded unless you opt in

─── Object Page: <EntityName> ───────────────────────────────────
  ✓ readFields          Read header field values
  ✓ editField           Set a field value (requires edit mode)
  ✓ enterEditMode       Click the Edit button
  ✓ saveChanges         Click Save
  ✓ executeAction       Click a toolbar action button by label
  ⚠ _validateEntry      Private validator — excluded unless you opt in

─── Cross-App Navigation ────────────────────────────────────────
  🔗 navigateToSalesOrders   Cross-app jump via CrossApplicationNavigation
     ⚠ Hard-coded variant IDs detected — confirm these are stable or
       parameterise before exposing. Breakage here is silent at runtime.

─── Shared ──────────────────────────────────────────────────────
  ✓ getAppContext       Return current route + selected entity key

Do any of these look wrong? Anything you'd like to add, remove, or rename?
Private/internal items above are excluded by default — tell me if you want them included.
Cross-app navigation items are flagged for explicit sign-off due to hard-coded routing params.
```

### Phase 2 — Ask targeted follow-up questions

After the developer's first response, ask ALL FOUR of these — do not skip any:

1. **Confirmation gates**: "Are any of these write operations (edit, save, submit, delete) sensitive enough that Joule should describe what it's about to do and ask for user confirmation before executing?"
2. **Page-scoping**: "Should any tools only appear on specific pages? (I can make the bridge return them dynamically based on the current route — useful if the same action name means different things on different pages.)"
3. **Read-before-write**: "For edit operations, should Joule first read the current field value before changing it? That allows Joule to say 'I'm about to change X from Y to Z, shall I?'"
4. **Specificity**: "For 'getVisibleRows' / 'readFields' — should they return everything visible, or only specific fields you care about?"

Incorporate their answers into the tool definitions before generating.

### Final confirmation

Show the final approved list with `frontend_action_name` handles AND ask where to place the file:

```
✅ Final tool list (ready to generate):

  com.sap.<ns>.filterByStatus.v1       → filterByStatus(status)
  com.sap.<ns>.getVisibleRows.v1       → getVisibleRows()
  com.sap.<ns>.navigateToDetail.v1     → navigateToDetail(id)
  com.sap.<ns>.readFields.v1           → readFields(sectionName?)
  com.sap.<ns>.editField.v1            → editField(fieldName, value)
  com.sap.<ns>.saveChanges.v1          → saveChanges()

📁 Suggested file placement:
  JS bridge:   webapp/joule-bridge.js          (app) — or —
               test/.../demokit/<Name>-webmcp-bridge.js  (library control)
  YAML:        joule/<appname>/...

Does this location work, or would you like the files placed somewhere else?
```

Wait for the developer to confirm or redirect before writing any files.

Proceeding to generate files now...
```

---

## STEP 3 — Generate files

Generate these files (ask before overwriting any existing file):

### `webapp/joule-bridge.js`

```javascript
'use strict';
var PROVIDER_ID = '<appNamespace>';

function wrap(name, fn) {
  return async function(params) {
    try { return await fn(params); } catch (e) {
      return { status: 'error', content: 'Error in ' + name + ': ' + e.message };
    }
  };
}

var bridgeCallbacks = {
  getApplicationContext: function(botName) {
    // Returns current app state so Joule understands where the user is
    var component = sap.ui.getCore().getComponent('<componentId>');
    var router = component && component.getRouter();
    var hash = router && router.getHashChanger().getHash();
    return {
      appId: '<appNamespace>',
      currentRoute: hash || window.location.hash,
      // Add entity keys, selected items, etc. for better Joule context
    };
  },

  getFrontendActions: function(jouleContext) {
    // Re-evaluated on every Joule message — return route-appropriate actions
    var actions = [];

    // --- Shared actions (always available) ---
    actions.push({
      frontend_action_name: 'com.sap.<ns>.getAppContext.v1',
      function: wrap('getAppContext', function() {
        return {
          status: 'success',
          content: JSON.stringify(bridgeCallbacks.getApplicationContext())
        };
      })
    });

    // --- Generated actions (one per confirmed tool) ---
    // TODO: replace with actual implementations per confirmed tool list
    /* EXAMPLE:
    actions.push({
      frontend_action_name: 'com.sap.<ns>.filterByStatus.v1',
      function: wrap('filterByStatus', function(params) {
        var filterBar = sap.ui.getCore().byId('<filterBarId>');
        // ... apply filter
        return { status: 'success', content: 'Filter applied: ' + params.status };
      })
    });
    */

    return actions;
  }
};

// Register with pre-registration fallback (page may load before Joule initialises)
if (window.sap && window.sap.das && window.sap.das.webclient) {
  window.sap.das.webclient.registerBridgeCallbacks(
    PROVIDER_ID, bridgeCallbacks, null,
    window.sap.das.webclient.CALL_PRIORITY.DEFAULT
  );
} else {
  window.sapdas = window.sapdas || {};
  window.sapdas.webclientPreregistration = window.sapdas.webclientPreregistration || {};
  window.sapdas.webclientPreregistration[PROVIDER_ID] = {
    callbacks: bridgeCallbacks, thisContext: null, priority: 3
  };
}
```

Then populate the `getFrontendActions` array with real implementations for each confirmed tool, using the app's actual control IDs and controller methods discovered in Step 2.

### `webapp/webmcp-bridge.js` (only if WebMCP target selected)

```javascript
if (!navigator.modelContext) return; // Chrome WebMCP not available

// One registerTool call per confirmed action
// Note: execute() returns a string directly (no status/content wrapper)
navigator.modelContext.registerTool({
  name: '<action_name>',
  description: '<LLM guidance — see standard below>',
  inputSchema: {
    type: 'object',
    properties: {
      // one entry per slot
    },
    required: [] // list required params
  },
  execute: function(params) {
    // call the same underlying function as joule-bridge.js
    return '<string result>';
  }
});
```

**WebMCP description quality standard (same bar as Joule scenario YAML):**

The `description` field is read by the AI model at call time — write it as LLM guidance, not API documentation.

Good — tells the model *when* to call, *how* to fill params, what to do when info is missing:
```
'Filter the product list by price range. Call this when the user mentions a price
bracket or asks to see products in a range. Map natural language to keys:
"0" = up to 100, "1" = 100–500, "2" = 500–1000, "3" = over 1000.
Example: "show me cheap products" → "0". Pass empty string if no range given.'
```

Bad — reads like API docs, gives the model no decision guidance:
```
'Applies a price range filter and triggers search on the list page.'
```

Apply the same standard to each `inputSchema` property `description` field — explain *when to pass empty string*, not just what the param means.

### YAML files (only if Joule + YAML target selected)

**`joule/<appname>/capability.sapdas.yaml`**:
```yaml
schema_version: 3.28.0
metadata:
  display_name: <App Display Name> Assistant
  namespace: com.sap.<namespace>
  name: <appname>_frontend
  version: 1.0.0
  description: >-
    Frontend actions for <App Display Name>.
```

**`joule/<appname>/deploy.sh`**:
```bash
#!/bin/bash
# Deploy Joule capability to BTP tenant
# Requires: joule CLI installed and logged in to BTP
joule deploy joule --compile -n <appname>_frontend
```

**Per confirmed action — scenario YAML** (`joule/<appname>/scenarios/frontend_action/<actionName>.yaml`):
```yaml
description: >-
  <Natural language description — max 1000 chars.>
  <Include LLM guidance: when to call this, how to fill each slot.>
  <For optional slots: "If not provided by user, pass empty string.">
  <Never ask the user for information they haven't given.>

slots:
  - name: <paramName>
    description: "<What this param means. When to pass empty string.>"

target:
  type: function
  name: frontend_action/<actionName>

response_context:
  - value: $target_result.actionStatus
    description: Status of the operation (success or error)
  - value: $target_result.actionContent
    description: Human-readable result or confirmation
```

**Per confirmed action — function YAML** (`joule/<appname>/functions/frontend_action/<actionName>.yaml`):
```yaml
parameters:
  - name: <paramName>

action_groups:
- actions:
  - type: frontend-action
    name: com.sap.<ns>.<ActionName>.v1
    parameters:
    - name: <paramName>
      value: "<? <paramName> ?>"
    result_variable: frontendActionResult

result:
  actionStatus: <? frontendActionResult.status ?>
  actionContent: <? frontendActionResult.content ?>
```

### Integration into `webapp/Component.js`

If `Component.js` does not already load `joule-bridge.js`, add it. For a UI5 component, add to `init()`:

```javascript
// In sap.ui.define callback, after other init work:
jQuery.sap.includeScript(sap.ui.require.toUrl('<appId>/joule-bridge.js'));
```

Or if using ES module imports, add to the define dependency list.

---

## STEP 4 — Post-generation summary

After generating all files, output a checklist:

```
✅ Generated files:
  webapp/joule-bridge.js              — JS bridge with pre-registration fallback
  [webapp/webmcp-bridge.js]           — Chrome WebMCP registration (if selected)
  joule/<appname>/capability.sapdas.yaml
  joule/<appname>/deploy.sh
  joule/<appname>/scenarios/frontend_action/<action>.yaml  (×N)
  joule/<appname>/functions/frontend_action/<action>.yaml  (×N)

📋 Next steps:
  1. Review joule-bridge.js — fill in any TODO placeholders with real control IDs
  2. Load joule-bridge.js from Component.js init() (if not already done)
  3. Install Joule CLI:  npm install -g @sap/joule-cli   (or check SAP tooling)
  4. Log in to BTP:     joule login
  5. Deploy:            cd joule/<appname> && bash deploy.sh
  6. Test in Joule:     Open app in BTP, open Joule chat, try a natural language phrase

🔍 Verification:
  - Joule: Joule-enabled BTP tenant → open app → Joule chat → trigger an action phrase
  - WebMCP: Chrome 149+ → chrome://flags/#enable-webmcp-testing → DevTools → Application → WebMCP
  - Console debug: Add ?debug=joule to app URL — bridge logs all calls

🧪 Testing WebMCP without the Chrome flag (mock pattern):
  Paste this in DevTools Console BEFORE the page loads (or in an initScript):

  ```javascript
  const _tools = {};
  Object.defineProperty(navigator, 'modelContext', {
    value: {
      registerTool: (def) => { _tools[def.name] = def; console.log('WebMCP tool registered:', def.name); }
    },
    configurable: true
  });
  ```

  Then after page load, call tools directly to verify logic:
  ```javascript
  JSON.parse(_tools.getFeedItems.execute())         // list all items
  _tools.readFeedItem.execute({ titleQuery: 'foo' }) // find by title
  ```

  This confirms registration and implementation without needing the flag enabled.

⚠ Security reminder:
  Browser-side registration alone is NOT sufficient for Joule. The capability YAML must be
  deployed to the Joule tenant via the CLI. Console injection cannot add Joule tools at runtime.
  Review all exposed tools — never expose private methods or auth/token handlers without team sign-off.
```

---

## Key constraints to respect in all generated code

- Handler return shape: `{ status: 'success'|'error', content: STRING }` — `content` must always be a string, never an object
- 15-second timeout — split multi-step operations into separate actions
- 10KB `response_context` limit — summarise data, never dump raw OData responses
- `getFrontendActions` is called fresh on every Joule message — register dynamically per current route
- Scenario description: max 1000 chars (Compiler-0190 error if exceeded)
- Joule has no `optional: true` for slots — use empty-string sentinel pattern and document it in the scenario description
- Naming convention: `com.sap.<namespace>.<ActionName>.v1` — must match exactly between JS and function YAML

---

## Standard Fiori Elements tool set (use as defaults when FE pages are detected)

**List Report** — add these unless developer removes them:
| Action | `frontend_action_name` suffix | Description |
|---|---|---|
| `filterList` | `.filterList.v1` | Apply filter bar values and trigger search |
| `getFilterState` | `.getFilterState.v1` | Return current filter state as JSON |
| `getTableRows` | `.getTableRows.v1` | Return visible rows as JSON string |
| `selectRow` | `.selectRow.v1` | Select a row by key field value |
| `navigateToDetail` | `.navigateToDetail.v1` | Open the detail page for a row |
| `getPageContext` | `.getPageContext.v1` | Return current route + selected key |

**Object Page** — add these unless developer removes them:
| Action | suffix | Description |
|---|---|---|
| `readSection` | `.readSection.v1` | Return field values from a named section |
| `editField` | `.editField.v1` | Set a form field value (requires edit mode) |
| `enterEditMode` | `.enterEditMode.v1` | Click the Edit button |
| `saveChanges` | `.saveChanges.v1` | Click Save |
| `discardChanges` | `.discardChanges.v1` | Click Cancel / Discard |
| `executeAction` | `.executeAction.v1` | Click a toolbar action button by label |
| `navigateBack` | `.navigateBack.v1` | Navigate back to the list |
