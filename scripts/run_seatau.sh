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

Script-owned options:
  --experiment <name>        Run one experiment preset.
  --all-experiments          Run every preset in config/sea-tau/experiments.yaml `all_experiments`.
  --mixed-tools-config <n>   Force a specific mixed-tools partition config (overrides default).
  --dry-run                  Print the `tau2 run` invocations without executing.
  -h, --help                 Show this help.

Experiment presets (source of truth: config/sea-tau/experiments.yaml):
  mixed_tools    EXP #1: English conversation + mixed-language tool descriptions
                 (default config: 5lang_uniform_en-th-vi-id-zh).
  crosslingual   EXP #2: English assets + L2 user/agent prompting.
  translated     EXP #3: translated context + translated tools + L2 prompting.
  localized      EXP #4: human-localized assets (same components as translated).
  baseline       English-only, no language components.
  (aliases: trans_tool->mixed_tools, mixed_2lang, mixed_3lang, mixed_5lang)

Supported SEA-TAU domains:
  airline, retail, telecom

Experiment language matrix:
  preset       | user convo | agent convo | tools                       | context(db/tasks/policy)
  baseline     | English    | English     | English                     | English
  mixed_tools  | English    | English     | Mixed (English + selected L2s) | English
  crosslingual | L2         | L2          | English                     | English
  translated   | L2         | L2          | L2                          | L2
  localized    | L2         | L2          | L2                          | L2

Language behavior:
  - If --lang-id is passed in tau2 args, only that language is run.
  - Otherwise, non-baseline experiments fan out across every non-English
    language in config/languages.json.

Do NOT pass `--lang-components` directly — the script manages it per experiment.

Examples:
  scripts/run_seatau.sh --experiment crosslingual \
    --domain retail --lang-id vi --agent-llm gpt-4.1 --user-llm gpt-4.1 --num-tasks 5

  scripts/run_seatau.sh --all-experiments \
    --domain retail --lang-id vi --agent-llm gpt-4.1 --user-llm gpt-4.1 --num-tasks 5

  scripts/run_seatau.sh --all-experiments --dry-run \
    --domain retail --lang-id vi --agent-llm gpt-4.1 --user-llm gpt-4.1 --num-tasks 5
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
elif op == "asset_mode":
    name = args[0]
    print(cfg["experiments"][name].get("asset_mode", "original"))
elif op == "supported_domains":
    for item in cfg.get("supported_domains", []):
        print(item)
elif op == "is_supported_domain":
    name = args[0]
    print("1" if name in set(cfg.get("supported_domains", [])) else "0")
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
  local -a cmd=("uv" "run" "tau2" "run" "$@")
  printf '$'
  printf ' %q' "${cmd[@]}"
  printf '\n'
  if [[ "$DRY_RUN" -eq 0 ]]; then
    (
      cd "$REPO_ROOT"
      "${cmd[@]}"
    )
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
    if code != "en":
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

remove_flag_with_value() {
  local needle="$1"
  shift

  FILTERED_ARGS=()
  local -a input_args=("$@")
  local i=0
  while [[ $i -lt ${#input_args[@]} ]]; do
    if [[ "${input_args[$i]}" == "$needle" ]]; then
      ((i+=2))
      continue
    fi
    FILTERED_ARGS+=("${input_args[$i]}")
    i=$((i + 1))
  done
}

print_experiment_settings() {
  local experiment="$1"
  local target_lang="$2"
  local run_lang_id="$3"
  local run_components="$4"
  local mixed_cfg="${5:-}"
  local asset_mode="${6:-original}"

  local user_conv="English"
  local agent_conv="English"
  local greeting_lang="English"
  local tool_lang="English"
  local context_lang="English"

  if [[ "$experiment" == "mixed_tools" || "$experiment" == "mixed_tools_2lang" || "$experiment" == "mixed_tools_3lang" || "$experiment" == "mixed_tools_5lang" ]]; then
    tool_lang="Mixed (${target_lang}+en)"
  else
    if [[ " $run_components " == *" user_system "* ]]; then
      user_conv="$target_lang"
    fi
    if [[ " $run_components " == *" agent_system "* ]]; then
      agent_conv="$target_lang"
    fi
    if [[ " $run_components " == *" greeting "* ]]; then
      greeting_lang="$target_lang"
    fi
    if [[ " $run_components " == *" tools "* ]]; then
      tool_lang="$target_lang"
    fi
    if [[ " $run_components " == *" policy "* || " $run_components " == *" db "* || " $run_components " == *" tasks "* ]]; then
      context_lang="$target_lang"
    fi
  fi

  echo "[SEA-TAU] experiment=${experiment} target_lang=${target_lang} run_lang_id=${run_lang_id} asset_mode=${asset_mode} lang_components=\"${run_components}\" mixed_tools_config=${mixed_cfg:-none}"
  echo "[SEA-TAU] user_conversation=${user_conv} agent_conversation=${agent_conv} greeting=${greeting_lang} tools=${tool_lang} context(db/tasks/policy)=${context_lang}"
}

log_experiment_settings() {
  local experiment="$1"
  local target_lang="$2"
  local run_lang_id="$3"
  local run_components="$4"
  local mixed_cfg="${5:-}"
  local asset_mode="${6:-original}"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    print_experiment_settings "$experiment" "$target_lang" "$run_lang_id" "$run_components" "$mixed_cfg" "$asset_mode"
    return 0
  fi

  local seatau_log_level="INFO"
  local explicit_log_level
  explicit_log_level="$(get_flag_value --log-level)"
  if [[ -n "$explicit_log_level" ]]; then
    seatau_log_level="$explicit_log_level"
  fi

  local -a cmd=(
    "uv" "run" "python" "-m" "tau2.scripts.seatau_logging"
    "--experiment" "$experiment"
    "--target-lang" "$target_lang"
    "--run-lang-id" "$run_lang_id"
    "--asset-mode" "$asset_mode"
    "--log-level" "$seatau_log_level"
  )

  if [[ -n "$mixed_cfg" ]]; then
    cmd+=("--mixed-tools-config" "$mixed_cfg")
  fi

  if [[ -n "$run_components" ]]; then
    local -a components=()
    read -r -a components <<< "$run_components"
    cmd+=("--lang-components" "${components[@]}")
  fi

  (
    cd "$REPO_ROOT"
    "${cmd[@]}"
  )
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

EXPLICIT_DOMAIN=""
if has_flag "--domain"; then
  EXPLICIT_DOMAIN="$(get_flag_value --domain)"
  if [[ -z "$EXPLICIT_DOMAIN" ]]; then
    echo "--domain was provided without a value." >&2
    exit 2
  fi
  if [[ "$EXPLICIT_DOMAIN" == "mock" ]]; then
    echo "[SKIP] SEA-TAU experiments do not run on domain 'mock'."
    exit 0
  fi
  if [[ "$(yaml_eval is_supported_domain "$EXPLICIT_DOMAIN")" != "1" ]]; then
    mapfile -t SUPPORTED_DOMAINS < <(yaml_eval supported_domains)
    echo "[SKIP] SEA-TAU experiments only run on supported domains: ${SUPPORTED_DOMAINS[*]}."
    exit 0
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
  IS_MIXED_TOOLS="$(yaml_eval is_mixed_tools "$exp")"
  ASSET_MODE="$(yaml_eval asset_mode "$exp")"
  if [[ "$IS_MIXED_TOOLS" != "1" && -z "$LANG_COMPONENTS" ]]; then
    echo "Experiment '${exp}' has no lang_components in ${EXPERIMENTS_CONFIG_PATH}." >&2
    exit 2
  fi

  for lang in "${LANGS[@]}"; do
    local_args=("${TAU_ARGS[@]}")

    if [[ "$IS_MIXED_TOOLS" == "1" ]]; then
      if CONFIG_NAME="$(resolve_mixed_config "$exp" "$lang")"; then
        # EXP #1 keeps prompting/greeting in English while varying only tool docs.
        remove_flag_with_value "--lang-id" "${local_args[@]}"
        local_args=("${FILTERED_ARGS[@]}")
        local_args+=("--lang-id" "en")
        local_args+=("--seatau-experiment" "$exp" "--seatau-target-lang" "$lang" "--seatau-asset-mode" "$ASSET_MODE")
        log_experiment_settings "$exp" "$lang" "en" "mixed_tools" "$CONFIG_NAME" "$ASSET_MODE"
        run_tau2 "${local_args[@]}" --lang-components mixed_tools --mixed-tools-config "$CONFIG_NAME"
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
      if [[ -n "$MIXED_CONFIG" ]]; then
        echo "[WARN] --mixed-tools-config is ignored for experiment '${exp}' (requires mixed_tools lang component)."
      fi
      if [[ -z "$EXPLICIT_LANG_ID" ]]; then
        local_args+=("--lang-id" "$lang")
      fi
      run_lang_id="$lang"
      if [[ -n "$EXPLICIT_LANG_ID" ]]; then
        run_lang_id="$EXPLICIT_LANG_ID"
      fi
      local_args+=("--seatau-experiment" "$exp" "--seatau-target-lang" "$lang" "--seatau-asset-mode" "$ASSET_MODE")
      log_experiment_settings "$exp" "$lang" "$run_lang_id" "$LANG_COMPONENTS" "" "$ASSET_MODE"
      run_tau2 "${local_args[@]}" --lang-components $LANG_COMPONENTS
    fi
  done
done
