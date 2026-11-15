"""Pure-Python diffusion simulation helpers for the Experiments page."""

from __future__ import annotations

import math
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    import networkx as nx
except ImportError:
    nx = None

from im_research.algorithms.evolutionary.ga import BaselineGA
from im_research.algorithms.evolutionary.cpp_ga import CppBaselineGA
from im_research.algorithms.evolutionary.iga import IGA
from im_research.algorithms.greedy.celf import CELF
from im_research.core.problem import IMProblem
from im_research.data.loader import build_cpp_graph, load_networkx_graph

try:
    from im_research import _im_core
except ImportError:
    _im_core = None

CPP_CORE_AVAILABLE = _im_core is not None

RAW_DIR = PROJECT_ROOT / "data" / "raw"

DATASET_NAMES = ["Karate Club", "Dolphins", "ego-Facebook", "NetHEPT", "Email-Enron"]

ALGO_OPTIONS = [
    ("celf", "Greedy / CELF"),
    ("ga", "Baseline GA"),
    ("iga", "Improved GA"),
]
ALGO_LABELS = dict(ALGO_OPTIONS)

DATASET_SPECS = {
    "Karate Club": {"full_n": 34, "full_m": 78, "source": "Zachary (1977)", "seed": 42},
    "Dolphins": {"full_n": 62, "full_m": 159, "source": "Lusseau (2003)", "seed": 43},
    "ego-Facebook": {"full_n": 4039, "full_m": 88234, "source": "SNAP [8]", "seed": 44},
    "NetHEPT": {"full_n": 15233, "full_m": 58891, "source": "arXiv / SNAP [15]", "seed": 45},
    "Email-Enron": {"full_n": 36692, "full_m": 183831, "source": "SNAP [8]", "seed": 46},
}


def _match_dataset(name: str) -> str:
    clean = name.lower().replace(" ", "").replace("-", "").replace("_", "")
    if "karate" in clean:
        return "Karate Club"
    if "dolphin" in clean:
        return "Dolphins"
    if "facebook" in clean:
        return "ego-Facebook"
    if "nethept" in clean or "hept" in clean:
        return "NetHEPT"
    if "enron" in clean:
        return "Email-Enron"
    return "Karate Club"


def _read_limited_edgelist(path: Path, max_nodes: int,
                           skip_header: bool = False,
                           skip_comments: bool = False):
    graph = nx.Graph()
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        first = True
        for line in handle:
            text = line.strip()
            if not text:
                continue
            if skip_comments and text.startswith("#"):
                continue
            parts = text.split()
            if len(parts) < 2:
                continue
            try:
                u, v = int(parts[0]), int(parts[1])
            except ValueError:
                continue
            if first and skip_header:
                first = False
                continue
            first = False
            if u == v:
                continue
            graph.add_edge(u, v)
            if graph.number_of_nodes() >= max_nodes:
                break
    return graph


def _largest_component(graph):
    if graph.number_of_nodes() == 0:
        return graph
    try:
        nodes = max(nx.connected_components(graph), key=len)
    except Exception:
        return graph
    if len(nodes) == graph.number_of_nodes():
        return graph
    return graph.subgraph(nodes).copy()


def _bfs_core(graph, max_nodes: int):
    start = max(graph.nodes(), key=lambda node: graph.degree(node))
    seen = {start}
    queue = [start]
    while queue and len(seen) < max_nodes:
        current = queue.pop(0)
        neighbours = sorted(graph.neighbors(current),
                            key=lambda node: graph.degree(node), reverse=True)
        for node in neighbours:
            if node in seen:
                continue
            seen.add(node)
            queue.append(node)
            if len(seen) >= max_nodes:
                break
    return graph.subgraph(seen).copy()


def _ensure_contiguous(graph):
    total = graph.number_of_nodes()
    if set(graph.nodes()) == set(range(total)):
        return graph
    return nx.convert_node_labels_to_integers(graph, ordering="sorted")


def load_graph_for_sim(dataset_name: str, max_nodes: int = 220):
    if nx is None:
        raise RuntimeError("Thiếu thư viện networkx để tải đồ thị.")

    key = _match_dataset(dataset_name)
    spec = DATASET_SPECS[key]
    name = key.lower()

    if "karate" in name:
        path = RAW_DIR / "karate.txt"
        graph = nx.read_edgelist(path, nodetype=int) if path.exists() else nx.karate_club_graph()
    elif "dolphin" in name:
        path = RAW_DIR / "dolphins.txt"
        if path.exists():
            graph = nx.read_edgelist(path, nodetype=int)
        else:
            graph = nx.powerlaw_cluster_graph(spec["full_n"], 3, 0.25, seed=spec["seed"])
    elif "facebook" in name:
        path = RAW_DIR / "facebook.txt"
        if path.exists():
            graph = _read_limited_edgelist(path, max_nodes * 2)
        else:
            graph = nx.powerlaw_cluster_graph(320, 8, 0.2, seed=spec["seed"])
    elif "nethept" in name or "hept" in name:
        path = RAW_DIR / "nethept.txt"
        if path.exists():
            graph = _read_limited_edgelist(path, max_nodes * 2, skip_header=True)
        else:
            graph = nx.powerlaw_cluster_graph(320, 6, 0.2, seed=spec["seed"])
    elif "enron" in name:
        path = RAW_DIR / "enron.txt"
        if path.exists():
            graph = _read_limited_edgelist(path, max_nodes * 2, skip_comments=True)
        else:
            graph = nx.powerlaw_cluster_graph(320, 8, 0.2, seed=spec["seed"])
    else:
        graph = nx.karate_club_graph()

    if graph is None or graph.number_of_nodes() == 0:
        raise ValueError(f"Không thể tải bộ dữ liệu {dataset_name}.")

    graph = nx.Graph(graph)
    graph.remove_edges_from(list(nx.selfloop_edges(graph)))
    if graph.number_of_nodes() == 0:
        raise ValueError(f"Đồ thị {dataset_name} rỗng.")

    graph = _largest_component(graph)
    if graph.number_of_nodes() > max_nodes:
        graph = _bfs_core(graph, max_nodes)
    graph = _ensure_contiguous(graph)

    meta = {
        "name": key,
        "n": graph.number_of_nodes(),
        "m": graph.number_of_edges(),
        "source": spec["source"],
        "full_n": spec["full_n"],
        "full_m": spec["full_m"],
        "reduced": graph.number_of_nodes() < spec["full_n"],
    }
    return graph, meta


def compute_layout(graph) -> Dict[int, tuple]:
    total = graph.number_of_nodes()
    if nx is None or total == 0:
        return {}
    if total == 1:
        return {next(iter(graph.nodes())): (0.5, 0.5)}

    try:
        if total <= 120:
            pos = nx.spring_layout(graph, seed=42, k=1.8 / math.sqrt(total), iterations=120)
        else:
            pos = nx.spring_layout(graph, seed=42, k=1.2 / math.sqrt(total), iterations=60)
    except Exception:
        pos = nx.circular_layout(graph)

    xs = [point[0] for point in pos.values()]
    ys = [point[1] for point in pos.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max_x - min_x
    span_y = max_y - min_y

    normalized = {}
    for node, (x, y) in pos.items():
        nx_value = (x - min_x) / span_x if span_x > 1e-12 else 0.5
        ny_value = (y - min_y) / span_y if span_y > 1e-12 else 0.5
        normalized[node] = (float(nx_value), float(ny_value))
    return normalized


def _simulate_ic(adjacency, seeds, probabilities, rng, max_steps):
    active = set(seeds)
    timeline = [list(seeds)]
    frontier = list(seeds)
    while frontier and len(timeline) <= max_steps:
        newly_active = []
        for node in frontier:
            for neighbour in adjacency[node]:
                if neighbour not in active and rng.random() < probabilities[neighbour]:
                    active.add(neighbour)
                    newly_active.append(neighbour)
        if not newly_active:
            break
        timeline.append(newly_active)
        frontier = newly_active
    return timeline


def _simulate_lt(adjacency, seeds, rng, max_steps):
    total = len(adjacency)
    degrees = [max(1, len(neighbours)) for neighbours in adjacency]
    thresholds = [rng.random() for _ in range(total)]
    active = set(seeds)
    timeline = [list(seeds)]
    frontier = list(seeds)

    while frontier and len(timeline) <= max_steps:
        candidates = set()
        for node in frontier:
            candidates.update(adjacency[node])
        candidates.difference_update(active)

        newly_active = []
        for node in candidates:
            weight = sum(1.0 / degrees[node] for parent in adjacency[node] if parent in active)
            if weight >= thresholds[node]:
                newly_active.append(node)
        if not newly_active:
            break
        newly_active.sort()
        active.update(newly_active)
        timeline.append(newly_active)
        frontier = newly_active
    return timeline


def simulate_diffusion(graph, seeds, model: str, rng, max_steps: int = 80):
    total = graph.number_of_nodes()
    if total == 0:
        return []

    adjacency = [list(graph.neighbors(node)) for node in range(total)]
    seed_list = sorted({int(seed) for seed in seeds if 0 <= int(seed) < total})
    if not seed_list:
        return []

    if model.upper().startswith("LT"):
        return _simulate_lt(adjacency, seed_list, rng, max_steps)

    if "WC" in model.upper():
        probabilities = [1.0 / max(1, len(neighbours)) for neighbours in adjacency]
    else:
        probabilities = [0.1] * total
    return _simulate_ic(adjacency, seed_list, probabilities, rng, max_steps)


def evaluate_seeds(graph, seeds, model: str, rng, runs: int) -> float:
    total_runs = max(1, int(runs))
    accumulated = 0.0
    for _ in range(total_runs):
        timeline = simulate_diffusion(graph, seeds, model, rng)
        accumulated += sum(len(step) for step in timeline)
    return accumulated / total_runs


class _NXAdapter:
    def __init__(self, graph):
        self._graph = graph
        self._n = graph.number_of_nodes()
        self._adjacency = [list(graph.neighbors(node)) for node in range(self._n)]
        self._row_ptr = [0]
        for neighbours in self._adjacency:
            self._row_ptr.append(self._row_ptr[-1] + len(neighbours))
        self._col_indices = [node for neighbours in self._adjacency for node in neighbours]

    def num_nodes(self) -> int:
        return self._n

    def num_edges(self) -> int:
        return self._graph.number_of_edges()

    def row_ptr(self):
        return self._row_ptr

    def col_indices(self):
        return self._col_indices


class _PythonEvaluator:
    def __init__(self, graph, model: str, mc: int, seed: int):
        self.graph = graph
        self.model = model
        self.mc = max(1, int(mc))
        self.rng = random.Random(seed)
        self.history = []

    def evaluate(self, seeds) -> float:
        score = evaluate_seeds(self.graph, seeds, self.model, self.rng, self.mc)
        self.history.append((
            tuple(sorted(int(node) for node in seeds)),
            float(score),
        ))
        return score

    def batch_evaluate(self, seed_sets):
        return [self.evaluate(seeds) for seeds in seed_sets]


def _evolution_params(full_n: int) -> dict:
    pop_size = 50 if full_n < 20000 else 100
    return {
        "N": pop_size,
        "q": max(1, int(round(0.10 * pop_size))),
        "Pc": 0.9,
        "Pm": 0.1,
        "E": max(1, int(round(0.04 * pop_size))),
        "Tmax": 100,
    }


def _make_algorithm(code: str, total_nodes: int, params: dict):
    if code == "celf":
        return CELF()
    if code == "ga":
        return BaselineGA(
            pop_size=params["N"],
            max_generations=params["Tmax"],
            crossover_rate=params["Pc"],
            mutation_rate=params["Pm"],
            tournament_size=params["q"],
            elitism=params["E"],
        )
    if code == "iga":
        return IGA(
            pop_size=params["N"],
            max_generations=params["Tmax"],
            crossover_rate=params["Pc"],
            mutation_rate_base=params["Pm"],
            tournament_size=params["q"],
            elitism=params["E"],
        )
    raise ValueError(f"Unknown algorithm code: {code}")
    raise ValueError(f"Thuật toán không hợp lệ: {code}")


def _top_individuals(history, k: int, graph, model: str, seed: int,
                     runs: int, best_seeds, best_spread) -> list:
    best_by_seeds = {}
    for seeds, fitness in history:
        if len(seeds) != k:
            continue
        previous = best_by_seeds.get(seeds)
        if previous is None or fitness > previous:
            best_by_seeds[seeds] = fitness

    ranked = sorted(
        best_by_seeds.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:5]

    if not ranked:
        ranked = [(tuple(best_seeds), float(best_spread))]

    validation_runs = max(1, int(runs))
    rng = random.Random(seed + 2024)
    individuals = []
    best_tuple = tuple(best_seeds)
    for rank, (seeds, fitness) in enumerate(ranked, start=1):
        if seeds == best_tuple:
            spread = best_spread
        else:
            spread = evaluate_seeds(
                graph, list(seeds), model, rng, validation_runs,
            )
        individuals.append({
            "rank": rank,
            "seeds": list(seeds),
            "fitness": round(float(fitness), 4),
            "spread": round(float(spread), 4),
        })
    return individuals


def run_cpp_ga_on_graph(dataset: str, model: str, k: int, mc: int,
                        params: dict, seed: int = -1,
                        progress=None) -> dict:
    if _im_core is None:
        raise RuntimeError(
            "C++ core (_im_core) chưa được build. Hãy build pybind11 extension trước."
        )
    if not model.upper().startswith("IC"):
        raise ValueError("C++ GA hiện chỉ hỗ trợ mô hình Independent Cascade.")
    model_label = model if "WC" in model.upper() else "IC (WC)"

    seed = int(seed)
    if seed < 0:
        seed = int(time.time_ns() % (2 ** 63 - 1)) or 1

    if progress:
        progress(0.02)

    nx_graph, meta = load_networkx_graph(dataset)
    cpp_graph = build_cpp_graph(nx_graph, probability_mode="wc")
    total_nodes = nx_graph.number_of_nodes()
    k = max(1, min(int(k), total_nodes))
    mc = max(1, int(mc))
    params = dict(params)

    if progress:
        progress(0.15)

    evaluator = _im_core.Evaluator(
        cpp_graph,
        _im_core.DiffusionModel.IndependentCascade,
        num_mc_simulations=mc,
        seed=seed,
    )
    problem = IMProblem(cpp_graph, k, evaluator)
    algorithm = CppBaselineGA(
        pop_size=params["N"],
        max_generations=params["Tmax"],
        crossover_rate=params["Pc"],
        mutation_rate=params["Pm"],
        tournament_size=params["q"],
        elitism=params["E"],
        num_mc=mc,
    )

    started = time.perf_counter()
    result = algorithm.run(
        problem,
        seed=seed,
        max_iterations=params["Tmax"],
    )
    seeds = sorted(int(node) for node in result.best_solution.seed_set)

    if progress:
        progress(0.75)

    spread_values = [
        int(value)
        for value in evaluator.evaluate_replications(seeds, mc)
    ]
    if not spread_values:
        spread_values = [int(result.best_solution.fitness or 0)]

    mean_spread = sum(spread_values) / len(spread_values)
    if len(spread_values) > 1:
        variance = sum((value - mean_spread) ** 2 for value in spread_values) / len(spread_values)
        std_spread = math.sqrt(variance)
    else:
        std_spread = 0.0

    validation_rng = random.Random(seed + 9999)
    timeline = simulate_diffusion(nx_graph, seeds, model_label, validation_rng)
    finished = time.perf_counter()

    cumulative = []
    active = set()
    for step in timeline:
        active.update(step)
        cumulative.append(len(active))

    final_spread = spread_values[0] if spread_values else 0
    individuals = [
        dict(individual)
        for individual in result.metadata.get("top_individuals", [])
    ]
    if not individuals:
        individuals = [{
            "rank": 1,
            "seeds": seeds,
            "fitness": float(result.best_solution.fitness or mean_spread),
            "spread": mean_spread,
        }]

    for individual in individuals:
        if list(individual.get("seeds", [])) == seeds:
            individual["fitness"] = float(result.best_solution.fitness or mean_spread)
            individual["spread"] = mean_spread

    outcome_meta = {
        key: value for key, value in meta.items()
        if key != "id_mapping"
    }
    outcome_meta["reduced"] = False
    outcome_meta["full_n"] = total_nodes
    outcome_meta["backend"] = "cpp"

    if progress:
        progress(1.0)

    return {
        "code": "ga",
        "name": ALGO_LABELS.get("ga", "Baseline GA"),
        "algorithm_name": result.algorithm_name,
        "dataset": meta.get("name", dataset),
        "model": model_label,
        "seeds": seeds,
        "timeline": timeline,
        "cumulative": cumulative,
        "final_spread": final_spread,
        "mean_spread": mean_spread,
        "std_spread": std_spread,
        "spreads": spread_values,
        "total_nodes": total_nodes,
        "full_n": total_nodes,
        "ratio": final_spread / total_nodes if total_nodes else 0.0,
        "mean_ratio": mean_spread / total_nodes if total_nodes else 0.0,
        "execution_time": finished - started,
        "params": params,
        "individuals": individuals,
        "meta": outcome_meta,
        "seed": seed,
        "generations": int(result.metadata.get("generations_completed", len(result.convergence_history))),
    }


def run_simulation_on_graph(graph, meta, dataset: str, model: str,
                            k: int, mc: int, algo_code: str,
                            seed: int = 42,
                            progress=None,
                            params: dict | None = None) -> dict:
    if nx is None:
        raise RuntimeError("Thiếu thư viện networkx.")

    graph = _ensure_contiguous(graph)
    total_nodes = graph.number_of_nodes()
    full_n = int(meta.get("full_n", total_nodes) or total_nodes)
    k = max(1, min(int(k), total_nodes))
    mc = max(1, int(mc))
    seed = int(seed)
    if seed < 0:
        seed = int(time.time_ns() % (2 ** 63 - 1)) or 1
    if algo_code == "celf":
        seed = 42
    params = dict(params) if params is not None else _evolution_params(full_n)

    if progress:
        progress(0.05)

    adapter = _NXAdapter(graph)
    evaluator = _PythonEvaluator(graph, model, mc, seed)
    problem = IMProblem(adapter, k, evaluator)
    algorithm = _make_algorithm(algo_code, total_nodes, params)

    if progress:
        progress(0.20)

    started = time.perf_counter()
    max_evaluations = None
    max_iterations = params["Tmax"] if algo_code in ("ga", "iga") else None

    result = algorithm.run(
        problem,
        seed=seed,
        max_evaluations=max_evaluations,
        max_iterations=max_iterations,
    )
    seeds = sorted(int(node) for node in result.best_solution.seed_set)

    if progress:
        progress(0.70)

    mc_val = max(1, mc)
    validation_rng = random.Random(seed + 9999)
    timelines = [
        simulate_diffusion(graph, seeds, model, validation_rng)
        for _ in range(mc_val)
    ]
    spreads = [sum(len(step) for step in timeline) for timeline in timelines]
    finished = time.perf_counter()

    timeline = timelines[0] if timelines else [seeds]
    cumulative = []
    active = set()
    for step in timeline:
        active.update(step)
        cumulative.append(len(active))

    mean_spread = sum(spreads) / len(spreads) if spreads else 0.0
    if len(spreads) > 1:
        variance = sum((value - mean_spread) ** 2 for value in spreads) / len(spreads)
        std_spread = math.sqrt(variance)
    else:
        std_spread = 0.0

    final_spread = spreads[0] if spreads else 0
    if algo_code == "celf":
        individuals = [{
            "rank": 1,
            "seeds": seeds,
            "fitness": mean_spread,
            "spread": mean_spread,
        }]
    else:
        individuals = _top_individuals(
            evaluator.history, k, graph, model, seed, mc_val, seeds, mean_spread,
        )

    if progress:
        progress(1.0)

    return {
        "code": algo_code,
        "name": ALGO_LABELS.get(algo_code, algo_code),
        "algorithm_name": getattr(result, "algorithm_name", ALGO_LABELS.get(algo_code, algo_code)),
        "dataset": meta.get("name", dataset),
        "model": model,
        "seeds": seeds,
        "timeline": timeline,
        "cumulative": cumulative,
        "final_spread": final_spread,
        "mean_spread": mean_spread,
        "std_spread": std_spread,
        "spreads": spreads,
        "total_nodes": total_nodes,
        "full_n": full_n,
        "ratio": final_spread / total_nodes if total_nodes else 0.0,
        "mean_ratio": mean_spread / total_nodes if total_nodes else 0.0,
        "execution_time": finished - started,
        "params": dict(params),
        "individuals": individuals,
        "meta": meta,
        "online_bound": (
            result.metadata.get("online_bound")
            if algo_code == "celf" else None
        ),
        "seed": seed,
        "generations": int(getattr(result, "metadata", {}).get("generations_completed", len(getattr(result, "convergence_history", [])))),
    }


def run_celf_on_graph(dataset: str, model: str, k: int, mc: int,
                      seed: int = 42, progress=None) -> dict:
    if _im_core is None:
        raise RuntimeError(
            "C++ core (_im_core) chưa được build. Hãy build pybind11 extension trước."
        )
    if not model.upper().startswith("IC"):
        raise ValueError("CELF hiện chỉ hỗ trợ mô hình Independent Cascade.")
    model_label = model if "WC" in model.upper() else "IC (WC)"

    seed = 42

    if progress:
        progress(0.02)

    nx_graph, meta = load_networkx_graph(dataset)
    cpp_graph = build_cpp_graph(nx_graph, probability_mode="wc")
    total_nodes = nx_graph.number_of_nodes()
    k = max(1, min(int(k), total_nodes))
    mc = max(1, int(mc))

    if progress:
        progress(0.15)

    evaluator = _im_core.Evaluator(
        cpp_graph,
        _im_core.DiffusionModel.IndependentCascade,
        num_mc_simulations=mc,
        seed=seed,
    )
    problem = IMProblem(cpp_graph, k, evaluator)
    algorithm = CELF()

    started = time.perf_counter()
    result = algorithm.run(problem, seed=seed)
    seeds = sorted(int(node) for node in result.best_solution.seed_set)

    if progress:
        progress(0.75)

    spread_values = [
        int(value)
        for value in evaluator.evaluate_replications(seeds, mc)
    ]
    if not spread_values:
        spread_values = [int(result.best_solution.fitness or 0)]

    mean_spread = sum(spread_values) / len(spread_values)
    if len(spread_values) > 1:
        variance = sum((value - mean_spread) ** 2 for value in spread_values) / len(spread_values)
        std_spread = math.sqrt(variance)
    else:
        std_spread = 0.0

    validation_rng = random.Random(seed + 9999)
    timeline = simulate_diffusion(nx_graph, seeds, model_label, validation_rng)
    finished = time.perf_counter()

    cumulative = []
    active = set()
    for step in timeline:
        active.update(step)
        cumulative.append(len(active))

    final_spread = spread_values[0] if spread_values else 0

    outcome_meta = {
        key: value for key, value in meta.items()
        if key != "id_mapping"
    }
    outcome_meta["reduced"] = False
    outcome_meta["full_n"] = total_nodes
    outcome_meta["backend"] = "cpp-evaluator"

    if progress:
        progress(1.0)

    return {
        "code": "celf",
        "name": ALGO_LABELS.get("celf", "Greedy / CELF"),
        "algorithm_name": getattr(result, "algorithm_name", "CELF"),
        "dataset": meta.get("name", dataset),
        "model": model_label,
        "seeds": seeds,
        "timeline": timeline,
        "cumulative": cumulative,
        "final_spread": final_spread,
        "mean_spread": mean_spread,
        "std_spread": std_spread,
        "spreads": spread_values,
        "total_nodes": total_nodes,
        "full_n": total_nodes,
        "ratio": final_spread / total_nodes if total_nodes else 0.0,
        "mean_ratio": mean_spread / total_nodes if total_nodes else 0.0,
        "execution_time": finished - started,
        "params": {},
        "individuals": [{
            "rank": 1,
            "seeds": seeds,
            "fitness": mean_spread,
            "spread": mean_spread,
        }],
        "meta": outcome_meta,
        "online_bound": result.metadata.get("online_bound"),
        "seed": seed,
        "generations": len(result.convergence_history),
    }
