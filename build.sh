#!/usr/bin/env bash
set -e

echo "=== Building IM Research C++ Core & Pybind11 Bindings ==="
mkdir -p build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
echo "=== Build completed successfully! ==="

