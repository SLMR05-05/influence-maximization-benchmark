import json
import random

from im_research.algorithms.evolutionary.ga import BaselineGA
from im_research.core.solution import Solution
from im_research.experiments.colab_benchmark import run_benchmark


def test_baseline_ga_uses_one_point_crossover_with_repair():
    algorithm = BaselineGA()
    child_a, child_b = algorithm._crossover(
        Solution([0, 1, 2, 3]),
        Solution([2, 3, 4, 5]),
        k=4,
        n=8,
        rng=random.Random(7),
    )

    assert child_a.is_valid(expected_k=4, max_node_id=8)
    assert child_b.is_valid(expected_k=4, max_node_id=8)
    assert algorithm.record_history is True


def test_colab_benchmark_writes_versioned_json_schema(tmp_path):
    result = run_benchmark(
        dataset_name="Karate Club",
        probability_model="WC",
        k=2,
        mc_runs=2,
        validation_mc_runs=3,
        independent_runs=1,
        algorithms=["CELF", "GA", "IGA"],
        population_size=4,
        generations=1,
        elite_size=1,
        random_seed=5,
        output_dir=tmp_path / "experiment",
        record_population_history=False,
        record_mc_details=True,
    )

    assert result["schema_version"] == "1.0.0"
    assert set(result["summary"]) == {"CELF", "GA", "IGA"}
    experiment_path = tmp_path / "experiment" / "experiment.json"
    payload = json.loads(experiment_path.read_text(encoding="utf-8"))
    assert payload["runs"][0]["algorithms"]["IGA"]["fitness_type"] == "monte_carlo"
    assert payload["runs"][0]["algorithms"]["CELF"]["validation_mc_details"]["spreads"]
