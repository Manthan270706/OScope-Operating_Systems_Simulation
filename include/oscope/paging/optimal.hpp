#ifndef OSCOPE_PAGING_OPTIMAL_HPP
#define OSCOPE_PAGING_OPTIMAL_HPP

#include <vector>

#include "oscope/paging/page_replacement_algorithm.hpp"

namespace oscope {

/**
 * @brief Optimal (OPT / MIN) page replacement algorithm.
 *
 * Evicts the resident page that will not be referenced for the longest period of time.
 * If a resident page will never be referenced again in the future, it is an optimal
 * candidate for eviction.
 */
class Optimal : public PageReplacementAlgorithm {
public:
    Optimal() = default;
    ~Optimal() override = default;

    PageReplacementResult
    simulate(const std::vector<int>& reference_string, int frame_count) override;
};

namespace paging {
    using oscope::Optimal;
}

} // namespace oscope

#endif // OSCOPE_PAGING_OPTIMAL_HPP
