# Hướng dẫn chạy dự án (Execution Guide)

## Luồng chạy từ End-User

### Bước 1: Chuẩn bị môi trường

```bash
# Mở WSL2 Ubuntu
wsl -d Ubuntu

# Kích hoạt venv Linux
source ~/im_env/bin/activate

# Vào workspace
cd /mnt/d/Khanh/Đồ\ án\ chuyên\ ngành
```

### Bước 2: Chạy GUI Desktop (khuyến nghị)

```bash
PYTHONPATH="/mnt/d/Khanh/Đồ án chuyên ngành/src" python src/im_research/gui/main_app.py
```

Hoặc dùng alias (sau khi tạo một lần):
```bash
imlab
```

Giao diện sẽ mở với 7 tab: Dashboard, Results, Comparison, Datasets, Experiments, Reports, Settings.

### Bước 3: Chạy Experiment qua CLI

```bash
python -m im_research.experiments.runner \
    --dataset "Karate Club" \
    --model IC \
    --k 10 \
    --mc 200 \
    --mc_val 1000 \
    --runs 5 \
    --algo celf --algo ga --algo degree --algo pagerank --algo degree_discount
```

**Tham số:**
| Tham số | Mô tả | Mặc định |
|---------|-------|----------|
| `--dataset` | Tên dataset (Karate Club, Dolphins, ego-Facebook, NetHEPT, Email-Enron) | Karate Club |
| `--model` | Mô hình lan truyền (IC hoặc LT) | IC |
| `--k` | Số đỉnh hạt giống | 10 |
| `--mc` | Số lần MC cho search | 200 |
| `--mc_val` | Số lần MC cho validation | 1000 |
| `--runs` | Số lần chạy độc lập | 1 |
| `--algo` | Thuật toán (có thể lặp lại) | celf, ga, degree_discount, pagerank, degree |
| `--out_dir` | Thư mục lưu kết quả | runs/EXP_<timestamp> |

### Bước 4: Chạy Unit Tests

```bash
python -m pytest tests/unit/ -v
```

### Bước 5: Build C++ Core (nếu cần)

```bash
cd cpp_core/build
cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-O3 -march=native -fopenmp"
make -j$(nproc)
```

---

## Luồng chạy chi tiết (End-to-End)

```
1. User mở GUI (main_app.py → IMApp)
   ↓
2. Chọn Dataset (tab Datasets) → Load đồ thị từ data/
   ↓
3. Chọn Experiment (tab Experiments) → Cấu hình k, model, mc, runs, algos
   ↓
4. Bấm "Khởi chạy" → GUI gọi WSL2 backend (subprocess)
   ↓
5. Backend (runner.py) → Load graph → Setup C++ Evaluator → Run algorithms
   ↓
6. Mỗi algorithm → run() → C++ MC simulation → fitness score
   ↓
7. Validation → val_problem.fitness() với R_val=10000
   ↓
8. Lưu kết quả → runs/EXP_<timestamp>/summary.json + latest_results.json
   ↓
9. GUI đọc latest_results.json → Hiển thị trong tab Results/Comparison
   ↓
10. Export → CSV / PDF / PNG / LaTeX (tab Reports)
```

---

## Cấu trúc thư mục kết quả

```
runs/
└── EXP_20261103_120000/
    ├── summary.json          # Tổng hợp kết quả
    ├── detailed_results.json # Chi tiết từng run
    └── convergence.csv       # Lịch sử hội tụ
runs/
└── latest_results.json        # Kết quả mới nhất (GUI đọc)
```

---

## Lưu ý quan trọng

- **GUI chạy trên Windows** (CustomTkinter), **Backend chạy trong WSL2** (C++ core)
- GUI gọi backend qua `wsl -d Ubuntu -e bash -c "..."`
- Thời gian đo phải thực hiện trong WSL2 để chính xác
- Venv Linux tại `~/im_env` (không bị reset khi tắt WSL2)
- Cờ biên dịch: `-O3 -march=native -fopenmp` (tối ưu cho CPU hiện tại)
