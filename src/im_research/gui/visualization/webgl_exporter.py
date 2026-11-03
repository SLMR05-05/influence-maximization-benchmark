"""
Standalone 3D WebGL Knowledge Graph Generator using Three.js & 3d-force-graph.
Produces a GPU-accelerated interactive 3D universe with bloom glow, particle links,
and orbital camera controls.
"""

from __future__ import annotations
import json
import webbrowser
from pathlib import Path
from typing import List, Set
import networkx as nx

PROJECT_ROOT = Path(__file__).resolve().parents[4]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>IM-Benchmark-Lab — 3D Knowledge Graph & Influence Universe</title>
  <style>
    body { margin: 0; background-color: #06090e; overflow: hidden; font-family: 'Segoe UI', Tahoma, sans-serif; }
    #3d-graph { width: 100vw; height: 100vh; }
    #hud {
      position: absolute; top: 18px; left: 24px; z-index: 100;
      color: #e0f2fe; pointer-events: none;
      background: rgba(8, 14, 24, 0.82); padding: 16px 22px; border-radius: 12px;
      border: 1px solid rgba(0, 229, 255, 0.3); backdrop-filter: blur(8px);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
    }
    #hud h1 { margin: 0 0 6px 0; font-size: 18px; color: #00e5ff; letter-spacing: 0.5px; }
    #hud p { margin: 3px 0; font-size: 12px; color: #94a3b8; }
    #legend {
      position: absolute; bottom: 24px; right: 24px; z-index: 100;
      background: rgba(8, 14, 24, 0.85); padding: 14px 20px; border-radius: 10px;
      border: 1px solid #1e293b; color: #e2e8f0; font-size: 11px;
    }
    .legend-item { display: flex; align-items: center; margin: 4px 0; }
    .dot { width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
  </style>
  <script src="https://unpkg.com/3d-force-graph"></script>
</head>
<body>
  <div id="hud">
    <h1>⚛ IM-Benchmark-Lab: 3D Network Explorer</h1>
    <p>Dataset: <strong>__DATASET_NAME__</strong> | Đỉnh: __NUM_NODES__ | Cạnh: __NUM_EDGES__</p>
    <p>Điều khiển: Chuột trái = Xoay 3D | Chuột phải = Di chuyển | Cuộn = Phóng to/Thu nhỏ</p>
  </div>
  <div id="legend">
    <div class="legend-item"><div class="dot" style="background:#ff3366; box-shadow:0 0 8px #ff3366"></div>Tập hạt giống (Seeds S)</div>
    <div class="legend-item"><div class="dot" style="background:#00e5ff; box-shadow:0 0 8px #00e5ff"></div>Đỉnh trung tâm (Hubs)</div>
    <div class="legend-item"><div class="dot" style="background:#818cf8"></div>Cộng đồng mạng</div>
  </div>
  <div id="3d-graph"></div>

  <script>
    const gData = __GRAPH_JSON_DATA__;

    const Graph = ForceGraph3D()
      (document.getElementById('3d-graph'))
      .graphData(gData)
      .backgroundColor('#06090e')
      .nodeLabel(node => `Đỉnh ${node.id} (Bậc: ${node.degree}) ${node.is_seed ? '★ Hạt giống' : ''}`)
      .nodeColor(node => node.is_seed ? '#ff3366' : (node.degree >= 10 ? '#00e5ff' : node.color))
      .nodeVal(node => node.is_seed ? 18 : Math.max(3, node.degree * 2.2))
      .linkWidth(link => link.is_active ? 2.5 : 0.8)
      .linkColor(link => link.is_active ? '#38bdf8' : '#0369a1')
      .linkOpacity(0.45)
      .linkDirectionalParticles(2)
      .linkDirectionalParticleWidth(1.2)
      .linkDirectionalParticleSpeed(0.006)
      .cameraPosition({ x: 0, y: 0, z: 320 });

    // Slow orbital rotation
    let angle = 0;
    setInterval(() => {
      Graph.cameraPosition({
        x: 320 * Math.sin(angle),
        z: 320 * Math.cos(angle)
      });
      angle += Math.PI / 1200;
    }, 25);
  </script>
</body>
</html>
"""


def export_and_open_webgl(nx_graph: nx.Graph, dataset_name: str = "Karate Club", seed_nodes: Set[int] = None):
    """Generates the interactive Three.js 3D Force Graph and opens it in the browser."""
    if seed_nodes is None:
        seed_nodes = set()

    nodes_json = []
    colors = ["#00e5ff", "#818cf8", "#a855f7", "#34d399", "#f472b6", "#38bdf8"]

    # Compute communities
    try:
        comms = list(nx.community.greedy_modularity_communities(nx_graph))
        comm_map = {}
        for cid, cset in enumerate(comms):
            for u in cset:
                comm_map[u] = cid
    except Exception:
        comm_map = {}

    for u in nx_graph.nodes():
        deg = nx_graph.degree(u)
        cid = comm_map.get(u, 0)
        nodes_json.append({
            "id": u,
            "degree": deg,
            "is_seed": u in seed_nodes,
            "color": colors[cid % len(colors)],
        })

    links_json = []
    for u, v in nx_graph.edges():
        is_seed_link = (u in seed_nodes) or (v in seed_nodes)
        links_json.append({
            "source": u,
            "target": v,
            "is_active": is_seed_link,
        })

    graph_payload = json.dumps({"nodes": nodes_json, "links": links_json})

    html_content = (
        HTML_TEMPLATE
        .replace("__DATASET_NAME__", dataset_name)
        .replace("__NUM_NODES__", str(nx_graph.number_of_nodes()))
        .replace("__NUM_EDGES__", str(nx_graph.number_of_edges()))
        .replace("__GRAPH_JSON_DATA__", graph_payload)
    )

    out_file = PROJECT_ROOT / "runs" / "knowledge_graph_3d.html"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    webbrowser.open(out_file.as_uri())
    return out_file

