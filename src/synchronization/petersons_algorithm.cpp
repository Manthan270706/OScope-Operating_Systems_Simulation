#include "oscope/synchronization/petersons_algorithm.hpp"

namespace oscope::synchronization {

PetersonsAlgorithm::PetersonsAlgorithm() {
    reset();
}

void PetersonsAlgorithm::reset() {
    flag_[0] = false;
    flag_[1] = false;
    turn_ = 0;
    in_cs_[0] = false;
    in_cs_[1] = false;
}

bool PetersonsAlgorithm::flag(int process_id) const {
    if (process_id == 0 || process_id == 1) {
        return flag_[process_id];
    }
    return false;
}

std::string PetersonsAlgorithm::get_educational_notes() {
    return "Peterson's Algorithm guarantees Mutual Exclusion, Progress, and Bounded Waiting "
           "for two processes assuming sequential consistency. On modern out-of-order superscalar "
           "processors with store buffers, memory barriers (mfence / std::atomic_thread_fence) "
           "or atomic variables with acquire-release / sequential consistency semantics are strictly "
           "required to prevent CPU instruction reordering.";
}

PetersonSimulationResult PetersonsAlgorithm::simulate(int rounds, int interleave_pattern) {
    reset();
    PetersonSimulationResult result;
    result.mutual_exclusion_maintained = true;
    result.explanation = get_educational_notes();

    if (rounds <= 0) rounds = 1;

    auto record_step = [&](int pid, PetersonAction action, const std::string& desc) {
        PetersonStep step;
        step.process_id = pid;
        step.action = action;
        step.description = desc;
        step.flag0 = flag_[0];
        step.flag1 = flag_[1];
        step.turn = turn_;
        step.p0_in_cs = in_cs_[0] ? 1 : 0;
        step.p1_in_cs = in_cs_[1] ? 1 : 0;
        step.mutual_exclusion_held = !(in_cs_[0] && in_cs_[1]);

        if (!step.mutual_exclusion_held) {
            result.mutual_exclusion_maintained = false;
        }

        result.trace.push_back(step);
    };

    for (int r = 0; r < rounds; ++r) {
        // Depending on interleave_pattern, alternate who expresses interest first
        int first = (interleave_pattern == 0) ? (r % 2) : (interleave_pattern == 1 ? 0 : 1);
        int second = 1 - first;

        // 1. First process sets its flag = true
        flag_[first] = true;
        record_step(first, PetersonAction::SetFlag, "Process " + std::to_string(first) + " sets flag = true (intends to enter CS)");

        // 2. Second process sets its flag = true (competing arrival)
        flag_[second] = true;
        record_step(second, PetersonAction::SetFlag, "Process " + std::to_string(second) + " sets flag = true (competing arrival)");

        // 3. First process gives turn to second
        turn_ = second;
        record_step(first, PetersonAction::SetTurn, "Process " + std::to_string(first) + " yields turn = " + std::to_string(second));

        // 4. Second process gives turn to first
        turn_ = first;
        record_step(second, PetersonAction::SetTurn, "Process " + std::to_string(second) + " yields turn = " + std::to_string(first));

        // Now evaluate entry conditions:
        // First process tests: (flag_[second] && turn_ == second) -> false, because turn_ == first!
        // So first process enters Critical Section!
        in_cs_[first] = true;
        if (first == 0) result.p0_critical_entries++;
        else result.p1_critical_entries++;

        record_step(first, PetersonAction::EnterCriticalSection, "Process " + std::to_string(first) + " enters Critical Section (turn == " + std::to_string(first) + ")");
        record_step(first, PetersonAction::ExecuteCriticalSection, "Process " + std::to_string(first) + " executes inside Critical Section");

        // Second process tests condition: flag_[first] is true AND turn_ == first -> busy wait!
        record_step(second, PetersonAction::WaitBusy, "Process " + std::to_string(second) + " waits: flag[" + std::to_string(first) + "] is true and turn == " + std::to_string(first));

        // First process leaves Critical Section
        in_cs_[first] = false;
        flag_[first] = false;
        record_step(first, PetersonAction::ExitCriticalSection, "Process " + std::to_string(first) + " exits Critical Section and sets flag = false");
        record_step(first, PetersonAction::ExecuteRemainder, "Process " + std::to_string(first) + " enters Remainder Section");

        // Now second process condition (flag_[first] && turn_ == first) is FALSE because flag_[first] is false!
        // Second process can now enter Critical Section!
        in_cs_[second] = true;
        if (second == 0) result.p0_critical_entries++;
        else result.p1_critical_entries++;

        record_step(second, PetersonAction::EnterCriticalSection, "Process " + std::to_string(second) + " enters Critical Section (flag[" + std::to_string(first) + "] cleared)");
        record_step(second, PetersonAction::ExecuteCriticalSection, "Process " + std::to_string(second) + " executes inside Critical Section");

        // Second process leaves Critical Section
        in_cs_[second] = false;
        flag_[second] = false;
        record_step(second, PetersonAction::ExitCriticalSection, "Process " + std::to_string(second) + " exits Critical Section and sets flag = false");
        record_step(second, PetersonAction::ExecuteRemainder, "Process " + std::to_string(second) + " enters Remainder Section");
    }

    result.total_steps = static_cast<int>(result.trace.size());
    return result;
}

} // namespace oscope::synchronization
