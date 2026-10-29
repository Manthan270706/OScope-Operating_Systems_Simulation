#ifndef OSCOPE_MEMORY_ALLOCATION_RESULT_HPP
#define OSCOPE_MEMORY_ALLOCATION_RESULT_HPP

#include <cstddef>
#include <optional>
#include <string>

namespace oscope::memory {

/**
 * @brief Represents the outcome of an allocation request.
 */
struct AllocationResult {
    bool success{false};
    std::optional<int> allocation_id{std::nullopt};
    std::size_t start_address{0};
    std::size_t size{0};
    std::string error_message;
};

/**
 * @brief Memory pool utilization and fragmentation metrics.
 */
struct MemoryMetrics {
    std::size_t total_memory{0};
    std::size_t allocated_memory{0};
    std::size_t free_memory{0};
    std::size_t largest_free_block{0};
    double external_fragmentation{0.0};
};

} // namespace oscope::memory

namespace oscope {
    using oscope::memory::AllocationResult;
    using oscope::memory::MemoryMetrics;
}

#endif // OSCOPE_MEMORY_ALLOCATION_RESULT_HPP
