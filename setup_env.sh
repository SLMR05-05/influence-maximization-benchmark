#!/usr/bin/env bash
set -e

echo "=== Setting up Python Virtual Environment in WSL2 ==="
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install numpy scipy pandas matplotlib seaborn pyyaml networkx tqdm pytest psutil

echo "=== Building C++ Core with CMake ==="
bash build.sh

echo "=== Installing im_research in editable mode ==="
pip install -e . --no-build-isolation

echo "=== All dependencies and C++ extensions installed! ==="

