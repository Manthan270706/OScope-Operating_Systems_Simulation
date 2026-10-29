#ifndef OSCOPE_PAGING_PAGE_REPLACEMENT_RESULT_HPP
#define OSCOPE_PAGING_PAGE_REPLACEMENT_RESULT_HPP

#include <optional>
#include <vector>

namespace oscope {

/**
 * @brief Represents a single step in a page replacement simulation.
 */
struct PageReplacementStep {
    int page{0};
    std::vector<int> frames;
    bool is_fault{false};
    std::optional<int> evicted_page{std::nullopt};
};

/**
 * @brief Summary and detailed result of a page replacement simulation.
 */
struct PageReplacementResult {
    std::vector<PageReplacementStep> steps;
    int total_references{0};
    int page_faults{0};
    int page_hits{0};
    double fault_rate{0.0};
    double hit_rate{0.0};
};

namespace paging {
    using oscope::PageReplacementStep;
    using oscope::PageReplacementResult;
}

} // namespace oscope

#endif // OSCOPE_PAGING_PAGE_REPLACEMENT_RESULT_HPP
