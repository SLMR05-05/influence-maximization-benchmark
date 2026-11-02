#include "im_core/monte_carlo.hpp"

namespace im_core {

MonteCarloSimulator::MonteCarloSimulator(uint64_t seed)
    : rng_(seed), dist_01_(0.0f, 1.0f) {}

void MonteCarloSimulator::set_seed(uint64_t seed) {
    rng_.seed(seed);
}

uint32_t MonteCarloSimulator::simulate_ic(const Graph& graph,
                                         const std::vector<uint32_t>& seed_set,
                                         std::vector<uint8_t>& visited_buffer,
                                         std::vector<uint32_t>& queue_buffer) {
    uint32_t num_nodes = graph.num_nodes();
    if (visited_buffer.size() < num_nodes) {
        visited_buffer.assign(num_nodes, 0);
    }
    if (queue_buffer.size() < num_nodes) {
        queue_buffer.resize(num_nodes);
    }

    uint32_t q_head = 0;
    uint32_t q_tail = 0;

    // Initialize seeds
    for (uint32_t seed : seed_set) {
        if (seed < num_nodes && !visited_buffer[seed]) {
            visited_buffer[seed] = 1;
            queue_buffer[q_tail++] = seed;
        }
    }

    uint32_t total_activated = q_tail;

    // BFS diffusion loop
    while (q_head < q_tail) {
        uint32_t u = queue_buffer[q_head++];
        const uint32_t* neighbors = graph.neighbors_begin(u);
        const uint32_t* end = graph.neighbors_end(u);
        const float* probs = graph.probs_begin(u);

        for (; neighbors != end; ++neighbors, ++probs) {
            uint32_t v = *neighbors;
            if (!visited_buffer[v]) {
                if (dist_01_(rng_) <= *probs) {
                    visited_buffer[v] = 1;
                    queue_buffer[q_tail++] = v;
                    total_activated++;
                }
            }
        }
    }

    // Reset visited buffer for nodes that were activated (much faster than memset whole vector)
    for (uint32_t i = 0; i < q_tail; ++i) {
        visited_buffer[queue_buffer[i]] = 0;
    }

    return total_activated;
}

double MonteCarloSimulator::simulate_ic_replications(const Graph& graph,
                                                    const std::vector<uint32_t>& seed_set,
                                                    uint32_t num_replications) {
    if (num_replications == 0 || seed_set.empty()) return 0.0;

    std::vector<uint8_t> visited(graph.num_nodes(), 0);
    std::vector<uint32_t> queue(graph.num_nodes(), 0);

    uint64_t total_activated = 0;
    for (uint32_t r = 0; r < num_replications; ++r) {
        total_activated += simulate_ic(graph, seed_set, visited, queue);
    }

    return static_cast<double>(total_activated) / num_replications;
}

} // namespace im_core

