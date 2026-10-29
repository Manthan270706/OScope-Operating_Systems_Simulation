#ifndef OSCOPE_PAGING_ADDRESS_TRANSLATION_HPP
#define OSCOPE_PAGING_ADDRESS_TRANSLATION_HPP

#include <cstdint>
#include <deque>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace oscope::paging {

struct PageTableEntry {
    int frame_number{-1};
    bool valid{false};
    bool dirty{false};
    bool referenced{false};
};

struct TranslationResult {
    uint64_t virtual_address{0};
    uint64_t page_number{0};
    uint64_t offset{0};
    bool page_fault{true};
    int frame_number{-1};
    uint64_t physical_address{0};
    std::string message;
};

struct DemandPagingStep {
    uint64_t virtual_address{0};
    uint64_t page_number{0};
    uint64_t offset{0};
    bool page_fault{false};
    int frame_number{-1};
    uint64_t physical_address{0};
    int victim_page{-1};
    std::vector<int> frame_contents; // frames at this step (-1 if empty)
};

struct DemandPagingResult {
    uint64_t page_size{0};
    int total_frames{0};
    std::vector<DemandPagingStep> steps;
    int total_accesses{0};
    int page_faults{0};
    int page_hits{0};
    double fault_rate{0.0};
};

struct ThrashingDataPoint {
    int frames{0};
    int page_faults{0};
    double fault_rate{0.0};
};

struct ThrashingSimulationResult {
    std::vector<int> reference_string;
    std::vector<ThrashingDataPoint> points;
    int thrashing_threshold_frames{0}; // frame count below which fault rate spikes significantly
};

/**
 * @brief Simulates virtual-to-physical address translation and demand paging.
 */
class AddressTranslator {
public:
    explicit AddressTranslator(uint64_t page_size = 4096);

    uint64_t page_size() const noexcept { return page_size_; }
    bool set_page_size(uint64_t size);

    void map_page(uint64_t page_number, int frame_number, bool dirty = false);
    bool unmap_page(uint64_t page_number);
    void clear_page_table() noexcept;

    std::optional<PageTableEntry> get_entry(uint64_t page_number) const;
    const std::unordered_map<uint64_t, PageTableEntry>& page_table() const noexcept {
        return page_table_;
    }

    /**
     * @brief Translates a virtual address to a physical address using the current page table.
     */
    TranslationResult translate(uint64_t virtual_address) const;

    /**
     * @brief Simulates demand paging using FIFO page replacement across a sequence of virtual addresses.
     */
    static DemandPagingResult simulate_demand_paging(
        uint64_t page_size,
        int num_frames,
        const std::vector<uint64_t>& virtual_addresses);

    /**
     * @brief Simulates thrashing behavior across varying frame allocations.
     */
    static ThrashingSimulationResult simulate_thrashing(
        const std::vector<int>& page_references,
        int min_frames,
        int max_frames);

private:
    uint64_t page_size_{4096};
    std::unordered_map<uint64_t, PageTableEntry> page_table_;
};

} // namespace oscope::paging

#endif // OSCOPE_PAGING_ADDRESS_TRANSLATION_HPP
