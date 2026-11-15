# 3.3. Các phương pháp đối chứng

Mục này trình bày các thuật toán đối chứng cho IGA theo ba nhóm: heuristic/tham lam (Degree, Degree Discount, PageRank, CELF), metaheuristic cơ sở (GA) và metaheuristic cải tiến (IGA). Tất cả được đánh giá trên cùng đồ thị, cùng $k$, cùng mô hình IC-WC và cùng bộ kiểm định Monte Carlo; thuật toán tất định chạy một lần, GA/IGA chạy 30 lần theo giao thức ở mục 3.2.3.

**Bảng 3.7. Các thuật toán đối chứng và thuật toán đề xuất**

| Thuật toán | Nhóm | Ngẫu nhiên | Dùng mô hình lan truyền khi tìm kiếm | Vai trò |
|---|---|---:|---:|---|
| Degree | Heuristic | Không | Không | Baseline bậc cao nhất |
| Degree Discount | Heuristic | Không | Một phần ($p$) | Baseline hiệu chỉnh trùng lặp |
| PageRank | Heuristic | Không | Không | Baseline quan trọng toàn cục |
| CELF | Tham lam + xấp xỉ | Không | Có (Monte Carlo) | Baseline chất lượng cao, có bảo đảm xấp xỉ |
| GA cơ sở | Metaheuristic | Có | Có (Monte Carlo) | Đối chứng di truyền chuẩn |
| IGA | Metaheuristic | Có | Có (LIE-2 + Monte Carlo cuối) | Thuật toán đề xuất |

## 3.3.1. Nhóm thuật toán tham lam và xấp xỉ

### a) Degree Centrality

Chọn $k$ đỉnh có bậc lớn nhất:

$$score_{deg}(v)=d(v),\qquad S=\operatorname{TopK}_{v\in V}score_{deg}(v).$$

Với CSR: $d(v)=row\_ptr[v+1]-row\_ptr[v]$. Tính bậc $O(|V|)$, sắp xếp $O(|V|\log |V|)$ (hoặc $O(|V|\log k)$ với heap), bộ nhớ $O(|V|)$.

**Ưu điểm:** rất nhanh, không phụ thuộc mô hình lan truyền, tất định.  
**Hạn chế:** bỏ qua trùng lặp vùng ảnh hưởng, cấu trúc cộng đồng và xác suất cạnh; dễ chọn nhiều hub gần nhau.

### b) Degree Discount

Degree Discount (Chen và cộng sự, 2009) giảm bậc hiệu dụng của lân cận sau mỗi hạt giống được chọn. Với IC xác suất đều $p$, gọi $t(v)$ là số hạt giống đã chọn trong lân cận của $v$:

$$dd(v)=d(v)-2t(v)-\left(d(v)-t(v)\right)t(v)p.$$

Quy trình: khởi tạo $t(v)=0$, $dd(v)=d(v)$; lặp $k$ lần chọn $u$ chưa chọn có $dd(u)$ lớn nhất, thêm vào $S$, rồi với mỗi lân cận $v$ chưa chọn tăng $t(v)$ và cập nhật $dd(v)$. Cài đặt dùng $p=0,01$ mặc định, duyệt toàn bộ $V$ mỗi vòng và cập nhật lân cận từ CSR.

Độ phức tạp:

$$O\left(k|V|+\sum_{u\in S}d(u)\right)=O\left(k(|V|+|E|)\right),$$

bộ nhớ $O(|V|+|E|)$.

**Ưu điểm:** nhanh hơn CELF, giảm chọn đỉnh kề nhau, thường tốt hơn Degree.  
**Hạn chế:** công thức chiết khấu chủ yếu đúng cho IC xác suất đều; với IC-WC chỉ là xấp xỉ; không có bảo đảm xấp xỉ.

### c) PageRank

PageRank đo tầm quan trọng toàn cục:

$$PR(v)=\frac{1-d}{N}+d\sum_{u\in In(v)}\frac{PR(u)}{outdeg(u)},$$

với $d=0,85$. Cài đặt khởi tạo $PR(v)=1/N$, lặp power iteration đến khi $L_1<10^{-6}$ hoặc tối đa 100 vòng, rồi chọn top $k$. Độ phức tạp $O(I|E|)$, bộ nhớ $O(|V|+|E|)$.

**Ưu điểm:** nắm tầm quan trọng toàn cục, tất định, chi phí thấp.  
**Hạn chế:** không mô hình hóa lan truyền/xác suất cạnh, có thể chọn đỉnh gần nhau, không có bảo đảm xấp xỉ.

### d) CELF — Cost-Effective Lazy Forward

Hàm lan truyền $\sigma(S)$ monotone và submodular, nên greedy đạt:

$$\sigma(S_{greedy})\ge\left(1-\frac{1}{e}\right)\sigma(S^*)\approx0,632\,\sigma(S^*).$$

CELF (Leskovec và cộng sự, 2007) dùng lazy forward: lợi ích biên

$$\Delta_S(v)=\sigma(S\cup\{v\})-\sigma(S)$$

chỉ giảm khi $S$ mở rộng, nên giá trị cũ là cận trên và chỉ cần tính lại khi cần. Quy trình: tính $\Delta_\emptyset(v)$ cho mọi $v$; đưa vào max-heap; lấy khóa lớn nhất; nếu giá trị được tính ở vòng hiện tại thì chọn, nếu là giá trị cũ thì tính lại rồi đẩy lại; lặp đến đủ $k$.

Hai biến thể: **UC** dùng khóa $\Delta_S(v)$; **CB** dùng $\Delta_S(v)/c(v)$. Với $c(v)=1$ hai biến thể trùng nhau; cài đặt chạy cả hai và chọn nghiệm có spread cuối lớn hơn.

Cận trên trực tuyến:

$$OPT\le\sigma(A)+\sum_{i=1}^{k-1}\Delta_{s_i}+\lambda\Delta_{s_k},$$

trong đó các đỉnh còn lại sắp giảm dần theo $\Delta_S(v)/c(v)$, $k$ là điểm cắt theo ngân sách, $\lambda$ là phần ngân sách còn lại chia cho chi phí đỉnh tại điểm cắt. Cận được lưu trong `metadata["online_bound"]`.

CELF chạy trên đồ thị gốc nếu C++ Core khả dụng, ngân sách mặc định $k$, seed 42, trả về một tập hạt giống và ghi lịch sử chọn. Khởi tạo tốn $O(|V|R|E|)$; trường hợp xấu nhất $O(k|V|R|E|)$; bộ nhớ $O(|V|+|E|)$.

**Ưu điểm:** chất lượng cao, bảo đảm $1-1/e$ khi hàm lan truyền chính xác và submodular, nhanh hơn greedy chuẩn.  
**Hạn chế:** vẫn tốn kém trên đồ thị lớn; nhiễu Monte Carlo có thể làm sai thứ tự lợi ích biên; chỉ cho một nghiệm tham lam, không có khám phá toàn cục.

### e) Vai trò

Degree, Degree Discount và PageRank là baseline chi phí thấp; CELF là baseline chất lượng cao có bảo đảm lý thuyết. Nếu IGA không vượt được các baseline này trên một số đồ thị, cần xem lại toán tử hoặc ngân sách đánh giá.

## 3.3.2. Thuật toán di truyền cơ sở

GA cơ sở là di truyền chuẩn, không dùng tri thức cộng đồng/bậc/PageRank, dùng làm đối chứng trực tiếp để đo đóng góp của IGA.

**Biểu diễn.** Mỗi cá thể là tập $k$ đỉnh phân biệt:

$$S=\{s_1,\ldots,s_k\},\quad s_i\in V,\ s_i\neq s_j,$$

sắp tăng dần; nếu $k\ge|V|$ thì chứa toàn bộ đỉnh.

**Khởi tạo.** $N$ cá thể chọn ngẫu nhiên đều $k$ đỉnh:

$$S_i\sim\operatorname{Uniform}\left(\binom{V}{k}\right).$$

**Fitness.** Spread trung bình trên $R_{search}$ lượt Monte Carlo:

$$f(S)=\frac{1}{R_{search}}\sum_{r=1}^{R_{search}}|A_r(S)|.$$

**Chọn lọc.** Tournament kích thước $q$: chọn ngẫu nhiên $q$ cá thể, giữ cá thể fitness cao nhất.

**Lai ghép.** Lai ghép theo tập: $U=S_{p1}\cup S_{p2}$; nếu $|U|<k$ bổ sung đỉnh ngẫu nhiên; sinh con bằng cách lấy ngẫu nhiên $k$ đỉnh từ $U$. Bản Python còn có one-point crossover sửa lỗi để bảo đảm đúng $k$ đỉnh phân biệt.

**Đột biến.** Với từng gene, nếu random $<P_m$ thì thay bằng một đỉnh chưa có trong cá thể, rồi sắp xếp lại.

**Elitism.** Giữ $E$ cá thể tốt nhất sang thế hệ sau.

**Vòng lặp:**

```text
Khởi tạo P gồm N cá thể; đánh giá bằng Monte Carlo; lưu best_ever
for t = 1..T_max:
    nếu đạt giới hạn đánh giá: dừng
    P_new = E cá thể tốt nhất
    while |P_new| < N:
        p1, p2 = tournament(P)
        (c1, c2) = crossover(p1, p2) nếu random() < Pc, ngược lại (p1, p2)
        c1, c2 = mutate(c1), mutate(c2)
        đánh giá c1, c2; thêm vào P_new
    P = P_new; cập nhật best_ever và lịch sử hội tụ
Đánh giá lại best_ever; trả về best_ever, lịch sử, top 5
```

Điều kiện dừng: đạt $T_{\max}$ hoặc chạm giới hạn đánh giá. Độ phức tạp:

$$O\left(T_{\max}NR_{search}|E|\right),$$

chi phí toán tử $O(Nk)$ mỗi thế hệ; bộ nhớ $O(Nk+|V|+|E|)$.

**Ưu điểm:** đơn giản, dễ tái lập, tìm kiếm toàn cục, không giả định cấu trúc cộng đồng, baseline công bằng.  
**Hạn chế:** khởi tạo ngẫu nhiên, chi phí Monte Carlo lớn, $P_c/P_m$ cố định, dễ chọn hạt giống gần nhau, hội tụ chậm trên đồ thị lớn.

## 3.3.3. Thuật toán di truyền cải tiến được đề xuất

IGA khắc phục bốn hạn chế của GA: (1) khởi tạo có tri thức bằng Louvain/PageRank; (2) $P_c,P_m$ thích nghi theo thế hệ và độ đa dạng; (3) lọc chồng lấn Jaccard và ưu tiên đỉnh biên; (4) dùng LIE-2 thay Monte Carlo trong tiến hóa, chỉ kiểm định Monte Carlo ở bước cuối.

IGA gồm bốn pha: tiền xử lý topo; khởi tạo 80% topo-guided + 20% ngẫu nhiên; tiến hóa thích nghi; sàng lọc tinh hoa bằng Monte Carlo.

### a) Pha 1 — Tiền xử lý và tri thức topo

- Dựng đồ thị vô hướng từ CSR, thêm $(u,v)$ khi $u<v$ để khử trùng.
- Louvain tối đa hóa modularity, trả về $\mathcal C=\{C_1,\ldots,C_{N_c}\}$ sắp giảm theo kích thước; nếu lỗi, dùng thành phần liên thông.
- PageRank với $d=0,85$, tối đa 100 vòng; nếu không hội tụ, dùng bậc chuẩn hóa $PR(v)\approx d(v)/\sum_u d(u)$.
- Hạn ngạch cộng đồng: $q_j=k|C_j|/N$; khởi tạo $k_j=\min(|C_j|,\lfloor q_j\rfloor)$; phân bổ phần dư $r_j=q_j-k_j$ cho các cộng đồng có $r_j$ lớn nhất đến khi đủ $k$ hoặc chạm trần.
- Đỉnh biên: $u\in Boundary\iff\exists v\in N(u):comm(v)\neq comm(u)$; nếu không có, dùng toàn bộ $V$.

### b) Pha 2 — Khởi tạo có định hướng

80% cá thể chọn theo hạn ngạch cộng đồng và PageRank:

$$P(u\mid C_j)=\frac{PR(u)}{\sum_{w\in C_j}PR(w)};$$

20% chọn ngẫu nhiên đều để duy trì khám phá. Nếu thiếu đỉnh, bổ sung theo PageRank; nếu vượt $k$, cắt bớt.

Hàm đánh giá nhanh LIE-2:

$$\sigma_{LIE\text{-}2}(S)=|S|+\sum_{v\in N_1(S)}P_1(v)+\sum_{w\in N_2(S)}P_2(w),$$

$$P_1(v)=1-\prod_{u\in S,(u,v)\in E}(1-p_{uv}),$$

$$P_2(w)=1-\prod_{v\in N_1(S),(v,w)\in E}(1-P_1(v)p_{vw}).$$

Chi phí gần $O(kd^2)$, rẻ hơn Monte Carlo $O(R|E|)$; đây là xấp xỉ heuristic để dẫn hướng tìm kiếm.

### c) Pha 3 — Tiến hóa thích nghi

**Tham số thích nghi:**

$$p_m(t)=p_{m,\max}-(p_{m,\max}-p_{m,\min})\frac{t}{T_{\max}},$$

$$p_c(t)=p_{c,\min}+(p_{c,\max}-p_{c,\min})\frac{t}{T_{\max}}.$$

Giai đoạn đầu ưu tiên khám phá bằng đột biến; giai đoạn sau ưu tiên khai thác bằng lai ghép.

**Đa dạng và giải cứu.** Đo bằng Jaccard trung bình giữa các cặp cá thể. Nếu $div<\varepsilon_{div}$:

$$p_m\leftarrow\min\left(p_{m,\max},p_m+\frac{\varepsilon_{div}-div}{\varepsilon_{div}}(p_{m,\max}-p_{m,\min})\right).$$

Nếu trì trệ ít nhất 3 thế hệ: giữ $E$ tinh hoa, tái sinh $N-E$ cá thể theo hạn ngạch cộng đồng không dùng PageRank, đánh giá lại bằng LIE-2.

**Giải đấu topo:**

$$Fitness_{tour}(S)=f_{LIE}(S)+\lambda_{tour}\left|\{C_j:S\cap C_j\neq\emptyset\}\right|,$$

với $\lambda_{tour}=0,25$ để khuyến khích phủ nhiều cộng đồng.

**Lai ghép lọc chồng lấn.** Với $U=S_{p1}\cup S_{p2}$, sắp giảm theo PageRank; chỉ nhận $cand$ nếu với mọi $s$ đã chọn:

$$J(cand,s)=\frac{|N(cand)\cap N(s)|}{|N(cand)\cup N(s)|}\le\tau_{overlap}=0,50.$$

Nếu thiếu, bổ sung từ $U$ rồi từ top PageRank toàn mạng.

**Đột biến biên.** Chọn $u_{weak}=\arg\min_{u\in S}PR(u)$, thay bằng đỉnh biên chưa dùng, chọn ngẫu nhiên trong top 20% PageRank; nếu hết đỉnh biên thì chọn ngẫu nhiên đỉnh chưa dùng.

**Leo đồi.** Trên $E$ tinh hoa, lặp tối đa $L_{\max}=10$: chọn ngẫu nhiên $u\in S$, xét lân cận $v\notin S$, chọn $v$ có PageRank cao nhất, thay $u$ nếu $f_{LIE}$ tăng; ngược lại dừng.

**Elitism.** Giữ $E=2$ cá thể tốt nhất; sau sinh sản, sắp xếp quần thể và leo đồi trên nhóm tinh hoa.

### d) Pha 4 — Sàng lọc bằng Monte Carlo

Hợp nhất cá thể tốt nhất $S^*_{LIE}$ và các cá thể tốt nhất thế hệ cuối, loại trùng, chọn $E$ ứng viên. Đánh giá lại:

$$\sigma_{MC}(S)=\frac{1}{R_{final}}\sum_{r=1}^{R_{final}}|A_r(S)|,$$

chọn ứng viên có $\sigma_{MC}$ lớn nhất. Bước này bảo đảm nghiệm cuối được đánh giá bằng mô hình lan truyền thật.

### e) Mã giả tổng quát

```text
Đầu vào: G, k, N, T_max, R_final, seed
Pha 1: G_u = vô hướng hóa(G); C = Louvain(G_u); PR = PageRank(G_u)
       quota = LargestRemainder(k, C); boundary = đỉnh biên
Pha 2: P = 80% topo-guided + 20% ngẫu nhiên; đánh giá bằng LIE-2
       S*_LIE = cá thể tốt nhất; stagnation = 0
Pha 3: for t = 1..T_max:
           cập nhật p_m(t), p_c(t); div = Jaccard(P)
           nếu div < epsilon_div: tăng p_m
           nếu stagnation >= 3: P = đột biến giải cứu(P); stagnation = 0
           P_new = E tinh hoa
           while |P_new| < N:
               p1, p2 = giải đấu topo(P)
               child = lai ghép lọc overlap(p1, p2) nếu random() < p_c(t), ngược lại p1
               nếu random() < p_m(t): child = đột biến biên(child)
               child.fitness = LIE-2(child); thêm child vào P_new
           leo đồi trên E tinh hoa; P = P_new; cập nhật S*_LIE, stagnation
Pha 4: ứng viên = S*_LIE + top E cá thể của P; loại trùng
       đánh giá bằng R_final lượt Monte Carlo; trả về nghiệm tốt nhất
```

### f) So sánh GA cơ sở và IGA

**Bảng 3.8. Đối chiếu GA cơ sở và IGA**

| Thành phần | GA cơ sở | IGA |
|---|---|---|
| Khởi tạo | Ngẫu nhiên đều | 80% topo-guided + 20% ngẫu nhiên |
| Fitness | Monte Carlo | LIE-2 khi tiến hóa, Monte Carlo cuối |
| Chọn lọc | Tournament theo fitness | Tournament topo có trọng số phủ cộng đồng |
| Lai ghép | Hợp tập + lấy ngẫu nhiên $k$ | Hợp tập + sắp PageRank + lọc Jaccard |
| Đột biến | Đều, thay gene ngẫu nhiên | Khai thác biên + PageRank |
| $P_c$ | Cố định | Thích nghi $[0,60;0,90]$ |
| $P_m$ | Cố định | Thích nghi $[0,05;0,35]$ |
| Trì trệ | Không | Đột biến giải cứu khi trì trệ ≥ 3 thế hệ |
| Tinh chỉnh | Không | Leo đồi $L_{\max}=10$ trên tinh hoa |
| Chi phí | Cao ($N\cdot T_{\max}$ lần MC) | Thấp hơn nhờ LIE-2 |

### g) Độ phức tạp

- Pha 1: Louvain trung bình $O(|E|)$; PageRank $O(I|E|)$, $I\le100$; hạn ngạch và đỉnh biên $O(|V|+|E|)$.
- Pha 2: $O(Nkd^2)$.
- Pha 3: $O\left(T_{\max}\left((N+EL_{\max})kd^2+Nk^2d\right)\right)$.
- Pha 4: $O(ER_{final}|E_{graph}|)$.
- Bộ nhớ: $O(|V|+|E|+Nk)$.

Trong đó $d$ là bậc trung bình, $E_{graph}$ là tập cạnh của đồ thị.

### h) Ưu điểm và hạn chế

**Ưu điểm:** tận dụng cấu trúc cộng đồng/PageRank; giảm chi phí Monte Carlo nhờ LIE-2; duy trì đa dạng và có giải cứu trì trệ; giảm trùng lặp nhờ Jaccard và đỉnh biên; có thể bật/tắt từng cơ chế để ablation.

**Hạn chế:** chi phí tiền xử lý tăng theo đồ thị; LIE-2 chỉ là xấp xỉ hai hop; chất lượng phụ thuộc phân hoạch cộng đồng; nhiều tham số cần điều chỉnh; GUI có thể chạy IGA trên đồ thị preview, nên cần bảo đảm cùng đồ thị khi so sánh chính thức.

## Tóm tắt mục 3.3

- **Heuristic/tham lam:** Degree chọn top $k$ theo bậc; Degree Discount chiết khấu bậc lân cận; PageRank chọn theo tầm quan trọng toàn cục; CELF dùng greedy + lazy forward, bảo đảm $1-1/e$ và có cận trên trực tuyến.
- **GA cơ sở:** khởi tạo ngẫu nhiên, tournament, lai ghép theo tập, đột biến đều, elitism; là baseline trực tiếp của IGA.
- **IGA:** bốn pha — tiền xử lý Louvain/PageRank, khởi tạo topo-guided, tiến hóa thích nghi với LIE-2, sàng lọc Monte Carlo cuối; có năm cơ chế cải tiến và hỗ trợ ablation.
- Bộ thuật toán tạo phổ đối chứng từ chi phí thấp (Degree, PageRank) đến chất lượng cao (CELF), từ metaheuristic thuần (GA) đến metaheuristic có tri thức cấu trúc (IGA).
