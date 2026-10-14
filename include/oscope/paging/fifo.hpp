#ifndef OSCOPE_PAGING_FIFO_HPP
#define OSCOPE_PAGING_FIFO_HPP

#include <vector>

#include "oscope/paging/page_replacement_algorithm.hpp"

namespace oscope {

/**
 * @brief First-In, First-Out (FIFO) page replacement algorithm.
 *
 * When a page fault occurs and frames are full, the oldest loaded page is evicted.
 */
class FIFO : public PageReplacementAlgorithm {
public:
    FIFO() = default;
    ~FIFO() override = default;

    PageReplacementResult
    simulate(const std::vector<int>& reference_string, int frame_count) override;
};

namespace paging {
    using oscope::FIFO;
}

} // namespace oscope

#endif // OSCOPE_PAGING_FIFO_HPP
