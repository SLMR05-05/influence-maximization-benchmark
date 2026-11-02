# Kiến Trúc Nền Tảng Nghiên Cứu Lấy Cảm Hứng Từ ESA Pygmo2

> **Tài liệu đối chiếu & Kế thừa kiến trúc:** Học hỏi từ framework tối ưu hóa song song đa ngôn ngữ `pagmo2 / pygmo2` của Cơ quan Vũ trụ Châu Âu (European Space Agency - ESA) và điều chỉnh chuyên biệt cho bài toán **Influence Maximization (IM)**.

---

## 1. Các Nguyên Lý Cốt Lõi Học Hỏi Từ Pygmo2

Trong bài báo và mã nguồn của `pygmo2` ([Biscani & Izzo, 2020](https://github.com/esa/pygmo2)), các kỹ sư tại ESA đã giải quyết triệt để bài toán: *"Làm thế nào để phát triển thuật toán tối ưu vừa linh hoạt, nhanh gọn bằng Python, vừa đạt tốc độ tính toán số học tối đa của C++ mà không gặp rào cản GIL (Global Interpreter Lock)?"*

Hệ thống của chúng ta kế thừa 5 nguyên lý cốt lõi từ `pygmo2`:

### 1.1. Tách biệt hoàn toàn Bài toán (Problem) và Thuật toán (Algorithm)
* Trong cách lập trình thông thường, người ta hay viết mã thuật toán GA lồng chặt vào hàm mô phỏng lan truyền đồ thị. Điều này làm thuật toán bị dính chặt với bài toán, rất khó thay thế bằng PSO, ACO hoặc tái sử dụng.
* **Theo chuẩn Pygmo2:**
  * **`IMProblem` (User-Defined Problem - UDP):** Đóng gói toàn bộ thông tin về đồ thị $G = (V, E)$, số đỉnh hạt giống cần chọn $k$, mô hình lan truyền (IC / LT), và cơ chế đánh giá fitness.
  * **`BaseAlgorithm` (User-Defined Algorithm - UDA):** Đóng gói logic tìm kiếm (GA, IGA, PSO, ACO, CELF). Thuật toán không cần quan tâm đồ thị được duyệt như thế nào; nó chỉ gửi các tập ứng viên $S \subset V$ cho `IMProblem` và nhận lại điểm ảnh hưởng (Influence Spread).

### 1.2. Thùng chứa cá thể và quần thể (Population as Value-Semantic Container)
* `Population` đóng vai trò là cấu trúc mang dữ liệu giữa Algorithm và Problem:
  * Lưu trữ danh sách các cá thể `Solution(seed_set, fitness)`.
  * Quản lý cá thể tốt nhất toàn cục (`best_solution`), điểm trung bình (`mean_fitness`).
  * Đo lường độ đa dạng của quần thể (`diversity_jaccard`) bằng khoảng cách Jaccard trung bình giữa các tập hạt giống:
    $$D(S_1, S_2) = 1 - \frac{|S_1 \cap S_2|}{|S_1 \cup S_2|}$$
    Đây là chỉ số sống còn để kích hoạt cơ chế Đột biến thích nghi (Adaptive Mutation) trong IGA.

### 1.3. Cơ chế Batch Fitness Evaluation & Giải phóng GIL (Pygmo Signature Feature)
* **Vấn đề hiệu năng khi gọi Python $\leftrightarrow$ C++:** Nếu một thế hệ GA có 100 cá thể, việc gọi hàm `evaluate()` 100 lần từ Python sang C++ sẽ tạo ra overhead chuyển đổi kiểu dữ liệu (data marshaling) và bị khóa bởi Python GIL.
* **Giải pháp Pygmo:** Cung cấp hàm `batch_evaluate(seed_sets)`:
  * Python truyền toàn bộ danh sách các tập hạt giống một lần duy nhất sang C++.
  * Trong C++, hàm sử dụng `py::call_guard<py::gil_scoped_release>()` để **giải phóng hoàn toàn Python GIL**.
  * C++ kích hoạt chỉ thị OpenMP `#pragma omp parallel for schedule(dynamic)` để chia đều các lượt mô phỏng Monte Carlo trên toàn bộ **12 luồng CPU** của chip AMD Ryzen 5 7430U, đạt hiệu năng tính toán 100% CPU!

### 1.4. Thiết kế dạng module cắm rút phục vụ Ablation Study cho IGA
* IGA không phải là một thuật toán nguyên khối (monolithic) mà là sự kết hợp của:
  1. **Khởi tạo định hướng (Biased Community-Aware Initialization):** 80% dựa trên bậc đỉnh & cộng đồng, 20% ngẫu nhiên.
  2. **Toán tử lai ghép tập hợp (Set-based Crossover).**
  3. **Đột biến thích nghi (Adaptive Mutation):** Tăng xác suất đột biến khi độ đa dạng Jaccard suy giảm.
  4. **Toán tử sửa lỗi (Repair Operator):** Đảm bảo không trùng đỉnh trong tập $k$.
* Mỗi cơ chế trên là một module độc lập trong `im_research.algorithms.evolutionary.iga`. Nhờ đó, ta có thể bật/tắt từng module để thực hiện **Ablation Study** đánh giá chính xác cải tiến nào đem lại giá trị.

---

## 2. Sơ Đồ Đối Ứng Kiến Trúc

| Khái niệm Pygmo2 | Thành phần tương ứng trong IM-Research | Vai trò trong nghiên cứu |
| :--- | :--- | :--- |
| `pagmo::problem` | `im_research.core.IMProblem` | Đại diện cho bài toán tối đa hóa tầm ảnh hưởng trên đồ thị |
| `pagmo::algorithm` | `im_research.core.BaseAlgorithm` | Lớp cơ sở cho Degree, CELF, GA, IGA, PSO, ACO |
| `pagmo::population` | `im_research.core.Population` | Chứa các tập hạt giống ứng viên, đo độ đa dạng Jaccard |
| `batch_fitness()` | `Evaluator::batch_evaluate()` | Song song hóa OpenMP đa luồng, giải phóng GIL |
| `island / archipelago` | `im_research.experiments.Runner` | Điều phối chạy hàng loạt qua nhiều hạt giống (seeds), đồ thị và giá trị $k$ |

