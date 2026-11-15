#include "im_core/graph.hpp"
#include <algorithm>
#include <numeric>
#include <set>

namespace im_core {

Graph::Graph(uint32_t num_nodes, const std::vector<uint32_t>& row_ptr,
             const std::vector<uint32_t>& col_indices,
             const std::vector<float>& edge_probs,
             bool is_directed)
    : num_nodes_(num_nodes),
      num_edges_(col_indices.size()),
      is_directed_(is_directed),
      row_ptr_(row_ptr),
      col_indices_(col_indices),
      edge_probs_(edge_probs) {
    if (row_ptr_.size() != num_nodes_ + 1) {
        throw std::invalid_argument("row_ptr size must be num_nodes + 1");
    }
    if (col_indices_.size() != edge_probs_.size()) {
        throw std::invalid_argument("col_indices and edge_probs must have identical size");
    }
}

Graph Graph::from_edge_list(uint32_t num_nodes,
                            const std::vector<std::pair<uint32_t, uint32_t>>& edges,
                            const std::vector<float>& probs,
                            bool is_directed) {
    if (edges.size() != probs.size()) {
        throw std::invalid_argument("edges and probs size mismatch");
    }

    // Build degree counts
    std::vector<uint32_t> counts(num_nodes, 0);
    for (size_t i = 0; i < edges.size(); ++i) {
        uint32_t u = edges[i].first;
        uint32_t v = edges[i].second;
        if (u < num_nodes) counts[u]++;
        if (!is_directed && v < num_nodes && u != v) counts[v]++;
    }

    std::vector<uint32_t> row_ptr(num_nodes + 1, 0);
    for (uint32_t i = 0; i < num_nodes; ++i) {
        row_ptr[i + 1] = row_ptr[i] + counts[i];
    }

    uint64_t total_entries = row_ptr.back();
    std::vector<uint32_t> col_indices(total_entries);
    std::vector<float> edge_probs(total_entries);
    std::vector<uint32_t> current_pos = row_ptr;

    for (size_t i = 0; i < edges.size(); ++i) {
        uint32_t u = edges[i].first;
        uint32_t v = edges[i].second;
        float p = probs[i];

        if (u < num_nodes && v < num_nodes) {
            uint32_t pos = current_pos[u]++;
            col_indices[pos] = v;
            edge_probs[pos] = p;

            if (!is_directed && u != v) {
                uint32_t r_pos = current_pos[v]++;
                col_indices[r_pos] = u;
                edge_probs[r_pos] = p;
            }
        }
    }

    return Graph(num_nodes, row_ptr, col_indices, edge_probs, is_directed);
}

Graph Graph::from_edge_list_wc(uint32_t num_nodes,
                               const std::vector<std::pair<uint32_t, uint32_t>>& edges,
                               bool is_directed) {
    if (num_nodes == 0) {
        throw std::invalid_argument("num_nodes must be greater than zero");
    }

    std::vector<std::pair<uint32_t, uint32_t>> clean_edges;
    clean_edges.reserve(edges.size());

    if (is_directed) {
        std::set<std::pair<uint32_t, uint32_t>> unique_edges;
        for (const auto& edge : edges) {
            uint32_t u = edge.first;
            uint32_t v = edge.second;
            if (u == v || u >= num_nodes || v >= num_nodes) {
                continue;
            }
            if (unique_edges.insert({u, v}).second) {
                clean_edges.push_back({u, v});
            }
        }
    } else {
        std::set<std::pair<uint32_t, uint32_t>> unique_edges;
        for (const auto& edge : edges) {
            uint32_t u = edge.first;
            uint32_t v = edge.second;
            if (u == v || u >= num_nodes || v >= num_nodes) {
                continue;
            }
            uint32_t a = std::min(u, v);
            uint32_t b = std::max(u, v);
            if (unique_edges.insert({a, b}).second) {
                clean_edges.push_back({a, b});
            }
        }
    }

    std::vector<double> degrees(num_nodes, 0.0);
    for (const auto& edge : clean_edges) {
        if (is_directed) {
            degrees[edge.second] += 1.0;
        } else {
            degrees[edge.first] += 1.0;
            degrees[edge.second] += 1.0;
        }
    }

    std::vector<uint32_t> counts(num_nodes, 0);
    for (const auto& edge : clean_edges) {
        counts[edge.first]++;
        if (!is_directed) {
            counts[edge.second]++;
        }
    }

    std::vector<uint32_t> row_ptr(num_nodes + 1, 0);
    for (uint32_t i = 0; i < num_nodes; ++i) {
        row_ptr[i + 1] = row_ptr[i] + counts[i];
    }

    const uint64_t total_entries = row_ptr.back();
    std::vector<uint32_t> col_indices(total_entries);
    std::vector<float> edge_probs(total_entries);
    std::vector<uint32_t> current_pos = row_ptr;

    auto add_arc = [&](uint32_t u, uint32_t v, float probability) {
        uint32_t pos = current_pos[u]++;
        col_indices[pos] = v;
        edge_probs[pos] = probability;
    };

    for (const auto& edge : clean_edges) {
        uint32_t u = edge.first;
        uint32_t v = edge.second;

        float p_uv = degrees[v] > 0.0
            ? static_cast<float>(1.0 / degrees[v])
            : 1.0f;
        add_arc(u, v, p_uv);

        if (!is_directed) {
            float p_vu = degrees[u] > 0.0
                ? static_cast<float>(1.0 / degrees[u])
                : 1.0f;
            add_arc(v, u, p_vu);
        }
    }

    return Graph(num_nodes, row_ptr, col_indices, edge_probs, is_directed);
}

} // namespace im_core

