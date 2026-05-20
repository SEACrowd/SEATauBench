# YYYYMMDD — {experiment} / {agent_llm}

Must follow `experiments/YYYYMMDD-experiment-and-analysis-template.md`

List of simulation sources (should be 15 for 3 domains, 5 languages):

1.
2.
3.

## Language Analysis

- In the same domain, rank `pass_hat_*` metrics by language. Does the agent perform worse in lower-resource language? How worse across number of trials?
- Does the above pattern hold across domains?

## Log & Trace Analysis

Run the following scripts against the results file and paste output below.

```bash
uv run analyze-action-sequences data/simulations/<simulation_source>/results.json
uv run analyze-user-language    data/simulations/<simulation_source>/results.json
uv run analyze-agent-language   data/simulations/<simulation_source>/results.json
```

### User Simulator Analysis

Is `Qwen3 235B` a reliable user simulator?

**Language drift** (`analyze-user-language` output):

```
# paste script output here
```

**Task-critical errors** — high-severity failures that preclude task completion
(e.g., intent contradicts user goal, irrecoverable state transition):

- TBD

**Task-benign errors** — errors that do not prevent task completion:

- TBD

### Agent Analysis

### Language drift

### Task-critical errors

Replace the text with actual errors by domain and by language. Some examples include:

- In retail and airline, agent doesn't ask for user credentials like name, user name, user id, phone numbers or emails. Instead, they either (1) skip asking and calls the tool with a placeholder or (2) hallucinate a credential (e.g, guess user_id from the name). Observed in retail/id/kimi-k2.5, telecom/vi/gpt-5-mini, telecom for Qwen3.6 35B across many languages

```
When the user doesn't volunteer their email in the opening message, kimi in Chinese/Vietnamese correctly asks:

  ▎ "请提供您的电子邮箱地址以验证身份" (Please provide
  ▎ your email to verify)

  The user provides it, the task proceeds.

  In Indonesian, kimi skips asking and calls the tool with
   a placeholder:
  find_user_id_by_email(email="user@example.com")   # →
  Error: User not found
  find_user_id_by_email(email="user@example.com")   # →
  Error: User not found
  ...  ×10  →  too_many_errors

  For name+zip tasks:
  find_user_id_by_name_zip(first_name="Yara",
  last_name="Muller", zip="12345")  # fake zip
  ...  ×10  →  too_many_errors

  For airline/id it's even more direct — kimi derives the
  user_id from the name:
  get_user_details(user_id="noah_muller")   # guessed from
   "Noah Muller"
```

## Task Analysis

### Action sequence patterns (`analyze-action-sequences` output)

```
# paste script output here
```

### Tasks that consistently succeed across all three trials

Per-domain quantification: [N tasks all-pass] / [total tasks] / [total simulations]

Examples (task id + one-line reason why it succeeds):

-

### Tasks that consistently fail across all three trials

Per-domain quantification: [N tasks all-fail] / [total tasks] / [total simulations]

Examples (task id + one-line reason why it fails):

- **Failure types observed** — describe the dominant patterns for this domain/language.
  Use the `analyze-action-sequences` output as a starting point, then add qualitative
  detail from trajectory inspection. Common buckets from retail (may not apply here):
  `read_ok_write_fail`, final-confirmation missing, long multi-step. Name new buckets if
  the domain surfaces different failure modes.

1.

2.

## Cross-Experiment Analysis

- Tasks that succeed here but failed in a prior experiment, and why:
- Tasks that fail here but succeeded in a prior experiment, and why:
