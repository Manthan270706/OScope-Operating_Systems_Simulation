#ifndef OSCOPE_MEMORY_ALLOCATION_STRATEGY_HPP
#define OSCOPE_MEMORY_ALLOCATION_STRATEGY_HPP

#include <string_view>

namespace oscope::memory {

/**
 * @brief Strategy used to select a free block for dynamic memory allocation.
 */
enum class AllocationStrategy {
    FirstFit,
    BestFit,
    WorstFit
};

using AllocationAlgorithm = AllocationStrategy;

/**
 * @brief Returns a human-readable display string for an allocation strategy.
 */
inline constexpr std::string_view to_string(AllocationStrategy strategy) noexcept {
    switch (strategy) {
        case AllocationStrategy::FirstFit:
            return "First Fit";
        case AllocationStrategy::BestFit:
            return "Best Fit";
        case AllocationStrategy::WorstFit:
            return "Worst Fit";
    }
    return "Unknown";
}

} // namespace oscope::memory

namespace oscope {
    using oscope::memory::AllocationStrategy;
    using oscope::memory::AllocationAlgorithm;
    using oscope::memory::to_string;
}

#endif // OSCOPE_MEMORY_ALLOCATION_STRATEGY_HPP
