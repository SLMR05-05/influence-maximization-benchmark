# 3.2. Thiết lập thuật toán và giao thức thực nghiệm

Mục này trình bày tham số của GA cơ sở và IGA, cách chọn số hạt giống $k$, số lần chạy độc lập, số lượt Monte Carlo và hệ tiêu chí đánh giá. Thực nghiệm dùng 5 bộ dữ liệu Karate Club, Dolphins, ego-Facebook, NetHEPT, Email-Enron; mô hình IC-WC với $p(u\to v)=1/d_{in}(v)$; C++ Core cho mô phỏng, Python cho điều phối và phân tích.

Nguyên tắc so sánh công bằng: cùng đồ thị, cùng $k$, cùng mô hình lan truyền, cùng seed theo từng cặp chạy và cùng bộ kiểm định Monte Carlo độc lập. Khi cần, dùng thêm chế độ **equal computational budget** (giới hạn cùng số lần đánh giá).

## 3.2.1. Thiết lập tham số của thuật toán di truyền

**Bảng 3.1. Tham số GA cơ sở**

| Ký hiệu | Ý nghĩa | Giá trị |
|---|---|---:|
| $N$ | Kích thước quần thể | 50 |
| $T_{\max}$ | Số thế hệ tối đa | 100 |
| $q$ | Kích thước tournament | 5 |
| $P_c$ | Xác suất lai ghép | 0,90 |
| $P_m$ | Xác suất đột biến | 0,10 |
| $E$ | Số cá thể tinh hoa | 2 |
| $R_{search}$ | Số lượt MC khi tìm kiếm | 200 |
| $R_{val}$ | Số lượt MC khi kiểm định | 1.000 |

GA cơ sở dùng khởi tạo ngẫu nhiên đều, tournament selection, lai ghép theo tập (hợp hai cha mẹ rồi lấy ngẫu nhiên $k$ đỉnh, có sửa lỗi trùng), đột biến đều và elitism. Điều kiện dừng là đạt $T_{\max}$ hoặc chạm giới hạn đánh giá.

**Bảng 3.2. Tham số IGA**

| Ký hiệu | Ý nghĩa | Giá trị |
|---|---|---:|
| $N$ | Kích thước quần thể | 50 |
| $T_{\max}$ | Số thế hệ tối đa | 100 |
| $q$ | Kích thước tournament | 3 |
| $E$ | Số cá thể tinh hoa | 2 |
| $P_{c,\min},P_{c,\max}$ | Miền xác suất lai ghép | 0,60; 0,90 |
| $P_{m,\min},P_{m,\max}$ | Miền xác suất đột biến | 0,05; 0,35 |
| $\varepsilon_{div}$ | Ngưỡng đa dạng Jaccard | 0,30 |
| $\tau_{overlap}$ | Ngưỡng chồng lấn láng giềng | 0,50 |
| $\lambda_{tour}$ | Trọng số phủ cộng đồng | 0,25 |
| $L_{\max}$ | Số bước leo đồi | 10 |
| $R_{final}$ | Số lượt MC sàng lọc cuối | 1.000 |
| Tỷ lệ khởi tạo | Topo-guided / ngẫu nhiên | 80% / 20% |

Các tham số thích nghi của IGA:

$$p_m(t)=p_{m,\max}-(p_{m,\max}-p_{m,\min})\frac{t}{T_{\max}},$$

$$p_c(t)=p_{c,\min}+(p_{c,\max}-p_{c,\min})\frac{t}{T_{\max}}.$$

Nếu độ đa dạng Jaccard $div<\varepsilon_{div}$:

$$p_m\leftarrow\min\left(p_{m,\max},\ p_m+\frac{\varepsilon_{div}-div}{\varepsilon_{div}}(p_{m,\max}-p_{m,\min})\right).$$

Ngoài ra, IGA dùng khởi tạo 80% theo cộng đồng/PageRank, lai ghép lọc chồng lấn Jaccard với $\tau_{overlap}$, đột biến ưu tiên đỉnh biên, leo đồi trên tinh hoa và đột biến giải cứu khi trì trệ từ 3 thế hệ.

Hai thuật toán có cùng $N,T_{\max},k$ và cùng bộ kiểm định cuối, nhưng khác hàm fitness: GA dùng Monte Carlo trong suốt quá trình, IGA dùng xấp xỉ LIE-2 khi tiến hóa và chỉ dùng Monte Carlo ở bước sàng lọc cuối. Vì vậy kết quả được báo cáo theo cả hai góc nhìn: **native** (chất lượng và thời gian thực tế) và **equal-budget** (cùng số lần đánh giá).

## 3.2.2. Các giá trị số lượng nút hạt giống

Dải chuẩn dùng cho phân tích xu hướng:

$$k\in\{5,10,15,20,25,30,40,50\}.$$

Với đồ thị nhỏ, dùng dải hẹp hơn để tránh $k$ tiến sát $n$.

**Bảng 3.3. Giá trị $k$ theo bộ dữ liệu**

| Bộ dữ liệu | $n$ | Giá trị $k$ |
|---|---:|---|
| Karate Club | 34 | $\{2,4,6,8\}$ |
| Dolphins | 62 | $\{5,10,15\}$ |
| ego-Facebook | 4.039 | $\{5,10,20,30,40,50\}$ |
| NetHEPT | 15.233 | $\{5,10,20,30,40,50\}$ |
| Email-Enron | 36.692 | $\{10,20,30,40,50\}$ |

$k$ nhỏ kiểm tra khả năng chọn đỉnh chiến lược; $k$ trung bình kiểm tra cân bằng khám phá–khai thác; $k$ lớn kiểm tra chi phí, trùng lặp hạt giống và bão hòa spread. Trong mã nguồn, nếu $k>n$ thì $k$ tự động giảm về $n$.

## 3.2.3. Số lần chạy độc lập và số lượt mô phỏng Monte Carlo

**Bảng 3.4. Số lần chạy và số lượt Monte Carlo**

| Thành phần | Giá trị | Ghi chú |
|---|---:|---|
| GA, IGA | 30 lần độc lập | Mỗi cặp (dataset, $k$) |
| CELF, Degree, Degree Discount, PageRank | 1 lần | Thuật toán tất định |
| Pilot | 3–5 lần | Kiểm tra cấu hình trước khi chạy chính thức |
| $R_{search}$ | 200 | Tín hiệu fitness khi tìm kiếm |
| $R_{val}$ | 1.000 | Kiểm định chuẩn |
| $R_{val}^{high}$ | 10.000 | Xác nhận độ chính xác cao |

Lịch seed:

$$s_r=42+1009(r-1),\quad s_{val,r}=100000+s_r,\quad r=1,\ldots,30.$$

CELF dùng seed tìm kiếm 42 và seed kiểm định 100042. Cách này bảo đảm các lần chạy độc lập, cùng một cặp chạy dùng cùng seed cho mọi thuật toán, và tách seed tìm kiếm khỏi seed kiểm định.

Với mỗi tập hạt giống $S$:

$$\sigma(S)\approx\frac{1}{R}\sum_{i=1}^{R}|A_i(S)|,\qquad SE=\frac{s}{\sqrt{R}}.$$

Tăng $R$ từ 200 lên 1.000 giảm sai số chuẩn khoảng 2,24 lần; lên 10.000 giảm khoảng 7,07 lần.

Tổng lượt Monte Carlo xấp xỉ:

$$M_{GA}\approx R_{search}\left[N+(T_{\max}-1)(N-E)\right],$$

$$M_{IGA}\approx R_{search}E+M_{LIE},$$

trong đó $M_{LIE}$ là số lần gọi LIE-2. Do chi phí khác nhau, kết quả luôn báo cáo kèm chất lượng, thời gian, số lần đánh giá và chế độ equal-budget.

## 3.2.4. Các tiêu chí đánh giá

**Bảng 3.5. Hệ tiêu chí đánh giá**

| Nhóm | Tiêu chí | Công thức / hướng |
|---|---|---|
| Chất lượng | Spread trung bình | $\bar\sigma=\frac{1}{n_{run}}\sum_r\sigma_r$ (cao) |
| Chất lượng | Tỷ lệ lan truyền | $\rho=\bar\sigma/n$ (cao) |
| Chất lượng | Spread tốt nhất | $\sigma_{\max}=\max_r\sigma_r$ (cao) |
| Ổn định | Độ lệch chuẩn | $s=\sqrt{\frac{1}{n_{run}-1}\sum_r(\sigma_r-\bar\sigma)^2}$ (thấp) |
| Ổn định | CI 95% | $\bar\sigma\pm t_{0,975,n-1}\,s/\sqrt{n_{run}}$ (hẹp) |
| Hiệu năng | Thời gian | $\bar T$; tách $T_{search},T_{val}$ (thấp) |
| Hội tụ | $g_{90},g_{98}$ | Số thế hệ đạt 90%/98% nghiệm tốt nhất (thấp) |
| Tổng hợp | Composite | $C=0,45S_{norm}+0,30T_{norm}+0,15(1-SD_{norm})+0,10G_{norm}$ (cao) |
| Tổng hợp | CPI | $CPI=\frac{\bar\sigma(1-SD_{norm})}{\bar T\cdot\bar G}$ (cao) |
| Đánh đổi | Pareto | Spread vs. thời gian |
| Thống kê | Wilcoxon | $p<0,05$ |
| Thống kê | Friedman | Thứ hạng trung bình (thấp) |
| Thống kê | Holm–Bonferroni | Hiệu chỉnh $p$-value |
| Cấu trúc | Jaccard | $J(A,B)=\frac{|A\cap B|}{|A\cup B|}$ |
| Cải thiện | $\Delta$ | $\frac{\bar\sigma_{IGA}-\bar\sigma_{GA}}{\bar\sigma_{GA}}100\%$ |

Trong đó $S_{norm}$ là chuẩn hóa min–max của spread; $T_{norm}=T_{\min}/T$; $SD_{norm}$ là chuẩn hóa độ lệch chuẩn; $G_{norm}=1-\bar G/\max(\bar G)$. Chỉ số $g_{90},g_{98}$ đo tốc độ hội tụ. Composite và CPI dùng để cân bằng chất lượng, tốc độ, độ ổn định và hội tụ. Pareto xác định các thuật toán không bị trội về spread và thời gian.

Wilcoxon signed-rank so sánh từng cặp thuật toán; Friedman so sánh nhiều thuật toán trên nhiều block; Holm–Bonferroni kiểm soát sai số khi so sánh bội với $\alpha=0,05$. Ngoài ra, Jaccard đo độ ổn định tập hạt giống, và ablation study bật/tắt 5 cơ chế của IGA (`enable_guided_init`, `enable_adaptive_mutation`, `enable_degree_guided_mutation`, `enable_local_search`, `enable_overlap_filtering`) để đo đóng góp từng thành phần.

## 3.2.5. Phương pháp tổng hợp và kiểm định kết quả

Kết quả được lưu theo ba tầng: từng lần chạy, từng block thực nghiệm (bộ dữ liệu, mô hình, giá trị $k$) và bảng tổng hợp toàn cục.

Trước khi phân tích, dữ liệu được làm sạch: bỏ bản ghi trùng hoặc lỗi, kiểm tra seed hợp lệ và không trùng lặp. Chỉ so sánh các kết quả cùng điều kiện, cùng số lượt kiểm định; không trộn thời gian chạy WSL2 và Colab.

Với mỗi block, báo cáo spread trung bình, độ lệch chuẩn, khoảng tin cậy 95% và hệ số biến thiên. Các chỉ số được chuẩn hóa trong từng block để tính Composite và CPI; trọng số Composite được cố định trước khi xem kết quả.

Xếp hạng gồm hạng theo spread/Composite, hạng Friedman trung bình và Pareto frontier. Kiểm định dùng thiết kế ghép cặp cùng seed: Wilcoxon cho so sánh từng cặp, Friedman cho nhiều thuật toán và Holm–Bonferroni khi so sánh bội, với mức ý nghĩa 0,05. Chỉ kết luận có cải thiện khi vừa đạt ý nghĩa thống kê vừa vượt ngưỡng thực tiễn (ví dụ 1% spread).

Độ ổn định được đánh giá bằng Jaccard tập hạt giống và tần suất chọn đỉnh; khả năng tái lập được bảo đảm bằng config hash, phiên bản môi trường và seed.

Lưu ý: CPI chỉ mang tính tương đối vì `generations` của CELF là số vòng greedy; IGA và GA/CELF phải chạy trên cùng đồ thị; Friedman hiện mới dùng thứ hạng trung bình.

## Tóm tắt

- GA cơ sở: $N=50$, $T_{\max}=100$, $q=5$, $P_c=0,90$, $P_m=0,10$, $E=2$.
- IGA: cùng $N,T_{\max}$; $P_c\in[0,60;0,90]$, $P_m\in[0,05;0,35]$, $\varepsilon_{div}=0,30$, $\tau_{overlap}=0,50$, $\lambda_{tour}=0,25$, $L_{\max}=10$.
- $k$ khảo sát theo dải $\{5,10,15,20,25,30,40,50\}$, điều chỉnh theo kích thước dữ liệu.
- GA/IGA chạy 30 lần; CELF và heuristic tất định chạy 1 lần; $R_{search}=200$, $R_{val}=1.000$ (xác nhận cao: 10.000).
- Đánh giá gồm spread, độ ổn định, thời gian, hội tụ, Composite, CPI, Pareto, Wilcoxon, Friedman, Holm–Bonferroni, Jaccard và ablation.
- Kết quả tổng hợp theo 3 tầng, chuẩn hóa trong từng block và kiểm định ở $\alpha=0,05$.
