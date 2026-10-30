import pytest

from ghosttab_api.meta import ModelFailure, actual_cost, reservation


def test_wonder_costs_are_not_accounted_at_spark_rates():
    usage = {
        "prompt_tokens": 1000,
        "completion_tokens": 1000,
        "prompt_tokens_details": {"cached_tokens": 200},
    }
    assert actual_cost(usage, "muse-wonder-1.0") == 23240
    assert actual_cost(usage, "muse-spark-1.3") == 5280
    assert reservation({"model": "muse-wonder-1.0"}) > reservation({"model": "muse-spark-1.3"})


def test_unknown_models_cannot_use_an_incorrect_budget_rate():
    with pytest.raises(ModelFailure, match="unsupported_model"):
        reservation({"model": "unknown"})
    assert actual_cost({}, "muse-wonder-1.0") is None
