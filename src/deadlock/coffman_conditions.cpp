#include "oscope/deadlock/coffman_conditions.hpp"

namespace oscope::deadlock {

std::string CoffmanEvaluator::get_educational_overview() {
    return "The Coffman conditions are four necessary and sufficient conditions for deadlock to occur "
           "in a system with non-preemptible, dedicated resources:\n"
           "1. Mutual Exclusion: At least one resource must be non-shareable.\n"
           "2. Hold and Wait: A process holds allocated resources while waiting for more.\n"
           "3. No Preemption: Resources cannot be forcibly taken; they must be voluntarily released.\n"
           "4. Circular Wait: A closed loop of processes exists where each waits for a resource held by the next.\n"
           "Eliminating ANY ONE of these four conditions guarantees deadlock prevention.";
}

CoffmanConditionReport CoffmanEvaluator::evaluate(
    bool mutual_exclusion,
    bool hold_and_wait,
    bool no_preemption,
    bool circular_wait) {

    CoffmanConditionReport report;
    report.mutual_exclusion = mutual_exclusion;
    report.hold_and_wait = hold_and_wait;
    report.no_preemption = no_preemption;
    report.circular_wait = circular_wait;

    // Deadlock is only possible if ALL four conditions hold simultaneously
    report.deadlock_possible = mutual_exclusion && hold_and_wait && no_preemption && circular_wait;

    if (mutual_exclusion) {
        report.condition_analyses.push_back("Mutual Exclusion: ACTIVE (one or more resources cannot be concurrently shared).");
    } else {
        report.condition_analyses.push_back("Mutual Exclusion: BROKEN (all resources are sharable or virtualized, e.g. read-only files, spooled printers).");
    }

    if (hold_and_wait) {
        report.condition_analyses.push_back("Hold and Wait: ACTIVE (processes are retaining allocated resources while requesting others).");
    } else {
        report.condition_analyses.push_back("Hold and Wait: BROKEN (processes must request all resources simultaneously upfront or release before requesting).");
    }

    if (no_preemption) {
        report.condition_analyses.push_back("No Preemption: ACTIVE (resources cannot be forcibly reclaimed from a running process).");
    } else {
        report.condition_analyses.push_back("No Preemption: BROKEN (system preempts resources when a process must wait, restarting or rolling back).");
    }

    if (circular_wait) {
        report.condition_analyses.push_back("Circular Wait: ACTIVE (a cyclical dependency chain of waiting processes exists).");
    } else {
        report.condition_analyses.push_back("Circular Wait: BROKEN (strict global resource ordering / hierarchy prevents circular dependencies).");
    }

    if (report.deadlock_possible) {
        report.summary = "DEADLOCK VULNERABLE: All four Coffman conditions are satisfied.";
    } else {
        report.summary = "DEADLOCK FREE: At least one Coffman condition is eliminated, preventing deadlocks.";
    }

    report.prevention_methods = {
        "1. Spooling/Sharing: Convert exclusive resources into shared virtual devices.",
        "2. All-at-Once Allocation: Require processes to request all needed resources at initiation.",
        "3. Preemption Protocol: Force release of held resources when an additional resource cannot be granted.",
        "4. Resource Ordering: Enforce a strict linear ordering F(R) on all resource types."
    };

    return report;
}

CoffmanConditionReport CoffmanEvaluator::demonstrate_prevention(PreventionStrategy strategy) {
    switch (strategy) {
    case PreventionStrategy::SpoolingOrSharing:
        return evaluate(false, true, true, true);
    case PreventionStrategy::AllOrNothingAllocation:
        return evaluate(true, false, true, true);
    case PreventionStrategy::ResourcePreemption:
        return evaluate(true, true, false, true);
    case PreventionStrategy::HierarchicalOrdering:
        return evaluate(true, true, true, false);
    }
    return evaluate(true, true, true, true);
}

} // namespace oscope::deadlock
