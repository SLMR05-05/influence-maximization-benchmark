"""
Improved Genetic Algorithm (IGA) for Influence Maximization.
Triển khai toàn diện theo quy trình 4 Pha:
  Pha 1: Tiền xử lý đồ thị và trích xuất tri thức topo (Louvain + PageRank + Largest Remainder Quota Allocation)
  Pha 2: Khởi tạo quần thể định hướng IGA thế hệ t = 0 (80% Topo-guided, 20% Controlled Random, đánh giá nhanh LIE-2)
  Pha 3: Chu trình tiến hóa thích nghi nhanh (p_m/p_c thích nghi, giám sát đa dạng, đột biến giải cứu,
         giải đấu topo, lai ghép thông minh lọc chồng lấn láng giềng tau_overlap, đột biến khai thác biên,
         tìm kiếm cục bộ leo đồi L_max trên nhóm tinh hoa)
  Pha 4: Sàng lọc tinh hoa cuối cùng bằng mô phỏng Monte Carlo (R_final)
"""

from __future__ import annotations
import time
import random
from typing import List, Dict, Any, Tuple, Set

import numpy as np
import networkx as nx

from im_research.core.interfaces import BaseAlgorithm, AlgorithmResult
from im_research.core.problem import IMProblem
from im_research.core.solution import Solution, Population


class IGA(BaseAlgorithm):
    """
    Improved Genetic Algorithm (IGA) for Influence Maximization (Central Proposed Method).

    Parameters:
    -----------
    pop_size : int
        Kích thước quần thể N (default: 50).
    max_generations : int
        Số thế hệ tiến hóa tối đa T_max (default: 100).
    p_c_min : float
        Xác suất lai ghép tối thiểu (default: 0.60).
    p_c_max : float
        Xác suất lai ghép tối đa (default: 0.90).
    p_m_min : float
        Xác suất đột biến tối thiểu (default: 0.05).
    p_m_max : float
        Xác suất đột biến tối đa (default: 0.35).
    tournament_size : int
        Kích thước giải đấu q (default: 3).
    elitism : int
        Số lượng cá thể tinh hoa N_elite (default: 2).
    epsilon_div : float
        Ngưỡng đa dạng di truyền epsilon_div (default: 0.30).
    tau_overlap : float
        Ngưỡng chồng lấn láng giềng tau_overlap (default: 0.50).
    lambda_tour : float
        Hệ số trọng số đa dạng cộng đồng trong giải đấu (default: 0.25).
    local_search_steps : int
        Số bước tìm kiếm cục bộ tối đa L_max (default: 10).
    r_final : int
        Số lượt mô phỏng Monte Carlo ở pha sàng lọc kết thúc R_final (default: 1000).

    Ablation Study Controls:
    ------------------------
    enable_guided_init : bool
        Bật/tắt khởi tạo định hướng topo (80% topo, 20% random).
    enable_adaptive_mutation : bool
        Bật/tắt tham số đột biến thích ứng động theo thế hệ & đa dạng.
    enable_degree_guided_mutation : bool
        Bật/tắt đột biến khai thác biên cộng đồng & PageRank.
    enable_local_search : bool
        Bật/tắt tìm kiếm cục bộ leo đồi L_max trên nhóm tinh hoa.
    enable_overlap_filtering : bool
        Bật/tắt lọc chồng lấn láng giềng tau_overlap trong lai ghép thông minh.
    """

    def __init__(
        self,
        pop_size: int = 50,
        max_generations: int = 100,
        p_c_min: float = 0.60,
        p_c_max: float = 0.90,
        p_m_min: float = 0.05,
        p_m_max: float = 0.35,
        tournament_size: int = 3,
        elitism: int = 2,
        epsilon_div: float = 0.30,
        tau_overlap: float = 0.50,
        lambda_tour: float = 0.25,
        local_search_steps: int = 10,
        r_final: int = 1000,
        # Backward compatibility parameters
        crossover_rate: float | None = None,
        mutation_rate_base: float | None = None,
        mutation_rate_max: float | None = None,
        diversity_threshold: float | None = None,
        # Ablation study controls
        enable_guided_init: bool = True,
        enable_adaptive_mutation: bool = True,
        enable_degree_guided_mutation: bool = True,
        enable_local_search: bool = True,
        enable_overlap_filtering: bool = True,
        log_callback: Any = None,
        progress_callback: Any = None,
    ):
        super().__init__(name="IGA")
        self.pop_size = pop_size
        self.max_generations = max_generations

        # Set crossover & mutation parameters with backward-compatibility fallbacks
        self.p_c_min = p_c_min
        self.p_c_max = crossover_rate if crossover_rate is not None else p_c_max
        self.p_m_min = mutation_rate_base if mutation_rate_base is not None else p_m_min
        self.p_m_max = mutation_rate_max if mutation_rate_max is not None else p_m_max

        self.tournament_size = tournament_size
        self.elitism = elitism
        self.epsilon_div = diversity_threshold if diversity_threshold is not None else epsilon_div
        self.tau_overlap = tau_overlap
        self.lambda_tour = lambda_tour
        self.local_search_steps = local_search_steps
        self.r_final = r_final
        self.log_callback = log_callback
        self.progress_callback = progress_callback

        # Ablation study toggles
        self.enable_guided_init = enable_guided_init
        self.enable_adaptive_mutation = enable_adaptive_mutation
        self.enable_degree_guided_mutation = enable_degree_guided_mutation
        self.enable_local_search = enable_local_search
        self.enable_overlap_filtering = enable_overlap_filtering

        # Internal caches for topology
        self._adj_cache: Dict[int, Set[int]] = {}

    def _log(self, msg: str) -> None:
        """Outputs log to stdout and forwards to optional GUI log_callback."""
        print(f"      [IGA] {msg}", flush=True)
        if self.log_callback is not None:
            try:
                self.log_callback(f"[IGA] {msg}")
            except Exception:
                pass

    # ═════════════════════════════════════════════════════════════════════════
    #  PHA 1: TIỀN XỬ LÝ ĐỒ THỊ VÀ TRÍCH XUẤT TRI THỨC TOPO
    # ═════════════════════════════════════════════════════════════════════════

    def _build_nx_graph(self, graph: Any, n: int) -> nx.Graph:
        """Constructs an undirected NetworkX graph from C++ CSR Graph or interface."""
        g_nx = nx.Graph()
        g_nx.add_nodes_from(range(n))

        if hasattr(graph, "row_ptr") and hasattr(graph, "col_indices"):
            row_ptr = graph.row_ptr()
            col_indices = graph.col_indices()
            for u in range(n):
                neighbors = col_indices[row_ptr[u] : row_ptr[u + 1]]
                for v in neighbors:
                    if u < v:
                        g_nx.add_edge(u, v)
        elif hasattr(graph, "edges"):
            g_nx.add_edges_from(graph.edges())
        return g_nx

    def _preprocess_topology(
        self, problem: IMProblem, seed: int
    ) -> Tuple[List[List[int]], List[int], np.ndarray, np.ndarray, List[int], nx.Graph]:
        """
        Pha 1: Tiền xử lý đồ thị:
        1. Phân hoạch cộng đồng bằng Louvain: {C_1, C_2, ..., C_Nc}
        2. Tính điểm PageRank cho toàn bộ đỉnh v in V: PR(v)
        3. Phân bổ hạn ngạch hạt giống theo Phương pháp phần dư lớn nhất: {k_j}
        4. Xác định danh sách đỉnh biên (boundary nodes) kết nối liên cộng đồng.
        """
        n = problem.num_nodes
        k = problem.k
        g_nx = self._build_nx_graph(problem.graph, n)

        # 1. Thuật toán Louvain phân hoạch cộng đồng
        try:
            communities_raw = list(nx.community.louvain_communities(g_nx, seed=seed))
        except Exception:
            # Fallback if graph is disconnected or single-node
            connected = list(nx.connected_components(g_nx))
            communities_raw = connected if connected else [{i} for i in range(n)]

        # Sắp xếp các cộng đồng theo kích thước giảm dần
        communities_raw.sort(key=len, reverse=True)
        communities = [sorted(list(c)) for c in communities_raw]
        num_comms = len(communities)

        # Mảng ánh xạ đỉnh -> ID cộng đồng
        node_community = np.zeros(n, dtype=np.int32)
        for c_idx, c_nodes in enumerate(communities):
            for u in c_nodes:
                node_community[u] = c_idx

        # 2. Tính toán điểm PageRank
        try:
            pr_dict = nx.pagerank(g_nx, alpha=0.85, max_iter=100)
            pr_scores = np.array([pr_dict.get(i, 1.0 / n) for i in range(n)], dtype=np.float64)
        except Exception:
            # Fallback to degree centrality if PageRank doesn't converge
            degs = np.array([g_nx.degree(i) for i in range(n)], dtype=np.float64)
            deg_sum = degs.sum()
            pr_scores = degs / (deg_sum if deg_sum > 0 else 1.0)

        # 3. Phân bổ hạn ngạch theo Phương pháp phần dư lớn nhất (Largest Remainder Method: CT 2.18 - 2.20)
        quotas_float = [k * (len(c) / n) for c in communities]
        k_quotas = [min(len(c), int(np.floor(q))) for q, c in zip(quotas_float, communities)]
        remainders = [q - ki for q, ki in zip(quotas_float, k_quotas)]
        allocated = sum(k_quotas)
        surplus = k - allocated

        # Phân bổ phần dư lớn nhất cho surplus cộng đồng có remainder cao nhất
        sorted_indices = sorted(range(num_comms), key=lambda i: remainders[i], reverse=True)
        for idx in sorted_indices:
            if surplus <= 0:
                break
            if k_quotas[idx] < len(communities[idx]):
                k_quotas[idx] += 1
                surplus -= 1

        # Nếu vẫn còn surplus do các cộng đồng đã đạt trần kích thước
        if surplus > 0:
            for idx in range(num_comms):
                while surplus > 0 and k_quotas[idx] < len(communities[idx]):
                    k_quotas[idx] += 1
                    surplus -= 1

        # 4. Xác định các đỉnh biên cộng đồng (boundary nodes)
        boundary_nodes = []
        for u in range(n):
            u_comm = node_community[u]
            is_boundary = any(node_community[v] != u_comm for v in g_nx.neighbors(u))
            if is_boundary:
                boundary_nodes.append(u)
        if not boundary_nodes:
            boundary_nodes = list(range(n))

        # Build adjacency set cache for fast neighborhood overlap calculations
        self._adj_cache = {u: set(g_nx.neighbors(u)) for u in range(n)}

        return communities, k_quotas, pr_scores, node_community, boundary_nodes, g_nx

    # ═════════════════════════════════════════════════════════════════════════
    #  HÀM ĐÁNH GIÁ THÍCH NGHI NHANH: LIE-2 (LOCAL INFLUENCE ESTIMATION 2-HOP)
    # ═════════════════════════════════════════════════════════════════════════

    def _evaluate_lie_2(
        self,
        seeds: List[int],
        row_ptr: List[int],
        col_indices: List[int],
        edge_probs: List[float],
    ) -> float:
        """
        Tính toán hàm thích nghi nhanh LIE-2 (Công thức 2.23):
        Ước lượng độ lan truyền phân tích giải tích 2-hop mà không cần mô phỏng Monte Carlo.
        sigma_LIE-2(S) = |S| + sum_{v in N1(S)} P_1(v) + sum_{w in N2(S)} P_2(w)
        """
        seed_set = set(seeds)

        # 1-hop activation probability: P_1(v) = 1 - prod_{u in S, (u, v) in E} (1 - p_uv)
        p1: Dict[int, float] = {}
        for u in seeds:
            for idx in range(row_ptr[u], row_ptr[u + 1]):
                v = col_indices[idx]
                if v not in seed_set:
                    p_uv = edge_probs[idx]
                    p1[v] = 1.0 - (1.0 - p1.get(v, 0.0)) * (1.0 - p_uv)

        # 2-hop activation probability: P_2(w) = 1 - prod_{v in N1, (v, w) in E} (1 - P_1(v) * p_vw)
        p2: Dict[int, float] = {}
        for v, prob_v in p1.items():
            for idx in range(row_ptr[v], row_ptr[v + 1]):
                w = col_indices[idx]
                if w not in seed_set and w not in p1:
                    p_vw = edge_probs[idx]
                    p2[w] = 1.0 - (1.0 - p2.get(w, 0.0)) * (1.0 - prob_v * p_vw)

        return float(len(seeds) + sum(p1.values()) + sum(p2.values()))

    # ═════════════════════════════════════════════════════════════════════════
    #  PHA 2: KHỞI TẠO QUẦN THỂ ĐỊNH HƯỚNG IGA (THẾ HỆ t = 0)
    # ═════════════════════════════════════════════════════════════════════════

    def _create_initial_population(
        self,
        problem: IMProblem,
        communities: List[List[int]],
        k_quotas: List[int],
        pr_scores: np.ndarray,
        np_rng: np.random.Generator,
        row_ptr: List[int],
        col_indices: List[int],
        edge_probs: List[float],
    ) -> Population:
        """
        Pha 2: Khởi tạo 80% cá thể định hướng topo và 20% cá thể ngẫu nhiên kiểm soát.
        Mỗi cá thể được gán điểm thích nghi nhanh f_LIE ban đầu.
        """
        n = problem.num_nodes
        k = problem.k
        individuals: List[Solution] = []

        if not self.enable_guided_init:
            # Baseline style: 100% random uniform
            for _ in range(self.pop_size):
                seeds = sorted(int(x) for x in np_rng.choice(n, size=k, replace=False))
                sol = Solution(seeds)
                sol.fitness = self._evaluate_lie_2(seeds, row_ptr, col_indices, edge_probs)
                individuals.append(sol)
            return Population(individuals)

        num_topo = int(round(0.80 * self.pop_size))
        num_random = self.pop_size - num_topo

        # Chuẩn bị phân bố xác suất PageRank cho từng cộng đồng
        comm_probs: List[np.ndarray] = []
        for c_nodes in communities:
            w = pr_scores[c_nodes]
            w_sum = w.sum()
            comm_probs.append(w / (w_sum if w_sum > 0 else 1.0))

        # 1. Khởi tạo 80% cá thể định hướng topo
        for _ in range(num_topo):
            candidate_seeds: List[int] = []
            for j, c_nodes in enumerate(communities):
                kj = k_quotas[j]
                if kj > 0 and len(c_nodes) > 0:
                    kj_actual = min(kj, len(c_nodes))
                    chosen = np_rng.choice(c_nodes, size=kj_actual, replace=False, p=comm_probs[j])
                    candidate_seeds.extend(int(x) for x in chosen)

            # Đảm bảo tập hạt giống có đúng k phần tử phân biệt
            unique_seeds = list(dict.fromkeys(candidate_seeds))
            if len(unique_seeds) < k:
                # Bổ sung các đỉnh có PageRank cao nhất chưa được chọn
                sorted_by_pr = np.argsort(pr_scores)[::-1]
                for node in sorted_by_pr:
                    if int(node) not in unique_seeds:
                        unique_seeds.append(int(node))
                    if len(unique_seeds) == k:
                        break
            elif len(unique_seeds) > k:
                unique_seeds = unique_seeds[:k]

            sol = Solution(sorted(unique_seeds))
            sol.fitness = self._evaluate_lie_2(sol.seed_set, row_ptr, col_indices, edge_probs)
            individuals.append(sol)

        # 2. Khởi tạo 20% cá thể ngẫu nhiên kiểm soát
        for _ in range(num_random):
            seeds = sorted(int(x) for x in np_rng.choice(n, size=k, replace=False))
            sol = Solution(seeds)
            sol.fitness = self._evaluate_lie_2(seeds, row_ptr, col_indices, edge_probs)
            individuals.append(sol)

        return Population(individuals)

    # ═════════════════════════════════════════════════════════════════════════
    #  TOÁN TỬ TIẾN HÓA: GIẢI ĐẤU TOPO, LAI GHÉP & ĐỘT BIẾN KHAI THÁC BIÊN
    # ═════════════════════════════════════════════════════════════════════════

    def _tournament_select_topo(
        self,
        pop: Population,
        node_community: np.ndarray,
        rng: random.Random,
    ) -> Solution:
        """
        Lựa chọn giải đấu topo theo hàm Fitness_tour (Công thức 2.26):
        Fitness_tour(C) = f_LIE(C) + lambda_tour * (Số cộng đồng khác nhau được bao phủ)
        """
        candidates = rng.sample(pop.individuals, min(self.tournament_size, len(pop)))

        def _tour_score(sol: Solution) -> float:
            base_fit = sol.fitness if sol.fitness is not None else 0.0
            covered_communities = len(set(node_community[u] for u in sol.seed_set))
            return base_fit + self.lambda_tour * covered_communities

        return max(candidates, key=_tour_score)

    def _calc_neighborhood_overlap(self, u: int, v: int) -> float:
        """Tính độ chồng lấn láng giềng Jaccard giữa 2 nút u và v: Overlap(u, v) = |N(u) ∩ N(v)| / |N(u) ∪ N(v)|."""
        nu = self._adj_cache.get(u, set())
        nv = self._adj_cache.get(v, set())
        if not nu and not nv:
            return 0.0
        intersection_len = len(nu & nv)
        union_len = len(nu | nv)
        return float(intersection_len / union_len) if union_len > 0 else 0.0

    def _crossover_smart(
        self,
        parent_a: Solution,
        parent_b: Solution,
        k: int,
        n: int,
        pr_scores: np.ndarray,
        rng: random.Random,
    ) -> Solution:
        """
        Lai ghép thông minh dựa trên hợp nhất và sàng lọc tập hợp:
        1. Hợp nhất tập hạt giống hai cha mẹ: U = S(p1) ∪ S(p2)
        2. Sắp xếp các ứng viên trong U theo PageRank giảm dần
        3. Chọn lọc các đỉnh không vượt ngưỡng chồng lấn láng giềng tau_overlap
        """
        union_candidates = list(set(parent_a.seed_set) | set(parent_b.seed_set))
        union_candidates.sort(key=lambda u: pr_scores[u], reverse=True)

        if not self.enable_overlap_filtering:
            # Standard random sampling from union
            if len(union_candidates) < k:
                remaining = list(set(range(n)) - set(union_candidates))
                rng.shuffle(remaining)
                union_candidates.extend(remaining[: k - len(union_candidates)])
            chosen = rng.sample(union_candidates, k)
            return Solution(sorted(chosen))

        child_seeds: List[int] = []
        for cand in union_candidates:
            # Kiểm tra xem cand có bị chồng lấn quá tau_overlap với bất kỳ hạt giống nào đã chọn không
            is_overlapping = any(
                self._calc_neighborhood_overlap(cand, s) > self.tau_overlap
                for s in child_seeds
            )
            if not is_overlapping:
                child_seeds.append(cand)
                if len(child_seeds) == k:
                    break

        # Nếu chưa đủ k hạt giống do ràng buộc khắt khe, bổ sung các đỉnh có PR cao nhất còn lại
        if len(child_seeds) < k:
            for cand in union_candidates:
                if cand not in child_seeds:
                    child_seeds.append(cand)
                if len(child_seeds) == k:
                    break

        # Nếu vẫn chưa đủ k (ví dụ |U| < k), chọn từ top PageRank toàn mạng
        if len(child_seeds) < k:
            sorted_nodes = np.argsort(pr_scores)[::-1]
            for u in sorted_nodes:
                int_u = int(u)
                if int_u not in child_seeds:
                    child_seeds.append(int_u)
                if len(child_seeds) == k:
                    break

        return Solution(sorted(child_seeds))

    def _mutate_boundary_directed(
        self,
        sol: Solution,
        n: int,
        node_community: np.ndarray,
        boundary_nodes: List[int],
        pr_scores: np.ndarray,
        rng: random.Random,
    ) -> Solution:
        """
        Đột biến định hướng khai thác biên (Công thức 2.27):
        Thay thế đỉnh hạt giống có đóng góp PageRank thấp nhất hoặc trùng cộng đồng
        bằng một đỉnh biên (boundary node) có PageRank cao chưa nằm trong tập hạt giống.
        """
        seed_set = set(sol.seed_set)
        if not self.enable_degree_guided_mutation:
            # Uniform mutation fallback
            seeds = list(sol.seed_set)
            idx_to_replace = rng.randrange(len(seeds))
            avail = list(set(range(n)) - seed_set)
            if avail:
                seeds[idx_to_replace] = rng.choice(avail)
            return Solution(sorted(seeds))

        # Tìm đỉnh hạt giống có PageRank thấp nhất để thay thế
        weakest_node = min(sol.seed_set, key=lambda u: pr_scores[u])

        # Tập ứng viên là các đỉnh biên cộng đồng chưa nằm trong seed_set
        boundary_candidates = [v for v in boundary_nodes if v not in seed_set]

        if boundary_candidates:
            # Chọn đỉnh biên có PageRank cao (chọn ngẫu nhiên từ top 20% đỉnh biên tốt nhất)
            boundary_candidates.sort(key=lambda v: pr_scores[v], reverse=True)
            top_bound_limit = max(1, int(0.20 * len(boundary_candidates)))
            replacement = rng.choice(boundary_candidates[:top_bound_limit])
        else:
            # Fallback nếu không còn đỉnh biên khả dụng
            all_avail = list(set(range(n)) - seed_set)
            replacement = rng.choice(all_avail) if all_avail else weakest_node

        new_seeds = [s if s != weakest_node else replacement for s in sol.seed_set]
        return Solution(sorted(new_seeds))

    # ═════════════════════════════════════════════════════════════════════════
    #  BƯỚC 3: TÌM KIẾM CỤC BỘ LEO ĐỒI (LOCAL SEARCH HILL CLIMBING: CT 2.28)
    # ═════════════════════════════════════════════════════════════════════════

    def _local_search_hill_climbing(
        self,
        sol: Solution,
        pr_scores: np.ndarray,
        row_ptr: List[int],
        col_indices: List[int],
        edge_probs: List[float],
        rng: random.Random,
    ) -> Solution:
        """
        Tìm kiếm cục bộ leo đồi tự thích ứng trên nhóm tinh hoa (Công thức 2.28):
        Lặp tối đa L_max bước: thử hoán đổi 1 đỉnh hạt giống bằng 1 đỉnh lân cận có tiềm năng,
        chấp nhận hoán đổi nếu hàm thích nghi nhanh f_LIE cải thiện.
        """
        if not self.enable_local_search or self.local_search_steps <= 0:
            return sol

        cur_seeds = list(sol.seed_set)
        cur_fit = sol.fitness if sol.fitness is not None else self._evaluate_lie_2(cur_seeds, row_ptr, col_indices, edge_probs)
        seed_set = set(cur_seeds)

        for _ in range(self.local_search_steps):
            improved = False
            # Chọn 1 đỉnh trong tập hạt giống (ưu tiên đỉnh có PR thấp hơn)
            u = rng.choice(cur_seeds)
            u_neighbors = col_indices[row_ptr[u] : row_ptr[u + 1]]
            candidates = [v for v in u_neighbors if v not in seed_set]
            if not candidates:
                continue

            # Chọn láng giềng có PageRank tốt nhất
            v = max(candidates, key=lambda x: pr_scores[x])

            # Thử nghiệm phương án hoán đổi u -> v
            test_seeds = sorted([x if x != u else v for x in cur_seeds])
            test_fit = self._evaluate_lie_2(test_seeds, row_ptr, col_indices, edge_probs)

            if test_fit > cur_fit:
                cur_seeds = test_seeds
                cur_fit = test_fit
                seed_set = set(cur_seeds)
                improved = True

            if not improved:
                break

        res = Solution(cur_seeds)
        res.fitness = cur_fit
        return res

    # ═════════════════════════════════════════════════════════════════════════
    #  PHA 3 & 4: VÒNG LẶP CHÍNH CỦA THUẬT TOÁN IGA
    # ═════════════════════════════════════════════════════════════════════════

    def run(
        self,
        problem: IMProblem,
        seed: int = 42,
        max_evaluations: int | None = None,
        max_iterations: int | None = None,
    ) -> AlgorithmResult:
        """
        Thực thi toàn diện quy trình 4 Pha của thuật toán IGA:
          Pha 1: Louvain + PageRank + Hạn ngạch phần dư lớn nhất
          Pha 2: Khởi tạo 80% Topo, 20% Random + Đánh giá LIE-2 ban đầu
          Pha 3: Tiến hóa thích nghi thích ứng nhanh (p_m, p_c, giải cứu, giải đấu topo,
                 lai ghép lọc overlap, đột biến biên, leo đồi L_max)
          Pha 4: Sàng lọc Monte Carlo cuối cùng với R_final mô phỏng
        """
        rng = random.Random(seed)
        np_rng = np.random.default_rng(seed)

        n = problem.num_nodes
        k = problem.k
        max_gen = max_iterations or self.max_generations
        budget = max_evaluations or float("inf")

        t_start = time.perf_counter()
        total_evals = 0
        convergence_history: List[Dict[str, Any]] = []

        # Trích xuất CSR structures cho hàm đánh giá nhanh LIE-2
        row_ptr = list(problem.graph.row_ptr())
        col_indices = list(problem.graph.col_indices())
        edge_probs = list(problem.graph.edge_probs())

        # ── Pha 1: Tiền xử lý đồ thị & trích xuất tri thức topo ─────────────────
        self._log("Pha 1: Đang trích xuất tri thức topo (Louvain & PageRank)...")
        (
            communities,
            k_quotas,
            pr_scores,
            node_community,
            boundary_nodes,
            g_nx,
        ) = self._preprocess_topology(problem, seed)
        self._log(
            f"Pha 1: Phân hoạch {len(communities)} cộng đồng; Hạn ngạch phần dư lớn nhất: {k_quotas[:min(5, len(k_quotas))]}... (Tổng k = {sum(k_quotas)})"
        )

        # ── Pha 2: Khởi tạo quần thể định hướng IGA thế hệ t = 0 ──────────────
        self._log(
            f"Pha 2: Khởi tạo quần thể N={self.pop_size} (80% Topo-guided, 20% Random) & đánh giá hàm LIE-2 ban đầu..."
        )
        pop = self._create_initial_population(
            problem,
            communities,
            k_quotas,
            pr_scores,
            np_rng,
            row_ptr,
            col_indices,
            edge_probs,
        )
        total_evals += self.pop_size

        best_ever = max(pop.individuals, key=lambda s: s.fitness or 0.0)
        c_best_lie = Solution(list(best_ever.seed_set), fitness=best_ever.fitness)
        stagnation_count = 0
        current_diversity = pop.diversity_jaccard()
        self._log(
            f"Pha 2: Hoàn tất t=0 | Nghiệm tốt nhất f_LIE = {c_best_lie.fitness:.2f} | Đa dạng Jaccard = {current_diversity:.3f}"
        )

        convergence_history.append({
            "generation": 0,
            "best_fitness": c_best_lie.fitness,
            "mean_fitness": float(np.mean([s.fitness or 0.0 for s in pop.individuals])),
            "diversity": current_diversity,
            "mutation_rate": self.p_m_max,
            "crossover_rate": self.p_c_min,
            "evaluations": total_evals,
        })

        # ── Pha 3: Chu trình tiến hóa thích nghi nhanh ────────────────────────
        log_interval = max(1, max_gen // 10)  # Log đều đặn ~10 mốc tiến trình trong quá trình tiến hóa
        self._log(f"Pha 3: Bắt đầu chu trình tiến hóa thích nghi nhanh (T_max = {max_gen} thế hệ)...")

        for gen in range(1, max_gen + 1):
            if total_evals >= budget:
                self._log(f"[Gen {gen}] Đã đạt giới hạn đánh giá budget={budget}. Dừng sớm.")
                break

            if self.progress_callback is not None:
                try:
                    self.progress_callback(gen / max_gen)
                except Exception:
                    pass

            # Cập nhật tham số thích ứng động (Công thức 2.29 & 2.30)
            progress = gen / max(1, max_gen)
            pm_t = self.p_m_max - (self.p_m_max - self.p_m_min) * progress
            pc_t = self.p_c_min + (self.p_c_max - self.p_c_min) * progress

            # Giám sát độ đa dạng di truyền (Công thức 2.31)
            div_val = pop.diversity_jaccard()
            if self.enable_adaptive_mutation and div_val < self.epsilon_div:
                # Tính p_m_boost theo Công thức (2.32)
                deficit = (self.epsilon_div - div_val) / self.epsilon_div
                pm_t = min(self.p_m_max, pm_t + deficit * (self.p_m_max - self.p_m_min))

                # Đột biến giải cứu nếu bị trì trệ 3 thế hệ liên tiếp
                if stagnation_count >= 3:
                    self._log(
                        f"[Gen {gen:3d}] ⚡ Kích hoạt Đột biến giải cứu (đa dạng={div_val:.3f} < {self.epsilon_div}, trì trệ {stagnation_count} thế hệ)"
                    )
                    sorted_curr = sorted(pop.individuals, key=lambda s: s.fitness or 0.0, reverse=True)
                    rescued_individuals: List[Solution] = []
                    # Bảo toàn N_elite cá thể tinh hoa
                    rescued_individuals.extend(sorted_curr[: self.elitism])
                    # Tái cấu trúc các cá thể còn lại để giải thoát khỏi cực tiểu địa phương
                    for _ in range(self.pop_size - self.elitism):
                        cand_seeds: List[int] = []
                        for j, c_nodes in enumerate(communities):
                            kj = k_quotas[j]
                            if kj > 0 and len(c_nodes) > 0:
                                chosen = np_rng.choice(c_nodes, size=min(kj, len(c_nodes)), replace=False)
                                cand_seeds.extend(int(x) for x in chosen)
                        cand_seeds = list(dict.fromkeys(cand_seeds))[:k]
                        while len(cand_seeds) < k:
                            cand_seeds.append(int(np_rng.integers(0, n)))
                            cand_seeds = list(dict.fromkeys(cand_seeds))
                        sol_r = Solution(sorted(cand_seeds))
                        sol_r.fitness = self._evaluate_lie_2(sol_r.seed_set, row_ptr, col_indices, edge_probs)
                        rescued_individuals.append(sol_r)
                    pop = Population(rescued_individuals)
                    stagnation_count = 0

            # Bước 1: Bảo tồn tuyệt đối nhóm cá thể tinh hoa
            sorted_pop = sorted(pop.individuals, key=lambda s: s.fitness or 0.0, reverse=True)
            p_new: List[Solution] = []
            for e_sol in sorted_pop[: self.elitism]:
                p_new.append(Solution(list(e_sol.seed_set), fitness=e_sol.fitness))

            # Bước 2: Sinh sản thế hệ mới
            while len(p_new) < self.pop_size:
                # Lựa chọn giải đấu topo (Công thức 2.26)
                p1 = self._tournament_select_topo(pop, node_community, rng)
                p2 = self._tournament_select_topo(pop, node_community, rng)

                # Lai ghép thông minh dựa trên hợp nhất và sàng lọc chồng lấn tau_overlap
                if rng.random() < pc_t:
                    child = self._crossover_smart(p1, p2, k, n, pr_scores, rng)
                else:
                    child = Solution(list(p1.seed_set))

                # Đột biến định hướng khai thác biên (Công thức 2.27)
                if rng.random() < pm_t:
                    child = self._mutate_boundary_directed(
                        child, n, node_community, boundary_nodes, pr_scores, rng
                    )

                # Đánh giá thích nghi nhanh bằng hàm LIE-2 (Công thức 2.23)
                child.fitness = self._evaluate_lie_2(child.seed_set, row_ptr, col_indices, edge_probs)
                total_evals += 1
                p_new.append(child)

            # Bước 3: Tìm kiếm cục bộ tự thích ứng trên nhóm tinh hoa thế hệ mới (Công thức 2.28)
            sorted_pnew = sorted(p_new, key=lambda s: s.fitness or 0.0, reverse=True)
            refined_elite: List[Solution] = []
            for e_idx in range(min(self.elitism, len(sorted_pnew))):
                improved_elite = self._local_search_hill_climbing(
                    sorted_pnew[e_idx], pr_scores, row_ptr, col_indices, edge_probs, rng
                )
                refined_elite.append(improved_elite)

            # Cập nhật lại các cá thể tinh hoa đã cải thiện vào quần thể
            for idx, ref_sol in enumerate(refined_elite):
                sorted_pnew[idx] = ref_sol

            pop = Population(sorted_pnew)

            # Cập nhật nghiệm LIE tốt nhất
            gen_best = pop.best
            if (gen_best.fitness or 0.0) > (c_best_lie.fitness or 0.0):
                c_best_lie = Solution(list(gen_best.seed_set), fitness=gen_best.fitness)
                stagnation_count = 0
            else:
                stagnation_count += 1

            # In nhật ký tiến trình định kỳ
            if gen == 1 or gen % log_interval == 0 or gen == max_gen:
                self._log(
                    f"Thế hệ {gen:3d}/{max_gen} | f_LIE: {c_best_lie.fitness:6.2f} | Đa dạng Jaccard: {div_val:.3f} | pm: {pm_t:.2f}, pc: {pc_t:.2f}"
                )

            convergence_history.append({
                "generation": gen,
                "best_fitness": c_best_lie.fitness,
                "mean_fitness": float(np.mean([s.fitness or 0.0 for s in pop.individuals])),
                "diversity": div_val,
                "mutation_rate": pm_t,
                "crossover_rate": pc_t,
                "evaluations": total_evals,
            })

        t_search_end = time.perf_counter()

        # ── Pha 4: Sàng lọc tinh hoa cuối cùng bằng mô phỏng Monte Carlo ──────
        final_elite = sorted(pop.individuals, key=lambda s: s.fitness or 0.0, reverse=True)[: self.elitism]
        self._log(
            f"Pha 4: Sàng lọc {len(final_elite)} cá thể tinh hoa bằng {self.r_final} lượt mô phỏng Monte Carlo (C++ OpenMP)..."
        )

        # Đánh giá chính xác cao bằng C++ Monte Carlo Engine
        best_mc_spread = -1.0
        best_overall_solution = final_elite[0]

        for cand_idx, cand in enumerate(final_elite, start=1):
            # problem.fitness() gọi trực tiếp C++ Evaluator OpenMP
            mc_spread = problem.fitness(cand)
            cand.fitness = mc_spread
            total_evals += 1
            self._log(f"Pha 4: Cá thể tinh hoa #{cand_idx}/{len(final_elite)} -> σ_MC = {mc_spread:.2f}")
            if mc_spread > best_mc_spread:
                best_mc_spread = mc_spread
                best_overall_solution = cand

        # Trích xuất top 5 cá thể đa dạng cho giao diện kết quả & so sánh
        seen_signatures = set()
        top_individuals = []
        top_individuals.append({
            "rank": 1,
            "seeds": sorted(best_overall_solution.seed_set),
            "fitness": float(best_overall_solution.fitness or best_mc_spread),
            "spread": float(best_mc_spread),
        })
        seen_signatures.add(tuple(sorted(best_overall_solution.seed_set)))

        for ind in sorted(pop.individuals, key=lambda s: s.fitness or 0.0, reverse=True):
            sig = tuple(sorted(ind.seed_set))
            if sig not in seen_signatures:
                seen_signatures.add(sig)
                try:
                    sp_val = float(problem.fitness(ind))
                except Exception:
                    sp_val = float(ind.fitness or best_mc_spread)
                top_individuals.append({
                    "rank": len(top_individuals) + 1,
                    "seeds": sorted(ind.seed_set),
                    "fitness": float(ind.fitness or sp_val),
                    "spread": sp_val,
                })
                if len(top_individuals) >= 5:
                    break

        t_total_end = time.perf_counter()
        self._log(
            f"Hoàn tất! S* = {best_overall_solution.seed_set[:min(k, 8)]}... | σ_MC = {best_mc_spread:.2f} | Thời gian: {t_total_end - t_start:.2f}s"
        )

        return AlgorithmResult(
            algorithm_name=self.name,
            best_solution=best_overall_solution,
            search_time=t_search_end - t_start,
            total_evaluations=total_evals,
            convergence_history=convergence_history,
            metadata={
                "total_time": t_total_end - t_start,
                "pop_size": self.pop_size,
                "generations_completed": len(convergence_history) - 1,
                "p_c_min": self.p_c_min,
                "p_c_max": self.p_c_max,
                "p_m_min": self.p_m_min,
                "p_m_max": self.p_m_max,
                "tournament_size": self.tournament_size,
                "elitism": self.elitism,
                "epsilon_div": self.epsilon_div,
                "tau_overlap": self.tau_overlap,
                "lambda_tour": self.lambda_tour,
                "local_search_steps": self.local_search_steps,
                "r_final": self.r_final,
                "num_communities": len(communities),
                "random_seed": seed,
                "top_individuals": top_individuals,
            },
        )
