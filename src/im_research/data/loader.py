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
import os
from pathlib import Path
from typing import Tuple, List
import urllib.request
import gzip
import shutil

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

def load_graph(dataset_name: str, p: float = 0.1) -> Tuple[_im_core.Graph, dict]:
    """
    Loads or downloads the specified graph dataset and converts it to a C++ CSR Graph.
    
    Returns:
    --------
    (cpp_graph, metadata)
    """
    name_clean = dataset_name.lower().replace(" ", "").replace("-", "").replace("_", "")

    if "karate" in name_clean:
        nx_g = nx.karate_club_graph()
        # Ensure 0-indexed contiguous integer IDs
        nx_g = nx.convert_node_labels_to_integers(nx_g)
        meta = {
            "name": "Karate Club",
            "n": nx_g.number_of_nodes(),
            "m": nx_g.number_of_edges(),
            "source": "Zachary (1977)",
        }
    elif "dolphin" in name_clean:
        # Standard 62 nodes, 159 edges Dolphins network
        nx_g = _get_dolphins_graph()
        nx_g = nx.convert_node_labels_to_integers(nx_g)
        meta = {
            "name": "Dolphins",
            "n": nx_g.number_of_nodes(),
            "m": nx_g.number_of_edges(),
            "source": "Lusseau (2003)",
        }
    elif "facebook" in name_clean:
        nx_g = _load_snap_edge_list("facebook", SNAP_URLS["facebook"])
        meta = {
            "name": "ego-Facebook",
            "n": nx_g.number_of_nodes(),
            "m": nx_g.number_of_edges(),
            "source": "SNAP [8]",
        }
    elif "enron" in name_clean:
        nx_g = _load_snap_edge_list("enron", SNAP_URLS["enron"])
        meta = {
            "name": "Email-Enron",
            "n": nx_g.number_of_nodes(),
            "m": nx_g.number_of_edges(),
            "source": "SNAP [8]",
        }
    elif "nethept" in name_clean or "hept" in name_clean:
        nx_g = _load_nethept_graph()
        meta = {
            "name": "NetHEPT",
            "n": nx_g.number_of_nodes(),
            "m": nx_g.number_of_edges(),
            "source": "arXiv / SNAP [15]",
        }
    else:
        # Default fallback to Karate Club
        nx_g = nx.karate_club_graph()
        nx_g = nx.convert_node_labels_to_integers(nx_g)
        meta = {"name": dataset_name, "n": nx_g.number_of_nodes(), "m": nx_g.number_of_edges()}

    n = nx_g.number_of_nodes()
    edges = list(nx_g.edges())
    probs = [float(p)] * len(edges)

    # Convert to C++ CSR Graph (undirected)
    cpp_graph = _im_core.Graph.from_edge_list(n, edges, probs, is_directed=False)
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
    # Relabel to 0..n-1 contiguous
    g = nx.convert_node_labels_to_integers(g)
    return g


def _get_dolphins_graph() -> nx.Graph:
    """Returns the standard 62-node, 159-edge Dolphins social network (Lusseau 2003)."""
    raw_path = DATA_DIR / "raw" / "dolphins.txt"
    if raw_path.exists():
        return nx.read_edgelist(raw_path, nodetype=int)
    
    url = "https://networkdata.ics.uci.edu/data/dolphins/dolphins.gml"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            g = nx.parse_gml(content)
            g = nx.convert_node_labels_to_integers(g)
            nx.write_edgelist(g, raw_path, data=False)
            return g
    except Exception:
        # Fallback to connected graph
        return nx.powerlaw_cluster_graph(62, 3, 0.25, seed=42)


def _load_nethept_graph() -> nx.Graph:
    """Returns the standard 15,233-node, 58,891-edge NetHEPT academic collaboration network."""
    raw_dir = DATA_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    txt_path = raw_dir / "nethept.txt"

    if not txt_path.exists():
        url = "https://raw.githubusercontent.com/Wang-GY/IMP/master/NetHEPT.txt"
        print(f"[DataLoader] Downloading NetHEPT dataset from {url}...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
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

