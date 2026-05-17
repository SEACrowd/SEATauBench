
```bash
conda activate exp-harry

Ok i want to run using gemini vertex ai (vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas


scripts/run_seatau.sh \
--experiment mixed_tools \
--domain retail \
--agent-llm vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas \
--user-llm vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas  \
--num-trials 1 \
--num-tasks 3 \
--max-concurrency 8

scripts/run_seatau.sh \
--experiment english_tools \
--domain retail \
--agent-llm ... --user-llm ... --num-trials 1 --num-tasks 3


I run this command and it save similar names in data/simulations it should save the langauge id in the simulation it should applied to multilingual tools also.


For the multilingaul tools. it 

scripts/run_english_tool_experiments.sh \
  --domain retail \
  --agent-llm vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas \
  --user-llm vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas \
  --num-trials 3 \
  --max-concurrency 8 \
  --auto-resume
  # --num-tasks 1 \

(exp-harry) mac_m2@fc4f4ac1-04:/data/workspace/mac_m2/tau3/multilingual-tau2-bench$ scripts/run_english_tool_experiments.sh   --domain telecom   --agent-llm vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas   --user-llm vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas   --num-trials 3   --max-concurrency 8 

tau2 summarize data/simulations_airline_full_v1 -o data/simulations_airline_full_v1/results_summary.csv
tau2 summarize data/simulations_telecom_full_v1 -o data/simulations_telecom_full_v1/results_summary.csv
tau2 summarize data/simulations_retail_full_v1 -o data/simulations_retail_full_v1/results_summary.csv
tau2 summarize data/simulations -o data/simulations/results_summary.csv

bash scripts/run_english_tool_experiments.sh \
  --api-base http://localhost:8000/v1 \
  --domain retail \
  --agent-llm /project/lt200394-thllmV/jab/seacrowd/models/Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 \
  --user-llm /project/lt200394-thllmV/jab/seacrowd/models/Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 \
  --num-trials 1 \
  --num-tasks 1

bash scripts/run_english_tool_experiments.sh \
  --domain retail \
  --agent-llm openai/gpt-5-mini \
  --user-llm vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas \
  --num-trials 1 \
  --num-tasks 1

```