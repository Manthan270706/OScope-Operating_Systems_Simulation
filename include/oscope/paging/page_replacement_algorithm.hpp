#ifndef OSCOPE_PAGING_PAGE_REPLACEMENT_ALGORITHM_HPP
#define OSCOPE_PAGING_PAGE_REPLACEMENT_ALGORITHM_HPP

#include <vector>

#include "oscope/paging/page_replacement_result.hpp"

namespace oscope {

/**
 * @brief Abstract base class for page-replacement simulation algorithms.
 */
class PageReplacementAlgorithm {
public:
    virtual ~PageReplacementAlgorithm() = default;

    /**
     * @brief Simulates page replacement on the provided page reference string.
     *
     * @param reference_string Sequence of referenced page numbers.
     * @param frame_count Positive number of allocated physical frames.
     * @return PageReplacementResult Detailed step-by-step and summary metrics.
     * @throws std::invalid_argument If frame_count <= 0 or reference_string has negative page numbers.
     */
    virtual PageReplacementResult
    simulate(const std::vector<int>& reference_string, int frame_count) = 0;
};

namespace paging {
    using oscope::PageReplacementAlgorithm;
}

} // namespace oscope

#endif // OSCOPE_PAGING_PAGE_REPLACEMENT_ALGORITHM_HPP
