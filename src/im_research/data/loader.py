"""
Graph Dataset Loader for Influence Maximization Benchmark.
Supports standard benchmarks:
- Karate Club (Zachary 1977, n=34, m=78)
- Dolphins (Lusseau 2003, n=62, m=159)
- ego-Facebook (SNAP, n=4039, m=88234)
- NetHEPT (arXiv / SNAP, n=15233, m=58891)
- Email-Enron (SNAP, n=36692, m=183831)
"""

from __future__ import annotations
import gzip
import shutil
import urllib.request
from pathlib import Path
from typing import Tuple

import networkx as nx

try:
    from im_research import _im_core
except ImportError:
    _im_core = None

DATA_DIR = Path(__file__).resolve().parents[3] / "data"

SNAP_URLS = {
    "facebook": "https://snap.stanford.edu/data/facebook_combined.txt.gz",
    "enron": "https://snap.stanford.edu/data/email-Enron.txt.gz",
}


def load_networkx_graph(dataset_name: str) -> Tuple[nx.Graph, dict]:
    name_clean = dataset_name.lower().replace(" ", "").replace("-", "").replace("_", "")

    if "karate" in name_clean:
        nx_g = nx.karate_club_graph()
        source = "Zachary (1977)"
        display_name = "Karate Club"
    elif "dolphin" in name_clean:
        nx_g = _get_dolphins_graph()
        source = "Lusseau (2003)"
        display_name = "Dolphins"
    elif "facebook" in name_clean:
        nx_g = _load_snap_edge_list("facebook", SNAP_URLS["facebook"])
        source = "SNAP [8]"
        display_name = "ego-Facebook"
    elif "enron" in name_clean:
        nx_g = _load_snap_edge_list("enron", SNAP_URLS["enron"])
        source = "SNAP [8]"
        display_name = "Email-Enron"
    elif "nethept" in name_clean or "hept" in name_clean:
        nx_g = _load_nethept_graph()
        source = "arXiv / SNAP [15]"
        display_name = "NetHEPT"
    else:
        nx_g = nx.karate_club_graph()
        source = "Zachary (1977)"
        display_name = dataset_name

    original_nodes = list(nx_g.nodes())
    ordered_nodes = sorted(original_nodes)
    relabel = {old: new for new, old in enumerate(ordered_nodes)}
    nx_g = nx.relabel_nodes(nx_g, relabel, copy=True)
    nx_g = nx.Graph(nx_g)
    nx_g.remove_edges_from(list(nx.selfloop_edges(nx_g)))

    if nx_g.number_of_nodes() == 0:
        raise ValueError(f"Graph dataset '{dataset_name}' is empty after preprocessing")

    nx_g = nx.convert_node_labels_to_integers(nx_g, ordering="sorted")

    meta = {
        "name": display_name,
        "n": nx_g.number_of_nodes(),
        "m": nx_g.number_of_edges(),
        "source": source,
        "directed": False,
        "preprocessed": True,
        "self_loops_removed": True,
        "duplicate_edges_removed": True,
        "id_mapping": ordered_nodes,
    }
    return nx_g, meta


def build_cpp_graph(nx_g: nx.Graph,
                    probability_mode: str = "wc",
                    p: float = 0.1):
    if _im_core is None:
        raise RuntimeError(
            "C++ core (_im_core) is not built. Build the pybind11 extension first."
        )

    n = nx_g.number_of_nodes()
    edges = list(nx_g.edges())

    mode = probability_mode.lower()
    if mode in ("wc", "weighted", "weighted_cascade"):
        return _im_core.Graph.from_edge_list_wc(n, edges, is_directed=False)

    if mode in ("uniform", "constant", "fixed"):
        probs = [float(p)] * len(edges)
        return _im_core.Graph.from_edge_list(n, edges, probs, is_directed=False)

    raise ValueError(f"Unsupported probability mode: {probability_mode}")


def load_graph(dataset_name: str,
               p: float = 0.1,
               probability_mode: str = "wc") -> Tuple[_im_core.Graph, dict]:
    nx_g, meta = load_networkx_graph(dataset_name)
    cpp_graph = build_cpp_graph(nx_g, probability_mode=probability_mode, p=p)
    meta["probability_model"] = (
        "WC" if probability_mode.lower() in ("wc", "weighted", "weighted_cascade")
        else "Uniform"
    )
    meta["p"] = None if meta["probability_model"] == "WC" else float(p)
    return cpp_graph, meta


def _load_snap_edge_list(name: str, url: str) -> nx.Graph:
    raw_dir = DATA_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    txt_path = raw_dir / f"{name}.txt"
    gz_path = raw_dir / f"{name}.txt.gz"

    if not txt_path.exists():
        if not gz_path.exists():
            print(f"[DataLoader] Downloading {name} dataset from SNAP...")
            urllib.request.urlretrieve(url, gz_path)
        print(f"[DataLoader] Extracting {gz_path.name}...")
        with gzip.open(gz_path, "rb") as f_in:
            with open(txt_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

    g = nx.read_edgelist(txt_path, nodetype=int)
    return nx.Graph(g)


def _get_dolphins_graph() -> nx.Graph:
    raw_path = DATA_DIR / "raw" / "dolphins.txt"
    if raw_path.exists():
        return nx.read_edgelist(raw_path, nodetype=int)

    url = "https://networkdata.ics.uci.edu/data/dolphins/dolphins.gml"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            g = nx.parse_gml(content)
            g = nx.convert_node_labels_to_integers(g)
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            nx.write_edgelist(g, raw_path, data=False)
            return g
    except Exception:
        return nx.powerlaw_cluster_graph(62, 3, 0.25, seed=42)


def _load_nethept_graph() -> nx.Graph:
    raw_dir = DATA_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    txt_path = raw_dir / "nethept.txt"

    if not txt_path.exists():
        url = "https://raw.githubusercontent.com/Wang-GY/IMP/master/NetHEPT.txt"
        print(f"[DataLoader] Downloading NetHEPT dataset from {url}...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as resp:
                txt_path.write_bytes(resp.read())
        except Exception as e:
            print(f"[DataLoader] Warning: failed to download NetHEPT ({e})")

    edges = []
    header_n = 15233
    if txt_path.exists():
        with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
            first_line = f.readline().strip().split()
            if len(first_line) >= 2:
                try:
                    header_n = int(first_line[0])
                except ValueError:
                    pass
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    u, v = int(parts[0]), int(parts[1])
                    if u != v:
                        edges.append((u, v))

    g = nx.Graph()
    g.add_nodes_from(range(header_n))
    g.add_edges_from(edges)
    return g
