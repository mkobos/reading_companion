import json

import pytest

from tests.eval.check_threshold import ThresholdNotMetError, check_latest_results


def _write_results(tmp_path, filename, scores):
    results = {
        "eval_case_results": [
            {
                "response_candidate_results": [
                    {
                        "metric_results": {
                            "custom_response_quality": {"score": score},
                        }
                    }
                ]
            }
            for score in scores
        ]
    }
    (tmp_path / filename).write_text(json.dumps(results))


def test_passes_when_mean_score_meets_the_threshold(tmp_path):
    _write_results(tmp_path, "results_1.json", [4.0, 5.0, 4.0])

    mean = check_latest_results(tmp_path, min_score=4.0)

    assert mean == pytest.approx(4.333333, rel=1e-4)


def test_raises_when_mean_score_is_below_the_threshold(tmp_path):
    _write_results(tmp_path, "results_1.json", [1.0, 2.0])

    with pytest.raises(ThresholdNotMetError):
        check_latest_results(tmp_path, min_score=4.0)


def test_uses_the_most_recently_modified_results_file(tmp_path):
    _write_results(tmp_path, "results_older.json", [1.0])
    _write_results(tmp_path, "results_newer.json", [5.0])

    mean = check_latest_results(tmp_path, min_score=4.0)

    assert mean == 5.0


def test_raises_when_no_results_files_exist(tmp_path):
    with pytest.raises(FileNotFoundError):
        check_latest_results(tmp_path, min_score=4.0)
