#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "im_core/graph.hpp"
#include "im_core/diffusion.hpp"
#include "im_core/monte_carlo.hpp"
#include "im_core/evaluator.hpp"

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
        .def("num_nodes", &Graph::num_nodes)
        .def("num_edges", &Graph::num_edges)
        .def("is_directed", &Graph::is_directed)
        .def("out_degree", &Graph::out_degree, py::arg("u"))
        .def("row_ptr", &Graph::row_ptr)
        .def("col_indices", &Graph::col_indices)
        .def("edge_probs", &Graph::edge_probs);

    py::class_<Evaluator, std::shared_ptr<Evaluator>>(m, "Evaluator")
        .def(py::init<std::shared_ptr<const Graph>, DiffusionModel, uint32_t, uint64_t>(),
             py::arg("graph"), py::arg("model") = DiffusionModel::IndependentCascade,
             py::arg("num_mc_simulations") = 1000, py::arg("seed") = 42)
        // Release GIL during simulation so multiple threads run at 100% CPU!
        .def("evaluate", &Evaluator::evaluate, py::arg("seed_set"),
             py::call_guard<py::gil_scoped_release>(),
             "Evaluate influence spread for a single seed set.")
        .def("batch_evaluate", &Evaluator::batch_evaluate, py::arg("seed_sets"),
             py::call_guard<py::gil_scoped_release>(),
             "Pygmo-style parallel batch evaluation of multiple candidate seed sets.")
        .def("total_evaluations", &Evaluator::total_evaluations)
        .def("total_mc_simulations", &Evaluator::total_mc_simulations)
        .def("reset_counters", &Evaluator::reset_counters)
        .def("set_num_mc_simulations", &Evaluator::set_num_mc_simulations)
        .def("num_mc_simulations", &Evaluator::num_mc_simulations)
        .def("set_seed", &Evaluator::set_seed)
        .def("seed", &Evaluator::seed);
}

