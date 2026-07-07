"""CI gate for `agents-cli eval grade` output.

Reads the most recently produced results_*.json under a results directory,
computes the mean `custom_response_quality` score across every case, and
fails if it's below a minimum. Wired in via the Makefile's `eval-gate`
target, run from CI after `make eval`.
"""

import argparse
import json
from pathlib import Path


class ThresholdNotMetError(Exception):
    pass


def _scores(results: dict) -> list[float]:
    scores = []
    for case in results.get("eval_case_results", []):
        for candidate in case.get("response_candidate_results", []):
            metric = candidate.get("metric_results", {}).get("custom_response_quality")
            if metric is not None:
                scores.append(metric["score"])
    return scores


def check_latest_results(results_dir: Path, min_score: float) -> float:
    files = sorted(Path(results_dir).glob("results_*.json"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"No results_*.json files found under {results_dir}")
    latest = files[-1]

    results = json.loads(latest.read_text())
    scores = _scores(results)
    mean = sum(scores) / len(scores) if scores else 0.0

    print(f"Read {latest.name}: {len(scores)} case(s), scores={scores}, mean={mean:.3f}")
    if mean < min_score:
        raise ThresholdNotMetError(
            f"Mean eval score {mean:.3f} is below the required minimum {min_score}"
        )
    return mean


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=Path("artifacts/results"))
    parser.add_argument("--min-score", type=float, default=4.0)
    args = parser.parse_args()

    check_latest_results(args.results_dir, args.min_score)


if __name__ == "__main__":
    main()
