#ifndef OSCOPE_PAGING_PAGE_REPLACEMENT_COMPARISON_HPP
#define OSCOPE_PAGING_PAGE_REPLACEMENT_COMPARISON_HPP

#include <cstddef>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "oscope/paging/page_replacement_algorithm.hpp"
#include "oscope/paging/page_replacement_result.hpp"

namespace oscope {

/**
 * @brief Evaluation result for an individual page replacement algorithm in a comparison.
 */
struct PageReplacementComparisonEntry {
    std::string algorithm_name;
    PageReplacementResult result;

    int total_references() const noexcept {
        return result.total_references;
    }

    int page_faults() const noexcept {
        return result.page_faults;
    }

    int page_hits() const noexcept {
        return result.page_hits;
    }

    double fault_rate() const noexcept {
        return result.fault_rate;
    }

    double hit_rate() const noexcept {
        return result.hit_rate;
    }

    const std::vector<PageReplacementStep>& steps() const noexcept {
        return result.steps;
    }
};

/**
 * @brief Comprehensive comparison result across multiple page replacement algorithms.
 */
struct PageReplacementComparisonResult {
    std::vector<int> reference_string;
    int frame_count{0};
    std::vector<PageReplacementComparisonEntry> entries;

    auto begin() noexcept { return entries.begin(); }
    auto end() noexcept { return entries.end(); }
    auto begin() const noexcept { return entries.begin(); }
    auto end() const noexcept { return entries.end(); }
    std::size_t size() const noexcept { return entries.size(); }
    bool empty() const noexcept { return entries.empty(); }
    const PageReplacementComparisonEntry& operator[](std::size_t idx) const { return entries[idx]; }
    PageReplacementComparisonEntry& operator[](std::size_t idx) { return entries[idx]; }

    const PageReplacementComparisonEntry* find(const std::string& name) const {
        for (const auto& entry : entries) {
            if (entry.algorithm_name == name) {
                return &entry;
            }
        }
        return nullptr;
    }
};

/**
 * @brief Compares page replacement algorithms on the same reference string and frame count.
 */
class PageReplacementComparator {
public:
    /**
     * @brief Constructs comparator pre-configured with FIFO, LRU, and Optimal algorithms.
     */
    PageReplacementComparator();

    void add_algorithm(std::string name, std::shared_ptr<PageReplacementAlgorithm> algorithm);
    void add_algorithm(std::string name, PageReplacementAlgorithm& algorithm);

    void clear() noexcept;
    std::size_t size() const noexcept;
    bool empty() const noexcept;

    /**
     * @brief Evaluates all registered algorithms on the given reference string and frame count.
     */
    PageReplacementComparisonResult
    compare(const std::vector<int>& reference_string, int frame_count) const;

    /**
     * @brief Static convenience helper comparing default FIFO, LRU, and Optimal algorithms.
     */
    static PageReplacementComparisonResult
    compare_all(const std::vector<int>& reference_string, int frame_count);

    static PageReplacementComparisonResult
    compare(
        const std::vector<int>& reference_string,
        int frame_count,
        const std::vector<std::pair<std::string, std::shared_ptr<PageReplacementAlgorithm>>>& algorithms);

    static PageReplacementComparisonResult
    compare(
        const std::vector<int>& reference_string,
        int frame_count,
        const std::vector<std::pair<std::string, PageReplacementAlgorithm*>>& algorithms);

private:
    std::vector<std::pair<std::string, std::shared_ptr<PageReplacementAlgorithm>>> algorithms_;
};

namespace paging {
    using oscope::PageReplacementComparisonEntry;
    using oscope::PageReplacementComparisonResult;
    using oscope::PageReplacementComparator;
}

} // namespace oscope
#endif // OSCOPE_PAGING_PAGE_REPLACEMENT_COMPARISON_HPP
