#include "im_core/ga.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <unordered_set>
#include <utility>

namespace im_core {

namespace {

using Clock = std::chrono::steady_clock;

double clamp_probability(double value) {
    if (value < 0.0) {
        return 0.0;
    }
    if (value > 1.0) {
        return 1.0;
    }
    return value;
}

} // namespace

GeneticAlgorithm::GeneticAlgorithm(std::shared_ptr<const Graph> graph,
                                   DiffusionModel model,
                                   GAConfig config)
    : graph_(std::move(graph)),
      model_(model),
      config_(config),
      rng_(0) {
    if (config_.seed < 0) {
        std::random_device rd;
        config_.seed = static_cast<int64_t>(
            (static_cast<uint64_t>(rd()) << 32) | rd()
        );
        if (config_.seed < 0) {
            config_.seed = -config_.seed;
        }
    }
    rng_.seed(static_cast<uint64_t>(config_.seed));

    if (!graph_) {
        throw std::invalid_argument("Graph pointer cannot be null in GeneticAlgorithm");
    }
    if (graph_->num_nodes() == 0) {
        throw std::invalid_argument("Graph must contain at least one node");
    }
    if (config_.k == 0) {
        throw std::invalid_argument("k must be greater than zero");
    }
    if (config_.population_size < 2) {
        throw std::invalid_argument("population_size must be at least 2");
    }

    config_.k = std::min(config_.k, graph_->num_nodes());
    config_.tournament_size = std::max<uint32_t>(1, config_.tournament_size);
    config_.tournament_size = std::min(config_.tournament_size, config_.population_size);
    config_.elitism = std::min(config_.elitism, config_.population_size - 1);
    config_.crossover_rate = clamp_probability(config_.crossover_rate);
    config_.mutation_rate = clamp_probability(config_.mutation_rate);
    config_.num_mc_simulations = std::max<uint32_t>(1, config_.num_mc_simulations);
    config_.max_generations = std::max<uint32_t>(1, config_.max_generations);
}

std::vector<uint32_t> GeneticAlgorithm::random_seed_set() {
    const uint32_t n = graph_->num_nodes();
    const uint32_t k = config_.k;

    std::vector<uint32_t> seeds;
    seeds.reserve(k);

    if (k >= n) {
        seeds.resize(n);
        std::iota(seeds.begin(), seeds.end(), 0);
        return seeds;
    }

    if (k <= n / 2) {
        std::unordered_set<uint32_t> used;
        used.reserve(static_cast<size_t>(k) * 2);
        std::uniform_int_distribution<uint32_t> dist(0, n - 1);
        while (seeds.size() < k) {
            uint32_t node = dist(rng_);
            if (used.insert(node).second) {
                seeds.push_back(node);
            }
        }
    } else {
        std::vector<uint32_t> all(n);
        std::iota(all.begin(), all.end(), 0);
        for (uint32_t i = 0; i < k; ++i) {
            std::uniform_int_distribution<uint32_t> dist(i, n - 1);
            uint32_t j = dist(rng_);
            std::swap(all[i], all[j]);
            seeds.push_back(all[i]);
        }
    }

    std::sort(seeds.begin(), seeds.end());
    return seeds;
}

std::vector<uint32_t> GeneticAlgorithm::sample_from(const std::vector<uint32_t>& pool) {
    const uint32_t k = config_.k;
    if (pool.size() <= k) {
        std::vector<uint32_t> result = pool;
        std::sort(result.begin(), result.end());
        return result;
    }

    std::vector<uint32_t> working = pool;
    for (uint32_t i = 0; i < k; ++i) {
        std::uniform_int_distribution<uint32_t> dist(
            i, static_cast<uint32_t>(working.size()) - 1);
        uint32_t j = dist(rng_);
        std::swap(working[i], working[j]);
    }
    working.resize(k);
    std::sort(working.begin(), working.end());
    return working;
}

std::vector<GAIndividual> GeneticAlgorithm::create_initial_population() {
    std::vector<GAIndividual> population;
    population.reserve(config_.population_size);
    for (uint32_t i = 0; i < config_.population_size; ++i) {
        GAIndividual individual;
        individual.seeds = random_seed_set();
        individual.fitness = std::numeric_limits<double>::quiet_NaN();
        population.push_back(std::move(individual));
    }
    return population;
}

const GAIndividual& GeneticAlgorithm::tournament_select(
    const std::vector<GAIndividual>& population) {
    const uint32_t size = static_cast<uint32_t>(population.size());
    const uint32_t q = std::min(config_.tournament_size, size);

    std::vector<uint32_t> indices(size);
    std::iota(indices.begin(), indices.end(), 0);
    for (uint32_t i = 0; i < q; ++i) {
        std::uniform_int_distribution<uint32_t> dist(i, size - 1);
        uint32_t j = dist(rng_);
        std::swap(indices[i], indices[j]);
    }

    uint32_t best = indices[0];
    for (uint32_t i = 1; i < q; ++i) {
        if (population[indices[i]].fitness > population[best].fitness) {
            best = indices[i];
        }
    }
    return population[best];
}

void GeneticAlgorithm::crossover(const GAIndividual& parent_a,
                                 const GAIndividual& parent_b,
                                 GAIndividual& child_a,
                                 GAIndividual& child_b) {
    const uint32_t n = graph_->num_nodes();
    const uint32_t k = config_.k;

    std::vector<uint32_t> union_pool;
    union_pool.reserve(parent_a.seeds.size() + parent_b.seeds.size());
    std::unordered_set<uint32_t> present;
    present.reserve(parent_a.seeds.size() + parent_b.seeds.size());

    for (uint32_t node : parent_a.seeds) {
        if (present.insert(node).second) {
            union_pool.push_back(node);
        }
    }
    for (uint32_t node : parent_b.seeds) {
        if (present.insert(node).second) {
            union_pool.push_back(node);
        }
    }

    std::uniform_int_distribution<uint32_t> dist(0, n - 1);
    while (union_pool.size() < k) {
        uint32_t node = dist(rng_);
        if (present.insert(node).second) {
            union_pool.push_back(node);
        }
    }

    child_a.seeds = sample_from(union_pool);
    child_b.seeds = sample_from(union_pool);
    child_a.fitness = std::numeric_limits<double>::quiet_NaN();
    child_b.fitness = std::numeric_limits<double>::quiet_NaN();
}

uint32_t GeneticAlgorithm::random_node_not_in(const std::vector<uint8_t>& present) {
    const uint32_t n = graph_->num_nodes();
    std::uniform_int_distribution<uint32_t> dist(0, n - 1);

    for (uint32_t attempt = 0; attempt < 64; ++attempt) {
        uint32_t node = dist(rng_);
        if (!present[node]) {
            return node;
        }
    }

    for (uint32_t node = 0; node < n; ++node) {
        if (!present[node]) {
            return node;
        }
    }

    return 0;
}

void GeneticAlgorithm::mutate(GAIndividual& individual) {
    const uint32_t n = graph_->num_nodes();
    const uint32_t k = static_cast<uint32_t>(individual.seeds.size());
    if (k == 0 || k >= n || config_.mutation_rate <= 0.0) {
        return;
    }

    std::vector<uint8_t> present(n, 0);
    for (uint32_t node : individual.seeds) {
        present[node] = 1;
    }

    std::uniform_real_distribution<double> probability(0.0, 1.0);
    for (uint32_t i = 0; i < k; ++i) {
        if (probability(rng_) < config_.mutation_rate) {
            present[individual.seeds[i]] = 0;
            uint32_t replacement = random_node_not_in(present);
            present[replacement] = 1;
            individual.seeds[i] = replacement;
        }
    }

    std::sort(individual.seeds.begin(), individual.seeds.end());
    individual.fitness = std::numeric_limits<double>::quiet_NaN();
}

void GeneticAlgorithm::evaluate_individuals(std::vector<GAIndividual>& population,
                                            Evaluator& evaluator,
                                            bool only_unevaluated) {
    std::vector<size_t> indices;
    std::vector<std::vector<uint32_t>> seed_sets;
    indices.reserve(population.size());
    seed_sets.reserve(population.size());

    for (size_t i = 0; i < population.size(); ++i) {
        if (!only_unevaluated || std::isnan(population[i].fitness)) {
            indices.push_back(i);
            seed_sets.push_back(population[i].seeds);
        }
    }

    if (seed_sets.empty()) {
        return;
    }

    std::vector<double> scores = evaluator.batch_evaluate(seed_sets);
    for (size_t i = 0; i < indices.size(); ++i) {
        population[indices[i]].fitness = scores[i];
    }
}

double GeneticAlgorithm::population_mean(
    const std::vector<GAIndividual>& population) const {
    if (population.empty()) {
        return 0.0;
    }

    double total = 0.0;
    size_t count = 0;
    for (const auto& individual : population) {
        if (!std::isnan(individual.fitness)) {
            total += individual.fitness;
            ++count;
        }
    }
    return count > 0 ? total / static_cast<double>(count) : 0.0;
}

double GeneticAlgorithm::population_diversity(
    const std::vector<GAIndividual>& population) const {
    const size_t size = population.size();
    if (size < 2) {
        return 0.0;
    }

    double total = 0.0;
    uint64_t count = 0;

    for (size_t i = 0; i < size; ++i) {
        for (size_t j = i + 1; j < size; ++j) {
            const auto& a = population[i].seeds;
            const auto& b = population[j].seeds;

            size_t ia = 0;
            size_t ib = 0;
            size_t intersection = 0;
            while (ia < a.size() && ib < b.size()) {
                if (a[ia] == b[ib]) {
                    ++intersection;
                    ++ia;
                    ++ib;
                } else if (a[ia] < b[ib]) {
                    ++ia;
                } else {
                    ++ib;
                }
            }

            size_t union_size = a.size() + b.size() - intersection;
            double distance = union_size > 0
                ? 1.0 - static_cast<double>(intersection) / static_cast<double>(union_size)
                : 0.0;
            total += distance;
            ++count;
        }
    }

    return count > 0 ? total / static_cast<double>(count) : 0.0;
}

void GeneticAlgorithm::record_top(
    const std::vector<GAIndividual>& population,
    std::map<std::vector<uint32_t>, double>& top_map) const {
    for (const auto& individual : population) {
        if (std::isnan(individual.fitness)) {
            continue;
        }
        auto it = top_map.find(individual.seeds);
        if (it == top_map.end() || individual.fitness > it->second) {
            top_map[individual.seeds] = individual.fitness;
        }
    }
}

GAResult GeneticAlgorithm::run() {
    const auto started = Clock::now();
    Evaluator evaluator(graph_, model_, config_.num_mc_simulations, config_.seed);

    std::vector<GAIndividual> population = create_initial_population();
    evaluate_individuals(population, evaluator, false);

    std::map<std::vector<uint32_t>, double> top_map;
    record_top(population, top_map);

    auto best_it = std::max_element(
        population.begin(), population.end(),
        [](const GAIndividual& a, const GAIndividual& b) {
            return a.fitness < b.fitness;
        });
    GAIndividual best = *best_it;

    GAResult result;
    result.config = config_;
    result.best_fitness_history.push_back(best.fitness);
    result.mean_fitness_history.push_back(population_mean(population));
    result.diversity_history.push_back(population_diversity(population));

    uint32_t generations_completed = 0;

    for (uint32_t generation = 1; generation <= config_.max_generations; ++generation) {
        if (config_.max_evaluations > 0 &&
            evaluator.total_evaluations() >= config_.max_evaluations) {
            break;
        }

        std::vector<size_t> order(population.size());
        std::iota(order.begin(), order.end(), 0);
        std::stable_sort(
            order.begin(), order.end(),
            [&population](size_t a, size_t b) {
                return population[a].fitness > population[b].fitness;
            });

        std::vector<GAIndividual> next_population;
        next_population.reserve(config_.population_size);

        for (uint32_t i = 0; i < config_.elitism; ++i) {
            next_population.push_back(population[order[i]]);
        }

        std::uniform_real_distribution<double> probability(0.0, 1.0);
        while (next_population.size() < config_.population_size) {
            const GAIndividual& parent_a = tournament_select(population);
            const GAIndividual& parent_b = tournament_select(population);

            GAIndividual child_a;
            GAIndividual child_b;

            if (probability(rng_) < config_.crossover_rate) {
                crossover(parent_a, parent_b, child_a, child_b);
            } else {
                child_a = parent_a;
                child_b = parent_b;
                child_a.fitness = std::numeric_limits<double>::quiet_NaN();
                child_b.fitness = std::numeric_limits<double>::quiet_NaN();
            }

            mutate(child_a);
            mutate(child_b);

            next_population.push_back(std::move(child_a));
            if (next_population.size() < config_.population_size) {
                next_population.push_back(std::move(child_b));
            }
        }

        population = std::move(next_population);
        evaluate_individuals(population, evaluator, true);
        record_top(population, top_map);

        auto generation_best = std::max_element(
            population.begin(), population.end(),
            [](const GAIndividual& a, const GAIndividual& b) {
                return a.fitness < b.fitness;
            });
        if (generation_best->fitness > best.fitness) {
            best = *generation_best;
        }

        result.best_fitness_history.push_back(best.fitness);
        result.mean_fitness_history.push_back(population_mean(population));
        result.diversity_history.push_back(population_diversity(population));
        generations_completed = generation;

        if (config_.max_evaluations > 0 &&
            evaluator.total_evaluations() >= config_.max_evaluations) {
            break;
        }
    }

    const double validated_fitness = evaluator.evaluate(best.seeds);
    best.fitness = validated_fitness;

    top_map[best.seeds] = validated_fitness;

    std::vector<std::pair<std::vector<uint32_t>, double>> ranked(
        top_map.begin(), top_map.end());
    std::stable_sort(
        ranked.begin(), ranked.end(),
        [](const auto& a, const auto& b) {
            return a.second > b.second;
        });
    if (ranked.size() > 5) {
        ranked.resize(5);
    }

    for (const auto& entry : ranked) {
        GAIndividual individual;
        individual.seeds = entry.first;
        individual.fitness = entry.second;
        result.top_individuals.push_back(std::move(individual));
    }

    const auto finished = Clock::now();
    result.best_seeds = best.seeds;
    result.best_fitness = best.fitness;
    result.generations_completed = generations_completed;
    result.total_evaluations = evaluator.total_evaluations();
    result.total_mc_simulations = evaluator.total_mc_simulations();
    result.search_time_seconds =
        std::chrono::duration<double>(finished - started).count();

    return result;
}

} // namespace im_core
