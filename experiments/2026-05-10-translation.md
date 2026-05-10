# 2026-05-10 Translation Review

## Scope

Reviewed generated translation artifacts for:

- `data/tau2/domains/{airline,retail,telecom}/{id,th,vi,zh,tl}/data_model.json`
- `data/tau2/domains/telecom/{id,th,vi,zh,tl}/user_data_model.json`
- `data/tau2/domains/{airline,retail,telecom}/{id,th,vi,zh,tl}/{tools,user_tools}.json`
- `data/tau2/domains/{airline,retail,telecom}/{id,th,vi,zh,tl}/tasks.json`
- translated DB/TOML/Markdown context artifacts discovered by
  `src/seatau/translation/config.py`

The review criterion is: translate agent-facing context as much as possible, but
preserve canonical runtime/evaluation values and structural keys.

## Verification Approach

- Rebuilt source schema artifacts from `src/tau2/domains/*/data_model.py` and
  `src/tau2/domains/telecom/user_data_model.py`.
- Compared generated translated schema artifacts against rebuilt source
  artifacts for:
  - same top-level structure
  - same model keys
  - same value-set keys
  - same `canonical` values
  - same enum `member` names where present
  - translated descriptions present for every source description
- Checked `localized` labels where `localized == canonical`, because these are
  the highest-risk signs of under-translation in the schema label layer.
- Reviewed runtime localization behavior in `src/seatau/translation/runtime_localization.py`:
  localized labels are exposed to tools, then normalized back to canonical values
  before tool execution/evaluation. Dict keys are not localized in tool payloads,
  so keys such as `phone` and `network` in telecom user DB stay safe.
- Ran a segment-level frozen-field review across translated JSON/TOML artifacts:
  task paths outside `TASK_TRANSLATABLE_PATTERNS`, DB string leaves outside
  configured translatable leaf keys, schema non-description/non-localized fields,
  all structural keys, and all list lengths must match source.
- Scanned translated artifacts for unresolved `__PH_N__` placeholders and
  checked manifest `generated_at`/`translated_at` metadata.

## Findings

### Schema Structure

- No structural mismatches found in reviewed `data_model.json` artifacts.
- No `canonical` value mismatches found in reviewed `data_model.json` artifacts.
- No missing translated description paths found in reviewed `data_model.json`
  artifacts.

### Under-Translated Localized Labels

Some `localized` labels are identical to `canonical`. Some are acceptable
technical/proper terms, but several should be improved because they are
agent-facing schema labels:

- `airline/tl/data_model.json`: `business`, `economy`, `gold`, `silver`,
  `regular`, `available`, `on time`.
- `retail/tl/data_model.json`: `refund`.
- `telecom/tl/data_model.json`: `phone`, `watch`, `Suspended`, `Draft`,
  `Overdue`, `Credit Card`, `Debit Card`.
- `telecom/{th,tl}/user_data_model.json`: network mode labels such as
  `4g_only`, `4g_5g_preferred` stayed code-like. These are localized labels,
  not canonicals, so they can be rendered more naturally while keeping the
  canonical values unchanged.

Likely acceptable unchanged labels:

- `PayPal`, `2G`, `3G`, `4G`, `5G`.
- `router`, `tablet`, and `internet` may be acceptable loanwords depending on
  language, but should be exposed to human reviewers.

### Manifest Metadata

- `translation_manifest.json` has per-asset `translated_at`, but no manifest-level
  generation timestamp. Add a top-level timestamp when writing the manifest.

### Translation Config

- `src/seatau/translation/config.py` still contains OpenRouter-oriented defaults even
  though the required route is Vertex AI Gemini 3.1 Flash Lite Preview.
- Current translation loop is effectively sequential at the batch-call layer;
  add controlled batch concurrency.

## Fix Log

- Done: patched translation config to default to
  `vertex_ai/gemini-3.1-flash-lite-preview`, removed OpenRouter-specific
  translation defaults, and added batch-level concurrency (`DEFAULT_MAX_CONCURRENCY = 8`).
- Done: added Vertex preflight checks for `google.auth`, `VERTEXAI_PROJECT`, and
  `VERTEXAI_LOCATION`. Added `google-auth` and `google-cloud-aiplatform` to core
  dependencies so gcloud/ADC Vertex translation works outside the voice extra.
- Done: added manifest-level `generated_at` and preserved per-asset
  `translated_at`.
- Done: improved the runtime-label prompt so code-like labels with underscores
  are translated as natural display labels while preserving technical standards
  and product names.
- Done: reran translation in the requested order:
  1. schema/data-model artifacts
  2. tools/user-tools artifacts
  3. context artifacts (`policy`, `db`, `tasks`)
- Done: manually patched remaining under-translated schema display labels while
  preserving all canonical values. Examples:
  - `airline/tl/data_model.json`: `business` -> `klase pang-negosyo`,
    `available` -> `may bakante`, `on time` -> `nasa oras`.
  - `retail/tl/data_model.json`: `refund` -> `pag-refund`.
  - `telecom/{id,th,tl}/user_data_model.json`: network-mode labels such as
    `4g_only` now use natural display labels.
- Done: own review after translation:
  - 20 schema artifacts checked.
  - 0 structural issue files.
  - 0 canonical mismatch files.
  - 0 unexpected unchanged localized-label files after allowing technical/product
    labels (`2G`, `5G`, `PayPal`, `internet`, etc.).
  - All expected translated files exist.
  - JSON/TOML structures match source where applicable.
  - Telecom `user_db.toml` permission keys such as `phone` and `network` remain
    unchanged across all languages.
  - Every expected manifest asset has `generated_at` and `translated_at`.
- Done: exported reviewer workbooks to:
  - `data/seatau/annotation/annotation_id.xlsx`
  - `data/seatau/annotation/annotation_th.xlsx`
  - `data/seatau/annotation/annotation_vi.xlsx`
  - `data/seatau/annotation/annotation_zh.xlsx`
  - `data/seatau/annotation/annotation_tl.xlsx`
- Done: regenerated `data/seatau/annotation/annotation_tl.xlsx` after the
  telecom Tagalog task rerun and IMEI schema patch.
- Done: improved workbook export structure:
  - guidance and examples tabs first
  - one tab per artifact
  - frozen/filterable headers
  - wrapped text and wider review columns
- Done: fixed annotation export domain inference so domain-specific DB fields are
  included. `airline_db` now exports 1,500 review rows per language instead of 0.
- Done: removed brittle translation-provider alternatives after the translation
  run:
  - only the exact LiteLLM route `vertex_ai/gemini-3.1-flash-lite-preview` is
    accepted for translation
  - removed provider/model alias normalization
  - removed non-Vertex API key/proxy/API-version options from the translation
    CLI/config path
  - kept `--max-concurrency` as the throughput control and removed custom RPM
    throttling
- Done: made schema runtime-label extraction more conservative so code-like
  labels with digits and multiple underscore groups stay canonical by default.
  This keeps labels such as `4g_only` and `4g_5g_preferred` from being treated
  like natural-language phrases while still translating simpler labels like
  `basic_economy` and `round_trip`.
- Done: added manifest-level `generated_at` in the writer code, not just in the
  generated files, so reruns keep writing a generation timestamp alongside the
  per-asset `translated_at` fields.
- Done: reran `data/tau2/domains/telecom/tl/tasks.json` after segment review
  found 6,253 eligible Tagalog task strings that were still English. The rerun
  used existing schema literal maps and rewrote only that task artifact.
- Done: manually patched the remaining eligible English schema segment in
  `data/tau2/domains/telecom/tl/data_model.json`:
  - `International Mobile Equipment Identity number` -> `Numero ng
    International Mobile Equipment Identity (IMEI)`
- Done: final own segment-level review after rerun/manual patch:
  - 110 translated files reviewed.
  - 1,306,405 string leaves checked against translatable/frozen path rules.
  - 0 structural mismatches.
  - 0 frozen evaluation/runtime string changes.
  - 0 unresolved placeholder leaks.
  - 0 manifest timestamp issues.
  - 0 unchanged eligible English segments under the automated threshold.
- Done: ran a stricter follow-up segment review that also checks line-level
  Markdown and tool-doc prose heuristics. It initially found a small set of
  eligible context segments still in English, with no frozen/evaluation fields
  changed.
- Done: patched the follow-up findings while preserving tool names, IDs, action
  names, manifest source fingerprints, canonical schema values, and frozen DB
  keys:
  - localized quoted transfer messages in translated airline/retail/telecom
    policies where the tool name remains `transfer_to_human_agents`
  - localized quoted user utterances in airline/retail task instructions
  - localized 69 repeated Tagalog retail DB product-name leaves:
    `Indoor Security Camera` and `LED Light Bulb`
  - localized the remaining Tagalog telecom schema description
    `Postal/ZIP code` -> `Kodigo postal/ZIP code`
- Done: reran the segment review after those patches:
  - 110 translated files reviewed.
  - 99,125 eligible context segments checked.
  - 1,306,405 frozen string leaves checked.
  - 0 issues.
- Done: regenerated all reviewer workbooks after the follow-up patches:
  - `data/seatau/annotation/annotation_id.xlsx`
  - `data/seatau/annotation/annotation_th.xlsx`
  - `data/seatau/annotation/annotation_vi.xlsx`
  - `data/seatau/annotation/annotation_zh.xlsx`
  - `data/seatau/annotation/annotation_tl.xlsx`
- Done: smoke-checked regenerated workbooks. Each workbook has 24 tabs, starts
  with `Annotation guideline` and `Examples`, and representative task tabs have
  reviewer `.final` columns.
- Done: ran `uv run tau2 check-data`; the data directory check passed.
- Done: normalized telecom `user_data_model.json` runtime labels for
  code-like underscore values, keeping `4g_only`/`4g_5g_preferred` and related
  network modes canonical in the translated artifacts and recording the manual
  patch timestamps in the manifests.
- Done: reran the annotation workbook export after the telecom schema label
  normalization. Each exported workbook still has 24 tabs with the expected
  `Annotation guideline` and `Examples` leading tabs.
- Done: added regression coverage for the new underscore-label heuristic and
  manifest `generated_at` handling in the translation tests.
- Done: verified the translation test subset and `uv run tau2 check-data` after
  the code and artifact changes.

## Remaining Human Review Items

- Confirm acceptable loanwords/technical labels that intentionally remain
  identical in some languages, such as `PayPal`, `2G`, `3G`, `4G`, `5G`,
  `router`, `tablet`, and `internet`.
- Review smoother phrasing in the workbook `*.final` columns, especially for
  large telecom task text and Tagalog retail phrasing where the model used
  mixed English/Tagalog terms such as `t-shirt`, `refund`, or `online store`.
