#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Run SITAW experiment presets on top of `tau2 run`.

Usage:
  scripts/run_sitaw_experiments.sh --experiment <name> [tau2 run args...]
  scripts/run_sitaw_experiments.sh --all-experiments [tau2 run args...]

Experiments:
  trans_tool   -> user_system agent_system greeting tools
  crosslingual -> user_system agent_system greeting
  translated   -> user_system agent_system greeting tools policy db tasks
  localized    -> user_system agent_system greeting tools policy db tasks
  baseline     -> no --lang-components added (English baseline)

  # Mixed-language tools (SITAW Experiment 1)
  mixed_2lang  -> user_system agent_system greeting mixed_tools (2-lang: en + target)
  mixed_3lang  -> user_system agent_system greeting mixed_tools (3-lang: en-th-vi)
  mixed_5lang  -> user_system agent_system greeting mixed_tools (5-lang: en-th-vi-id-zh)

  Use --mixed-tools-config to override the default config for mixed_* experiments.

Notes:
  - For non-baseline experiments, pass --lang-id in tau2 args.
  - All other options are passed through directly to `tau2 run`.
EOF
}

EXPERIMENT=""
ALL_EXPERIMENTS=0
DRY_RUN=0
MIXED_CONFIG=""
TAU_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --experiment)
      EXPERIMENT="${2:-}"
      shift 2
      ;;
    --all-experiments)
      ALL_EXPERIMENTS=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --mixed-tools-config)
      MIXED_CONFIG="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      TAU_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ "$ALL_EXPERIMENTS" -eq 1 && -n "$EXPERIMENT" ]]; then
  echo "Use either --experiment or --all-experiments, not both." >&2
  exit 2
fi

if [[ "$ALL_EXPERIMENTS" -eq 1 ]]; then
  EXPERIMENTS=(trans_tool crosslingual translated localized)
elif [[ -n "$EXPERIMENT" ]]; then
  EXPERIMENTS=("$EXPERIMENT")
else
  echo "Missing --experiment or --all-experiments." >&2
  usage
  exit 2
fi

has_flag() {
  local needle="$1"
  local arg
  for arg in "${TAU_ARGS[@]}"; do
    if [[ "$arg" == "$needle" ]]; then
      return 0
    fi
  done
  return 1
}

# Get the value of --lang-id from TAU_ARGS
get_lang_id() {
  local i=0
  while [[ $i -lt ${#TAU_ARGS[@]} ]]; do
    if [[ "${TAU_ARGS[$i]}" == "--lang-id" ]]; then
      echo "${TAU_ARGS[$((i+1))]:-}"
      return 0
    fi
    ((i++))
  done
  echo ""
}

run_tau2() {
  local -a cmd=("tau2" "run" "${TAU_ARGS[@]}" "$@")
  printf '$'
  printf ' %q' "${cmd[@]}"
  printf '\n'
  if [[ "$DRY_RUN" -eq 0 ]]; then
    "${cmd[@]}"
  fi
}

for exp in "${EXPERIMENTS[@]}"; do
  case "$exp" in
    trans_tool)
      if ! has_flag "--lang-id"; then
        echo "--lang-id is required for experiment '${exp}'." >&2
        exit 2
      fi
      run_tau2 --lang-components user_system agent_system greeting tools
      ;;
    crosslingual)
      if ! has_flag "--lang-id"; then
        echo "--lang-id is required for experiment '${exp}'." >&2
        exit 2
      fi
      run_tau2 --lang-components user_system agent_system greeting
      ;;
    translated|localized)
      if ! has_flag "--lang-id"; then
        echo "--lang-id is required for experiment '${exp}'." >&2
        exit 2
      fi
      run_tau2 --lang-components user_system agent_system greeting tools policy db tasks
      ;;
    baseline)
      run_tau2
      ;;
    mixed_2lang)
      if ! has_flag "--lang-id"; then
        echo "--lang-id is required for experiment '${exp}'." >&2
        exit 2
      fi
      LANG_ID=$(get_lang_id)
      CONFIG="${MIXED_CONFIG:-2lang_uniform_en-${LANG_ID}}"
      run_tau2 --lang-components user_system agent_system greeting mixed_tools --mixed-tools-config "$CONFIG"
      ;;
    mixed_3lang)
      if ! has_flag "--lang-id"; then
        echo "--lang-id is required for experiment '${exp}'." >&2
        exit 2
      fi
      CONFIG="${MIXED_CONFIG:-3lang_uniform_en-th-vi}"
      run_tau2 --lang-components user_system agent_system greeting mixed_tools --mixed-tools-config "$CONFIG"
      ;;
    mixed_5lang)
      if ! has_flag "--lang-id"; then
        echo "--lang-id is required for experiment '${exp}'." >&2
        exit 2
      fi
      CONFIG="${MIXED_CONFIG:-5lang_uniform_en-th-vi-id-zh}"
      run_tau2 --lang-components user_system agent_system greeting mixed_tools --mixed-tools-config "$CONFIG"
      ;;
    *)
      echo "Unknown experiment: ${exp}" >&2
      usage
      exit 2
      ;;
  esac
done
