#pragma once

#include "graph.hpp"
#include "diffusion.hpp"
#include "monte_carlo.hpp"
#include <vector>
#include <cstdint>
#include <memory>

namespace im_core {

/**
 * @brief High-performance Evaluator for Influence Maximization.
 * 
 * Inspired by pygmo's batch_fitness architecture: supports evaluating
 * single solutions and batches of solutions in parallel with OpenMP.
 */
class Evaluator {
public:
    Evaluator(std::shared_ptr<const Graph> graph,
              DiffusionModel model = DiffusionModel::IndependentCascade,
              uint32_t num_mc_simulations = 1000,
              uint64_t seed = 42);

    double evaluate(const std::vector<uint32_t>& seed_set);

    /**
     * @brief Pygmo-style batch evaluation.
     * Evaluates multiple candidate seed sets in parallel via OpenMP.
     */
    std::vector<double> batch_evaluate(const std::vector<std::vector<uint32_t>>& seed_sets);

    uint64_t total_evaluations() const { return total_evaluations_; }
    uint64_t total_mc_simulations() const { return total_mc_simulations_; }
    void reset_counters() {
        total_evaluations_ = 0;
        total_mc_simulations_ = 0;
    }

    void set_num_mc_simulations(uint32_t mc) { num_mc_simulations_ = mc; }
    uint32_t num_mc_simulations() const { return num_mc_simulations_; }

    void set_seed(uint64_t seed);
    uint64_t seed() const { return base_seed_; }

    const Graph& graph() const { return *graph_; }
    DiffusionModel model() const { return model_; }

private:
    std::shared_ptr<const Graph> graph_;
    DiffusionModel model_;
    uint32_t num_mc_simulations_;
    uint64_t base_seed_;

    uint64_t total_evaluations_{0};
    uint64_t total_mc_simulations_{0};
};

} // namespace im_core

