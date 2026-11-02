#include "im_core/graph.hpp"
#include <algorithm>
#include <numeric>

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

} // namespace im_core

