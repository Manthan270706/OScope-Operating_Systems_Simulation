#ifndef OSCOPE_DEADLOCK_COFFMAN_CONDITIONS_HPP
#define OSCOPE_DEADLOCK_COFFMAN_CONDITIONS_HPP

#include <string>
#include <vector>

namespace oscope::deadlock {

enum class PreventionStrategy {
    SpoolingOrSharing,      // Invalidate Mutual Exclusion
    AllOrNothingAllocation, // Invalidate Hold and Wait
    ResourcePreemption,     // Invalidate No Preemption
    HierarchicalOrdering    // Invalidate Circular Wait
};

struct CoffmanConditionReport {
    bool mutual_exclusion{true};
    bool hold_and_wait{true};
    bool no_preemption{true};
    bool circular_wait{true};
    bool deadlock_possible{true};
    std::string summary;
    std::vector<std::string> condition_analyses;
    std::vector<std::string> prevention_methods;
};

class CoffmanEvaluator {
public:
    /**
     * @brief Evaluates the four Coffman conditions given boolean indicators for each condition.
     */
    static CoffmanConditionReport evaluate(
        bool mutual_exclusion,
        bool hold_and_wait,
        bool no_preemption,
        bool circular_wait);

    /**
     * @brief Demonstrates how applying a specific prevention strategy eliminates deadlock vulnerability.
     */
    static CoffmanConditionReport demonstrate_prevention(PreventionStrategy strategy);

    static std::string get_educational_overview();
};

} // namespace oscope::deadlock

#endif // OSCOPE_DEADLOCK_COFFMAN_CONDITIONS_HPP
