#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LANG_REGISTRY_PATH="${REPO_ROOT}/config/languages.json"
MIXED_CONFIG_DIR="${REPO_ROOT}/config/sea-tau/mixed_tools"
EXPERIMENTS_CONFIG_PATH="${REPO_ROOT}/config/sea-tau/experiments.yaml"

usage() {
  cat <<'EOF'
Run SEA-TAU experiment presets on top of `tau2 run`.

Usage:
  scripts/run_seatau.sh --experiment <name> [tau2 run args...]
  scripts/run_seatau.sh --all-experiments [tau2 run args...]

Experiment mapping source of truth:
  config/sea-tau/experiments.yaml

Language behavior:
  - If --lang-id is passed in tau2 args, only that language is run.
  - Otherwise, non-baseline experiments run all languages in config/languages.json.

Mixed-tools config behavior:
  - Use --mixed-tools-config <name> to force a config.
  - Otherwise defaults are read from config/sea-tau/experiments.yaml.
EOF
}

yaml_eval() {
  python - "$EXPERIMENTS_CONFIG_PATH" "$@" <<'PY'
import json
import sys
from pathlib import Path

import yaml

config_path = Path(sys.argv[1])
op = sys.argv[2]
args = sys.argv[3:]
cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))

if op == "all_experiments":
    for item in cfg.get("all_experiments", []):
        print(item)
elif op == "resolve_alias":
    raw = args[0]
    aliases = cfg.get("aliases", {})
    print(aliases.get(raw, raw))
elif op == "known_experiment":
    name = args[0]
    print("1" if name in cfg.get("experiments", {}) else "0")
elif op == "lang_components":
    name = args[0]
    comps = cfg["experiments"][name].get("lang_components", [])
    print(" ".join(comps))
elif op == "is_mixed_tools":
    name = args[0]
    print("1" if cfg["experiments"][name].get("mixed_tools", False) else "0")
elif op == "default_mixed_config":
    name = args[0]
    value = cfg["experiments"][name].get("default_mixed_config")
    print("" if value is None else value)
else:
    raise SystemExit(f"Unknown operation: {op}")
PY
}

if [[ ! -f "$EXPERIMENTS_CONFIG_PATH" ]]; then
  echo "Missing experiments config: ${EXPERIMENTS_CONFIG_PATH}" >&2
  exit 2
fi

EXPERIMENT=""
ALL_EXPERIMENTS=0
ALL_LANGUAGES=0
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
    --all-languages)
      ALL_LANGUAGES=1
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
  mapfile -t EXPERIMENTS < <(yaml_eval all_experiments)
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

get_flag_value() {
  local needle="$1"
  local i=0
  while [[ $i -lt ${#TAU_ARGS[@]} ]]; do
    if [[ "${TAU_ARGS[$i]}" == "$needle" ]]; then
      echo "${TAU_ARGS[$((i+1))]:-}"
      return 0
    fi
    ((i++))
  done
  echo ""
}

run_tau2() {
  local -a cmd=("tau2" "run" "$@")
  printf '$'
  printf ' %q' "${cmd[@]}"
  printf '\n'
  if [[ "$DRY_RUN" -eq 0 ]]; then
    "${cmd[@]}"
  fi
}

load_all_languages() {
  python - "$LANG_REGISTRY_PATH" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
for code in sorted(data.keys()):
    print(code)
PY
}

mixed_config_exists() {
  local name="$1"
  [[ -f "${MIXED_CONFIG_DIR}/${name}.json" ]]
}

resolve_mixed_config() {
  local experiment="$1"
  local lang="$2"

  if [[ -n "$MIXED_CONFIG" ]]; then
    echo "$MIXED_CONFIG"
    return 0
  fi

  local from_experiment
  from_experiment="$(yaml_eval default_mixed_config "$experiment")"
  if [[ -n "$from_experiment" ]]; then
    echo "$from_experiment"
    return 0
  fi

  local two_lang="2lang_uniform_en-${lang}"
  if mixed_config_exists "$two_lang"; then
    echo "$two_lang"
    return 0
  fi

  if [[ "$lang" == "th" || "$lang" == "vi" || "$lang" == "id" || "$lang" == "zh" ]]; then
    local five_lang="5lang_uniform_en-th-vi-id-zh"
    if mixed_config_exists "$five_lang"; then
      echo "$five_lang"
      return 0
    fi
  fi

  return 1
}

if has_flag "--lang-components"; then
  echo "Do not pass --lang-components directly; this script manages it per experiment." >&2
  exit 2
fi

if has_flag "--mixed-tools-config" && [[ -n "$MIXED_CONFIG" ]]; then
  echo "Pass --mixed-tools-config only once (script option)." >&2
  exit 2
fi

EXPLICIT_LANG_ID=""
if has_flag "--lang-id"; then
  EXPLICIT_LANG_ID="$(get_flag_value --lang-id)"
  if [[ -z "$EXPLICIT_LANG_ID" ]]; then
    echo "--lang-id was provided without a value." >&2
    exit 2
  fi
fi

if [[ -n "$EXPLICIT_LANG_ID" && "$ALL_LANGUAGES" -eq 1 ]]; then
  echo "Use either --lang-id or --all-languages, not both." >&2
  exit 2
fi

for raw_exp in "${EXPERIMENTS[@]}"; do
  exp="$(yaml_eval resolve_alias "$raw_exp")"
  if [[ "$(yaml_eval known_experiment "$exp")" != "1" ]]; then
    echo "Unknown experiment: ${raw_exp} (resolved to '${exp}')" >&2
    usage
    exit 2
  fi

  if [[ "$exp" == "baseline" ]]; then
    run_tau2 "${TAU_ARGS[@]}"
    continue
  fi

  if [[ -n "$EXPLICIT_LANG_ID" ]]; then
    LANGS=("$EXPLICIT_LANG_ID")
  else
    mapfile -t LANGS < <(load_all_languages)
  fi

  LANG_COMPONENTS="$(yaml_eval lang_components "$exp")"
  if [[ -z "$LANG_COMPONENTS" ]]; then
    echo "Experiment '${exp}' has no lang_components in ${EXPERIMENTS_CONFIG_PATH}." >&2
    exit 2
  fi

  for lang in "${LANGS[@]}"; do
    local_args=("${TAU_ARGS[@]}")
    if [[ -z "$EXPLICIT_LANG_ID" ]]; then
      local_args+=("--lang-id" "$lang")
    fi

    if [[ "$(yaml_eval is_mixed_tools "$exp")" == "1" ]]; then
      if CONFIG_NAME="$(resolve_mixed_config "$exp" "$lang")"; then
        run_tau2 "${local_args[@]}" --lang-components $LANG_COMPONENTS --mixed-tools-config "$CONFIG_NAME"
      else
        if [[ -n "$MIXED_CONFIG" ]]; then
          echo "Mixed-tools config '${MIXED_CONFIG}' not found in ${MIXED_CONFIG_DIR}." >&2
          exit 2
        fi
        if [[ -n "$EXPLICIT_LANG_ID" ]]; then
          echo "No default mixed-tools config available for lang '${lang}'. Use --mixed-tools-config." >&2
          exit 2
        fi
        echo "[SKIP] mixed_tools for lang '${lang}': no default config available. Pass --mixed-tools-config to force a config."
      fi
    else
      run_tau2 "${local_args[@]}" --lang-components $LANG_COMPONENTS
    fi
  done
done
