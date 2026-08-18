.PHONY: assert-default-llm-backend eval-generate eval-grade eval eval-gate

# LLM_BACKEND=ollama|fake (app/model_selection.py) swaps in a local or
# canned model whose quality/tool-calling differs from Gemini — eval scores
# from either would say nothing about the deployed agent, so eval refuses
# to run under anything but the default vertex backend.
assert-default-llm-backend:
	@if [ -n "$$LLM_BACKEND" ] && [ "$$LLM_BACKEND" != "vertex" ]; then \
		echo "eval requires the default Gemini/Vertex LLM_BACKEND; got LLM_BACKEND=$$LLM_BACKEND" >&2; \
		exit 1; \
	fi

eval-generate: assert-default-llm-backend
	agents-cli eval generate --dataset tests/eval/datasets/basic-dataset.json --output artifacts/traces/

eval-grade:
	agents-cli eval grade --traces artifacts/traces/ --config tests/eval/eval_config.yaml --output artifacts/results/

eval: eval-generate eval-grade

eval-gate: eval
	uv run python tests/eval/check_threshold.py --results-dir artifacts/results --min-score 4.0
