.PHONY: eval-generate eval-grade eval eval-gate

eval-generate:
	agents-cli eval generate --dataset tests/eval/datasets/basic-dataset.json --output artifacts/traces/

eval-grade:
	agents-cli eval grade --traces artifacts/traces/ --config tests/eval/eval_config.yaml --output artifacts/results/

eval: eval-generate eval-grade

eval-gate: eval
	uv run python tests/eval/check_threshold.py --results-dir artifacts/results --min-score 4.0
