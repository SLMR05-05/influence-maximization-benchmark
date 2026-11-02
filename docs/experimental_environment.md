# Thiết Lập Môi Trường Thực Nghiệm (Experimental Environment Specification)

> **Dự án:** Nền tảng thực nghiệm và so sánh các thuật toán Metaheuristic cho bài toán Tối đa hóa tầm ảnh hưởng (Influence Maximization - IM)  
> **Thuật toán đề xuất:** Improved Genetic Algorithm (IGA)  
> **Môi trường thực thi chuẩn:** Ubuntu 24.04 LTS trên nền tảng WSL2 (Windows Subsystem for Linux)  
> **Ngày lập cấu hình:** Tháng 11/2026  

---

## 1. Cấu hình Phần cứng và Hệ điều hành (Hardware & OS Configuration)

Nhằm đảm bảo tính công bằng và khả năng tái lập (reproducibility) của các phép đo thời gian chạy (execution time / CPU time), toàn bộ các thực nghiệm và benchmark sẽ được thực thi thống nhất trên một môi trường phần cứng và hệ điều hành cố định:

### 1.1. Phần cứng máy chủ vật lý (Host Machine)
* **Bộ vi xử lý (CPU):** AMD Ryzen 5 7430U with Radeon Graphics
  * Kiến trúc: Zen 3 (x86_64)
  * Số nhân / Số luồng: 6 Cores / 12 Threads
  * Xung nhịp: Base 2.3 GHz, Boost tối đa 4.3 GHz
* **Bộ nhớ RAM vật lý:** 16 GB DDR4 (13.84 GB khả dụng)
* **Hệ điều hành Host:** Microsoft Windows 11 Home Single Language (Build 26200)

### 1.2. Môi trường thực thi thực nghiệm (Target Research Environment - WSL2)
* **Nền tảng ảo hóa:** WSL2 (Windows Subsystem for Linux 2)
* **Phân phối Linux (Distro):** Ubuntu 24.04.3 LTS (Noble Numbat)
* **Nhân hệ điều hành (Kernel):** Linux 6.6.87.2-microsoft-standard-WSL2 x86_64
* **Tài nguyên cấp phát cho WSL2:**
  * RAM khả dụng: ~6.85 GB (có thể cấu hình tăng trong file `.wslconfig` nếu cần)
  * Số luồng CPU: Cấp phát toàn bộ 12 luồng tính toán
* **Ánh xạ đường dẫn (Workspace Path):**
  * Windows path: `D:\Khanh\Đồ án chuyên ngành`
  * WSL2 path: `/mnt/d/Khanh/Đồ án chuyên ngành`

---

## 2. Ngôn ngữ Lập trình và Thư viện Sử dụng (Software Stack)

Hệ thống được thiết kế theo kiến trúc lai **Python + C++**:
* **C++ Core:** Đóng vai trò là cỗ máy tính toán hiệu năng cao (xử lý cấu trúc đồ thị, mô phỏng lan truyền Monte Carlo).
* **Python Layer:** Đóng vai trò điều phối logic thuật toán, quản lý bộ thí nghiệm, thống kê dữ liệu và trực quan hóa kết quả.

```
+-------------------------------------------------------------+
|                     Python Layer (High-Level)               |
|   - Algorithm Orchestration (GA, IGA, PSO, ACO, Heuristics) |
|   - Experiment Runner, Configs, Logs, Results Management    |
|   - Statistical Analysis (SciPy), Plotting (Matplotlib)     |
+-------------------------------------------------------------+
                              |
                     pybind11 Binding API
                              |
+-------------------------------------------------------------+
|                     C++ Core (Low-Level)                    |
|   - CSR Graph Representation (Cache-Friendly)               |
|   - Monte Carlo Simulation Engine (IC / LT)                 |
|   - Batch Solution Evaluator (Parallelized with OpenMP)     |
+-------------------------------------------------------------+
```

### 2.1. Tầng tính toán C++ (Computation Core)
* **Chuẩn ngôn ngữ:** C++17 (hoặc C++20)
* **Trình biên dịch:** GNU Compiler Collection `g++` (phiên bản 13.x trên Ubuntu 24.04)
* **Chế độ biên dịch (Compilation Flags):** 
  * `-O3` (Tối ưu hóa mã máy tối đa)
  * `-march=native` (Tối ưu riêng cho vi kiến trúc Zen 3 của Ryzen 5 7430U)
  * `-fopenmp` (Song song hóa đa luồng trên CPU)
  * `-Wall -Wextra` (Cảnh báo lỗi nghiêm ngặt)
* **Hệ thống Build:** CMake (phiên bản 3.28+)
* **Cầu nối Python - C++:** `pybind11` (v2.12+)

### 2.2. Tầng điều phối và phân tích Python (Algorithm & Analysis Layer)
* **Phiên bản Python:** Python 3.12+ (trên môi trường ảo `venv` của Ubuntu)
* **Các thư viện chính:**
  * **Khoa học dữ liệu & Tính toán số:** `numpy` (>= 1.26.0), `pandas` (>= 2.2.0)
  * **Kiểm định thống kê:** `scipy` (>= 1.12.0) - Cung cấp Wilcoxon Signed-Rank Test, Friedman Test, Holm-Bonferroni correction
  * **Trực quan hóa đồ thị & kết quả:** `matplotlib` (>= 3.8.0), `seaborn` (>= 0.13.0)
  * **Quản lý cấu hình:** `pyyaml` (>= 6.0)
  * **Hỗ trợ tiền xử lý đồ thị:** `networkx` (>= 3.2)
  * **Kiểm thử tự động:** `pytest` (>= 8.0.0)

---

## 3. Các Bộ Dữ Liệu Thực Nghiệm Chuẩn (Standard Benchmark Datasets)

Để kiểm chứng tính tổng quát của IGA và các thuật toán đối chứng, hệ thống chốt cố định **5 bộ dữ liệu đồ thị mạng xã hội chuẩn mực** đại diện cho các quy mô và đặc trưng cấu trúc tô-pô mạng khác nhau:

| Bộ dữ liệu đồ thị | Số lượng đỉnh ($n$) | Số lượng cạnh ($m$) | Bậc trung bình ($\langle k \rangle$) | Hệ số gom cụm ($C$) | Đường kính mạng ($D$) | Phân loại đồ thị | Nguồn dữ liệu |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **Karate Club** | 34 | 78 | 4,59 | 0,571 | 5 | Mạng xã hội nhỏ | Zachary (1977) |
| **Dolphins** | 62 | 159 | 5,13 | 0,259 | 8 | Mạng quan hệ xã hội | Lusseau (2003) |
| **ego-Facebook** | 4.039 | 88.234 | 43,69 | 0,605 | 8 | Mạng xã hội trực tuyến | SNAP [8] |
| **NetHEPT** | 15.233 | 58.891 | 7,73 | 0,659 | 15 | Mạng đồng tác giả học thuật | arXiv / SNAP [15] |
| **Email-Enron** | 36.692 | 183.831 | 10,02 | 0,497 | 11 | Mạng truyền thông thư điện tử | SNAP [8] |

### Ý nghĩa lựa chọn 5 bộ dữ liệu trong nghiên cứu:
1. **Karate Club & Dolphins:** Đồ thị quy mô nhỏ ($n < 100$), cho phép chạy brute-force / so sánh chi tiết từng cá thể, kiểm tra tính đúng đắn và tốc độ hội tụ của thuật toán trong giai đoạn phát triển và unit testing.
2. **ego-Facebook:** Đồ thị mạng xã hội trực tuyến thực tế với hệ số gom cụm rất cao ($C = 0,605$) và bậc trung bình lớn ($\langle k \rangle = 43,69$), là bài test lý tưởng để kiểm chứng cơ chế khởi tạo dựa trên cấu trúc cộng đồng của IGA.
3. **NetHEPT:** Đồ thị mạng cộng tác học thuật kinh điển, được sử dụng làm chuẩn mực trong hầu hết các công trình nghiên cứu về bài toán Influence Maximization (Kempe et al., Chen et al.).
4. **Email-Enron:** Đồ thị quy mô lớn ($n \approx 37.000$, $m \approx 184.000$), đường kính mạng $D = 11$, dùng để đánh giá khả năng mở rộng (scalability) và hiệu năng tính toán của C++ Core khi số lượng đỉnh tăng cao.

### Thiết lập kích thước tập hạt giống $k$:
* Thử nghiệm trên dải giá trị chuẩn: $k \in \{5, 10, 15, 20, 25, 30, 40, 50\}$.
* Với mỗi giá trị $k$, các thuật toán ngẫu nhiên (GA, IGA, PSO, ACO) sẽ chạy độc lập **$30$ lần** với các random seed khác nhau để đảm bảo ý nghĩa thống kê.

---

## 4. Tiền Xử Lý Dữ Liệu Đồ Thị (Graph Preprocessing)

Trước khi chuyển dữ liệu cho C++ Core xử lý, toàn bộ đồ thị thô (Raw Edge List) phải trải qua quy trình chuẩn hóa nghiêm ngặt:

```
[Raw Graph File]
       │
       ▼
 1. Kiểm tra & Loại bỏ Self-loops (u == v)
       │
       ▼
 2. Loại bỏ Duplicate edges (Cạnh song song)
       │
       ▼
 3. Chuẩn hóa ID Đỉnh: Ánh xạ tập V ngẫu nhiên về {0, 1, 2, ..., |V|-1}
    (Lưu file mapping.json để phục vụ truy vết ngược)
       │
       ▼
 4. Chuẩn hóa Hướng: Nếu vô hướng, tự động sinh 2 cung (u, v) và (v, u)
       │
       ▼
 5. Gán xác suất lan truyền p(u, v) theo mô hình đã định cấu hình
       │
       ▼
 6. Đóng gói sang cấu trúc CSR (Compressed Sparse Row) và lưu nhị phân
       │
       ▼
 7. Xuất file Metadata (.json: |V|, |E|, density, sha256 checksum)
```

### Cấu trúc lưu trữ Compressed Sparse Row (CSR) trong C++:
Thay vì dùng ma trận kề (gây tốn bộ nhớ $O(|V|^2)$) hoặc danh sách kề qua `std::vector<std::vector<int>>` (phân mảnh bộ nhớ cache), C++ Core sử dụng cấu trúc CSR gồm các mảng phẳng 1 chiều:
* `row_ptr`: Mảng số nguyên kích thước $|V| + 1$, lưu chỉ số bắt đầu của danh sách hàng xóm của từng đỉnh.
* `col_indices`: Mảng số nguyên kích thước $|E|$, lưu liên tiếp ID của các đỉnh láng giềng.
* `edge_probs`: Mảng số thực `float` kích thước $|E|$, lưu xác suất lan truyền tương ứng của từng cạnh.

---

## 5. Mô Hình Lan Truyền & Phương Pháp Thiết Lập Xác Suất Cạnh

### 5.1. Các mô hình lan truyền (Diffusion Models)
1. **Independent Cascade (IC) - Mô hình chính:**
   * Ban đầu, chỉ có tập đỉnh hạt giống $S$ ở trạng thái kích hoạt (Active) tại bước $t = 0$.
   * Tại mỗi bước $t \ge 1$, một đỉnh $u$ mới được kích hoạt ở bước $t-1$ có **duy nhất 1 cơ hội** kích hoạt từng láng giềng chưa kích hoạt $v$ với xác suất $p(u, v)$.
   * Quá trình dừng lại khi không còn đỉnh mới nào được kích hoạt.
2. **Linear Threshold (LT) - Mô hình mở rộng:**
   * Mỗi đỉnh $v$ có một ngưỡng kích hoạt ngẫu nhiên $\theta_v \sim U[0, 1]$.
   * Đỉnh $v$ chuyển sang kích hoạt khi tổng trọng số ảnh hưởng từ các láng giềng đã kích hoạt đạt ngưỡng: $\sum_{u \in N_{in}(v) \cap A} b_{u,v} \ge \theta_v$.

### 5.2. Các phương pháp gán xác suất cạnh $p(u, v)$
Hệ thống hỗ trợ cấu hình linh hoạt 3 cơ chế gán xác suất:
1. **Weighted Cascade (WC) - Khuyến nghị mặc định:**
   $$p(u, v) = \frac{1}{d_{in}(v)}$$
   (với $d_{in}(v)$ là bán bậc vào của đỉnh $v$). Mô hình này phản ánh thực tế: nút càng nổi tiếng (nhiều người theo dõi) thì ảnh hưởng của một người cụ thể lên nút đó càng giảm.
2. **Trivalency Model (TR):**
   Xác suất $p(u, v)$ được chọn ngẫu nhiên đồng đều từ tập hữu hạn:
   $$p(u, v) \in \{0.1, 0.01, 0.001\}$$
   tương ứng với 3 cấp độ quan hệ xã hội: Thân thiết, Quen biết, và Xã giao.
3. **Uniform Model (Constant Probability):**
   Gán xác suất cố định cho toàn bộ các cạnh, ví dụ $p(u, v) = 0.01$ hoặc $p(u, v) = 0.05$.

### 5.3. Quy định đo lường & Đánh giá công bằng (Evaluation Protocol)
* **Search Worlds (Thế giới tìm kiếm):** Sử dụng số lượt mô phỏng Monte Carlo $R_{search} = 100 \sim 200$ (hoặc tập đồ thị ngẫu nhiên tiền sinh) để cung cấp tín hiệu fitness cho GA/IGA/PSO/ACO một cách nhanh chóng.
* **Validation Worlds (Thế giới kiểm định):** Khi thuật toán đã chốt tập hạt giống $S$, toàn bộ nghiệm của TẤT CẢ các thuật toán sẽ được đưa vào bộ đánh giá kiểm định độc lập với $R_{val} = 10.000$ lượt mô phỏng Monte Carlo. Điểm số từ bộ kiểm định này mới là điểm số chính thức ghi nhận vào bảng báo cáo.

---

## 6. Định Hướng Tối Ưu Hóa & Tinh Chỉnh Trong Tương Lai (Future Optimizations)

Các thành phần sau đây đã được thiết kế dưới dạng module cắm rút (pluggable) để dễ dàng nâng cấp và tối ưu ở các giai đoạn sau:

1. **Tối ưu tốc độ C++ Core:**
   * Tích hợp OpenMP đa luồng để tận dụng trọn vẹn 12 luồng CPU của chip AMD Ryzen 5 7430U.
   * Áp dụng kỹ thuật tiền sinh đồ thị con ngẫu nhiên (Live-Edge Graphs / Sample Reuse) giúp tăng tốc độ đánh giá cá thể lên từ 50x đến 200x.
   * Cân nhắc bổ sung thuật toán xấp xỉ lấy mẫu ngược (Reverse Influence Sampling - RIS / TIM+) cho các đồ thị có quy mô lớn hàng trăm nghìn đỉnh.
2. **Tối ưu thuật toán IGA đề xuất:**
   * Module hóa cơ chế khởi tạo quần thể kết hợp cấu trúc cộng đồng (Community-aware + Degree-biased initialization: 80% chọn lọc, 20% ngẫu nhiên).
   * Module hóa toán tử đột biến thích nghi (Adaptive Mutation) dựa trên sự suy giảm đa dạng của quần thể.
   * Module hóa toán tử sửa lỗi cá thể (Repair Operator) để đảm bảo tập hạt giống luôn có đúng $k$ đỉnh duy nhất mà không tốn chi phí $O(k^2)$.
   * Sẵn sàng cho **Ablation Study** (bật/tắt từng module cải tiến để đo lường tỷ lệ đóng góp thực tế).
3. **Mở rộng năng lực phân tích:**
   * Tự động xuất biểu đồ đường hội tụ (Convergence curve) theo cả 3 trục: Vòng lặp (Generation), Số lần gọi hàm mục tiêu (Evaluations), và Thời gian thực thi (Wall-clock seconds).
   * Tự động xuất bảng kiểm định thống kê $p$-value (Wilcoxon rank-sum test) chuẩn định dạng bảng LaTeX/Markdown để đưa thẳng vào báo cáo đồ án.

