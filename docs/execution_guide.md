# Hướng Dẫn Vận Hành Nền Tảng (Execution Guide)

Hệ thống được thiết kế theo kiến trúc lai **Python + C++** lấy cảm hứng từ thư viện [ESA pygmo2](https://github.com/esa/pygmo2):
* **C++ Core (`cpp_core/`):** Xử lý đồ thị CSR, mô phỏng lan truyền Monte Carlo Independent Cascade (IC) song song qua OpenMP.
* **Python Layer (`src/im_research/`):** Điều phối thuật toán, bài toán (`IMProblem`), quần thể (`Population`), thống kê và vẽ biểu đồ.
* **Môi trường thực thi chuẩn:** Ubuntu 24.04 LTS trên WSL2.

---

## 1. Cài đặt môi trường (Chỉ cần chạy 1 lần đầu)

Từ terminal PowerShell trên Windows (hoặc terminal WSL), chạy script thiết lập tự động:

```bash
# Lệnh chạy từ Windows PowerShell:
wsl -d Ubuntu --cd "D:\Khanh\Đồ án chuyên ngành" -- bash setup_env.sh
```

Script này sẽ tự động:
1. Tạo môi trường ảo Python `.venv` bên trong WSL.
2. Cài đặt các thư viện: `numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `pytest`, `networkx`, `tqdm`.
3. Biên dịch C++ Core và liên kết pybind11 module `_im_core` ở chế độ **Release** (`-O3 -march=native -fopenmp`).
4. Cài đặt gói `im_research` ở chế độ editable (`pip install -e .`).

---

## 2. Cách chạy thử nghiệm mẫu (Demo Run)

Sau khi cài đặt xong, bạn có thể chạy file demo mẫu tại `examples/demo_run.py`:

### Cách 1: Chạy trực tiếp từ Windows PowerShell
```powershell
wsl -d Ubuntu --cd "D:\Khanh\Đồ án chuyên ngành" -- .venv/bin/python examples/demo_run.py
```

### Cách 2: Chạy bên trong Terminal WSL2 (Ubuntu)
```bash
cd "/mnt/d/Khanh/Đồ án chuyên ngành"
source .venv/bin/activate
python examples/demo_run.py
```

---

## 3. Cách chạy kiểm thử tự động (Unit Tests)

Để kiểm tra tính đúng đắn của C++ Core, cấu trúc đồ thị CSR và cơ chế đánh giá OpenMP:

```powershell
wsl -d Ubuntu --cd "D:\Khanh\Đồ án chuyên ngành" -- .venv/bin/python tests/unit/test_cpp_core.py
```

Hoặc dùng `pytest`:
```powershell
wsl -d Ubuntu --cd "D:\Khanh\Đồ án chuyên ngành" -- .venv/bin/pytest tests/
```

---

## 4. Biên dịch lại C++ khi chỉnh sửa mã nguồn C++

Mỗi khi bạn thêm tính năng hoặc chỉnh sửa code trong thư mục `cpp_core/`:
```powershell
wsl -d Ubuntu --cd "D:\Khanh\Đồ án chuyên ngành" -- bash build.sh
```
File thư viện động `.so` mới sẽ được tự động biên dịch và đặt thẳng vào `src/im_research/` để Python gọi trực tiếp.

