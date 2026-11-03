# Nguồn gốc và Tác giả các Thuật toán (Algorithm Sources & Attribution)

## Tổng quan

Tài liệu này liệt kê nguồn gốc, bài báo gốc và repository GitHub tham khảo cho từng thuật toán trong dự án IM-Benchmark-Lab.

---

## 1. Degree Centrality Heuristic

| Thuộc tính | Chi tiết |
|-----------|----------|
| **Tên đầy đủ** | Degree Centrality Heuristic for Influence Maximization |
| **Bài báo gốc** | Khái niệm cơ bản trong lý thuyết đồ thị (Wasserman & Faust, 1994) |
| **Repository tham khảo** | [lorenzobloise/netmax](https://github.com/lorenzobloise/netmax) — MIT License |
| **Tác giả repo** | Lorenzo Bloise (DIMES Department, University of Calabria, Italy) |
| **File trong dự án** | `src/im_research/algorithms/heuristics/degree.py` |
| **Mô tả** | Chọn top-k đỉnh có bậc cao nhất. Thuật toán cơ sở, không cần bài báo cụ thể. |
| **Độ phức tạp** | O(|V| log k) |

---

## 2. Degree Discount Heuristic

| Thuộc tính | Chi tiết |
|-----------|----------|
| **Tên đầy đủ** | Degree Discount Heuristic for Influence Maximization (IC model) |
| **Bài báo gốc** | Chen, W., Wang, Y., & Yang, S. (2009). "Efficient Influence Maximization in Social Networks." *KDD 2009*, pp. 199–208. DOI: 10.1145/1557019.1557047 |
| **Repository tham khảo** | [lorenzobloise/netmax](https://github.com/lorenzobloise/netmax) — MIT License (class `DegDis`) |
| **Tác giả repo** | Lorenzo Bloise (DIMES Department, University of Calabria, Italy) |
| **Tác giả bài báo** | Wei Chen, Yajun Wang, Siyu Yang (Microsoft Research Asia & Tsinghua University) |
| **File trong dự án** | `src/im_research/algorithms/heuristics/degree_discount.py` |
| **Mô tả** | Giảm bậc lân cận sau khi chọn đỉnh hạt giống. Khi chọn node u làm seed, discount bậc hiệu dụng của láng giềng v theo số seed đã chọn trong lân cận v. |
| **Độ phức tạp** | O(k · \|V\|) |

---

## 3. PageRank Heuristic

| Thu thuộc tính | Chi tiết |
|-----------|----------|
| **Tên đầy đủ** | PageRank-based Heuristic for Influence Maximization |
| **Bài báo gốc** | Page, L., Brin, S., Motwani, R., & Winograd, T. (1999). "The PageRank Citation Ranking: Bringing Order to the Web." Stanford InfoLab. |
| **Repository tham khảo** | [lorenzobloise/netmax](https://github.com/lorenzobloise/netmax) — MIT License (class `Group_PR`) |
| **Tác giả repo** | Lorenzo Bloise (DIMES Department, University of Calabria, Italy) |
| **Tác giả bài báo** | Larry Page, Sergey Brin, Rajeev Motwani, Terry Winograd (Stanford University) |
| **File trong dự án** | `src/im_research/algorithms/heuristics/pagerank.py` |
| **Mô tả** | Power Iteration: PR(v) = (1-d)/N + d × Σ PR(u)/out_degree(u). Chọn top-k đỉnh theo PageRank score. |
| **Độ phức tạp** | O(iterations × \|E\|) |

---

## 4. CELF (Cost-Effective Lazy Forward)

| Thuộc tính | Chi tiết |
|-----------|----------|
| **Tên đầy đủ** | CELF Greedy Algorithm for Influence Maximization |
| **Bài báo gốc** | Leskovec, J., Krause, A., Guestrin, C., Faloutsos, C., VanBriesen, J., & Glance, N. (2007). "Cost-effective Outbreak Detection in Networks." *KDD 2007*, pp. 420–429. |
| **Repository tham khảo** | [lorenzobloise/netmax](https://github.com/lorenzobloise/netmax) — MIT License (class `CELF`) |
| **Tác giả repo** | Lorenzo Bloise (DIMES Department, University of Calabria, Italy) |
| **Tác giả bài báo** | Jure Leskovec, Andreas Krause, Carlos Guestrin, Christos Faloutsos, Jeanne VanBriesen, Natalie Glance |
| **File trong dự án** | `src/im_research/algorithms/greedy/celf.py` |
| **Mô tả** | Tối ưu Greedy bằng submodularity + lazy evaluation. Giảm ~700x số lần đánh giá so với Greedy gốc. |
| **Độ phức tạp** | O(k × R × \|E\|) với hằng số giảm đáng kể |

---

## 5. Baseline GA (Genetic Algorithm)

| Thuộc tính | Chi tiết |
|-----------|----------|
| **Tên đầy đủ** | Baseline Genetic Algorithm for Influence Maximization |
| **Bài báo gốc** | Holland, J. H. (1975). "Adaptation in Natural and Artificial Systems." University of Michigan Press. |
| **Repository tham khảo** | Tự triển khai theo chuẩn GA (không có repo cụ thể) |
| **Tác giả bài báo** | John H. Holland (University of Michigan) |
| **File trong dự án** | `src/im_research/algorithms/evolutionary/ga.py` |
| **Mô tả** | GA chuẩn: random uniform init, tournament selection, set-based crossover, uniform mutation, elitism. |
| **Độ phức tạp** | O(gen × pop × R) |

---

## Thuật toán đã xóa

| Thuật toán | Nguồn | Trạng thái |
|-----------|-------|------------|
| **IGA** (Improved GA) | Thuật toán đề xuất của dự án (tự phát triển) | ❌ Đã xóa |

---

## Thuật toán chưa triển khai

| Thuật toán | Nguồn tham khảo | Repository gợi ý |
|-----------|-----------------|-----------------|
| **Discrete PSO** | Kennedy & Eberhart (1995) — "Particle Swarm Optimization" | [arartawil/Influence-Maximization-Algorithms-Comprehensive-Benchmark](https://github.com/arartawil/Influence-Maximization-Algorithms-Comprehensive-Benchmark) |
| **ACO** | Dorigo et al. (1996) — "Ant System: Optimization by a Colony of Cooperating Agents" | [arartawil/Influence-Maximization-Algorithms-Comprehensive-Benchmark](https://github.com/arartawil/Influence-Maximization-Algorithms-Comprehensive-Benchmark) |

---

## Repository tham khảo chính

| Repository | URL | License | Stars |
|-----------|-----|---------|-------|
| **netmax** | https://github.com/lorenzobloise/netmax | MIT | 16 |
| **IM Comprehensive Benchmark** | https://github.com/arartawil/Influence-Maximization-Algorithms-Comprehensive-Benchmark | MIT | — |
| **CELF Implementation** | https://github.com/mmoghey/CELF-Hill-Climbing-Algorithm-Implementation | — | 3 |

---

## Ghi chú về Attribution

- Tất cả thuật toán trong dự án đều được **tự triển khai lại** (re-implemented) theo mô tả trong bài báo gốc, **không copy trực tiếp** mã nguồn từ bất kỳ repository nào.
- Mã nguồn trong dự án tuân theo **interface chung** (`BaseAlgorithm` + `AlgorithmResult`) để đảm bảo tính nhất quán.
- Repository **netmax** (Lorenzo Bloise) là nguồn tham khảo chính cho Degree Discount, PageRank, CELF và Degree Centrality.
- Repository **arartawil** là nguồn tham khảo cho PSO và ACO (chưa triển khai).
