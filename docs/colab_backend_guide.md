# Hướng dẫn chạy Benchmark Backend trên Colab

Tài liệu này hướng dẫn chạy thực nghiệm Influence Maximization bằng notebook
`colab_backend_benchmark.ipynb`. Notebook này chỉ chạy backend benchmark, không
mở giao diện GUI Tkinter.

Các thuật toán hiện được chạy là:

- **CELF**: thuật toán greedy lazy evaluation.
- **GA**: Genetic Algorithm.
- **IGA**: Improved Genetic Algorithm.

Các thuật toán dùng chung đồ thị, mô hình khuếch tán IC và cách gán xác suất
cạnh WC để kết quả có thể so sánh công bằng.

## 1. Điều kiện và phạm vi chạy

Notebook được thiết kế cho:

- Google Colab runtime, kể cả khi mở notebook thông qua VS Code.
- Python runtime Linux của Colab.
- Build C++ core bằng CMake, g++ và OpenMP.
- Lưu kết quả vào Google Drive để không mất khi Colab reset.

Nếu output có các đường dẫn như `/content`, `/usr/local` hoặc
`/tmp/ipykernel`, đó là dấu hiệu notebook đang chạy trên Colab runtime. Không
thay các đường dẫn này bằng đường dẫn Windows như `D:\...`.

Notebook không dùng để chạy GUI. GUI CustomTkinter phải chạy trên Windows hoặc
WSL2 có desktop display riêng.

## 2. File cần mở

Mở file ở thư mục gốc repository:

```text
colab_backend_benchmark.ipynb
```

Notebook gồm các nhóm cell chính:

1. Cài system dependencies và lấy source từ GitHub.
2. Cài Python dependencies và build C++ extension.
3. Mount Google Drive và khai báo cấu hình benchmark.
4. Chạy benchmark.
5. Kiểm tra các file JSON được tạo.
6. Chạy unit tests.

## 3. Chọn đúng branch

Backend benchmark mới nằm trên branch `minh`. Notebook hiện dùng:

```bash
BRANCH=minh
```

Cell setup sẽ tự:

```bash
git fetch origin minh
git checkout minh
git pull --ff-only origin minh
```

Không nên đổi sang `main` nếu muốn chạy notebook backend mới, vì `main` có thể
chưa chứa `colab_benchmark.py` và các thay đổi liên quan.

### Đổi branch trong notebook

Chỉ sửa dòng `BRANCH` trong cell setup:

```bash
BRANCH=minh
```

Sau khi đổi branch:

1. Restart kernel.
2. Chạy lại cell setup.
3. Chạy lại cell cài dependencies/build.
4. Chạy lại cell cấu hình.
5. Chạy lại cell benchmark.

Restart kernel giúp tránh trường hợp Python giữ `loader.py` hoặc module khác của
branch cũ trong `sys.modules`.

### Đổi branch bằng Git ở máy local

```bash
git fetch origin
git switch minh
git pull --ff-only origin minh
```

Kiểm tra branch hiện tại:

```bash
git branch --show-current
git log -1 --oneline
```

Nếu chỉnh notebook local và muốn Colab lấy bản mới:

```bash
git add colab_backend_benchmark.ipynb docs/colab_backend_guide.md
git commit -m "Document Colab backend benchmark"
git push origin minh
```

## 4. Quy trình chạy từ đầu

### Bước 1: Mở notebook và chọn kernel

Chọn Python/Colab kernel mà nhóm đang sử dụng. Nếu chạy qua VS Code, cần phân
biệt:

- **Remote Colab kernel**: dùng được `apt-get`, `/content` và `/content/drive`.
- **Python local Windows**: không dùng được các lệnh Colab này trực tiếp.

### Bước 2: Restart kernel

Nên restart kernel trước một lần chạy mới, đặc biệt sau khi đổi branch hoặc
pull source mới.

### Bước 3: Chạy cell setup

Cell setup sẽ:

- Cài `git`, `cmake`, `build-essential`, `g++`, `python3-dev`, `libgomp1`.
- Clone hoặc cập nhật repository tại:

  ```text
  /content/influence-maximization-benchmark
  ```

- Kiểm tra file:

  ```text
  src/im_research/experiments/colab_benchmark.py
  ```

### Bước 4: Chạy cell build/install

Cell này sẽ:

- Cài packages trong `requirements.txt`.
- Cấu hình và build C++ core.
- Cài project ở editable mode.

Khi thành công, output thường có:

```text
Backend build completed
```

### Bước 5: Chạy cell cấu hình

Cell cấu hình mount Google Drive và tạo thư mục output gốc. Chỉ thay đổi các
giá trị trong dictionary `CONFIG`.

### Bước 6: Chạy cell benchmark

Cell benchmark tạo một thư mục riêng theo timestamp, ví dụ:

```text
/content/drive/MyDrive/IM-Benchmark-Lab/Experiments/
└── Karate_Club/
    └── experiment_20261115_090453/
```

Không nên chạy lại benchmark bằng cách dùng cùng thư mục thí nghiệm cũ nếu đã
đổi cấu hình. Mỗi cấu hình nên có thư mục `experiment_<timestamp>` riêng.

### Bước 7: Kiểm tra output và test

Cell kiểm tra output phải hiển thị `OK` cho các file JSON. Cell test chạy unit
tests và kết quả thành công có dạng:

```text
29 passed
```

## 5. Thay đổi tham số benchmark

Các tham số nằm trong cell `CONFIG`.

| Tham số | Ý nghĩa | Ví dụ |
|---|---|---|
| `dataset_name` | Tên dataset dựng sẵn | `"Karate Club"` |
| `dataset_path` | Đường dẫn file edge list riêng | `None` hoặc `"/content/drive/MyDrive/.../graph.txt"` |
| `directed` | Đồ thị có hướng hay vô hướng | `False` |
| `diffusion_model` | Mô hình khuếch tán | `"IC"` |
| `probability_model` | Cách gán xác suất cạnh | `"WC"` |
| `p` | Xác suất cạnh khi dùng uniform/fixed | `0.1` |
| `k` | Số seed node cần chọn | `10` |
| `mc_runs` | Số Monte Carlo khi tìm kiếm | `100` |
| `validation_mc_runs` | Số Monte Carlo đánh giá cuối | `1000` |
| `independent_runs` | Số lần chạy độc lập | `3` |
| `algorithms` | Các thuật toán cần chạy | `["CELF", "GA", "IGA"]` |
| `population_size` | Kích thước quần thể GA/IGA | `50` |
| `generations` | Số thế hệ GA/IGA | `100` |
| `elite_size` | Số cá thể elite giữ lại | `2` |
| `crossover_rate` | Tỷ lệ lai ghép | `0.8` |
| `mutation_rate` | Tỷ lệ đột biến | `0.1` |
| `tournament_size` | Kích thước tournament selection | `3` |
| `random_seed` | Seed cho GA/IGA; notebook tự tạo theo thời gian | `int(time.time_ns() % (2**31 - 1))` |
| `celf_random_seed` | Seed cố định cho Monte Carlo của CELF | `42` |
| `record_population_history` | Lưu lịch sử quần thể | `True` |
| `record_mc_details` | Lưu từng spread của validation MC | `False` |
| `record_failed_edges` | Lưu cạnh thất bại trong diffusion history | `False` |
| `resume` | Tiếp tục từ checkpoint | `True` |

### Cấu hình chạy thử nhanh

Dùng để kiểm tra pipeline, không dùng làm kết quả báo cáo cuối:

```python
CONFIG = {
    "dataset_name": "Karate Club",
    "dataset_path": None,
    "directed": False,
    "diffusion_model": "IC",
    "probability_model": "WC",
    "p": 0.1,
    "k": 5,
    "mc_runs": 20,
    "validation_mc_runs": 50,
    "independent_runs": 1,
    "algorithms": ["CELF", "GA", "IGA"],
    "population_size": 20,
    "generations": 10,
    "elite_size": 2,
    "crossover_rate": 0.8,
    "mutation_rate": 0.1,
    "tournament_size": 3,
    "random_seed": 42,
    "record_population_history": False,
    "record_mc_details": False,
    "record_failed_edges": False,
    "resume": True,
}
```

### Cấu hình chạy báo cáo

Tăng `mc_runs`, `validation_mc_runs`, `independent_runs`, `population_size` và
`generations`. Ví dụ cấu hình mặc định trong notebook dùng:

```python
"mc_runs": 100,
"validation_mc_runs": 1000,
"independent_runs": 3,
"population_size": 50,
"generations": 100,
```

Thời gian chạy tăng mạnh khi tăng các tham số này. Không so sánh kết quả được
tạo từ các cấu hình khác nhau mà không ghi rõ cấu hình trong báo cáo.

### Chỉ chạy một số thuật toán

Ví dụ chỉ so sánh GA và IGA:

```python
"algorithms": ["GA", "IGA"],
```

Tên hợp lệ hiện tại là `CELF`, `GA` và `IGA`.

## 6. Dataset và mô hình xác suất

### Dataset dựng sẵn

Có thể dùng tên dataset mà loader hỗ trợ, ví dụ:

```python
"dataset_name": "Karate Club"
"dataset_name": "Dolphins"
"dataset_name": "Facebook"
"dataset_name": "Email-Enron"
"dataset_name": "NetHEPT"
```

Một số dataset lớn cần tải về từ Internet ở lần chạy đầu tiên và có thể cần
nhiều RAM/thời gian.

### Dataset riêng

Đặt file edge list vào Google Drive, mỗi dòng chứa hai node:

```text
0 1
1 2
2 3
```

Sau đó cấu hình:

```python
"dataset_name": "My Graph",
"dataset_path": "/content/drive/MyDrive/IM-Benchmark-Lab/data/my_graph.txt",
"directed": False,
```

Nếu file là đồ thị có hướng:

```python
"directed": True,
```

### IC và WC

- `diffusion_model="IC"`: Independent Cascade.
- `probability_model="WC"`: Weighted Cascade. Xác suất cạnh được suy ra từ
  bậc node đích.
- `p` chỉ có ý nghĩa khi dùng cách gán xác suất uniform/fixed. Với WC, `p`
  không quyết định xác suất từng cạnh.

Backend hiện tại thực thi IC. Không cấu hình `diffusion_model="LT"` cho notebook
này.

## 7. Các file kết quả được tạo

Mỗi lần chạy tạo một thư mục `experiment_<timestamp>` trong Google Drive.

| File | Nội dung |
|---|---|
| `config.json` | Toàn bộ tham số chạy và `config_hash` |
| `graph_info.json` | Số node, số cạnh, directed, dataset và thông tin tiền xử lý |
| `runs.json` | Kết quả chi tiết của từng independent run và từng thuật toán |
| `summary.json` | Mean, std, min, max, median, confidence interval và các thống kê tổng hợp |
| `comparison.json` | So sánh spread, thời gian chạy và độ ổn định giữa thuật toán |
| `statistical_tests.json` | Các kiểm định thống kê giữa các thuật toán |
| `experiment.json` | File tổng hợp đầy đủ: môi trường, cấu hình, runs, summary và comparison |
| `manifest.json` | Danh sách file output cần có |
| `logs.txt` | Log stdout/stderr của toàn bộ benchmark |
| `checkpoint.json` | Các run đã hoàn thành để hỗ trợ resume |

## 8. Xem kết quả nào?

### Xem tổng quan nhanh

Mở:

```text
summary.json
```

Các trường quan trọng:

- `final_spread.mean`: spread trung bình.
- `final_spread.std`: độ lệch chuẩn.
- `final_spread.minimum` và `maximum`.
- `final_spread.median`.
- `final_spread.confidence_interval_95`.
- `execution_time.mean`: thời gian trung bình.
- `evaluations.mean`: số lần đánh giá trung bình.
- `mc_simulations.mean`: số Monte Carlo trung bình.
- `seed_set_consistency`: kiểm tra seed set cuối cùng giữa các independent run.
  - `unique_seed_sets`: có bao nhiêu seed set khác nhau.
  - `all_runs_same`: tất cả run có chọn đúng cùng seed set hay không.
  - `best_run_seed_set`: seed set của run có `final_spread` cao nhất.
  - `best_run_id`: số thứ tự của run tốt nhất.

Đối với GA và IGA, việc chạm `max_generations` không có nghĩa là mất kết quả.
Thuật toán vẫn trả về cá thể tốt nhất đã tìm được đến thời điểm dừng. Thông tin
này nằm trong:

```text
runs[] → algorithms → GA/IGA → parameters → algorithm_metadata
```

Các trường cần xem:

- `termination_reason`: lý do dừng, thường là `max_generations_reached`.
- `generations_completed`: số thế hệ đã chạy.
- `best_solution_at_termination.seed_set`: seed set tốt nhất được giữ lại.
- `best_solution_at_termination.fitness`: fitness của cá thể đó.

Sau đó, `seed_set` ở cấp thuật toán trong cùng record là seed set đã được đánh
giá lại bằng validation Monte Carlo và được dùng làm kết quả cuối của run.

Notebook dùng seed tách riêng: `random_seed` thay đổi theo thời gian cho GA/IGA,
còn `celf_random_seed` giữ cố định để kết quả CELF không thay đổi chỉ vì bấm
chạy benchmark lần khác. Cả hai seed đều được lưu trong `config.json` và
`runs.json`.

Trong `runs.json`, GA và IGA cũng có trường ngắn gọn ở cấp thuật toán:

```text
runs[] → algorithms → GA/IGA → termination
```

Trường này chứa `reason`, `generations_completed` và
`best_solution_at_termination`, nên có thể xem kết quả ngay cả khi thuật toán
dừng vì đạt số thế hệ tối đa.

### Xem so sánh trực tiếp

Mở:

```text
comparison.json
```

Các nhóm chính:

- `spread_comparison`: so sánh influence spread.
- `runtime_comparison`: so sánh thời gian chạy.
- `stability_comparison`: so sánh độ lệch chuẩn; nhỏ hơn thường ổn định hơn.

### Xem từng lần chạy

Mở:

```text
runs.json
```

File này dùng khi cần biết:

- Seed node được chọn.
- Seed random của từng run.
- Spread của từng thuật toán.
- Convergence history.
- Thời gian search và validation.
- Lịch sử diffusion.
- Số evaluation và số MC simulation.

### Xem cấu hình để đảm bảo công bằng

Luôn kiểm tra:

```text
config.json
```

Trước khi so sánh hai experiment, cần đảm bảo các tham số sau giống nhau:

- Dataset và `graph_info`.
- `directed`.
- `diffusion_model` và `probability_model`.
- `k`.
- `mc_runs` và `validation_mc_runs`.
- Số `independent_runs`.
- Seed và các tham số GA/IGA tương ứng.

## 9. Cách so sánh kết quả

Thứ tự nên dùng khi phân tích:

1. So sánh `summary.json` theo `final_spread.mean`.
2. Kiểm tra `final_spread.std` và confidence interval.
3. Kiểm tra `execution_time.mean`.
4. Kiểm tra `statistical_tests.json`.
5. Mở `runs.json` để xem từng run có bất thường hay không.

Diễn giải cơ bản:

- **Spread mean cao hơn**: thuật toán tạo ảnh hưởng trung bình lớn hơn.
- **Std thấp hơn**: kết quả ổn định hơn giữa các lần chạy.
- **Runtime thấp hơn**: hiệu quả tính toán tốt hơn.
- **Confidence interval hẹp hơn**: ước lượng trung bình ổn định hơn.
- Không kết luận chỉ dựa vào một lần chạy hoặc một giá trị spread đơn lẻ.

Một kết quả spread cao hơn nhưng thời gian chạy lớn hơn cần được báo cáo theo
cả hai tiêu chí, không chỉ gọi đó là “tốt hơn” một cách tuyệt đối.

## 10. Resume và checkpoint

Khi `resume=True`, backend đọc:

```text
checkpoint.json
```

Sau mỗi independent run, checkpoint được cập nhật. Nếu Colab bị ngắt, chạy lại
đúng experiment directory và đúng cấu hình có thể tiếp tục các run còn thiếu.

Nếu đã thay đổi cấu hình, backend sẽ báo lỗi:

```text
Existing checkpoint configuration does not match this benchmark.
```

Đây là hành vi bảo vệ dữ liệu, tránh trộn các kết quả không cùng điều kiện.
Khi đổi cấu hình, hãy tạo experiment directory mới hoặc đặt `resume=False`
cho một lần chạy mới.

## 11. Các lỗi thường gặp

### `ModuleNotFoundError: No module named ... colab_benchmark`

Nguyên nhân thường là notebook đang lấy branch cũ.

Kiểm tra:

```bash
git branch --show-current
test -f /content/influence-maximization-benchmark/src/im_research/experiments/colab_benchmark.py
```

Đảm bảo branch là `minh`, sau đó restart kernel và chạy lại setup/build.

### `load_networkx_graph() got an unexpected keyword argument 'dataset_path'`

Kernel đang giữ `loader.py` cũ trong import cache hoặc source chưa được
checkout đồng bộ. Cách xử lý:

1. Restart kernel.
2. Pull branch `minh`.
3. Chạy lại cell build/install.
4. Chạy lại cell benchmark.

### `k exceeds the graph size`

Giá trị `k` lớn hơn số node của dataset. Giảm `k` hoặc chọn dataset lớn hơn.

### Checkpoint không khớp cấu hình

Không dùng lại thư mục experiment cũ sau khi đổi tham số. Tạo experiment mới
hoặc tắt resume cho lần chạy mới.

### Colab hết thời gian hoặc hết RAM

Giảm lần lượt:

```python
mc_runs
validation_mc_runs
independent_runs
population_size
generations
```

Đồng thời tắt các lịch sử chi tiết nếu không cần:

```python
record_population_history = False
record_mc_details = False
record_failed_edges = False
```

## 12. Phân biệt notebook backend và GUI

`colab_backend_benchmark.ipynb` chỉ thực nghiệm backend và lưu JSON. File GUI
chính là:

```text
src/im_research/gui/main_app.py
```

GUI chạy local trên Windows/WSL2, không mở cửa sổ Tkinter tương tác trong Colab.
Kết quả backend có thể được dùng để phân tích bằng JSON, nhưng notebook hiện
không tự điều khiển GUI.

## 13. Checklist trước khi dùng kết quả trong báo cáo

- [ ] Đã chạy đúng branch `minh`.
- [ ] Đã restart kernel sau khi đổi branch hoặc source.
- [ ] C++ core build thành công.
- [ ] `graph_info.json` đúng dataset và số node/cạnh.
- [ ] Các thuật toán dùng cùng `k`, diffusion model, probability model và MC config.
- [ ] Có đủ số `independent_runs`.
- [ ] Đã lưu `config.json`, `summary.json`, `comparison.json` và `statistical_tests.json`.
- [ ] Đã kiểm tra `logs.txt` không có lỗi.
- [ ] Không dùng kết quả chạy thử nhanh làm số liệu chính thức.
- [ ] Ghi rõ dataset, tham số, seed, số MC, phần cứng và thời gian chạy trong báo cáo.
