# SEA-Tau Cost Analysis

Generated on 2026-05-26.

## Scope

This note estimates inference and translation costs for the runs indexed in
`data/seatau/experiments.csv`. Experiment token counts are read from
`results.json` LiteLLM usage metadata for trial `0`, then multiplied by three
for the three-trial estimate.

## Generation Configuration

| Role | Default model | Generation args |
|---|---|---|
| Agent | `openrouter/qwen/qwen3-235b-a22b-2507` | `{"temperature": 0.0}` |
| User simulator | `vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas` | `{"temperature": 0.0}` |

Other sampling controls are not set by default: `top_p`, `top_k`,
`max_tokens`, `max_completion_tokens`, and frequency/presence penalties.

## Pricing

OpenRouter pricing:

| Model | Input / 1M tokens | Output / 1M tokens |
|---|---:|---:|
| GPT-5-mini | `$0.25` | `$2.00` |
| Qwen3 235B | `$0.071` | `$0.100` |
| Kimi K2.5 | `$0.40` | `$1.90` |
| Qwen3.6 35B | `$0.15` | `$1.00` |

Vertex AI Gemini 3.1 Flash-Lite standard pricing:

| Model | Input / 1M tokens | Output / 1M tokens |
|---|---:|---:|
| Gemini 3.1 Flash-Lite | `$0.25` | `$1.50` |

Sources: <https://openrouter.ai/api/v1/models>,
<https://cloud.google.com/vertex-ai/generative-ai/pricing>

Formula:

```text
cost = input_tokens / 1_000_000 * input_price
     + output_tokens / 1_000_000 * output_price
```

## Experiment Cost Summary

| Scenario | Rows used | Agent cost, 3 trials | User simulator cost, 3 trials | Combined |
|---|---:|---:|---:|---:|
| `1-english-only` | 8 | `$70.40` | `$9.22` | `$79.63` |
| `2-multilingual-tools` | 54 | `$340.73` | `$60.06` | `$400.78` |
| `3-crosslingual` | 56 | `$403.27` | `$57.41` | `$460.68` |
| `4-translated` | 48 | `$440.43` | `$56.50` | `$496.94` |
| **Total** | **166** | **`$1,254.83`** | **`$183.19`** | **`$1,438.03`** |

## Agent Cost By Scenario

Rows are grouped by `(scenario, domain, agent model)`. Token counts are average
trial-0 counts for one indexed row in the group; total cost sums all rows in the
group and multiplies by three trials.

| Scenario | Domain | Agent model | Rows | Avg input | Avg output | Avg tokens | Total cost |
|---|---|---:|---:|---:|---:|---:|---:|
| `1-english-only` | retail | GPT-5-mini | 1 | 6,750,913 | 668,119 | 7,419,032 | `$9.07` |
| `1-english-only` | retail | Kimi K2.5 | 1 | 5,103,532 | 213,165 | 5,316,697 | `$7.34` |
| `1-english-only` | retail | Qwen3.6 35B | 1 | 9,109,933 | 507,135 | 9,617,068 | `$5.62` |
| `1-english-only` | airline | GPT-5-mini | 1 | 2,083,955 | 301,913 | 2,385,868 | `$3.37` |
| `1-english-only` | airline | Kimi K2.5 | 1 | 1,605,252 | 108,074 | 1,713,326 | `$2.54` |
| `1-english-only` | telecom | GPT-5-mini | 1 | 15,343,100 | 1,397,491 | 16,740,591 | `$19.89` |
| `1-english-only` | telecom | Kimi K2.5 | 1 | 10,388,755 | 340,752 | 10,729,507 | `$14.41` |
| `1-english-only` | telecom | Qwen3.6 35B | 1 | 13,777,566 | 650,971 | 14,428,537 | `$8.15` |
| `2-multilingual-tools` | retail | GPT-5-mini | 9 | 6,877,051 | 692,038 | 7,569,089 | `$83.79` |
| `2-multilingual-tools` | retail | Qwen3 235B | 9 | 10,601,968 | 117,774 | 10,719,742 | `$20.64` |
| `2-multilingual-tools` | airline | GPT-5-mini | 9 | 2,387,569 | 353,384 | 2,740,953 | `$35.20` |
| `2-multilingual-tools` | airline | Qwen3 235B | 9 | 4,370,593 | 61,533 | 4,432,126 | `$8.54` |
| `2-multilingual-tools` | telecom | GPT-5-mini | 9 | 13,608,467 | 1,263,689 | 14,872,156 | `$160.10` |
| `2-multilingual-tools` | telecom | Qwen3 235B | 9 | 16,789,601 | 100,016 | 16,889,617 | `$32.46` |
| `3-crosslingual` | retail | GPT-5-mini | 5 | 7,686,544 | 849,845 | 8,536,389 | `$54.32` |
| `3-crosslingual` | retail | Qwen3 235B | 5 | 9,678,990 | 150,211 | 9,829,201 | `$10.53` |
| `3-crosslingual` | retail | Kimi K2.5 | 5 | 6,667,382 | 351,116 | 7,018,498 | `$50.01` |
| `3-crosslingual` | retail | Qwen3.6 35B | 4 | 9,465,614 | 503,077 | 9,968,691 | `$23.08` |
| `3-crosslingual` | airline | GPT-5-mini | 5 | 2,418,397 | 405,671 | 2,824,068 | `$21.24` |
| `3-crosslingual` | airline | Qwen3 235B | 5 | 4,154,613 | 70,802 | 4,225,415 | `$4.53` |
| `3-crosslingual` | airline | Kimi K2.5 | 5 | 2,226,517 | 167,166 | 2,393,683 | `$18.12` |
| `3-crosslingual` | airline | Qwen3.6 35B | 5 | 3,666,112 | 327,699 | 3,993,811 | `$13.16` |
| `3-crosslingual` | telecom | GPT-5-mini | 5 | 14,670,094 | 1,403,885 | 16,073,979 | `$97.13` |
| `3-crosslingual` | telecom | Qwen3 235B | 5 | 16,461,243 | 209,531 | 16,670,774 | `$17.85` |
| `3-crosslingual` | telecom | Kimi K2.5 | 4 | 11,579,284 | 581,200 | 12,160,484 | `$68.83` |
| `3-crosslingual` | telecom | Qwen3.6 35B | 3 | 14,907,078 | 482,424 | 15,389,502 | `$24.47` |
| `4-translated` | retail | GPT-5-mini | 5 | 9,762,125 | 894,324 | 10,656,449 | `$63.44` |
| `4-translated` | retail | Qwen3 235B | 5 | 15,371,492 | 154,761 | 15,526,253 | `$16.60` |
| `4-translated` | retail | Kimi K2.5 | 5 | 9,083,664 | 342,145 | 9,425,809 | `$64.25` |
| `4-translated` | retail | Qwen3.6 35B | 1 | 9,914,309 | 463,757 | 10,378,066 | `$5.85` |
| `4-translated` | airline | GPT-5-mini | 5 | 2,779,028 | 370,304 | 3,149,332 | `$21.53` |
| `4-translated` | airline | Qwen3 235B | 5 | 4,824,582 | 71,584 | 4,896,166 | `$5.25` |
| `4-translated` | airline | Kimi K2.5 | 3 | 3,437,989 | 179,795 | 3,617,784 | `$15.45` |
| `4-translated` | airline | Qwen3.6 35B | 5 | 4,252,764 | 257,059 | 4,509,823 | `$13.42` |
| `4-translated` | telecom | GPT-5-mini | 5 | 17,488,658 | 1,299,192 | 18,787,850 | `$104.56` |
| `4-translated` | telecom | Qwen3 235B | 5 | 24,431,032 | 227,806 | 24,658,838 | `$26.36` |
| `4-translated` | telecom | Kimi K2.5 | 4 | 18,828,568 | 585,044 | 19,413,612 | `$103.72` |

## User Simulator Cost

The user simulator is priced as Qwen3 235B.

```text
trial-0 user input tokens = 847,486,164
trial-0 user output tokens = 8,925,349
trial-0 user total tokens = 856,411,513

three-trial user input tokens = 2,542,458,492
three-trial user output tokens = 26,776,047
three-trial user total tokens = 2,569,234,539

three-trial user cost
= 2,542.458492M * $0.071 + 26.776047M * $0.100
= $183.19
```

| Scenario | Rows | Trial-0 input | Trial-0 output | Trial-0 tokens | Three-trial cost |
|---|---:|---:|---:|---:|---:|
| `1-english-only` | 8 | 42,740,631 | 404,016 | 43,144,647 | `$9.22` |
| `2-multilingual-tools` | 54 | 277,974,494 | 2,824,186 | 280,798,680 | `$60.06` |
| `3-crosslingual` | 56 | 265,546,095 | 2,821,058 | 268,367,153 | `$57.41` |
| `4-translated` | 48 | 261,224,944 | 2,876,089 | 264,101,033 | `$56.50` |

| Domain | Rows | Trial-0 input | Trial-0 output | Trial-0 tokens | Three-trial cost |
|---|---:|---:|---:|---:|---:|
| retail | 56 | 51,325,547 | 2,486,533 | 53,812,080 | `$11.68` |
| airline | 58 | 20,206,970 | 1,068,432 | 21,275,402 | `$4.62` |
| telecom | 52 | 775,953,647 | 5,370,384 | 781,324,031 | `$166.89` |

## Translation Cost

The translation pipeline used `vertex_ai/gemini-3.1-flash-lite-preview` for all
three domains and five target languages.

| Languages | Files per language | Segments per language | Calls per language | Input tokens per language | Output tokens per language |
|---:|---:|---:|---:|---:|---:|
| 5 | 22 | 18,979 | 791 | 1,793,553 | 1,441,564 |

```text
translation input tokens = 1,793,553 * 5 = 8,967,765
translation output tokens = 1,441,564 * 5 = 7,207,820

standard Gemini 3.1 Flash-Lite cost
= 8.967765M * $0.25 + 7.207820M * $1.50
= $13.05
```

## Validation Examples

```text
2-multilingual-tools retail GPT-5-mini agent cost
= 6.877051M * $0.25 + 0.692038M * $2.00
= $3.103339 per row trial
= $3.103339 * 9 rows * 3 trials
= $83.79
```

```text
all-scenario user simulator cost
= 2,542.458492M * $0.071 + 26.776047M * $0.100
= $180.514553 + $2.677605
= $183.19
```
