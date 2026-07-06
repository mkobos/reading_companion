.PHONY: eval-generate eval-grade eval

eval-generate:
	agents-cli eval generate --dataset tests/eval/datasets/basic-dataset.json --output artifacts/traces/

eval-grade:
	agents-cli eval grade --traces artifacts/traces/ --config tests/eval/eval_config.yaml --output artifacts/results/

eval: eval-generate eval-grade
