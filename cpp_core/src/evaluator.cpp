#include "im_core/evaluator.hpp"
#include <stdexcept>
#include <iostream>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace im_core {

Evaluator::Evaluator(std::shared_ptr<const Graph> graph,
                     DiffusionModel model,
                     uint32_t num_mc_simulations,
                     uint64_t seed)
    : graph_(std::move(graph)),
      model_(model),
      num_mc_simulations_(num_mc_simulations),
      base_seed_(seed) {
    if (!graph_) {
        throw std::invalid_argument("Graph pointer cannot be null in Evaluator");
    }
}

void Evaluator::set_seed(uint64_t seed) {
    base_seed_ = seed;
}

double Evaluator::evaluate(const std::vector<uint32_t>& seed_set) {
    total_evaluations_++;
    total_mc_simulations_ += num_mc_simulations_;

    MonteCarloSimulator sim(base_seed_ + total_evaluations_);
    if (model_ == DiffusionModel::IndependentCascade) {
        return sim.simulate_ic_replications(*graph_, seed_set, num_mc_simulations_);
    } else {
        throw std::runtime_error("Linear Threshold simulation not yet implemented");
    }
}

std::vector<double> Evaluator::batch_evaluate(const std::vector<std::vector<uint32_t>>& seed_sets) {
    size_t batch_size = seed_sets.size();
    std::vector<double> results(batch_size, 0.0);

    total_evaluations_ += batch_size;
    total_mc_simulations_ += static_cast<uint64_t>(batch_size) * num_mc_simulations_;

    uint64_t current_seed_offset = base_seed_ + total_evaluations_;
    uint32_t mc_reps = num_mc_simulations_;
    const Graph& g = *graph_;

    #pragma omp parallel for schedule(dynamic)
    for (int64_t i = 0; i < static_cast<int64_t>(batch_size); ++i) {
        MonteCarloSimulator sim(current_seed_offset + i * 10007ULL);
        results[i] = sim.simulate_ic_replications(g, seed_sets[i], mc_reps);
    }

    return results;
}

} // namespace im_core

