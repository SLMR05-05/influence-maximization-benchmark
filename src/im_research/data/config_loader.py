#!/usr/bin/env python3
"""
Dataset Configuration Loader and Importer.
Scans, parses, and imports dataset definitions from configs/datasets/*.yaml.
"""

from __future__ import annotations
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
import networkx as nx

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIGS_DIR = PROJECT_ROOT / "configs" / "datasets"
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Palette colors assigned cyclically to datasets
BADGE_PALETTE = [
    "#10b981",  # Emerald / Green (Karate)
    "#0284c7",  # Sky / Blue (Dolphins)
    "#2563eb",  # Royal Blue (Facebook)
    "#8b5cf6",  # Violet (NetHEPT)
    "#f59e0b",  # Amber (Enron)
    "#ec4899",  # Pink
    "#06b6d4",  # Cyan
    "#14b8a6",  # Teal
    "#f97316",  # Orange
]

CATEGORY_TRANSLATIONS = {
    "small social network": "Mạng xã hội nhỏ",
    "animal social network": "Mạng quan hệ xã hội",
    "online social network": "Mạng xã hội trực tuyến",
    "academic collaboration network": "Mạng đồng tác giả học thuật",
    "email communication network": "Mạng truyền thông thư điện tử",
}


def _format_vi_number(val: int | float, decimals: int = 0) -> str:
    """Formats numbers with dots for thousands and comma for decimal separator (Vietnamese style)."""
    if isinstance(val, int) or (isinstance(val, float) and decimals == 0 and val.is_integer()):
        return f"{int(val):,}".replace(",", ".")
    elif isinstance(val, (int, float)):
        s = f"{val:,.{decimals}f}"
        # Swap comma and dot
        parts = s.split(".")
        int_part = parts[0].replace(",", ".")
        dec_part = parts[1] if len(parts) > 1 else ""
        return f"{int_part},{dec_part}" if dec_part else int_part
    return str(val)


def load_all_dataset_configs(configs_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Scans configs/datasets/ and returns a sorted list of dataset metadata dictionaries.
    """
    if configs_dir is None:
        configs_dir = DEFAULT_CONFIGS_DIR

    configs_dir = Path(configs_dir)
    if not configs_dir.exists():
        configs_dir.mkdir(parents=True, exist_ok=True)
        return []

    yaml_files = sorted(list(configs_dir.glob("*.yaml")) + list(configs_dir.glob("*.yml")))
    datasets = []

    for idx, yf in enumerate(yaml_files):
        try:
            with open(yf, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                continue

            name = data.get("name", yf.stem.capitalize())
            ident = data.get("identifier", yf.stem.lower())
            n_raw = int(data.get("num_nodes", data.get("n", 0)))
            m_raw = int(data.get("num_edges", data.get("m", 0)))
            avg_deg_raw = float(data.get("average_degree", data.get("avg_deg", 0.0)))
            clust_raw = float(data.get("clustering_coefficient", data.get("clustering", 0.0)))
            diam_raw = data.get("diameter", "—")

            raw_path_str = data.get("raw_path", f"data/raw/{ident}.txt")
            raw_path = PROJECT_ROOT / raw_path_str if not Path(raw_path_str).is_absolute() else Path(raw_path_str)

            # Category translation
            category = data.get("classification", data.get("category", "Đồ thị mạng phức hợp"))
            cat_key = category.strip().lower()
            category_vi = CATEGORY_TRANSLATIONS.get(cat_key, category)

            # Color assignment
            badge_color = data.get("badge_color") or BADGE_PALETTE[idx % len(BADGE_PALETTE)]

            ds_item = {
                "name": name,
                "identifier": ident,
                "file": raw_path.name,
                "raw_path": str(raw_path),
                "raw_n": n_raw,
                "raw_m": m_raw,
                "raw_avg_deg": avg_deg_raw,
                "raw_clustering": clust_raw,
                "n": _format_vi_number(n_raw),
                "m": _format_vi_number(m_raw),
                "avg_deg": _format_vi_number(avg_deg_raw, 2),
                "clustering": _format_vi_number(clust_raw, 3),
                "diameter": str(diam_raw),
                "category": category_vi,
                "source": data.get("source", "N/A"),
                "badge_color": badge_color,
                "default_k_values": data.get("default_k_values", [5, 10, 15, 20]),
                "config_file": yf.name,
                "exists_on_disk": raw_path.exists(),
            }
            datasets.append(ds_item)

        except Exception as e:
            print(f"[config_loader] Error loading {yf}: {e}")

    # Sort small to large by node count (or standard ordering)
    datasets.sort(key=lambda d: d["raw_n"])
    return datasets


def import_dataset_yaml_file(src_yaml_path: Path, target_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Imports an external YAML dataset config file into configs/datasets/.
    """
    if target_dir is None:
        target_dir = DEFAULT_CONFIGS_DIR

    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    src_yaml_path = Path(src_yaml_path)

    with open(src_yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Tệp YAML không hợp lệ: Cần chứa cấu trúc dictionary.")

    name = data.get("name", src_yaml_path.stem.capitalize())
    ident = data.get("identifier", re.sub(r"[^a-zA-Z0-9_]", "_", name.lower()))
    dest_path = target_dir / f"{ident}.yaml"

    # Copy / Write to configs/datasets/
    shutil.copyfile(src_yaml_path, dest_path)
    return data


def generate_config_from_edgelist(
    name: str,
    edgelist_path: Path,
    category: str = "Đồ thị mạng phức hợp",
    source: str = "Tải lên từ người dùng",
    target_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Analyzes an edgelist file, computes basic graph topological metrics,
    and writes a corresponding YAML configuration file into configs/datasets/.
    """
    if target_dir is None:
        target_dir = DEFAULT_CONFIGS_DIR

    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    edgelist_path = Path(edgelist_path)

    if not edgelist_path.exists():
        raise FileNotFoundError(f"Không tìm thấy tệp đồ thị: {edgelist_path}")

    # Read graph using networkx
    g = nx.read_edgelist(edgelist_path, nodetype=int)
    n = g.number_of_nodes()
    m = g.number_of_edges()
    avg_deg = (2.0 * m) / n if n > 0 else 0.0

    # Approximate clustering if graph is moderate/small
    if n <= 5000:
        clust = float(nx.average_clustering(g))
    else:
        # Sample for large graphs
        clust = float(nx.average_clustering(g, count=1000))

    # Diameter approximation or calculation
    if n <= 1000 and nx.is_connected(g):
        diam = int(nx.diameter(g))
    else:
        diam = "—"

    ident = re.sub(r"[^a-zA-Z0-9_]", "_", name.lower()).strip("_")
    yaml_dest = target_dir / f"{ident}.yaml"

    # Ensure raw copy in data/raw if needed
    raw_dest = DEFAULT_RAW_DIR / edgelist_path.name
    if edgelist_path.resolve() != raw_dest.resolve():
        DEFAULT_RAW_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(edgelist_path, raw_dest)

    rel_raw = f"data/raw/{edgelist_path.name}"

    cfg_data = {
        "name": name,
        "identifier": ident,
        "type": "undirected",
        "num_nodes": int(n),
        "num_edges": int(m),
        "average_degree": round(avg_deg, 2),
        "clustering_coefficient": round(clust, 3),
        "diameter": diam,
        "classification": category,
        "source": source,
        "raw_path": rel_raw,
        "processed_path": f"data/processed/{ident}.csr",
        "metadata_path": f"data/metadata/{ident}.json",
        "default_k_values": [5, 10, 20, 30, 50],
    }

    with open(yaml_dest, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg_data, f, sort_keys=False, allow_unicode=True)

    return cfg_data
