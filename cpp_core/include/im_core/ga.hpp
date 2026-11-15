#pragma once

#include "graph.hpp"
#include "diffusion.hpp"
#include "evaluator.hpp"

#include <cstdint>
#include <map>
#include <memory>
#include <random>
#include <vector>

namespace im_core {

struct GAConfig {
    uint32_t k = 10;
    uint32_t population_size = 50;
    uint32_t max_generations = 100;
    uint32_t tournament_size = 5;
    double crossover_rate = 0.9;
    double mutation_rate = 0.1;
    uint32_t elitism = 2;
    uint32_t num_mc_simulations = 100;
    int64_t seed = -1;

    uint32_t max_evaluations = 0;
};

struct GAIndividual {
    std::vector<uint32_t> seeds;
    double fitness = 0.0;
};

struct GAResult {
    std::vector<uint32_t> best_seeds;
    double best_fitness = 0.0;
    std::vector<double> best_fitness_history;
    std::vector<double> mean_fitness_history;
    std::vector<double> diversity_history;
    std::vector<GAIndividual> top_individuals;
    uint64_t total_evaluations = 0;
    uint64_t total_mc_simulations = 0;
    uint32_t generations_completed = 0;
    double search_time_seconds = 0.0;
    GAConfig config;
};

class GeneticAlgorithm {
public:
    GeneticAlgorithm(std::shared_ptr<const Graph> graph,
                     DiffusionModel model,
                     GAConfig config);

    GAResult run();

private:
    std::shared_ptr<const Graph> graph_;
    DiffusionModel model_;
    GAConfig config_;

    std::vector<GAIndividual> create_initial_population();
    std::vector<uint32_t> random_seed_set();
    std::vector<uint32_t> sample_from(const std::vector<uint32_t>& pool);
    const GAIndividual& tournament_select(const std::vector<GAIndividual>& population);
    void crossover(const GAIndividual& parent_a,
                   const GAIndividual& parent_b,
                   GAIndividual& child_a,
                   GAIndividual& child_b);
    void mutate(GAIndividual& individual);
    void evaluate_individuals(std::vector<GAIndividual>& population,
                              Evaluator& evaluator,
                              bool only_unevaluated);
    double population_diversity(const std::vector<GAIndividual>& population) const;
    double population_mean(const std::vector<GAIndividual>& population) const;
    void record_top(const std::vector<GAIndividual>& population,
                    std::map<std::vector<uint32_t>, double>& top_map) const;
    uint32_t random_node_not_in(const std::vector<uint8_t>& present);

    std::mt19937_64 rng_;
};

} // namespace im_core
