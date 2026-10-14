#include "oscope/paging/page_replacement_comparison.hpp"

#include <stdexcept>
#include <utility>

#include "oscope/paging/fifo.hpp"
#include "oscope/paging/lru.hpp"
#include "oscope/paging/optimal.hpp"

namespace oscope {

PageReplacementComparator::PageReplacementComparator() {
    algorithms_.emplace_back("FIFO", std::make_shared<FIFO>());
    algorithms_.emplace_back("LRU", std::make_shared<LRU>());
    algorithms_.emplace_back("Optimal", std::make_shared<Optimal>());
}

void PageReplacementComparator::add_algorithm(
    std::string name,
    std::shared_ptr<PageReplacementAlgorithm> algorithm) {
    if (!algorithm) {
        throw std::invalid_argument("Algorithm cannot be null.");
    }
    algorithms_.emplace_back(std::move(name), std::move(algorithm));
}

void PageReplacementComparator::add_algorithm(
    std::string name,
    PageReplacementAlgorithm& algorithm) {
    std::shared_ptr<PageReplacementAlgorithm> non_owning(&algorithm, [](PageReplacementAlgorithm*) {});
    algorithms_.emplace_back(std::move(name), std::move(non_owning));
}

void PageReplacementComparator::clear() noexcept {
    algorithms_.clear();
}

std::size_t PageReplacementComparator::size() const noexcept {
    return algorithms_.size();
}

bool PageReplacementComparator::empty() const noexcept {
    return algorithms_.empty();
}

PageReplacementComparisonResult
PageReplacementComparator::compare(
    const std::vector<int>& reference_string,
    int frame_count) const {
    if (frame_count <= 0) {
        throw std::invalid_argument("Frame count must be positive (> 0).");
    }

    for (int page : reference_string) {
        if (page < 0) {
            throw std::invalid_argument("Page number cannot be negative.");
        }
    }

    PageReplacementComparisonResult result;
    result.reference_string = reference_string;
    result.frame_count = frame_count;
    result.entries.reserve(algorithms_.size());

    for (const auto& [name, algorithm] : algorithms_) {
        if (!algorithm) {
            throw std::invalid_argument("Algorithm cannot be null.");
        }
        PageReplacementResult sim_result = algorithm->simulate(reference_string, frame_count);
        result.entries.push_back({name, std::move(sim_result)});
    }

    return result;
}

PageReplacementComparisonResult
PageReplacementComparator::compare_all(
    const std::vector<int>& reference_string,
    int frame_count) {
    PageReplacementComparator comparator;
    return comparator.compare(reference_string, frame_count);
}

PageReplacementComparisonResult
PageReplacementComparator::compare(
    const std::vector<int>& reference_string,
    int frame_count,
    const std::vector<std::pair<std::string, std::shared_ptr<PageReplacementAlgorithm>>>& algorithms) {
    PageReplacementComparator comparator;
    comparator.clear();
    for (const auto& [name, algorithm] : algorithms) {
        comparator.add_algorithm(name, algorithm);
    }
    return comparator.compare(reference_string, frame_count);
}

PageReplacementComparisonResult
PageReplacementComparator::compare(
    const std::vector<int>& reference_string,
    int frame_count,
    const std::vector<std::pair<std::string, PageReplacementAlgorithm*>>& algorithms) {
    PageReplacementComparator comparator;
    comparator.clear();
    for (const auto& [name, algorithm] : algorithms) {
        if (!algorithm) {
            throw std::invalid_argument("Algorithm pointer cannot be null.");
        }
        comparator.add_algorithm(name, *algorithm);
    }
    return comparator.compare(reference_string, frame_count);
}

} // namespace oscope
