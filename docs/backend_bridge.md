# Backend Bridge — Windows GUI ↔ WSL2 C++ Backend

## Kiến trúc

```
┌─────────────────────┐                    ┌─────────────────────────┐
│  Windows GUI        │   write config      │  WSL2 Backend           │
│  (CustomTkinter)    │ ──────────────────► │  (Python + C++ core)   │
│                     │   subprocess call   │                         │
│                     │ ◄────────────────── │  Monte Carlo / GA / IGA │
│                     │   read results      │  (g++ -O3 -march=native) │
└─────────────────────┘                    └─────────────────────────┘
```

## Cách hoạt động

1. **GUI (Windows)**: Người dùng chọn dataset, thuật toán, tham số → Ghi file `config.json` vào workspace chung (Windows path: `D:\Khanh\Đồ án chuyên ngành\runs\temp\config.json`)
2. **WSL2 Backend**: GUI gọi `wsl -d Ubuntu -e bash -c "cd /mnt/d/... && python backend_runner.py"` → Backend đọc config, chạy C++ core, ghi kết quả vào `results.json`
3. **GUI (Windows)**: Đọc `results.json` và hiển thị biểu đồ/bảng

## Implementation

### 1. Tạo Backend Runner (`backend/backend_runner.py`)

```python
#!/usr/bin/env python3
"""WSL2 Backend Runner — Called by Windows GUI via subprocess."""
import sys, os, json
sys.path.insert(0, "/mnt/d/Khanh/Đồ án chuyên ngành/src")

from im_research.core.problem import Problem
from im_research.evaluation.evaluator import Evaluator
# ... load algorithms

def main(config_path, result_path):
    with open(config_path) as f:
        config = json.load(f)

    # Build graph, run algorithms, save results
    results = run_experiment(config)
    with open(result_path, "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
```

### 2. Windows GUI Bridge (`src/im_research/gui/backend_bridge.py`)

```python
import subprocess, json, os, threading

WORKSPACE = r"D:\Khanh\Đồ án chuyên ngành"
WSL_PATH = "/mnt/d/Khanh/Đồ án chuyên ngành"

def run_backend(config: dict, callback=None):
    """Run C++ backend in WSL2 from Windows GUI."""
    # Write config to shared workspace
    config_path = os.path.join(WORKSPACE, "runs", "temp", "config.json")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f)

    result_path = os.path.join(WORKSPACE, "runs", "temp", "result.json")

    # Call WSL2 backend
    cmd = [
        "wsl", "-d", "Ubuntu", "-e", "bash", "-c",
        f'cd "{WSL_PATH}" && PYTHONPATH="{WSL_PATH}/src:$PYTHONPATH" python3 backend/backend_runner.py "{WSL_PATH}/runs/temp/config.json" "{WSL_PATH}/runs/temp/result.json"'
    ]

    def worker():
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode == 0:
            with open(result_path) as f:
                results = json.load(f)
            if callback:
                callback(results)
        else:
            if callback:
                callback({"error": stderr.decode()})

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread
```

### 3. C++ Core trong WSL2

C++ core (`_im_core.so`) phải được build trong WSL2:
```bash
# Trong WSL2
cd /mnt/d/Khanh/Đồ án chuyên ngành/cpp_core/build
cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-O3 -march=native -fopenmp"
make -j$(nproc)
```

Windows GUI chỉ import `_im_core.pyd` (nếu có Windows build) hoặc gọi qua WSL2 backend.

---

## Cách chạy

### Bước 1: Build C++ trong WSL2
```bash
wsl -d Ubuntu
cd /mnt/d/Khanh/Đồ\ án\ chuyên\ ngành/cpp_core/build
cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)
```

### Bước 2: Chạy GUI trên Windows
```powershell
cd "D:\Khanh\Đồ án chuyên ngành"
python src/im_research/gui/main_app.py
```

### Bước 3: GUI tự động gọi WSL2 backend
Khi bấm "Run Experiment" trong GUI, nó sẽ:
1. Ghi config vào `runs/temp/config.json`
2. Gọi `wsl -d Ubuntu -e bash -c "..."`
3. Backend đọc config, chạy C++ core, ghi `results.json`
4. GUI đọc kết quả và hiển thị

---

## Lưu ý

- **Không import `_im_core.so` trực tiếp từ Windows Python** — file `.so` là Linux binary, Windows không load được
- GUI Windows chỉ dùng để **hiển thị** và **gọi subprocess** vào WSL2
- Tất cả tính toán nặng (Monte Carlo, GA/IGA) chạy trong WSL2 với `-O3 -march=native -fopenmp`
- Thời gian đo phải thực hiện trong WSL2 (không đo từ Windows subprocess)
- File giao tiếp qua `runs/temp/` (shared folder giữa Windows và WSL2)
