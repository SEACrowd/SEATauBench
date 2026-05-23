# Translation Pipeline Appendix

## Language details

| Code | Language                      | Script family      |
| ---- | ----------------------------- | ------------------ |
| `id` | Indonesian                    | Latin              |
| `th` | Thai                          | Thai abugida       |
| `tl` | Tagalog (Filipino)            | Latin              |
| `vi` | Vietnamese                    | Latin + diacritics |
| `zh` | Mandarin Chinese (Simplified) | CJK logographic    |

These five target languages are typologically distinct from English and from one
another, covering three script families and four language families.

## Tau2 Bench Context

Each Tau2 domain exposes the agent to two coupled surfaces.

1. `data/tau2/domains/{domain}/` contains the benchmark content seen during an
   interaction: task definitions in `tasks.json`, domain policies and workflow
   documents in markdown files `*.md`, and structured databases in `db.json`, `db.toml`, or
   user-side DB files.
2. `src/tau2/domains/{domain}/` contains the executable tool interface:
   toolkits in `tools.py` and `user_tools.py`, schema definitions in
   `data_model.py` and `user_data_model.py`, and in telecom, tool-return string
   templates.

At runtime, the agent must read policy, reason about tasks, call tools, inspect
tool outputs, and communicate with a simulated user entirely in the target
language. The benchmark therefore requires more than document translation: it
requires a localized agent-facing interface whose visible natural language is in
the target language, while the underlying execution layer continues to operate
on the original canonical English values.

The table below summarizes the surfaces that must remain aligned.

| Surface               | Example source files                   | Why it matters                                                                                           |
| --------------------- | -------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Task setup            | `tasks.json`                           | Defines user personas, instructions, initial dialogue, and evaluation-facing natural-language assertions |
| Policy and workflow   | `policy.md`, telecom workflow manuals  | Governs the agent's allowed behavior and domain procedures                                               |
| Tool descriptions     | `tools.py`, `user_tools.py` docstrings | Conditions how the agent interprets tool semantics and arguments                                         |
| Schemas and literals  | `data_model.py`, `user_data_model.py`  | Define enum choices and field descriptions that appear in tool schemas                                   |
| Database content      | `db.json`, `db.toml`, `user_db.toml`   | Supplies names, titles, and other textual fields surfaced through tool results                           |
| Runtime tool messages | `tool_returns.json`                    | Ensures exact strings and templates returned by tools remain localized                                   |

## Design principles

Adapting τ-bench to non-English languages requires translating the
_natural-language content_ seen by the language model while leaving untouched
the _runtime-canonical tokens_ consumed by the tool execution layer: enum
literals, entity identifiers, status codes, and tool argument names.
Conflating these two layers corrupts evaluation: a translated enum value that
reaches the execution engine triggers a lookup failure, while an untranslated
persona description breaks the monolingual interaction we intend to test. We
therefore build the pipeline around four invariants:

1. **Runtime invariance.** Canonical tokens remain English at execution time.
   Only the LLM-visible surface is localized.
2. **Terminological consistency.** A canonical value should surface with the
   same target-language realization everywhere it appears.
3. **Format fidelity.** Translation is applied only to natural-language leaves.
   Structural keys, numeric fields, booleans, and program identifiers are never
   modified.
4. **Bidirectional transparency.** Localized values can be mapped back to
   canonical English forms before execution and before metric computation.

The implementation has two phases: an **offline translation phase** that
materializes language-specific assets, and a **runtime localization phase** that
patches the environment presented to the agent.

## Offline translation phase

The offline phase consumes a domain's static artifacts and writes translated
outputs to `data/tau2/domains/{domain}/{lang_id}/`.

| Artifact class        | Source files                          | Translatable content                                                                             |
| --------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Task definitions      | `tasks.json`                          | Persona text, instructions, reason-for-call fields, message history, natural-language assertions |
| Policy documents      | `*.md`                                | Full document prose                                                                              |
| Databases             | `db.json`, `db.toml`, `user_db.*`     | Selected natural-language leaf fields only                                                       |
| Tool docstrings       | `tools.py`, `user_tools.py`           | Docstrings of tool-decorated methods                                                             |
| Data-model schema     | `data_model.py`, `user_data_model.py` | Descriptions, enum values, and `Literal[...]` values                                             |
| Tool return templates | `tool_returns.json`                   | Exact messages and parameterized output templates                                                |

**Step 1 — Artifact discovery and typing.** For each selected domain, the
pipeline discovers files from `data/tau2/domains/{domain}/` and
`src/tau2/domains/{domain}/`, then assigns each file a processing kind
(`markdown`, `json`, `toml`, or `python`). Component selection is explicit:
`tools`, `schema`, `policy`, `db`, and `tasks`, with `context` expanding to
`policy + db + tasks`.

**Step 2 — Segment extraction with path-sensitive rules.** Each file is reduced
to minimal translatable segments together with metadata describing its source
path and type.

- Markdown files yield a single full-document segment.
- Task JSON is walked recursively, but only a curated allowlist of paths is
  translated, including persona fields, task instructions, reason-for-call,
  natural-language assertions, and user- or assistant-visible message history.
- Database JSON/TOML is translated only at conservative natural-language leaf
  keys such as `name`, `title`, `description`, `summary`, and `notes`.
- Tool Python files are parsed with `ast`; only docstrings attached to
  `@is_tool` or `@is_discoverable_tool` methods are extracted.
- Google-style tool docstrings are decomposed into short description, long
  description, parameter descriptions, returns text, and raises text so that
  each part can be translated independently and later reassembled.
- Schema Python files are converted into JSON artifacts whose translatable
  fields include class descriptions, field descriptions, enum values, and
  `Literal[...]` alternatives.
- Tool return files expose both exact response strings and template strings as
  translatable segments.

**Step 3 — Canonical-token protection.** Before translation, the pipeline
collects and masks strings that must remain canonical: IDs such as
`order_*` or `booking_*`, status values, structural task markers, tool names,
and docstring section headers such as `Args` or `Returns`. Protection is partly
global and partly contextual. For example, airline literals such as
`basic_economy` or `round_trip` are protected when they occur in cabin-class or
trip-type contexts, but not when similar surface strings appear as ordinary
prose. The masking layer replaces protected strings with opaque placeholders and
restores them after translation.

**Step 4 — Schema-first literal translation.** Schema enum labels and
`Literal[...]` values are translated first in a dedicated literal mode. This
produces language-specific schema artifacts from which the pipeline builds a
domain literal map, including alias forms such as underscore, space-separated,
or hyphenated variants of the same canonical value. This step fixes the
localized terminology before any longer-form prose is translated.

**Step 5 — Standard translation with glossary injection.** All remaining
segments, including task prose, policy text, tool docstrings, database leaves,
and tool-return templates, are translated in standard mode. The model receives
the schema-derived literal map as a glossary, and segments are pre-masked so
that localized forms are restored consistently. Requests are deduplicated when
possible, batched as structured JSON, and executed concurrently through
LiteLLM. The current implementation requires the exact Vertex route
`vertex_ai/gemini-3.1-flash-lite-preview`. Batch failures can be retried,
recursively split, or rerun individually if placeholder restoration fails.

**Step 6 — Format-aware writing and manifest recording.** The translated text is
written back using format-specific writers: markdown is emitted directly;
JSON/TOML files are patched only at extracted addresses; tool docstrings are
reconstructed and saved as `tools.json` or `user_tools.json`; schema artifacts
are written as `data_model.json` and `user_data_model.json`; and DB files with
no translated leaves are still copied through so the translated directory
remains complete. Each language directory also receives
`translation_manifest.json`, which records the output file, component, source
language, target language, model, translation timestamp, and SHA-256
fingerprints of the source files. This manifest enables later staleness checks
without forcing retranslation.

## Runtime localization phase

The offline artifacts cover static content, but the agent also sees dynamic tool
schemas and tool outputs at inference time. These are handled by a runtime
localization layer built from the paired source and translated schema artifacts.

**Step 7 — Build runtime localization maps.** A
`SchemaRuntimeLocalizer` constructs four resources from the source and localized
schema artifacts: a description map, a canonical-to-localized literal map, a
localized-to-canonical inverse map, and optional maps for exact and templated
tool-return localizations.

**Step 8 — Localize the tool schema shown to the agent.** The environment's
`get_tools()` path is wrapped so that the agent receives localized tool schemas:
descriptions are translated, enum choices are shown in the target language, and
default or example literal values are localized where appropriate. The tool
implementation itself is unchanged.

**Step 9 — Normalize localized arguments and localize tool outputs.** Before
tool execution, localized enum arguments supplied by the agent are mapped back
to their canonical English values. After execution, structured response payloads
and tool-return messages are localized back into the target language so the
interaction remains monolingual from the agent's perspective.

**Step 10 — Canonicalize localized values for evaluation.** Prior to metric
computation, localized payloads are canonicalized back to English. This makes
pass-rate comparisons directly comparable across languages and against the
original English benchmark.

## Translation corpus statistics

All translations were produced with **Vertex AI Gemini Flash Lite**
(`vertex_ai/gemini-3.1-flash-lite-preview`).

### Coverage

The current pipeline materializes the following core artifacts per language,
excluding `translation_manifest.json` and excluding legacy side files such as
`split_tasks.json` that were not produced by the main pipeline:

| Domain    | Languages translated        | Core translated artifacts per language                                                                                                                                 | Total core translated artifacts |
| --------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| Airline   | id, th, tl, vi, zh          | 5 (`data_model.json`, `db.json`, `policy.md`, `tasks.json`, `tools.json`)                                                                                              | 25                              |
| Retail    | id, th, tl, vi, zh          | 5 (`data_model.json`, `db.json`, `policy.md`, `tasks.json`, `tools.json`)                                                                                              | 25                              |
| Telecom   | id, th, tl, vi, zh          | 13 (`data_model.json`, `user_data_model.json`, `db.toml`, `user_db.toml`, `tasks.json`, 5 policy/workflow files, `tools.json`, `user_tools.json`, `tool_returns.json`) | 65                              |
| **Total** | **5 languages × 3 domains** | —                                                                                                                                                                      | **115**                         |

### Artifact composition

**Tasks** (scenario definitions, persona instructions, natural-language
assertions, and visible message history):

| Domain  | Tasks in source | Source string fields | Source chars | Translated task instances (×5 langs) |
| ------- | --------------- | -------------------- | ------------ | ------------------------------------ |
| Airline | 50              | 1,305                | 53,361       | 250                                  |
| Retail  | 114             | 3,398                | 90,370       | 570                                  |
| Telecom | 2,285           | 131,657              | 6,232,533    | 11,425                               |

**Tool docstrings** (translated tool-facing descriptions emitted as JSON):

| Domain  | Agent tools | User tools | Total translated docstrings per language | Approx. source docstring chars |
| ------- | ----------- | ---------- | ---------------------------------------- | ------------------------------ |
| Airline | 14          | 0          | 14                                       | 6,438                          |
| Retail  | 16          | 0          | 16                                       | 10,588                         |
| Telecom | 13          | 30         | 43                                       | 9,684                          |

**Policy and workflow documents** (full-document markdown translation):

| Domain  | Source markdown files | Approx. English word count | Translated document instances (×5 langs) |
| ------- | --------------------- | -------------------------- | ---------------------------------------- |
| Airline | 1                     | 1,313                      | 5                                        |
| Retail  | 1                     | 1,158                      | 5                                        |
| Telecom | 5                     | 10,172                     | 25                                       |

**Schema artifacts** (localized descriptions and literal inventories):

| Domain  | Agent schema value sets | Agent localized values | User schema value sets | User localized values |
| ------- | ----------------------- | ---------------------- | ---------------------- | --------------------- |
| Airline | 15                      | 21                     | 0                      | 0                     |
| Retail  | 6                       | 14                     | 0                      | 0                     |
| Telecom | 5                       | 22                     | 7                      | 29                    |

**Database artifacts** (structure preserved; only selected natural-language leaf
fields translated):

| Domain  | Format | Translated DB outputs per language | Underlying records                                                 |
| ------- | ------ | ---------------------------------- | ------------------------------------------------------------------ |
| Airline | JSON   | `db.json`                          | 500 users, 300 flights, 2,000 reservations                         |
| Retail  | JSON   | `db.json`                          | 500 users, 1,000 orders, 50 products                               |
| Telecom | TOML   | `db.toml`, `user_db.toml`          | 4 customers, 5 plans, 9 devices, 9 lines, 6 bills, 20 user devices |

## Examples

### Example 1: Tool docstring extraction and reconstruction (`tools.json`)

The source tool code stores human-facing descriptions as Python docstrings. The
offline pipeline extracts those docstrings, translates them, and writes the
result to `tools.json` or `user_tools.json`, leaving the Python code unchanged.

English (`src/tau2/domains/telecom/user_tools.py`):

```text
Checks your phone's connection status to cellular networks and Wi-Fi. Shows
airplane mode status, signal strength, network type, whether mobile data is
enabled, and whether data roaming is enabled.
```

Chinese (`data/tau2/domains/telecom/zh/user_tools.json`):

```text
Checks 您 手机 的蜂窝网络和 Wi-Fi 连接状态。显示飞行模式状态、信号强度、网络类型、移动数据是否已启用以及数据漫游是否已启用。
```

The important property here is not stylistic perfection but interface
consistency: the agent sees the translated tool description through the runtime
tool schema, while the callable tool name and argument keys remain canonical.

### Example 2: Tool-return templates with placeholders preserved

Tool-return localization is slightly different from ordinary prose translation
because the response string also serves as a runtime template. The textual
scaffold is translated, while placeholders and matching patterns remain
canonical.

English (`src/tau2/domains/telecom/tool_returns.json`):

```json
{
  "pattern": "^Successfully added (?P<gb_amount>.+) GB of data for line (?P<line_id>.+) for \\$(?P<charge>.+)$",
  "template": "Successfully added {gb_amount} GB of data for line {line_id} for ${charge}"
}
```

Chinese (`data/tau2/domains/telecom/zh/tool_returns.json`):

```json
{
  "pattern": "^Successfully added (?P<gb_amount>.+) GB of data for line (?P<line_id>.+) for \\$(?P<charge>.+)$",
  "template": "已成功为线路 {line_id} 添加 {gb_amount} GB 数据，费用为 {charge} 美元"
}
```

This illustrates the central invariant of the pipeline: target-language prose is
localized, but runtime-bearing slots such as `{gb_amount}` and `{line_id}`
remain intact.

### Example 3: Nested database structures with selective leaf translation

Database translation is intentionally surgical. The structure, IDs, options, and
status fields are left untouched, while selected leaf strings are localized.

English (`data/tau2/domains/retail/db.json`):

```json
{
  "order_id": "#W2611340",
  "address": {
    "address1": "215 River Road",
    "address2": "Suite 991",
    "city": "New York",
    "country": "USA",
    "state": "NY",
    "zip": "10083"
  },
  "items": [
    {
      "name": "Water Bottle",
      "product_id": "8310926033",
      "item_id": "6469567736",
      "price": 47.84,
      "options": {
        "capacity": "1000ml",
        "material": "glass",
        "color": "blue"
      }
    }
  ],
  "status": "processed"
}
```

Chinese (`data/tau2/domains/retail/zh/db.json`):

```json
{
  "order_id": "#W2611340",
  "address": {
    "address1": "215 River Road",
    "address2": "Suite 991",
    "city": "New York",
    "country": "USA",
    "state": "NY",
    "zip": "10083"
  },
  "items": [
    {
      "name": "水瓶",
      "product_id": "8310926033",
      "item_id": "6469567736",
      "price": 47.84,
      "options": {
        "capacity": "1000ml",
        "material": "glass",
        "color": "blue"
      }
    }
  ],
  "status": "processed"
}
```

The nested JSON container is unchanged. Only the designated natural-language
leaf `items[].name` is translated; IDs, addresses, option keys, and the runtime
status literal remain canonical.
