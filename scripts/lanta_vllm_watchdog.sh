#!/usr/bin/env bash
set -euo pipefail

REMOTE_USER="${REMOTE_USER:-ppayoung}"
REMOTE_HOST="${REMOTE_HOST:-lanta.nstda.or.th}"
REMOTE="${REMOTE_USER}@${REMOTE_HOST}"
WORKDIR="${WORKDIR:-/project/lt200394-thllmV/jab/seacrowd}"
LOCAL_PORT="${LOCAL_PORT:-8000}"
MODEL_PATH="${MODEL_PATH:-/project/lt200394-thllmV/jab/seacrowd/models/Qwen/Qwen3-235B-A22B-Instruct-2507-FP8}"
EXPECTED_MODEL_NAME="${EXPECTED_MODEL_NAME:-${MODEL_PATH##*/}}"
JOB_ID="${JOB_ID:-}"
LOG_FILE="${LOG_FILE:-logs/lanta_vllm_watchdog.log}"
STATE_FILE="${STATE_FILE:-logs/lanta_vllm_watchdog.state}"
HEALTHY_SLEEP_MIN="${HEALTHY_SLEEP_MIN:-900}"
HEALTHY_SLEEP_MAX="${HEALTHY_SLEEP_MAX:-1200}"
RECOVERY_SLEEP="${RECOVERY_SLEEP:-180}"

mkdir -p "$(dirname "${LOG_FILE}")" "$(dirname "${STATE_FILE}")"

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "${LOG_FILE}" >/dev/null
}

ssh_remote() {
  ssh -o BatchMode=yes -o ConnectTimeout=10 "${REMOTE}" "$@"
}

persist_job_id() {
  printf 'JOB_ID=%s\n' "${JOB_ID}" >"${STATE_FILE}"
}

load_job_id_from_state() {
  if [[ -z "${JOB_ID}" && -f "${STATE_FILE}" ]]; then
    JOB_ID="$(sed -n 's/^JOB_ID=//p' "${STATE_FILE}" | tail -n1)"
  fi
}

discover_job_id() {
  local latest_file latest_job job_state

  while IFS= read -r latest_file; do
    latest_job="$(printf '%s\n' "${latest_file}" | sed -n 's/.*vllm_connection_info_\([0-9][0-9]*\)\.txt/\1/p' | head -n1)"
    if [[ -z "${latest_job}" ]]; then
      continue
    fi

    job_state="$(ssh_remote "squeue -h -j ${latest_job} -o '%T %R %M'" 2>/dev/null || true)"
    if [[ -n "${job_state}" ]]; then
      JOB_ID="${latest_job}"
      persist_job_id
      return 0
    fi
  done < <(ssh_remote "cd '${WORKDIR}' && ls -1t log/vllm_connection_info_*.txt 2>/dev/null" 2>/dev/null || true)

  return 1
}

discover_queue_job_id() {
  local queue_line queue_job

  queue_line="$(
    ssh_remote "squeue -h -u ${REMOTE_USER} -o '%i %T %j' | awk '\$3 ~ /oracle-llm/ {print; exit}'" 2>/dev/null || true
  )"
  if [[ -z "${queue_line}" ]]; then
    queue_line="$(
      ssh_remote "squeue -h -u ${REMOTE_USER} -o '%i %T %j' | tail -n1" 2>/dev/null || true
    )"
  fi
  queue_job="$(printf '%s\n' "${queue_line}" | awk '{print $1}' | head -n1)"
  if [[ -z "${queue_job}" ]]; then
    return 1
  fi

  JOB_ID="${queue_job}"
  persist_job_id
  return 0
}

job_state() {
  ssh_remote "squeue -h -j ${JOB_ID} -o '%T %R %M'" 2>/dev/null || true
}

job_host() {
  ssh_remote "cd '${WORKDIR}' && sed -n 's/^Hardware Host:[[:space:]]*//p' log/vllm_connection_info_${JOB_ID}.txt | head -n1" \
    2>/dev/null || true
}

listener_pid() {
  lsof -tiTCP:"${LOCAL_PORT}" -sTCP:LISTEN 2>/dev/null | head -n1 || true
}

health_ok() {
  curl -fsS --max-time 5 "http://127.0.0.1:${LOCAL_PORT}/v1/models" >/dev/null 2>&1
}

model_id() {
  local payload model

  payload="$(
    curl -fsS --max-time 5 "http://127.0.0.1:${LOCAL_PORT}/v1/models" 2>/dev/null || true
  )"
  if [[ -z "${payload}" ]]; then
    return 1
  fi

  if command -v jq >/dev/null 2>&1; then
    model="$(
      printf '%s\n' "${payload}" | jq -r '.data[0].id // empty' 2>/dev/null | head -n1
    )"
  else
    model="$(
      printf '%s\n' "${payload}" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p' | head -n1
    )"
  fi

  [[ -n "${model}" ]] || return 1
  printf '%s\n' "${model}"
}

sleep_for_next_poll() {
  local min_seconds="${1:-${HEALTHY_SLEEP_MIN}}"
  local max_seconds="${2:-${HEALTHY_SLEEP_MAX}}"
  local spread delay

  if (( max_seconds < min_seconds )); then
    max_seconds="${min_seconds}"
  fi

  spread=$((max_seconds - min_seconds + 1))
  delay=$((min_seconds + (RANDOM % spread)))
  log "next health poll in ${delay}s"
  sleep "${delay}"
}

kill_listener() {
  local pid="${1:-}"
  if [[ -n "${pid}" ]]; then
    kill "${pid}" 2>/dev/null || true
    wait "${pid}" 2>/dev/null || true
  fi
}

submit_job() {
  local out new_id

  out="$(
    ssh_remote "cd '${WORKDIR}' && sbatch start_oracle_llm_lanta_multi2.sh" 2>&1
  )" || {
    log "sbatch failed: ${out}"
    return 1
  }

  new_id="$(printf '%s\n' "${out}" | sed -n 's/.*Submitted batch job \([0-9][0-9]*\).*/\1/p' | tail -n1)"
  if [[ -z "${new_id}" ]]; then
    log "could not parse job id from: ${out}"
    return 1
  fi

  JOB_ID="${new_id}"
  persist_job_id
  log "submitted replacement job ${JOB_ID}"
}

open_tunnel() {
  local host="$1"

  ssh -fN \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -L "${LOCAL_PORT}:${host}:8000" \
    "${REMOTE}" \
    2>>"${LOG_FILE}"
}

load_job_id_from_state
if [[ -z "${JOB_ID}" ]]; then
  discover_job_id || true
fi
if [[ -z "${JOB_ID}" ]]; then
  discover_queue_job_id || true
fi
if [[ -z "${JOB_ID}" ]]; then
  submit_job
fi

log "watchdog started for job ${JOB_ID} on localhost:${LOCAL_PORT} (polling every ${HEALTHY_SLEEP_MIN}-${HEALTHY_SLEEP_MAX}s)"

while true; do
  state="$(job_state)"
  state_name="${state%% *}"
  pid="$(listener_pid)"
  model=""

  if [[ -n "${pid}" ]]; then
    model="$(model_id || true)"
  fi

  if [[ -z "${state}" ]]; then
    if [[ -n "${pid}" ]]; then
      kill_listener "${pid}"
      log "listener ${pid} present while job ${JOB_ID} is missing; closing stale tunnel"
    fi
    log "job ${JOB_ID} not found; trying to rediscover or resubmit"
    if discover_job_id; then
      log "rediscovered running job ${JOB_ID}"
      sleep "${RECOVERY_SLEEP}"
      continue
    fi
    if discover_queue_job_id; then
      log "rediscovered queued job ${JOB_ID}"
      sleep "${RECOVERY_SLEEP}"
      continue
    fi
    submit_job || sleep "${RECOVERY_SLEEP}"
    sleep "${RECOVERY_SLEEP}"
    continue
  fi

  case "${state_name}" in
    RUNNING|COMPLETING)
      host="$(job_host)"
      if [[ -n "${pid}" ]] && health_ok && [[ -n "${model}" ]]; then
        if [[ "${model}" == "${EXPECTED_MODEL_NAME}" || "${model}" == "${MODEL_PATH}" || "${model}" == *"${EXPECTED_MODEL_NAME}"* ]]; then
          log "healthy: job ${JOB_ID} state=${state_name}, port ${LOCAL_PORT}, model=${model}"
        else
          log "healthy: job ${JOB_ID} state=${state_name}, port ${LOCAL_PORT}, model endpoint returned ${model} (expected ${EXPECTED_MODEL_NAME})"
        fi
        sleep_for_next_poll
        continue
      fi

      if [[ -n "${pid}" ]]; then
        kill_listener "${pid}"
        log "listener ${pid} failed health/model check; reopening"
      fi

      if [[ -z "${host}" ]]; then
        log "job ${JOB_ID} is running, but connection info is not ready"
        sleep "${RECOVERY_SLEEP}"
        continue
      fi

      if open_tunnel "${host}"; then
        log "opened tunnel to ${host} for ${MODEL_PATH}"
      else
        log "failed to open tunnel to ${host}; will retry on next poll"
      fi
      sleep "${RECOVERY_SLEEP}"
      ;;
    PENDING)
      if [[ -n "${pid}" ]]; then
        kill_listener "${pid}"
        log "listener ${pid} present while job ${JOB_ID} is pending; closing stale tunnel"
      fi
      log "job ${JOB_ID} is pending"
      sleep "${RECOVERY_SLEEP}"
      ;;
    *)
      if [[ -n "${pid}" ]]; then
        kill_listener "${pid}"
        log "listener ${pid} present while job ${JOB_ID} state is ${state_name}; closing stale tunnel"
      fi
      log "job ${JOB_ID} state is ${state_name}; waiting"
      sleep "${RECOVERY_SLEEP}"
      ;;
  esac
done
