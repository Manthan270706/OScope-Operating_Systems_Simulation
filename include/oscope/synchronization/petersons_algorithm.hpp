#ifndef OSCOPE_SYNCHRONIZATION_PETERSONS_ALGORITHM_HPP
#define OSCOPE_SYNCHRONIZATION_PETERSONS_ALGORITHM_HPP

#include <string>
#include <vector>

namespace oscope::synchronization {

enum class PetersonAction {
    SetFlag,
    SetTurn,
    WaitBusy,
    EnterCriticalSection,
    ExecuteCriticalSection,
    ExitCriticalSection,
    ExecuteRemainder
};

struct PetersonStep {
    int process_id{0}; // 0 or 1
    PetersonAction action{PetersonAction::ExecuteRemainder};
    std::string description;
    bool flag0{false};
    bool flag1{false};
    int turn{0};
    int p0_in_cs{0};
    int p1_in_cs{0};
    bool mutual_exclusion_held{true};
};

struct PetersonSimulationResult {
    bool mutual_exclusion_maintained{true};
    int p0_critical_entries{0};
    int p1_critical_entries{0};
    int total_steps{0};
    std::vector<PetersonStep> trace;
    std::string explanation;
};

/**
 * @brief Deterministic, educational simulation of Peterson's Two-Process Solution.
 */
class PetersonsAlgorithm {
public:
    PetersonsAlgorithm();

    void reset();

    /**
     * @brief Simulates an interleaved execution of Process 0 and Process 1 for a specified number of rounds.
     * @param rounds Number of iterations each process attempts.
     * @param interleave_pattern Determines which process steps first in each phase.
     */
    PetersonSimulationResult simulate(int rounds = 3, int interleave_pattern = 0);

    bool flag(int process_id) const;
    int turn() const noexcept { return turn_; }

    static std::string get_educational_notes();

private:
    bool flag_[2]{false, false};
    int turn_{0};
    bool in_cs_[2]{false, false};
};

} // namespace oscope::synchronization

#endif // OSCOPE_SYNCHRONIZATION_PETERSONS_ALGORITHM_HPP
