# IM-Benchmark-Lab — Influence Maximization Benchmark Laboratory

Hệ thống nghiên cứu và so sánh thuật toán Metaheuristic cho bài toán Influence Maximization (IM) trên mạng xã hội.

---

## 1. Yêu cầu hệ thống

| Thành phần | Yêu cầu |
|-----------|---------|
| **Python** | 3.12+ (khuyên dùng 3.12) |
| **C++ Compiler** | g++ 13+ (WSL2 Ubuntu 24.04) hoặc MSVC (Windows) |
| **CMake** | 3.28+ |
| **pybind11** | v2.12+ |
| **RAM** | 8 GB+ (khuyên dùng 16 GB) |
| **OS** | Windows 11 + WSL2 Ubuntu 24.04 (để đo thời gian chuẩn) |

---

## 2. Cấu trúc dự án

```
IM-Metaheuristic-Research/
├── README.md
├── pyproject.toml
├── CMakeLists.txt
├── .gitignore
├── docs/
│   ├── design_rules.md          # Quy tắc thiết kế GUI
│   ├── experimental_environment.md
│   └── workflows.md
├── cpp_core/                    # C++ core (pybind11)
│   ├── include/im_core/
│   ├── src/
│   └── bindings/
├── src/im_research/             # Python layer
│   ├── core/                    # problem, solution, interfaces, theme_config
│   ├── algorithms/              # heuristics, greedy, metaheuristics, evolutionary
│   ├── evaluation/              # evaluator, fitness, metrics
│   ├── experiments/             # runner, scheduler, logger
│   ├── analysis/                # statistics, comparison, visualization
│   └── gui/                     # Desktop GUI (CustomTkinter)
├── configs/                     # YAML configurations
├── data/                        # Datasets & SQLite config
├── runs/                        # Experiment results (generated)
└── tests/                       # Unit & integration tests
```

---

## 3. Cài đặt

### 3.1. Python environment

**Trên WSL2 (Ubuntu) — Khuyến nghị:**
```bash
# Tạo venv Linux (một lần, nằm ở ~/im_env — không bị reset khi tắt WSL2)
python3 -m venv ~/im_env
source ~/im_env/bin/activate

# Cài đặt đầy đủ
pip install --upgrade pip
pip install -r /mnt/d/Khanh/Đồ\ án\ chuyên\ ngành/requirements.txt
```

**Trên Windows (PowerShell) — Chỉ dùng cho GUI nếu không có WSL2:**
```powershell
python -m venv im_env
.\im_env\Scripts\activate
pip install -r requirements.txt
```

### 3.2. Build C++ Core (WSL2 — khuyến nghị)

```bash
cd /mnt/d/Khanh/Đồ\ án\ chuyên\ ngành
mkdir -p cpp_core/build && cd cpp_core/build
cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-O3 -march=native -fopenmp"
make -j$(nproc)
```

Kiểm tra:
```bash
python -c "import sys; sys.path.insert(0,'cpp_core/build'); import im_core; print('C++ bind OK')"
```

### 3.3. Build C++ Core (Windows — dùng MSYS2)

Nếu không có WSL2, cài MSYS2 rồi:
```bash
pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake mingw-w64-x86_64-pybind11
```
Sau đó build tương tự trên PowerShell.

---

## 4. Chạy dự án

### 4.1. Chạy GUI Desktop (WSL2 — Khuyến nghị)

```bash
# Mở WSL2 Ubuntu
wsl -d Ubuntu

# Kích hoạt venv Linux
source ~/im_env/bin/activate

# Vào workspace
cd /mnt/d/Khanh/Đồ\ án\ chuyên\ ngành

# Chạy GUI (CustomTkinter với WSLg)
# main_app.py tự động redirect đến IMApp (app.py)
PYTHONPATH="/mnt/d/Khanh/Đồ án chuyên ngành/src" python src/im_research/gui/main_app.py
```

**Tạo alias shortcut (chỉ cần gõ `imlab`):**
```bash
echo "alias imlab='source ~/im_env/bin/activate && cd /mnt/d/Khanh/Đồ\ án\ chuyên\ ngành && PYTHONPATH=\"/mnt/d/Khanh/Đồ án chuyên ngành/src\" python src/im_research/gui/main_app.py'" >> ~/.bashrc
source ~/.bashrc
# Sau đó chỉ cần gõ: imlab
```

> **Lưu ý:** `main_app.py` là entry point chính, tự động redirect đến `IMApp` (trong `app.py`). Không cần sửa file nào.

### 4.1b. Chạy GUI Desktop (Windows PowerShell — Nếu không có WSL2)

```powershell
cd "D:\Khanh\Đồ án chuyên ngành"
python src/im_research/gui/main_app.py
```

- Giao diện hiện đại với Dark/Light mode (lưu trong `data/config.db`)
- 9 tab: Dashboard, Dataset Manager, Graph Explorer, Algorithm Library, Experiment Setup, Experiment Monitor, Result Analysis, Ablation Study, Research Reports

### 4.2. Chạy Unit Tests

```bash
# Windows
python -m pytest tests/unit/ -v

# WSL2
source ~/im_env/bin/activate
python -m pytest tests/unit/ -v
```

### 4.3. Chạy Experiment (CLI)

```bash
python -m im_research.cli.main --config configs/experiments/benchmark_small.yaml
```

---

## 5. Lưu ý quan trọng

| Vấn đề | Giải pháp |
|--------|-----------|
| `ModuleNotFoundError: No module named 'im_research'` | Thêm `PYTHONPATH="src:$PYTHONPATH"` hoặc chạy `python src/im_research/gui/main_app.py` |
| `g++ not found` trên Windows | Dùng WSL2 hoặc cài MSYS2 |
| `customtkinter not found` | `python -m pip install customtkinter` |
| Thời gian đo không chính xác | Chỉ đo trên WSL2, không trộn với Windows |
| GUI block khi chạy experiment | Chạy async, không block main thread |

---

## 6. Môi trường chuẩn (WSL2)

Theo `docs/experimental_environment.md`:
- **CPU**: AMD Ryzen 5 7430U (6C/12T)
- **RAM**: 16 GB (WSL2 cấp ~6.85 GB)
- **OS**: Ubuntu 24.04 LTS trên WSL2
- **Compiler**: g++ 13.3.0, CMake 3.28.3
- **Python**: 3.12.3 trong venv `~/im_env`

---

## 7. Quy trình nghiên cứu (7 giao thức)

1. **Dataset Management** — Tải, chuẩn hóa, CSR format
2. **Diffusion Engine** — IC (Independent Cascade) Monte Carlo, cấu hình p/MC/seed trong GUI (C++ core); LT trong lộ trình mở rộng
3. **Algorithm Development** — Heuristic / Greedy / GA / IGA / PSO / ACO
4. **Experiment Runner** — Chạy hàng loạt theo config
5. **Result Management** — Lưu trữ CSV/JSONL trong `runs/`
6. **Statistical Analysis** — Wilcoxon / Friedman / Holm
7. **Research Reporting** — Xuất CSV / PDF / Figures

---

## 8. License

MIT License — see LICENSE file for details.
