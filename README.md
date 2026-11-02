# Influence Maximization Benchmark

This is an Experimental Research Platform for evaluating metaheuristic algorithms for the Influence Maximization problem in social networks.

## Project Structure

```
IM-Metaheuristic-Research/
├── README.md
├── pyproject.toml
├── CMakeLists.txt
├── .gitignore
├── cpp_core/          # C++ core with evaluation engine
│   ├── include/
│   ├── src/
│   └── bindings/
├── docs/              # Documentation
│   ├── experimental_environment.md
│   └── workflows.md
├── src/               # Python layer
│   └── im_research/   # Main Python package
├── runs/              # Runtime directory (generated)
└── tests/             # Test suite
```

## Key Components

- **C++ Core**: High-performance graph algorithms, Monte Carlo simulations, and evaluation engine
- **Python Layer**: Algorithm implementation, experiment runner, statistical analysis
- **pybind11**: Python-C++ binding
- **CMake**: Build system
- **YAML**: Configuration files for experiments

## Setup

1. Clone the repository
2. Set up Python environment (Python 3.12+)
3. Install dependencies: `pip install -r requirements.txt`
4. Build C++ core with CMake: `mkdir build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make`
5. Run experiments using the CLI or Python API

## License

This project is licensed under the MIT License - see the LICENSE file for details.