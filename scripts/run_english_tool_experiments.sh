#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SEATAU_SH="${SCRIPT_DIR}/run_seatau.sh"

usage() {
  cat <<'EOF'
Run English-conversation SEA-TAU tool-language experiments in sequence.
Only translated tools.json docstrings are used; all other assets and tool
values remain English/canonical.

This wrapper runs:
  1. english_tools with explicit lang-id: th, vi, id, zh
  2. english_mixed_bi
  3. english_mixed_tri
  4. english_mixed_fourth
  5. english_mixed_multi

Usage:
  scripts/run_english_tool_experiments.sh [wrapper args...] [tau2 run args...]

Wrapper options:
  --save-to-prefix <prefix>  Base save directory prefix to use for each sub-run.
                             Each experiment appends its own label.
  --api-base <url>           OpenAI-compatible API base URL to pass to both
                             agent and user LiteLLM calls.
  --api-key <key>            API key to use with --api-base. Defaults to
                             $LITELLM_API_KEY, $OPENAI_API_KEY, or sk-local.
  -h, --help                 Show this help.

Examples:
  scripts/run_english_tool_experiments.sh \
    --domain retail \
    --agent-llm vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas \
    --user-llm vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas \
    --num-trials 1 \
    --num-tasks 3 \
    --max-concurrency 8

  scripts/run_english_tool_experiments.sh --dry-run \
    --domain retail \
    --agent-llm gpt-4.1 \
    --user-llm gpt-4.1 \
    --num-tasks 1

  scripts/run_english_tool_experiments.sh \
    --api-base http://localhost:8000/v1 \
    --save-to-prefix retail_qwen_run \
    --auto-resume \
    --domain retail \
    --agent-llm openai//project/lt200394-thllmV/jab/seacrowd/models/Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 \
    --user-llm openai//project/lt200394-thllmV/jab/seacrowd/models/Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 \
    --num-trials 3



Notes:
  - All arguments are forwarded to scripts/run_seatau.sh.
  - Vertex/Qwen stability defaults are applied to every sub-run before
    forwarded args, so passing the same flags to this wrapper overrides them.
  - --api-base sets default --agent-llm-args and --user-llm-args. Passing those
    flags manually still overrides the wrapper defaults.
  - With --api-base, --agent-llm or --user-llm values beginning with "/" are
    normalized to LiteLLM's openai//... provider form.
  - Do not pass --experiment, --experiment-name, or --save-to; this wrapper
    manages them.
  - Re-running the same command reuses stable per-experiment save paths, so
    adding --auto-resume will continue incomplete runs cleanly.
EOF
}

if [[ ! -x "${RUN_SEATAU_SH}" ]]; then
  echo "Missing executable helper: ${RUN_SEATAU_SH}" >&2
  exit 2
fi

sanitize_component() {
  local value="$1"
  value="${value##*/}"
  value="${value//[^A-Za-z0-9._-]/_}"
  printf '%s\n' "$value"
}

COMMON_ARGS=()
SAVE_TO_PREFIX=""
API_BASE=""
API_KEY="${LITELLM_API_KEY:-${OPENAI_API_KEY:-}}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --save-to-prefix)
      SAVE_TO_PREFIX="${2:-}"
      if [[ -z "$SAVE_TO_PREFIX" ]]; then
        echo "--save-to-prefix requires a value." >&2
        exit 2
      fi
      shift 2
      ;;
    --api-base)
      API_BASE="${2:-}"
      if [[ -z "$API_BASE" ]]; then
        echo "--api-base requires a value." >&2
        exit 2
      fi
      shift 2
      ;;
    --api-key)
      API_KEY="${2:-}"
      if [[ -z "$API_KEY" ]]; then
        echo "--api-key requires a value." >&2
        exit 2
      fi
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --experiment)
      echo "Do not pass --experiment; this wrapper manages the sequence." >&2
      exit 2
      ;;
    --experiment-name)
      echo "Do not pass --experiment-name; this wrapper manages the sequence." >&2
      exit 2
      ;;
    --save-to)
      echo "Do not pass --save-to; use --save-to-prefix so each sub-run gets its own directory." >&2
      exit 2
      ;;
    *)
      COMMON_ARGS+=("$1")
      shift
      ;;
  esac
done

build_default_llm_args() {
  local api_base="$1"
  local api_key="$2"
  python - "$api_base" "$api_key" <<'PY'
import json
import sys

api_base = sys.argv[1]
api_key = sys.argv[2]
args = {"vertex_location": "us-south1", "num_retries": 6}
if api_base:
    args["api_base"] = api_base
    args["api_key"] = api_key or "sk-local"
print(json.dumps(args, separators=(",", ":")))
PY
}

normalize_api_base_model_paths() {
  if [[ -z "$API_BASE" ]]; then
    return 0
  fi

  local i=0
  while [[ $i -lt ${#COMMON_ARGS[@]} ]]; do
    case "${COMMON_ARGS[$i]}" in
      --agent-llm|--user-llm)
        local value="${COMMON_ARGS[$((i+1))]:-}"
        if [[ "$value" == /* ]]; then
          COMMON_ARGS[$((i+1))]="openai/${value}"
        fi
        i=$((i+2))
        ;;
      *)
        i=$((i+1))
        ;;
    esac
  done
}

normalize_api_base_model_paths

DEFAULT_LLM_ARGS="$(build_default_llm_args "$API_BASE" "$API_KEY")"
DEFAULT_TAU2_ARGS=(
  --max-concurrency 8
  --max-retries 10
  --retry-delay 30
  --agent-llm-args "$DEFAULT_LLM_ARGS"
  --user-llm-args "$DEFAULT_LLM_ARGS"
)

get_common_flag_value() {
  local needle="$1"
  local i=0
  while [[ $i -lt ${#COMMON_ARGS[@]} ]]; do
    if [[ "${COMMON_ARGS[$i]}" == "$needle" ]]; then
      echo "${COMMON_ARGS[$((i+1))]:-}"
      return 0
    fi
    ((i++))
  done
  echo ""
}

build_default_save_to_prefix() {
  local prefix="english_tool_experiments"
  local domain
  local agent_llm
  local user_llm

  domain="$(get_common_flag_value --domain)"
  agent_llm="$(get_common_flag_value --agent-llm)"
  user_llm="$(get_common_flag_value --user-llm)"

  if [[ -n "$domain" ]]; then
    prefix+="_$(sanitize_component "$domain")"
  fi
  if [[ -n "$agent_llm" ]]; then
    prefix+="_$(sanitize_component "$agent_llm")"
  fi
  if [[ -n "$user_llm" ]]; then
    prefix+="_$(sanitize_component "$user_llm")"
  fi

  printf '%s\n' "$prefix"
}

if [[ -z "$SAVE_TO_PREFIX" ]]; then
  SAVE_TO_PREFIX="$(build_default_save_to_prefix)"
fi

run_named() {
  local label="$1"
  shift
  echo
  echo "==> ${label}"
  "${RUN_SEATAU_SH}" "${DEFAULT_TAU2_ARGS[@]}" "$@" --experiment-name "${label}" --save-to "${SAVE_TO_PREFIX}_${label}"
}

# run_named "english_en_tools" \
#   --experiment english_tools \
#   --lang-id en \
#   "${COMMON_ARGS[@]}"

# run_named "english_th_tools" \
#   --experiment english_tools \
#   --lang-id th \
#   "${COMMON_ARGS[@]}"

# run_named "english_vi_tools" \
#   --experiment english_tools \
#   --lang-id vi \
#   "${COMMON_ARGS[@]}"

# run_named "english_id_tools" \
#   --experiment english_tools \
#   --lang-id id \
#   "${COMMON_ARGS[@]}"

# run_named "english_zh_tools" \
#   --experiment english_tools \
#   --lang-id zh \
#   "${COMMON_ARGS[@]}"

run_named "english_mixed_bi" \
  --experiment english_mixed_bi \
  "${COMMON_ARGS[@]}"

run_named "english_mixed_tri" \
  --experiment english_mixed_tri \
  "${COMMON_ARGS[@]}"

run_named "english_mixed_fourth" \
  --experiment english_mixed_fourth \
  "${COMMON_ARGS[@]}"

run_named "english_mixed_multi" \
  --experiment english_mixed_multi \
  "${COMMON_ARGS[@]}"
