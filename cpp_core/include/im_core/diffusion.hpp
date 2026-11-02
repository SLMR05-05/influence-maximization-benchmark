#pragma once

#include <string>

namespace im_core {

enum class DiffusionModel {
    IndependentCascade = 0,
    LinearThreshold = 1
};

inline std::string to_string(DiffusionModel model) {
    switch (model) {
        case DiffusionModel::IndependentCascade: return "IndependentCascade";
        case DiffusionModel::LinearThreshold: return "LinearThreshold";
        default: return "Unknown";
    }
}

inline DiffusionModel diffusion_model_from_string(const std::string& name) {
    if (name == "IC" || name == "IndependentCascade") {
        return DiffusionModel::IndependentCascade;
    }
    if (name == "LT" || name == "LinearThreshold") {
        return DiffusionModel::LinearThreshold;
    }
    return DiffusionModel::IndependentCascade;
}

} // namespace im_core

