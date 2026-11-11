#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "im_core/graph.hpp"
#include "im_core/diffusion.hpp"
#include "im_core/monte_carlo.hpp"
#include "im_core/evaluator.hpp"
#include "im_core/ga.hpp"

namespace py = pybind11;
using namespace im_core;

PYBIND11_MODULE(_im_core, m) {
    m.doc() = "High-performance C++ Core for Influence Maximization Research Platform";

    py::enum_<DiffusionModel>(m, "DiffusionModel")
        .value("IndependentCascade", DiffusionModel::IndependentCascade)
        .value("LinearThreshold", DiffusionModel::LinearThreshold)
        .export_values();

    py::class_<Graph, std::shared_ptr<Graph>>(m, "Graph")
        .def(py::init<uint32_t, const std::vector<uint32_t>&, const std::vector<uint32_t>&, const std::vector<float>&, bool>(),
             py::arg("num_nodes"), py::arg("row_ptr"), py::arg("col_indices"), py::arg("edge_probs"), py::arg("is_directed") = false)
        .def_static("from_edge_list", &Graph::from_edge_list,
             py::arg("num_nodes"), py::arg("edges"), py::arg("probs"), py::arg("is_directed") = false)
        .def_static("from_edge_list_wc", &Graph::from_edge_list_wc,
             py::arg("num_nodes"), py::arg("edges"), py::arg("is_directed") = false)
        .def("num_nodes", &Graph::num_nodes)
        .def("num_edges", &Graph::num_edges)
        .def("is_directed", &Graph::is_directed)
        .def("out_degree", &Graph::out_degree, py::arg("u"))
        .def("row_ptr", &Graph::row_ptr)
        .def("col_indices", &Graph::col_indices)
        .def("edge_probs", &Graph::edge_probs)
        .def("edge_prob", &Graph::edge_prob, py::arg("u"), py::arg("v"));

    py::class_<Evaluator, std::shared_ptr<Evaluator>>(m, "Evaluator")
        .def(py::init<std::shared_ptr<const Graph>, DiffusionModel, uint32_t, uint64_t>(),
             py::arg("graph"), py::arg("model") = DiffusionModel::IndependentCascade,
             py::arg("num_mc_simulations") = 1000, py::arg("seed") = 42)
        // Release GIL during simulation so multiple threads run at 100% CPU!
        .def("evaluate", &Evaluator::evaluate, py::arg("seed_set"),
             py::call_guard<py::gil_scoped_release>(),
             "Evaluate influence spread for a single seed set.")
        .def("evaluate_replications", &Evaluator::evaluate_replications,
             py::arg("seed_set"), py::arg("num_replications"),
             py::call_guard<py::gil_scoped_release>(),
             "Return the activated-node count for each Monte Carlo replication.")
        .def("batch_evaluate", &Evaluator::batch_evaluate, py::arg("seed_sets"),
             py::call_guard<py::gil_scoped_release>(),
             "Pygmo-style parallel batch evaluation of multiple candidate seed sets.")
        .def("total_evaluations", &Evaluator::total_evaluations)
        .def("total_mc_simulations", &Evaluator::total_mc_simulations)
        .def("reset_counters", &Evaluator::reset_counters)
        .def("set_num_mc_simulations", &Evaluator::set_num_mc_simulations)
        .def("num_mc_simulations", &Evaluator::num_mc_simulations)
        .def("model", &Evaluator::model)
        .def("set_seed", &Evaluator::set_seed)
        .def("seed", &Evaluator::seed);

    py::class_<GAConfig>(m, "GAConfig")
        .def(py::init<>())
        .def_readwrite("k", &GAConfig::k)
        .def_readwrite("population_size", &GAConfig::population_size)
        .def_readwrite("max_generations", &GAConfig::max_generations)
        .def_readwrite("tournament_size", &GAConfig::tournament_size)
        .def_readwrite("crossover_rate", &GAConfig::crossover_rate)
        .def_readwrite("mutation_rate", &GAConfig::mutation_rate)
        .def_readwrite("elitism", &GAConfig::elitism)
        .def_readwrite("num_mc_simulations", &GAConfig::num_mc_simulations)
        .def_readwrite("seed", &GAConfig::seed)
        .def_readwrite("max_evaluations", &GAConfig::max_evaluations);

    py::class_<GAIndividual>(m, "GAIndividual")
        .def(py::init<>())
        .def_readonly("seeds", &GAIndividual::seeds)
        .def_readonly("fitness", &GAIndividual::fitness);

    py::class_<GAResult>(m, "GAResult")
        .def_readonly("best_seeds", &GAResult::best_seeds)
        .def_readonly("best_fitness", &GAResult::best_fitness)
        .def_readonly("best_fitness_history", &GAResult::best_fitness_history)
        .def_readonly("mean_fitness_history", &GAResult::mean_fitness_history)
        .def_readonly("diversity_history", &GAResult::diversity_history)
        .def_readonly("top_individuals", &GAResult::top_individuals)
        .def_readonly("total_evaluations", &GAResult::total_evaluations)
        .def_readonly("total_mc_simulations", &GAResult::total_mc_simulations)
        .def_readonly("generations_completed", &GAResult::generations_completed)
        .def_readonly("search_time_seconds", &GAResult::search_time_seconds)
        .def_readonly("config", &GAResult::config);

    py::class_<GeneticAlgorithm, std::shared_ptr<GeneticAlgorithm>>(m, "GeneticAlgorithm")
        .def(py::init<std::shared_ptr<const Graph>, DiffusionModel, GAConfig>(),
             py::arg("graph"), py::arg("model"), py::arg("config"))
        .def("run", &GeneticAlgorithm::run,
             py::call_guard<py::gil_scoped_release>(),
             "Run the baseline genetic algorithm.");
}

