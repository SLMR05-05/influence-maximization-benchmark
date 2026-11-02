# Kịch bản Nghiên cứu – Đánh giá thuật toán Metaheuristic

## Tổng quan
Đây là 7 giao thức cốt lõi cho nền tảng Nghiên cứu Thực nghiệm về việc đánh giá thuật toán metaheuristic. Nền tảng tích hợp Python để quản lý thuật toán và điều phối thử nghiệm, và C++ để tính toán hiệu năng cao với đồ thị và mô phỏng lan truyền.

---

## Giao thức 1 — Quản lý dữ liệu (Dataset Management)

**Mục tiêu:** Chuẩn hoá đồ thị mạng xã hội trước khi đưa vào thuật toán.

### Dữ liệu đầu vào
- Các đồ thị mạng xã hội (danh sách cạnh, ma trận kề, v.v.)

### Các bước xử lý
- Kiểm tra danh sách cạnh: tìm kiếm cạnh trùng, vòng lặp tự liên kết (self‑loop)
- Kiểm tra ID đỉnh và trọng số
- Chuẩn hoá đồ thị có hướng và vô hướng
- Xây dựng ánh xạ ID đỉnh
- Chuyển đổi sang định dạng CSR (Compressed Sparse Row) để C++ xử lý hiệu quả
- Tạo metadata cho dataset (số đỉnh, số cạnh, mật độ, tính hướng, nguồn dữ liệu)

### Kết quả ra
- Một đồ thị đã chuẩn hoá, có thể dùng cho tất cả thuật toán.
- File metadata chứa: hash đồ thị, số đỉnh, số cạnh, tính hướng, nguồn dữ liệu gốc.

### Ghi chú
- Quy trình tiền xử lý không được thay đổi dữ liệu gốc mà không thông báo.
- Mỗi dataset cần có metadata độc lập.
- Dữ liệu và kết quả lớn nên loại bỏ khỏi Git; chỉ lưu cấu hình, metadata, mã nguồn và báo cáo.

---

## Giao thức 2 — Động cơ mô phỏng lan truyền (Diffusion Simulation Engine)

**Mục tiêu:** Tạo một nền tảng đánh giá độc lập, là phần quan trọng nhất của dự án.

### Các mô hình lan truyền được hỗ trợ
| Mô hình | Vai trò |
|--------|--------|
| Independent Cascade (IC) | Mô hình lan truyền chính |
| Linear Threshold (LT) | Kiểm tra khả năng tổng quát (sẽ bổ sung sau) |

### Quy trình
1. **Đồ thị + Tập đỉnh hạt giống** – Tải đồ thị chuẩn hoá và tập đỉnh hạt giống được chọn.
2. **Chọn mô hình lan truyền** – Chọn IC hoặc LT qua cấu hình.
3. **Tải xác suất lan truyền / rãng cắt** – Đọc từ file cấu hình hoặc tính toán từ đồ thị.
4. **Khởi tạo các đỉnh hoạt động** – Đánh dấu các đỉnh hạt giống ban đầu là hoạt động.
5. **Chạy một lần mô phỏng lan truyền** – Lan truyền hoạt động qua mạng.
6. **Đếm số đỉnh hoạt động** – Đếm tổng số đỉnh mà đã được kích hoạt.
7. **C có đủ lần mô phỏng?** – Kiểm tra xem đã thực hiện đủ số lần Monte Carlo được quy định chưa.
8. **Tính trung bình ảnh hưởng lan truyền** – Trung bình của số đỉnh hoạt động trên tất cả các lần mô phỏng.
9. **Trả về giá trị fitness** – In ra giá trị trung bình ảnh hưởng lan truyền.

### Tính năng của động cơ
- Đánh giá một tập đỉnh hạt giống.
- Đánh giá nhiều tập đỉnh hạt giống cùng lúc (batch).
- Tính trung bình ảnh hưởng qua Monte Carlo.
- Ghi nhận số lần mô phỏng thực tế.
- Kiểm soát seed ngẫu nhiên để tái lập.
- Hỗ trợ cả IC và LT qua cấu hình.

### Kết quả ra
- Hàm đánh giá chung có thể gọi bởi tất cả thuật toán.

---

## Giao thức 3 — Phát triển và kiểm thử thuật toán (Algorithm Development)

**Mục tiêu:** Phát triển và kiểm thử từng thuật toán với một hợp đồng chung.

### Hợp đồng chung
| Thành phần | Yêu cầu |
|------------|----------|
| **Input** | Đồ thị, k (số đỉnh hạt giống), evaluator, cấu hình, seed ngẫu nhiên |
| **Processing** | Phương pháp chọn tập đỉnh hạt giống |
| **Output** | Tập đỉnh hạt giống có đúng k phần tử, không trùng lặp |
| **Evaluation** | Giá trị fitness được trả về từ evaluator chung |
| **Tracking** | Thời gian, số lần đánh giá, lịch sử hội tụ |

### Nhóm triển khai

#### A. Heuristic
- **Degree** – Chọn k đỉnh có bậc cao nhất.
- **Degree Discount** – Heuristic đặc biệt cho Influence Maximization.
- **PageRank** – Heuristic dựa trên quan trọng của đỉnh.

#### B. Greedy
- **Greedy / CELF** – Chọn tuần tự các đỉnh có lợi ích biên cao nhất.
  - CELF tối ưu để giảm tính toán lợi ích biên không cần thiết.

#### C. Metaheuristic
- **Discrete PSO** – Tối ưu hoá bầy đàn cho bài toán discrete.
- **ACO** – Tối ưu hoá đàn kiến cho bài toán kết hợp.

#### D. Evolutionary
- **Baseline GA** – Thuật toán di truyền cơ sở.
- **IGA** – Thuật toán di truyền cải tiến (đề xuất).

### Yêu cầu đặc biệt cho IGA
- Tách các cơ chế cải tiến trong IGA thành các thành phần cấu hình độc lập:
  - Khởi tạo quần thể.
  - Lựa chọn.
  - Lai ghép.
  - Đột biến.
  - Duy trì đa dạng.
  - Tiêu chí dừng.
- Cho phép thực hiện **ablation study** để đánh giá đóng góp của từng cải tiến, thay vì chỉ so sánh IGA và GA như hai "hộp đen".

### Kết quả của mỗi thuật toán
- Tập đỉnh hạt giống kích thước k.
- Giá trị fitness từ evaluator chung.
- Lịch sử hội tụ.
- Thông tin thời gian và số lần đánh giá.

---

## Giao thức 4 — Điều phối thử nghiệm (Experiment Runner)

**Mục tiêu:** Điều khiển toàn bộ nghiên cứu dựa trên cấu hình.

### Định nghĩa thử nghiệm
Một thử nghiệm được xác định bởi các tham số:
| Tham số | Ý nghĩa |
|--------|----------|
| Dataset | Đồ thị được dùng |
| Diffusion model | IC hoặc LT |
| Edge probability / threshold | Tham số lan truyền |
| k | Số đỉnh hạt giống |
| Algorithm | Thuật toán cần chạy |
| Population size | Kích thước quần thể (nếu áp dụng) |
| Max iterations | Số vòng lặp tối đa |
| Max evaluations | Ngân sách đánh giá fitness |
| Random seed | Seed RNG cho tính tái lập |
| Repetitions | Số lần chạy độc lập (đối với thuật toán ngẫu nhiên) |

### Quy trình chạy thử nghiệm
1. Tải cấu hình thử nghiệm.
2. Tải dataset.
3. Tải mô hình lan truyền.
4. Chọn các giá trị k.
5. Chọn thuật toán.
6. Thiết lập seed ngẫu nhiên.
7. Thực thi thuật toán.
8. Đánh giá kết quả cuối cùng bằng evaluator chung.
9. Ghi lại thời gian và các chỉ số.
10. Kiểm tra còn thử nghiệm nào không.
11. Hoàn thiện thử nghiệm.

### Ví dụ
Chạy tất cả thuật toán trên 3 dataset, 4 giá trị k, với 30 lần chạy độc lập cho mỗi thuật toán.

### Nguyên tắc quan trọng
- Tất cả các tham số được quản lý qua cấu hình, không cần sửa code để thay đổi kịch bản.
- Mỗi lần chạy phải lưu **tập đỉnh hạt giống** mà thuật toán tìm ra. Điều này cho phép tái kiểm tra, thay đổi số lần mô phỏng Monte Carlo hoặc đánh giá lại bằng mô hình khác mà không cần chạy toàn bộ thuật toán.

### Cấu trúc lưu trữ
```
runs/
└── EXP_001/
    ├── manifest.json
    ├── configurations/experiment_config.yaml
    ├── raw/runs.csv
    ├── raw/seed_sets.jsonl
    ├── raw/convergence.csv
    ├── logs/experiment.log
    ├── logs/errors.log
    ├── summary/algorithm_summary.csv
    ├── summary/statistical_tests.csv
    ├── summary/comparison.csv
    └── figures/
        ├── influence_comparison.png
        ├── runtime_comparison.png
        ├── convergence.png
        └── performance_profile.png
```

### Dữ liệu bắt buộc lưu
- **Xác định**: Experiment ID, dataset, algorithm, run ID
- **Cấu hình**: Diffusion model, k, tham số thuật toán
- **Kết quả**: Best spread, mean spread, spread deviation
- **Hiệu năng**: Search runtime, evaluation runtime, total runtime
- **Chi phí tính toán**: Objective evaluations, diffusion simulations
- **Theo dõi**: Iterations, convergence history
- **Tái lập**: Random seed, graph hash, config hash, Git commit

### Nguyên tắc
- Mỗi lần chạy phải lưu được tập đỉnh hạt giống mà thuật toán tìm ra, để cho phép tái sử dụng, thay đổi số lần mô phỏng Monte Carlo hoặc đánh giá lại bằng mô hình khác mà không cần chạy lại toàn bộ thuật toán.

---

## Giao thức 5 — Quản lý kết quả (Result Management)

**Mục tiêu:** Lưu trữ có khả năng truy xuất ngược các lần chạy thử nghiệm.

### Cấu trúc lưu trữ
```
runs/
└── EXP_001/
    ├── manifest.json
    ├── configurations/
    │   └── experiment_config.yaml
    ├── raw/
    │   ├── runs.csv
    │   ├── seed_sets.jsonl
    │   └── convergence.csv
    ├── logs/
    │   ├── experiment.log
    │   └── errors.log
    ├── summary/
    │   ├── algorithm_summary.csv
    │   ├── statistical_tests.csv
    │   └── comparison.csv
    └── figures/
        ├── influence_comparison.png
        ├── runtime_comparison.png
        ├── convergence.png
        └── performance_profile.png
```

### Các nhóm dữ liệu cần lưu

| Nhóm | Trường dữ liệu |
|------|----------------|
| **Xác định** | Experiment ID, dataset, algorithm, run ID |
| **Cấu hình** | Diffusion model, k, tham số thuật toán |
| **Kết quả** | Best spread, mean spread, spread deviation |
| **Hiệu năng** | Search runtime, evaluation runtime, total runtime |
| **Chi phí tính toán** | Objective evaluations, diffusion simulations |
| **Theo dõi** | Iterations, convergence history |
| **Tái lập** | Random seed, graph hash, config hash, Git commit |

### Yêu cầu đặc biệt
- Mỗi lần chạy phải lưu **tập đỉnh hạt giống** mà thuật toán tìm ra, để cho phép:
  - Kiểm tra lại nghiệm.
  - Thay đổi số lần mô phỏng Monte Carlo.
  - Đánh giá nghiệm bằng mô hình lan truyền khác mà không cần chạy lại thuật toán.

### Lưu trữ
- Dữ liệu thô (CSV, JSONL) để dễ kiểm tra.
- Tóm tắt thống kê trước tính.
- Log để theo dõi lỗi và khắc phục.
- Hình ảnh cho trực quan hóa nhanh.

---

## Giao thức 6 — Phân tích thống kê (Statistical Analysis)

**Mục tiêu:** Tự động tổng hợp kết quả để đưa ra các kết luận khoa học.

### Nhóm phân tích

#### A. So sánh chất lượng nghiệm
- **Best Influence Spread** – Độ lan truyền tốt nhất.
- **Mean Influence Spread** – Trung bình ảnh hưởng.
- **Median Influence Spread** – Trung vị.
- **Standard Deviation** – Độ biến vi.
- **Tỷ lệ kích hoạt** – Tỷ lệ số đỉnh kích hoạt / tổng số đỉnh.

#### B. So sánh hiệu năng
- Thời gian thực thi trung bình.
- Thời gian đánh giá fitness.
- Số lần gọi hàm đánh giá.
- Tổng số mô phỏng lan truyền.
- Sử dụng bộ nhớ (nếu cần).

#### C. Phân tích quá trình hội tụ
Theo dõi giá trị fitness tốt nhất qua:
- Số vòng lặp.
- Số lần đánh giá fitness.
- Thời gian thực thi.
  - Ba cách biểu diễn giúp phân biệt thuật toán nào hội tụ nhanh, nào tốn nhiều tính toán, và nào tìm được nghiệm tốt hơn.

#### D. Kiểm định thống kê
- **Wilcoxon Signed-Rank Test** – So sánh cặp.
- **Friedman Test** – So sánh nhiều thuật toán trên nhiều trường hợp thực nghiệm.
- **Holm correction** – Sửa chữa hậu nghiệm.
- Báo cáo khoảng tin cậy và effect size khi phù hợp.

### Lưu ý quan trọng
- Không chỉ dựa vào giá trị trung bình một lần để rút ra kết luận.
- Phân biệt rõ ràng:
  - **Algorithm repetitions** – Số lần chạy độc lập của thuật toán.
  - **Monte Carlo replications** – Số lần mô phỏng để ước lượng ảnh hưởng.
- Hai đại lượng này hoàn toàn khác nhau.

### Kết quả ra
- Bảng kết quả kiểm định thống kê.
- Khoảng tin cậy, effect size.
- Tổng hợp ý nghĩa thống kê.

---

## Giao thức 7 — Báo cáo nghiên cứu (Research Reporting)

**Mục tiêu:** Tạo ra các nhóm kết quả tự động, phục vụ trực tiếp cho báo cáo nghiên cứu.

### Các nhóm nội dung báo cáo

| Nội dung báo cáo | Dạng đầu ra |
|----------------|-------------|
| Mô tả dataset | Bảng thống kê |
| Cấu hình thử nghiệm | Bảng tham số |
| So sánh chất lượng nghiệm | Bảng và biểu đồ |
| So sánh thời gian | Bảng và biểu đồ |
| Khả năng hội tụ | Biểu đồ hội tụ |
| Kiểm định thống kê | Bảng kiểm định |
| Đánh giá từng cải tiến IGA | Ablation study |
| So sánh trên nhiều k | Bảng và biểu đồ đa trường hợp |

### Cấu trúc báo cáo
1. Thống kê và đặc điểm dataset.
2. Chi tiết cấu hình thử nghiệm (tất cả tham số).
3. So sánh chất lượng nghiệm (bảng + đồ thị).
4. So sánh thời gian/ hiệu năng (bảng + đồ thị).
5. Biểu đồ hội tụ.
6. Kết quả kiểm định thống kê.
7. Phân tích ablation study cho IGA.
8. So sánh hiệu năng trên các giá trị k khác nhau (bảng + đồ thị).

### Đối tượng sử dụng
- Bài báo nghiên cứu, chương trình tesis, báo cáo học bổng – mọi phần được thiết kế để chèn trực tiếp vào tài liệu.

---

## Tóm tắt Kiến trúc và Quy tắc Nghiên cứu

### Nguyên tắc cốt lõi
1. **Cùng dữ liệu, cùng mô hình lan truyền** – Mọi thuật toán nhận cùng một đồ thị và cùng tham số lan truyền.
2. **Chỉ dùng một công cụ đánh giá fitness** – C++ Evaluation Engine duy nhất.
3. **Cân bằng ngân sách tính toán** – Hai chế độ: equal computational budget hoặc native runtime.
4. **Chạy nhiều lần độc lập** – 30+ lần cho thuật toán ngẫu nhiên; 1 lần cho heuristic.
5. **Tách thời gian đo** – Preprocessing, search runtime, validation runtime, và end‑to‑end runtime.
6. **Ablation Study cho IGA** – Tách các cơ chế cải tiến để xem chúng đóng góp gì.

### Quyết định kỹ thuật ban đầu
| Khía cạnh | Quyết định |
|-----------|-----------|
| Ngôn ngữ chính | Python |
| Ngôn ngữ tăng tốc | C++ |
| Python‑C++ binding | pybind11 |
| Hệ thống build | CMake |
| Đại diện đồ thị | CSR |
| Lan truyền chính | Independent Cascade |
| Lan truyền mở rộng | Linear Threshold |
| Đánh giá fitness | Monte Carlo Simulation |
| Thuật toán đề xuất | IGA |
| Thuật toán đối thủ | Degree, Degree Discount, PageRank, CELF, GA, PSO, ACO |
| Định dạng cấu hình | YAML |
| Kết quả thô | CSV, JSONL |
| Phân tích | NumPy, pandas, SciPy |
| Vẽ biểu đồ | Matplotlib |
| Kiểm thử | pytest, CTest |

### Lộ trình triển khai (từ 0 đến 7)

#### Phase 0 — Research Protocol
- Tạo `research_protocol.md` và `experiment_design.md`.
- Xác định bài toán, mô hình lan truyền, dataset, thuật toán, tham số, ngân sách tính toán và tiêu chí đánh giá.

#### Phase 1 — Project Foundation
- Xây dựng workspace, thiết lập môi trường Python, CMake, trình biên dịch C++, pybind11, Git, hệ thống test.
- Kiểm tra module C++ có thể gọi từ Python thành công.

#### Phase 2 — Dataset Management
- Xây dựng Dataset Manager: đọc, xác thực, chuẩn hoá, chuyển đổi sang CSR.
- Tạo metadata cho từng dataset.
- Kết quả: Dataset Manager và Graph Loader.

#### Phase 3 — Diffusion Engine
- Triển khai C++ Evaluation Engine, mô phỏng lan truyền (IC và LT), Monte Carlo.
- Thực hiện unit test để chắc chắn tính đúng đắn.
- Kết quả: C++ Core đã được kiểm thử.

#### Phase 4 — Algorithm Development (theo thứ tự)
1. Degree, Degree Discount, PageRank.
2. Greedy / CELF.
3. Baseline GA.
4. IGA.
5. Discrete PSO và ACO.
- Mỗi thuật toán tuân theo cùng một interface.

#### Phase 5 — Experiment Runner
- Tạo bộ điều phối tự động, hỗ trợ tiếp tục thử nghiệm bị gián đoạn.
- Điều phối dựa trên cấu hình.
- Kết quả: Automated Experiment Runner.

#### Phase 6 — Analysis & Statistics
- Tính Mean, Best, Std, Runtime, Convergence, kiểm định thống kê, vẽ biểu đồ.
- Kết quả: Analysis Engine và Report Generator.

#### Phase 7 — Full Benchmark & Ablation Study
- Chạy thử nghiệm đầy đủ, so sánh các nhóm thuật toán, phân tích từng thành phần cải tiến của IGA.
- Kết quả: Bộ kết quả hoàn chỉnh phục vụ báo cáo nghiên cứu.

---

## Lưu ý cuối cùng
- Kịch bản được thiết kế như một **nền tảng nghiên cứu** (research platform), không phải một chương trình thực hiện một lần. Nó phải dễ mở rộng – chỉ cần thêm module thuật toán mới và đăng ký vào Experiment Runner, không cần sửa code cốt lõi.
- Giai đoạn đầu tiên cần tập trung vào **Research Protocol, Dataset Management và Diffusion Evaluation Engine** làm nền móng vững chắc cho toàn bộ dự án.
- Tương cận **CLI‑first**: ban đầu chỉ cần CLI và cấu hình YAML, không cần giao diện web hay desktop.

---

## Giao thức 8 — Chạy trên Google Colab (tối ưu tốc độ)

Google Colab cung cấp máy ảo miễn phí với CPU cao cấp (khoảng 12 luồng) và GPU tùy chọn (Tesla T4 / A100 tùy phiên bản), phù hợp để chạy các mô phỏng Monte Carlo lớn trên C++ Core. Bạn có thể dùng Colab làm môi trường chạy thử nghiệm thứ hai, song song với máy chủ WSL2 cục bộ.

### 8.1. Lưu ý quan trọng khi so sánh thời gian trên Colab
- **Không trộn kết quả đo thời gian giữa WSL2 và Colab** vào cùng một bảng báo cáo. Colab chia sẻ tài nguyên CPU với các người dùng khác, thời gian thực thi có độ dao động cao.
- Chỉ dùng Colab để chạy các mô phỏng Monte Carlo nhiều lượt (ví dụ $R_{val} = 10.000$), hoặc để làm quick‑test các thuật toán trước khi chạy chính thức trên WSL2.
- Nếu cần báo cáo thời gian chính thống, hãy chỉ đo trên WSL2 cục bur theo `experimental_environment.md`.

### 8.2. Cấu hình Colab (Notebook)

#### Bước 1: Mount Google Drive
```python
from google.colab import drive
drive.mount('/content/drive')
```
Workspace trên Colab: `/content/drive/MyDrive/IM-Metaheuristic-Research/`

#### Bước 2: Cài đặt công cụ build C++ và pybind11
```bash
!apt-get update -y && apt-get install -y build-essential cmake libboost-all-dev
!pip install pybind11[global] numpy pandas scipy matplotlib pyyaml networkx
```

#### Bước 3: Biên dịch C++ Core trên Colab
```bash
%cd /content/drive/MyDrive/IM-Metaheuristic-Research/cpp_core
!mkdir -p build && cd build
!cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-O3 -march=native -fopenmp"
!make -j$(nproc)
```
**Lưu ý:** Cờ `-march=native` trên Colab sẽ tối ưu theo CPU mà Google cung cấp (thường là Intel Xeon hoặc AMD EPYC), không phải Zen 3 như máy cục bộ.

#### Bước 4: Kiểm tra import từ Python
```python
import sys
sys.path.append('/content/drive/MyDrive/IM-Metaheuristic-Research/cpp_core/build')
import im_core  # module pybind11 đã biên dịch
print(dir(im_core))
```

### 8.3. Điều chỉnh các giao thức để chạy trên Colab

| Giao thức | Điều chỉnh trên Colab |
|-----------|----------------------|
| **GPT 1 Dataset Management** | Tải dữ liệu thô từ Google Drive hoặc GitHub, chuẩn hóa và lưu CSR vào Drive. |
| **GPT 2 Diffusion Engine** | Chạy Monte Carlo nhiều lượt trên C++ Core, tận dụng số luồng CPU cao của Colab. |
| **GPT 3 Algorithm Development** | Chạy các thuật toán Python thông qua notebook, gọi C++ evaluator qua pybind11. |
| **GPT 4 Experiment Runner** | Chạy theo từng batch, lưu kết quả vào `runs/` trên Drive. |
| **GPT 5-7 Result Management & Analysis** | Tải dữ liệu về máy cục bộ hoặc lưu vào Drive để phân tích, vẽ biểu đồ bằng matplotlib. |

### 8.4. Quy trình đề xuất kết hợp Colab + WSL2

1. **Phát triển & debug:** Chạy trên WSL2 cục bộ (WSL2 + Ubuntu 24.04), kiểm tra tính đúng đắn với dataset nhỏ (Karate, Dolphins).
2. **Chạy thử nghiệm lớn:** Đẩy code lên Google Colab, sử dụng bộ nhớ và CPU cao hơn để chạy Monte Carlo $10.000$ lượt trên dataset lớn (Email-Enron, NetHEPT).
3. **Tổng hợp & báo cáo:** Tải kết quả về máy cục bộ, phân tích thống kê và vẽ biểu đồ cuối cùng.

---

## Bổ sung chi tiết môi trường thực nghiệm từ `docs/experimental_environment.md`

### Các bộ dữ liệu chuẩn (5 dataset)
| Dataset | Số đỉnh ($n$) | Số cạnh ($m$) | Loại | Nguồn |
|---------|--------------|--------------|------|-------|
| Karate Club | 34 | 78 | Mạng xã hội nhỏ | Zachary (1977) |
| Dolphins | 62 | 159 | Mạng quan hệ xã hội | Lusseau (2003) |
| ego-Facebook | 4.039 | 88.234 | Mạng xã hội trực tuyến | SNAP |
| NetHEPT | 15.233 | 58.891 | Mạng đồng tác giả học thuật | arXiv / SNAP |
| Email-Enron | 36.692 | 183.831 | Mạng thư điện tử | SNAP |

### Giá trị $k$ đề xuất
$k \in \{5, 10, 15, 20, 25, 30, 40, 50\}$

### Số lần chạy độc lập
- Thuật toán ngẫu nhiên (GA, IGA, PSO, ACO): **30 lần** mỗi cấu hình.
- Heuristic (Degree, PageRank, Degree Discount): Chạy 1 lần (kết quả xác định).

### Phương pháp gán xác suất cạnh
1. **Weighted Cascade (WC):** $p(u,v) = 1/d_{in}(v)$ — khuyến nghị mặc định.
2. **Trivalency (TR):** $p(u,v) \in \{0.1, 0.01, 0.001\}$.
3. **Uniform:** Xác suất cố định (ví dụ $0.01$ hoặc $0.05$).

### Mô phỏng Monte Carlo
- **Search worlds:** $R_{search} = 100 \sim 200$ lượt (dùng trong quá trình tối ưu).
- **Validation worlds:** $R_{val} = 10.000$ lượt (dùng để đánh giá nghiệm cuối cùng, công bằng cho tất cả thuật toán).
