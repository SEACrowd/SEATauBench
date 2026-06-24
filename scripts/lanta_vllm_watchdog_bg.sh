#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

WATCHDOG_SCRIPT="${WATCHDOG_SCRIPT:-${SCRIPT_DIR}/lanta_vllm_watchdog.sh}"
LOG_FILE="${LOG_FILE:-${ROOT_DIR}/logs/lanta_vllm_watchdog.launcher.log}"
PID_FILE="${PID_FILE:-${ROOT_DIR}/logs/lanta_vllm_watchdog.pid}"

mkdir -p "$(dirname "${LOG_FILE}")" "$(dirname "${PID_FILE}")"

if [[ ! -x "${WATCHDOG_SCRIPT}" ]]; then
  printf 'watchdog script is not executable: %s\n' "${WATCHDOG_SCRIPT}" >&2
  exit 1
fi

if [[ -f "${PID_FILE}" ]]; then
  existing_pid="$(<"${PID_FILE}")"
  if [[ -n "${existing_pid}" ]] && kill -0 "${existing_pid}" 2>/dev/null; then
    printf 'watchdog already running with pid %s\n' "${existing_pid}"
    exit 0
  fi
fi

nohup bash "${WATCHDOG_SCRIPT}" >>"${LOG_FILE}" 2>&1 </dev/null &
watchdog_pid="$!"
printf '%s\n' "${watchdog_pid}" >"${PID_FILE}"

printf 'watchdog launched in background with pid %s\n' "${watchdog_pid}"
printf 'log: %s\n' "${LOG_FILE}"
