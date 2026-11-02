#pragma once

#include <vector>
#include <string>
#include <cstdint>
#include <stdexcept>
#include <fstream>
#include <iostream>

namespace im_core {

/**
 * @brief High-performance Compressed Sparse Row (CSR) Graph representation.
 * 
 * Optimized for CPU cache locality and multi-threaded parallel BFS traversals.
 */
class Graph {
public:
    Graph() : num_nodes_(0), num_edges_(0), is_directed_(false) {}

    Graph(uint32_t num_nodes, const std::vector<uint32_t>& row_ptr,
          const std::vector<uint32_t>& col_indices,
          const std::vector<float>& edge_probs,
          bool is_directed = false);

    uint32_t num_nodes() const { return num_nodes_; }
    uint64_t num_edges() const { return num_edges_; }
    bool is_directed() const { return is_directed_; }

    uint32_t out_degree(uint32_t u) const {
        return row_ptr_[u + 1] - row_ptr_[u];
    }

    // Direct access to CSR buffers
    const uint32_t* neighbors_begin(uint32_t u) const {
        return &col_indices_[row_ptr_[u]];
    }

    const uint32_t* neighbors_end(uint32_t u) const {
        return &col_indices_[row_ptr_[u + 1]];
    }

    const float* probs_begin(uint32_t u) const {
        return &edge_probs_[row_ptr_[u]];
    }

    const std::vector<uint32_t>& row_ptr() const { return row_ptr_; }
    const std::vector<uint32_t>& col_indices() const { return col_indices_; }
    const std::vector<float>& edge_probs() const { return edge_probs_; }

    static Graph from_edge_list(uint32_t num_nodes,
                                const std::vector<std::pair<uint32_t, uint32_t>>& edges,
                                const std::vector<float>& probs,
                                bool is_directed = false);

private:
    uint32_t num_nodes_;
    uint64_t num_edges_;
    bool is_directed_;

    std::vector<uint32_t> row_ptr_;     // Size: num_nodes + 1
    std::vector<uint32_t> col_indices_; // Size: num_edges
    std::vector<float> edge_probs_;     // Size: num_edges
};

} // namespace im_core

