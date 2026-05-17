#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_ENGLISH_TOOL_EXPERIMENTS_SH="${SCRIPT_DIR}/run_english_tool_experiments.sh"

if [[ ! -x "${RUN_ENGLISH_TOOL_EXPERIMENTS_SH}" ]]; then
  echo "Missing executable helper: ${RUN_ENGLISH_TOOL_EXPERIMENTS_SH}" >&2
  exit 2
fi

DOMAINS=(telecom retail airline)
AGENT_LLMS=(
  "vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas"
  "openai/gpt-5-mini"
)
USER_LLM="vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas"

COMMON_ARGS=(
  --user-llm "${USER_LLM}"
  --num-trials 3
  --max-concurrency 8
  --auto-resume
)

for agent_llm in "${AGENT_LLMS[@]}"; do
  for domain in "${DOMAINS[@]}"; do
    echo
    echo "==> Running long English-tool experiment batch for agent: ${agent_llm}, domain: ${domain}"
    "${RUN_ENGLISH_TOOL_EXPERIMENTS_SH}" \
      --agent-llm "${agent_llm}" \
      --domain "${domain}" \
      "${COMMON_ARGS[@]}" \
      "$@"
  done
done
