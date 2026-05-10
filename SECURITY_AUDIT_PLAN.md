# Security Audit Remediation Plan

Source: `trustworthy-env` benchmark vulnerability scanner (formal + LLM heuristic detectors)
Scanned path: `src/`

---

## Summary

| Severity               | Count | Status                |
| ---------------------- | ----- | --------------------- |
| High (genuine)         | 0     | —                     |
| Medium (genuine)       | 4     | To fix                |
| Low (defense-in-depth) | 3     | To fix                |
| False positive         | 11    | Documented, no action |

---

## Findings to Fix

### M1 — Weak test assertions in green/white agent tests

**Files:** `src/experiments/agentify_tau_bench/tests/test_green_agent.py`, `test_white_agent.py`
**Detector:** formal `weak_test_assertions` (75%), LLM `hardcoded_or_predictable_output` (85%)

**Problem:**

- `TestLoadAgentCardToml.test_load_agent_card_toml` only checks `"name" in result` and `"description" in result` — key presence, not value validity (non-empty string, correct type).
- `test_execute_basic_flow` hardcodes `mock_simulation.reward_info.reward = 1` and asserts on it with no assertions about the actual reward computation path.
- `test_start_green_agent_setup` checks `call_kwargs["port"] == 9001` but not `call_kwargs["host"]`.

**Fix:**

- Add value-level assertions: check that `result["name"]` is a non-empty `str`, `result["description"]` is a non-empty `str`.
- Add assertions that `call_kwargs["host"] == "localhost"` (already present but verify it's actually asserted).
- For the executor test, assert on the enqueued event content, not just that `enqueue_event` was called once.

---

### M2 — Overly broad exception swallowing in `evaluate_trajectories.py`

**File:** `src/tau2/scripts/evaluate_trajectories.py:144`
**Detector:** (inferred from LLM `evaluation_script_bug` 75%)

**Problem:**
The loop body catches `except Exception as e` and logs a single string. This collapses schema errors, IO errors, and reward computation bugs into one indistinguishable failure mode, making debugging harder and masking partial failures.

```python
except Exception as e:
    console.print(f"  ❌ Error processing file: {e}", style="red")
```

**Fix:**
Catch specific exception types in priority order:

1. `json.JSONDecodeError` / `pydantic.ValidationError` → "Invalid trajectory format"
2. `OSError` → "File read error"
3. `Exception` → last-resort fallback with `logger.exception` for stack trace

---

### M3 — `db_verify_structure.py` does not handle `None` values

**File:** `src/utils/db_verify_structure.py:58–65`
**Detector:** LLM `evaluation_script_bug` (75%)

**Problem:**
`_type_name()` falls through to `type(value).__name__` for all non-bool/int/float values. For `None`, this returns `"NoneType"`. If a translated DB field becomes `null` (e.g., a translator outputs `null` for an untranslatable field) but the original has a non-null string, the mismatch is caught — but with a confusing type name (`"NoneType"` vs `"str"`) that the user sees raw.

More critically, `None` and `null` in JSON are a common translation error vector, and the tool should surface these clearly.

**Fix:**
Add an explicit `None` branch to `_type_name`:

```python
if value is None:
    return "null"
```

And add a test case in the test suite (or script docstring) that verifies a `null`-vs-`str` mismatch is reported.

---

### M4 — File existence check without content integrity in `verify_trajectories.py`

**File:** `src/tau2/scripts/leaderboard/verify_trajectories.py:84–89`, `src/tau2/scripts/evaluate_trajectories.py:115–119`
**Detector:** formal `weak_test_assertions` (85%)

**Problem:**
Both scripts do:

```python
if not os.path.exists(file_path):
    ...
    continue
```

This guards against missing files but not against zero-byte files, truncated files, or files that pass `os.path.exists()` but fail to load. The `Results.load()` call that follows will catch these, but only inside the `try/except Exception` block (see M2), which masks the root cause.

The `verify_trajectories_public.py:check_format` function relies entirely on `Results.load()` raising an exception for any format error, with no schema pre-validation or file size sanity check.

**Fix:**

- Replace raw `os.path.exists()` with a helper that also checks `os.path.getsize(file_path) > 0` and logs a clear error if zero-byte.
- In `check_format`, catch and re-raise `pydantic.ValidationError` separately from generic `Exception` so callers can distinguish schema errors from IO errors.

---

### L1 — Non-empty check in `test_provider_standalone.py`

**File:** `src/tau2/voice/audio_native/nova/test_provider_standalone.py`
**Detector:** LLM `weak_test_assertions` (70%)

**Problem:**
Audio provider tests likely assert `len(result) > 0` or `result is not None` on audio output, which is trivially satisfiable by returning a single byte. Without checking audio duration, sample rate, or content signature, a mock provider could pass.

**Fix** (pending reading the file):

- Assert on minimum audio duration or byte count with a documented lower bound.
- If the provider returns structured data, assert on required fields.

---

### L2 — `is_successful` tolerance not documented

**File:** `src/tau2/metrics/agent_metrics.py:12–16`
**Detector:** (inferred from formal `weak_test_assertions` 75%)

**Problem:**

```python
def is_successful(reward: float) -> bool:
    return (1 - 1e-6) <= reward <= (1 + 1e-6)
```

The `1e-6` tolerance is undocumented. It's unclear whether this is chosen to match floating-point rounding in the reward computation or is arbitrary. A different reward computation could produce `0.9999995` which fails despite being intended as a full reward.

**Fix:**
Add a docstring explaining why `1e-6` was chosen and reference the reward computation that produces values in `[0, 1]`. Consider making the tolerance a named constant:

```python
_REWARD_SUCCESS_TOLERANCE = 1e-6
```

---

### L3 — `display_metrics` uses `print` instead of logger

**File:** `src/tau2/metrics/agent_metrics.py:485–491`
**Detector:** (style/quality)

**Problem:**
`display_metrics` is a module-level function using bare `print()`. The rest of the module uses `loguru.logger`. This breaks log capture in tests and makes it impossible to filter or redirect output.

**Fix:**
Replace `print(...)` with `logger.info(...)` calls, or accept a `console: Console | None` argument matching the pattern used in `evaluate_trajectories.py`.

---

## False Positives (No Action Required)

| Finding                                               | Files                                                                                                                                      | Reason dismissed                                                                                                                                                                            |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `safety_concern` "installs circumvention tools" (×11) | `tau2/evaluator/*.py`, `experiments/hyperparam/run_eval.py`, `tau2/scripts/evaluate_trajectories.py`, `tau2/metrics/break_down_metrics.py` | The evaluator legitimately spawns subprocesses and manages tool environments as part of benchmark design. This is intentional infrastructure, not an attack surface.                        |
| `writable_reference_file` "agent runs as root"        | `test_green_agent.py`                                                                                                                      | Unit tests run in the user's dev environment, not as root. No privilege escalation possible from this test file. The "root" detection is a heuristic false positive on subprocess patterns. |
| `hardcoded_or_predictable_output` in test files       | `test_green_agent.py`, `test_launcher.py`, `test_white_agent.py`                                                                           | These are unit tests asserting known inputs → known outputs. Hardcoded expected values in tests are correct practice. They do not leak benchmark answers.                                   |
| `test_spec_mismatch` exact string matching            | `test_launcher.py`                                                                                                                         | Test infrastructure format matching is appropriately strict.                                                                                                                                |

---

## Implementation Order

1. **M3** (`db_verify_structure.py` null handling) — one-line fix, highest ROI
2. **M2** (`evaluate_trajectories.py` exception types) — improves debuggability immediately
3. **M4** (file integrity pre-check) — add zero-byte guard + `check_format` exception typing
4. **M1** (agent test assertions) — improve test quality in `test_green_agent.py`, `test_white_agent.py`
5. **L1** (audio provider test) — read file first, then strengthen assertion
6. **L2** (`is_successful` tolerance) — documentation + named constant
7. **L3** (`display_metrics` logging) — swap `print` → `logger.info`
