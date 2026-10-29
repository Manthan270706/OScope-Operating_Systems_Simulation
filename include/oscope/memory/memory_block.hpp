#ifndef OSCOPE_MEMORY_MEMORY_BLOCK_HPP
#define OSCOPE_MEMORY_MEMORY_BLOCK_HPP

#include <cstddef>
#include <optional>

namespace oscope::memory {

/**
 * @brief Represents a contiguous segment of memory within the pool.
 */
struct MemoryBlock {
    std::optional<int> allocation_id{std::nullopt};
    std::size_t start_address{0};
    std::size_t size{0};
    bool is_allocated{false};
    std::optional<int> process_id{std::nullopt};
};

} // namespace oscope::memory

namespace oscope {
    using oscope::memory::MemoryBlock;
}

#endif // OSCOPE_MEMORY_MEMORY_BLOCK_HPP
