#ifndef OSCOPE_PAGING_LRU_HPP
#define OSCOPE_PAGING_LRU_HPP

#include <vector>

#include "oscope/paging/page_replacement_algorithm.hpp"

namespace oscope {

/**
 * @brief Least Recently Used (LRU) page replacement algorithm.
 *
 * When a page fault occurs and frames are full, the page that has not been
 * referenced for the longest period of time is selected for eviction.
 */
class LRU : public PageReplacementAlgorithm {
public:
    LRU() = default;
    ~LRU() override = default;

    PageReplacementResult
    simulate(const std::vector<int>& reference_string, int frame_count) override;
};

namespace paging {
    using oscope::LRU;
}

} // namespace oscope

#endif // OSCOPE_PAGING_LRU_HPP
