# Mã giả thuật toán IGA (Improved Genetic Algorithm)

> **Nguồn:** `src/im_research/algorithms/evolutionary/iga.py` (792 dòng).
> Mã giả dưới đây bám sát **đúng implementation hiện có**, kể cả các điểm khác với mô tả lý thuyết/comment trong code. Các điểm đó được liệt kê ở mục 8.

---

## 1. Tham số

| Ký hiệu | Tên trong code | Mặc định | Ý nghĩa |
|---------|----------------|----------|---------|
| `N` | `pop_size` | 50 | Kích thước quần thể |
| `T_max` | `max_generations` | 100 | Số thế hệ tối đa |
| `p_c_min`, `p_c_max` | `p_c_min`, `p_c_max` | 0.60, 0.90 | Cận dưới / trên của xác suất lai ghép |
| `p_m_min`, `p_m_max` | `p_m_min`, `p_m_max` | 0.05, 0.35 | Cận dưới / trên của xác suất đột biến |
| `q` | `tournament_size` | 3 | Kích thước giải đấu |
| `N_elite` | `elitism` | 2 | Số cá thể tinh hoa |
| `ε_div` | `epsilon_div` | 0.30 | Ngưỡng đa dạng tối thiểu |
| `τ_overlap` | `tau_overlap` | 0.50 | Ngưỡng chồng lấn láng giềng Jaccard |
| `λ_tour` | `lambda_tour` | 0.25 | Trọng số phủ cộng đồng trong giải đấu |
| `L_max` | `local_search_steps` | 10 | Số bước leo đồi tối đa |
| `R_final` | `r_final` | 1000 | Chỉ được ghi vào metadata (xem mục 8.4) |

**Cờ ablation:** `enable_guided_init`, `enable_adaptive_mutation`, `enable_degree_guided_mutation`, `enable_local_search`, `enable_overlap_filtering` — mặc định đều `True`.

**Tương thích ngược:** nếu truyền `crossover_rate`, `mutation_rate_base`, `mutation_rate_max`, `diversity_threshold` thì chúng ghi đè lần lượt `p_c_max`, `p_m_min`, `p_m_max`, `ε_div`.

---

## 2. Mã giả tổng quát

```text
THUẬT TOÁN IGA(problem, seed = 42, max_evaluations = None, max_iterations = None)

Đầu vào:
    problem         : IMProblem { graph CSR (row_ptr, col_indices, edge_probs), k, evaluator }
    seed            : seed cho cả random.Random và numpy.random.default_rng
    max_evaluations : ngân sách đánh giá; None → +∞
    max_iterations  : số thế hệ; None → self.max_generations

Bước 0 — Khởi tạo:
    rng    ← Random(seed)
    np_rng ← default_rng(seed)
    n ← problem.num_nodes
    k ← problem.k
    T ← max_iterations nếu khác None, ngược lại self.max_generations
    B ← max_evaluations nếu khác None, ngược lại +∞

    t_start      ← perf_counter()
    total_evals  ← 0
    history      ← ∅
    row_ptr, col_indices, edge_probs ← trích từ problem.graph

Bước 1 — Tiền xử lý topo:
    (C, quota, PR, comm_of, boundary, G) ← TIEN_XU_LY(problem, seed)

Bước 2 — Khởi tạo quần thể:
    P ← KHOI_TAO_QUAN_THE(problem, C, quota, PR, np_rng)
    total_evals ← total_evals + N

    best_lie  ← cá thể có fitness lớn nhất trong P
    S*_lie    ← bản sao của best_lie
    stagnation ← 0
    div       ← DA_DANG_JACCARD(P)

    history.thêm({
        generation = 0,
        best_fitness = S*_lie.fitness,
        mean_fitness = trung_bình fitness của P,
        diversity = div,
        mutation_rate = p_m_max,       // giá trị khởi tạo, không phải p_m_min
        crossover_rate = p_c_min,
        evaluations = total_evals
    })

Bước 3 — Tiến hóa:
    for t ← 1 .. T do
        nếu total_evals ≥ B thì break

        progress ← t / max(1, T)
        p_m ← p_m_max − (p_m_max − p_m_min) · progress
        p_c ← p_c_min + (p_c_max − p_c_min) · progress
        div ← DA_DANG_JACCARD(P)

        // Tăng đột biến khi quần thể kém đa dạng
        nếu enable_adaptive_mutation và div < ε_div thì
            deficit ← (ε_div − div) / ε_div
            p_m ← min(p_m_max, p_m + deficit · (p_m_max − p_m_min))

            // Đột biến giải cứu khi trì trệ ≥ 3 thế hệ
            nếu stagnation ≥ 3 thì
                P ← DOT_BIEN_GIAI_CUU(P, C, quota, n, k, np_rng)
                stagnation ← 0

        // (1) Bảo tồn tinh hoa
        P_new ← N_elite cá thể tốt nhất của P (sao chép nguyên vẹn)

        // (2) Sinh sản
        while |P_new| < N do
            p1 ← GIAI_DAU_TOPO(P, comm_of, rng)
            p2 ← GIAI_DAU_TOPO(P, comm_of, rng)

            nếu rng.random() < p_c thì
                child ← LAI_GHEP_THONG_MINH(p1, p2, k, n, PR, rng)
            ngược lại
                child ← bản sao của p1

            nếu rng.random() < p_m thì
                child ← DOT_BIEN_BIEN(child, n, comm_of, boundary, PR, rng)

            child.fitness ← LIE2(child.seed_set, row_ptr, col_indices, edge_probs)
            total_evals ← total_evals + 1
            P_new.thêm(child)

        // (3) Leo đồi trên nhóm tinh hoa của thế hệ mới
        P_new ← sắp xếp P_new giảm dần theo fitness
        for i ← 0 .. min(N_elite, |P_new|) − 1 do
            P_new[i] ← LEO_DOI(P_new[i], PR, row_ptr, col_indices, edge_probs, L_max, rng)

        P ← Population(P_new)

        // (4) Cập nhật nghiệm LIE tốt nhất
        gen_best ← cá thể tốt nhất của P
        nếu gen_best.fitness > S*_lie.fitness thì
            S*_lie ← bản sao của gen_best
            stagnation ← 0
        ngược lại
            stagnation ← stagnation + 1

        history.thêm({
            generation = t,
            best_fitness = S*_lie.fitness,
            mean_fitness = trung_bình fitness của P,
            diversity = div,               // đo trước khi tiến hóa
            mutation_rate = p_m,
            crossover_rate = p_c,
            evaluations = total_evals
        })
    end for

    t_search_end ← perf_counter()

Bước 4 — Sàng lọc Monte Carlo:
    E ← N_elite cá thể tốt nhất của P theo fitness LIE
    σ*_MC ← −1
    S*    ← E[0]

    for i ← 1 .. |E| do
        σ_MC ← problem.fitness(E[i])       // gọi C++ Evaluator
        total_evals ← total_evals + 1
        nếu σ_MC > σ*_MC thì
            σ*_MC ← σ_MC
            S*    ← E[i]

    t_end ← perf_counter()

Bước 5 — Trả về:
    return AlgorithmResult(
        algorithm_name = "IGA",
        best_solution = S*,
        search_time = t_search_end − t_start,
        total_evaluations = total_evals,
        convergence_history = history,
        metadata = {
            total_time = t_end − t_start,
            pop_size = N,
            generations_completed = |history| − 1,
            p_c_min, p_c_max, p_m_min, p_m_max,
            tournament_size = q,
            elitism = N_elite,
            epsilon_div = ε_div,
            tau_overlap = τ_overlap,
            lambda_tour = λ_tour,
            local_search_steps = L_max,
            r_final = R_final,
            num_communities = |C|,
            random_seed = seed
        }
    )
```

---

## 3. Pha 1 — Tiền xử lý topo

```text
HÀM TIEN_XU_LY(problem, seed):
    n ← problem.num_nodes
    k ← problem.k

    // 1. Dựng đồ thị vô hướng từ CSR
    G ← đồ thị rỗng có n đỉnh
    for u ← 0 .. n−1 do
        for v ∈ col_indices[row_ptr[u] : row_ptr[u+1]] do
            nếu u < v thì G.thêm_cạnh(u, v)
    // CSR của đồ thị vô hướng chứa cả hai chiều (u→v và v→u),
    // điều kiện u < v để mỗi cạnh chỉ được thêm một lần.

    // 2. Louvain
    thử:
        C_raw ← louvain_communities(G, seed)
    ngoại lệ:
        C_raw ← các thành phần liên thông của G
        nếu C_raw = ∅ thì C_raw ← [{0}, {1}, ..., {n−1}]

    sắp xếp C_raw giảm dần theo kích thước
    C ← [sắp xếp tăng dần các đỉnh trong từng cộng đồng]
    N_c ← |C|

    comm_of[u] ← chỉ số j sao cho u ∈ C[j], với mọi u ∈ [0, n)

    // 3. PageRank
    thử:
        pr ← pagerank(G, alpha = 0.85, max_iter = 100)
        PR[u] ← pr[u] nếu có, ngược lại 1/n
    ngoại lệ:
        PR[u] ← degree(u) / Σ_v degree(v)
        (nếu Σ_v degree(v) = 0 thì chia cho 1)

    // 4. Hạn ngạch theo phương pháp phần dư lớn nhất
    for j ← 0 .. N_c−1 do
        q_j        ← k · |C[j]| / n
        quota[j]   ← min(|C[j]|, ⌊q_j⌋)
        r[j]       ← q_j − quota[j]          // có thể âm nếu quota bị chặn trần
    surplus ← k − Σ_j quota[j]

    for j ∈ các chỉ số sắp xếp giảm dần theo r[j] do
        nếu surplus ≤ 0 thì break
        nếu quota[j] < |C[j]| thì
            quota[j] ← quota[j] + 1
            surplus  ← surplus − 1

    // Nếu vẫn dư do các cộng đồng đã đạt trần kích thước
    nếu surplus > 0 thì
        for j ← 0 .. N_c−1 do
            while surplus > 0 và quota[j] < |C[j]| do
                quota[j] ← quota[j] + 1
                surplus  ← surplus − 1

    // 5. Đỉnh biên cộng đồng
    boundary ← [u ∈ [0, n) | ∃ v kề u : comm_of[v] ≠ comm_of[u]]
    nếu boundary = ∅ thì boundary ← [0, 1, ..., n−1]

    // 6. Cache láng giềng
    adj[u] ← {v | v kề u}, với mọi u ∈ [0, n)

    return (C, quota, PR, comm_of, boundary, G)
```

---

## 4. Hàm thích nghi nhanh LIE-2

```text
HÀM LIE2(S, row_ptr, col_indices, edge_probs):
    S_set ← set(S)

    // Xác suất kích hoạt 1-hop
    P1 ← từ điển rỗng
    for u ∈ S do
        for idx ∈ [row_ptr[u], row_ptr[u+1]) do
            v ← col_indices[idx]
            nếu v ∉ S_set thì
                p ← edge_probs[idx]
                P1[v] ← 1 − (1 − P1.get(v, 0)) · (1 − p)

    // Xác suất kích hoạt 2-hop
    P2 ← từ điển rỗng
    for (v, p_v) ∈ P1 do
        for idx ∈ [row_ptr[v], row_ptr[v+1]) do
            w ← col_indices[idx]
            nếu w ∉ S_set và w ∉ P1 thì
                p ← edge_probs[idx]
                P2[w] ← 1 − (1 − P2.get(w, 0)) · (1 − p_v · p)

    return |S| + Σ_{v ∈ P1} P1[v] + Σ_{w ∈ P2} P2[w]
```

Công thức:

$$\sigma_{LIE\text{-}2}(S) = |S| + \sum_{v \in N_1(S)} P_1(v) + \sum_{w \in N_2(S)} P_2(w)$$

$$P_1(v) = 1 - \prod_{u \in S,\ (u,v) \in E} (1 - p_{uv})$$

$$P_2(w) = 1 - \prod_{v \in N_1(S),\ (v,w) \in E} \left(1 - P_1(v)\,p_{vw}\right)$$

---

## 5. Pha 2 — Khởi tạo quần thể

```text
HÀM KHOI_TAO_QUAN_THE(problem, C, quota, PR, np_rng):
    n ← problem.num_nodes
    k ← problem.k
    P ← ∅

    // Chế độ baseline: 100% ngẫu nhiên đều
    nếu not enable_guided_init thì
        lặp N lần:
            S ← chọn đều k đỉnh phân biệt từ [0, n)
            P.thêm(Solution(S, fitness = LIE2(S)))
        return P

    N_topo ← round(0.80 · N)
    N_rand ← N − N_topo

    // Phân bố PageRank chuẩn hóa trong từng cộng đồng
    for j ← 0 .. N_c−1 do
        w ← PR[C[j]]
        nếu Σ w > 0 thì comm_prob[j] ← w / Σ w
        ngược lại comm_prob[j] ← phân bố đều

    // 80% cá thể định hướng topo
    lặp N_topo lần:
        S ← ∅
        for j ← 0 .. N_c−1 do
            nếu quota[j] > 0 thì
                m ← min(quota[j], |C[j]|)
                S ← S ∪ chọn m đỉnh phân biệt từ C[j] theo comm_prob[j]
        S ← khử trùng, giữ thứ tự

        nếu |S| < k thì
            bổ sung các đỉnh có PR giảm dần chưa nằm trong S cho đủ k
        ngược lại nếu |S| > k thì
            S ← k phần tử đầu

        P.thêm(Solution(sắp xếp(S), fitness = LIE2(S)))

    // 20% cá thể ngẫu nhiên kiểm soát
    lặp N_rand lần:
        S ← chọn đều k đỉnh phân biệt từ [0, n)
        P.thêm(Solution(S, fitness = LIE2(S)))

    return P
```

---

## 6. Các toán tử tiến hóa

### 6.1. Giải đấu topo

```text
HÀM GIAI_DAU_TOPO(P, comm_of, rng):
    Q ← rng.sample(P.individuals, min(q, |P|))

    với mỗi s ∈ Q:
        base  ← s.fitness nếu khác None, ngược lại 0
        cover ← |{ comm_of[u] : u ∈ s.seed_set }|
        score(s) ← base + λ_tour · cover

    return argmax_{s ∈ Q} score(s)
```

$$\text{Fitness}_{tour}(S) = f_{LIE}(S) + \lambda_{tour} \cdot |\{C_j : S \cap C_j \neq \emptyset\}|$$

### 6.2. Chồng lấn láng giềng Jaccard

```text
HÀM JACCARD_LANG_GIENG(u, v):
    Nu ← adj[u]
    Nv ← adj[v]
    nếu Nu = ∅ và Nv = ∅ thì return 0
    hợp ← Nu ∪ Nv
    nếu |hợp| = 0 thì return 0
    return |Nu ∩ Nv| / |hợp|
```

### 6.3. Lai ghép thông minh

```text
HÀM LAI_GHEP_THONG_MINH(p1, p2, k, n, PR, rng):
    U ← danh sách các đỉnh trong set(p1.seed_set) ∪ set(p2.seed_set)
    sắp xếp U giảm dần theo PR

    // Chế độ tắt lọc overlap
    nếu not enable_overlap_filtering thì
        nếu |U| < k thì
            bổ sung ngẫu nhiên các đỉnh ngoài U cho đủ k
        return Solution(rng.sample(U, k))

    child ← ∅
    for cand ∈ U do
        nếu với mọi s ∈ child: JACCARD_LANG_GIENG(cand, s) ≤ τ_overlap thì
            child.thêm(cand)
            nếu |child| = k thì break

    // Bổ sung từ chính U nếu chưa đủ
    nếu |child| < k thì
        for cand ∈ U do
            nếu cand ∉ child thì child.thêm(cand)
            nếu |child| = k thì break

    // Bổ sung từ toàn mạng theo PR nếu |U| < k
    nếu |child| < k thì
        for u ∈ các đỉnh sắp xếp giảm dần theo PR do
            nếu u ∉ child thì child.thêm(u)
            nếu |child| = k thì break

    return Solution(sắp xếp(child))
```

### 6.4. Đột biến khai thác biên

```text
HÀM DOT_BIEN_BIEN(sol, n, comm_of, boundary, PR, rng):
    S ← set(sol.seed_set)

    // Chế độ đột biến đều
    nếu not enable_degree_guided_mutation thì
        S_list ← list(S)
        i ← rng.randrange(|S_list|)
        avail ← [0, n) \ S
        nếu avail ≠ ∅ thì S_list[i] ← rng.choice(avail)
        return Solution(sắp xếp(S_list))

    yếu ← argmin_{u ∈ S} PR[u]
    ứng_viên ← [v ∈ boundary | v ∉ S]

    nếu ứng_viên ≠ ∅ thì
        sắp xếp ứng_viên giảm dần theo PR
        top  ← max(1, ⌊0.20 · |ứng_viên|⌋)
        thay ← rng.choice(ứng_viên[0 : top])
    ngược lại
        avail ← [0, n) \ S
        thay ← rng.choice(avail) nếu avail ≠ ∅, ngược lại yếu

    return Solution(sắp xếp((S \ {yếu}) ∪ {thay}))
```

### 6.5. Tìm kiếm cục bộ leo đồi

```text
HÀM LEO_DOI(sol, PR, row_ptr, col_indices, edge_probs, L_max, rng):
    nếu not enable_local_search hoặc L_max ≤ 0 thì return sol

    cur ← list(sol.seed_set)
    f   ← sol.fitness nếu khác None, ngược lại LIE2(cur)
    S   ← set(cur)

    for step ← 1 .. L_max do
        u ← rng.choice(cur)                  // chọn đều, KHÔNG ưu tiên PR thấp
        cands ← [v ∈ CSR_out(u) | v ∉ S]
        nếu cands = ∅ thì continue

        v    ← argmax_{x ∈ cands} PR[x]
        test ← sắp xếp(thay u bằng v trong cur)
        f_test ← LIE2(test)

        nếu f_test > f thì
            cur ← test
            f   ← f_test
            S   ← set(cur)
        ngược lại
            break

    return Solution(cur, fitness = f)
```

### 6.6. Đột biến giải cứu

```text
HÀM DOT_BIEN_GIAI_CUU(P, C, quota, n, k, np_rng):
    sorted_P ← sắp xếp P giảm dần theo fitness
    R ← N_elite cá thể đầu tiên (giữ nguyên)

    lặp N − N_elite lần:
        S ← ∅
        for j ← 0 .. N_c−1 do
            nếu quota[j] > 0 thì
                m ← min(quota[j], |C[j]|)
                S ← S ∪ chọn đều m đỉnh phân biệt từ C[j]
                // Không dùng trọng số PageRank

        S ← khử trùng, cắt còn k
        while |S| < k do
            S ← khử trùng(S ∪ {np_rng.integers(0, n)})

        R.thêm(Solution(sắp xếp(S), fitness = LIE2(S)))

    return Population(R)
```

---

## 7. Pha 4 — Sàng lọc Monte Carlo

```text
E ← N_elite cá thể tốt nhất của P theo fitness LIE
σ*_MC ← −1
S*    ← E[0]

for i ← 1 .. |E| do
    // problem.fitness() gọi C++ Evaluator với R do evaluator cấu hình
    σ_MC ← problem.fitness(E[i])
    total_evals ← total_evals + 1

    nếu σ_MC > σ*_MC thì
        σ*_MC ← σ_MC
        S*    ← E[i]
```

---

## 8. Các điểm implementation khác mô tả lý thuyết

### 8.1. Leo đồi không ưu tiên PR thấp

Comment trong `_local_search_hill_climbing` ghi *"ưu tiên đỉnh có PR thấp hơn"*, nhưng code dùng:

```python
u = rng.choice(cur_seeds)
```

tức chọn **đều ngẫu nhiên**, không dựa trên PageRank.

### 8.2. `node_community` không được dùng trong đột biến biên

`_mutate_boundary_directed` nhận tham số `node_community` nhưng không sử dụng. Việc chọn đỉnh thay thế chỉ dựa trên `boundary_nodes` và `pr_scores`.

### 8.3. Không có kho tinh hoa toàn cục

`S*_lie` chỉ phục vụ log/hội tụ. Quần thể không lưu lại cá thể tốt nhất của các thế hệ trước. Vì vậy cá thể tốt nhất có thể bị mất; Pha 4 chỉ chọn trong `N_elite` cá thể tốt nhất của **thế hệ cuối**.

### 8.4. `r_final` không điều khiển số lượt Monte Carlo

`self.r_final` chỉ được ghi vào `metadata`. Pha 4 gọi `problem.fitness()`, nên số lượt MC thực tế do `Evaluator.num_mc_simulations` quyết định (trong runner là `--mc`, không phải `--mc_val`). Runner sau đó kiểm định lại nghiệm bằng `val_problem` với `--mc_val`.

### 8.5. Đếm `total_evaluations` không đầy đủ

`total_evals` chỉ tăng ở:
- khởi tạo: `+N`
- mỗi cá thể sinh ra: `+1`
- mỗi cá thể tinh hoa ở Pha 4: `+1`

Các lần gọi LIE-2 trong **leo đồi** và **đột biến giải cứu** không được cộng vào. Ngoài ra, một lần MC ở Pha 4 được tính là `1` dù bên trong chạy `R` lượt mô phỏng.

### 8.6. Kiểm tra ngân sách chỉ ở đầu mỗi thế hệ

`total_evals ≥ B` chỉ được kiểm tra ở đầu vòng lặp thế hệ. Một thế hệ có thể vượt ngân sách; khởi tạo và Pha 4 vẫn chạy dù ngân sách đã hết.

### 8.7. `div` trong lịch sử hội tụ là giá trị cũ

`div` được đo **trước** khi giải cứu/tiến hóa nhưng được ghi vào `convergence_history` sau khi thế hệ kết thúc. Nếu đột biến giải cứu xảy ra, giá trị này không phản ánh quần thể mới.

### 8.8. Không sắp xếp lại sau leo đồi

`P_new` được sắp xếp trước khi leo đồi. Sau khi thay các tinh hoa bằng phiên bản cải thiện, danh sách không được sắp xếp lại. Thứ tự không còn đảm bảo giảm dần theo fitness.

### 8.9. Giá trị khởi tạo trong history

Bản ghi `generation = 0` dùng `mutation_rate = p_m_max` và `crossover_rate = p_c_min`, trong khi vòng lặp thực tế bắt đầu với `p_m` gần `p_m_max` và `p_c` gần `p_c_min`.

### 8.10. `elitism = 0` gây lỗi ở Pha 4

`final_elite = ...[:0]` là danh sách rỗng, sau đó `final_elite[0]` ném `IndexError`. Cần `N_elite ≥ 1`.

### 8.11. Đồ thị đầu vào được xử lý như vô hướng

`_build_nx_graph` chỉ thêm cạnh khi `u < v`. Với đồ thị vô hướng của dự án (CSR chứa cả hai chiều), cách này khử trùng đúng. Nếu truyền đồ thị **có hướng**, cạnh chỉ tồn tại theo chiều `u → v` với `u > v` sẽ bị bỏ sót.

### 8.12. LIE-2 là xấp xỉ, không phải kỳ vọng chính xác

Công thức loại các đỉnh đã là seed khỏi `P1`, loại các đỉnh thuộc `P1` khỏi `P2`, và giả định độc lập giữa các đường lan truyền. Vì vậy LIE-2 **không** bằng xác suất kích hoạt kỳ vọng thật; đây là hàm heuristic rẻ tiền để dẫn hướng tìm kiếm.

---

## 9. Độ phức tạp ước lượng

| Pha | Chi phí |
|-----|---------|
| 1 — Louvain + PageRank | `O(m)` trung bình cho Louvain; `O(I·m)` cho PageRank (`I = 100`) |
| 1 — Hạn ngạch + biên | `O(n + m)` |
| 2 — Khởi tạo | `O(N · k · d²)` (mỗi LIE-2 duyệt tối đa 2 hop) |
| 3 — Mỗi thế hệ | `O((N + N_elite · L_max) · k · d² + N · k² · d)` |
| 4 — Sàng lọc MC | `O(N_elite · R · m)` |
| Bộ nhớ | `O(n + m + N · k)` |

Trong đó `d` là bậc trung bình, `R` là số lượt MC của evaluator.

---

## 10. Ánh xạ mã giả ↔ code

| Mã giả | Hàm trong `iga.py` | Dòng |
|--------|--------------------|------|
| `TIEN_XU_LY` | `_preprocess_topology` | 148–227 |
| `LIE2` | `_evaluate_lie_2` | 233–265 |
| `KHOI_TAO_QUAN_THE` | `_create_initial_population` | 271–343 |
| `GIAI_DAU_TOPO` | `_tournament_select_topo` | 349–366 |
| `JACCARD_LANG_GIENG` | `_calc_neighborhood_overlap` | 368–376 |
| `LAI_GHEP_THONG_MINH` | `_crossover_smart` | 378–435 |
| `DOT_BIEN_BIEN` | `_mutate_boundary_directed` | 437–478 |
| `LEO_DOI` | `_local_search_hill_climbing` | 484–532 |
| `run` (Pha 3 + 4) | `run` | 538–792 |
