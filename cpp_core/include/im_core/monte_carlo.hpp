#pragma once

#include "graph.hpp"
#include "diffusion.hpp"
#include <vector>
#include <random>
#include <cstdint>

namespace im_core {

/**
 * @brief Thread-local simulation state and Monte Carlo simulation routines.
 */
class MonteCarloSimulator {
public:
    explicit MonteCarloSimulator(uint64_t seed = 42);

    void set_seed(uint64_t seed);

    /**
     * @brief Run a single simulation step of Independent Cascade.
     * @return Number of nodes activated in this run.
     */
    uint32_t simulate_ic(const Graph& graph,
                         const std::vector<uint32_t>& seed_set,
                         std::vector<uint8_t>& visited_buffer,
                         std::vector<uint32_t>& queue_buffer);

    /**
     * @brief Run multiple Monte Carlo simulations and return the average spread.
     */
    double simulate_ic_replications(const Graph& graph,
                                   const std::vector<uint32_t>& seed_set,
                                   uint32_t num_replications);

private:
    std::mt19937_64 rng_;
    std::uniform_real_distribution<float> dist_01_;
};

} // namespace im_core

