#include <gtest/gtest.h>

#include "oscope/process.hpp"
#include "oscope/process_manager.hpp"
#include "oscope/process_state.hpp"

// 1. Successful process registration and initial state
TEST(OScopeProcessManagerTest, RegistersProcessWithInitialStateNew) {
    oscope::ProcessManager manager;
    oscope::Process proc{1, 0, 10, 1};

    EXPECT_TRUE(manager.register_process(proc));
    EXPECT_EQ(manager.process_count(), 1);
    EXPECT_FALSE(manager.empty());
    EXPECT_TRUE(manager.has_process(1));

    auto state = manager.get_state(1);
    ASSERT_TRUE(state.has_value());
    EXPECT_EQ(state.value(), oscope::ProcessState::New);

    auto retrieved_proc = manager.get_process(1);
    ASSERT_TRUE(retrieved_proc.has_value());
    EXPECT_EQ(retrieved_proc->pid, 1);
    EXPECT_EQ(retrieved_proc->arrival_time, 0);
    EXPECT_EQ(retrieved_proc->burst_time, 10);
    EXPECT_EQ(retrieved_proc->priority, 1);
}

// 2. Every permitted transition
// Permitted:
// - New -> Ready
// - Ready -> Running
// - Running -> Ready
// - Running -> Waiting
// - Running -> Terminated
// - Waiting -> Ready
TEST(OScopeProcessManagerTest, ExecutesEveryPermittedTransition) {
    oscope::ProcessManager manager;

    // Transition 1: New -> Ready
    EXPECT_TRUE(manager.register_process({1, 0, 5, 0}));
    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::New);

    EXPECT_TRUE(manager.transition_to(1, oscope::ProcessState::Ready));
    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::Ready);

    // Transition 2: Ready -> Running
    EXPECT_TRUE(manager.transition_to(1, oscope::ProcessState::Running));
    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::Running);

    // Transition 3: Running -> Ready (Preemption)
    EXPECT_TRUE(manager.transition_to(1, oscope::ProcessState::Ready));
    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::Ready);

    // Transition 4: Ready -> Running again
    EXPECT_TRUE(manager.transition_to(1, oscope::ProcessState::Running));
    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::Running);

    // Transition 5: Running -> Waiting (I/O block)
    EXPECT_TRUE(manager.transition_to(1, oscope::ProcessState::Waiting));
    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::Waiting);

    // Transition 6: Waiting -> Ready (I/O completion)
    EXPECT_TRUE(manager.transition_to(1, oscope::ProcessState::Ready));
    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::Ready);

    // Transition 7: Ready -> Running
    EXPECT_TRUE(manager.transition_to(1, oscope::ProcessState::Running));
    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::Running);

    // Transition 8: Running -> Terminated
    EXPECT_TRUE(manager.transition_to(1, oscope::ProcessState::Terminated));
    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::Terminated);
}

// 3. Rejected transitions from New state
TEST(OScopeProcessManagerTest, RejectsIllegalTransitionsFromNew) {
    oscope::ProcessManager manager;
    manager.register_process({1, 0, 5, 0});

    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::New));
    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::Running));
    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::Waiting));
    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::Terminated));

    // State remains New
    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::New);
}

// 4. Rejected transitions from Ready state
TEST(OScopeProcessManagerTest, RejectsIllegalTransitionsFromReady) {
    oscope::ProcessManager manager;
    manager.register_process({1, 0, 5, 0});
    manager.transition_to(1, oscope::ProcessState::Ready);

    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::New));
    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::Ready));
    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::Waiting));
    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::Terminated));

    // State remains Ready
    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::Ready);
}

// 5. Rejected transitions from Running state
TEST(OScopeProcessManagerTest, RejectsIllegalTransitionsFromRunning) {
    oscope::ProcessManager manager;
    manager.register_process({1, 0, 5, 0});
    manager.transition_to(1, oscope::ProcessState::Ready);
    manager.transition_to(1, oscope::ProcessState::Running);

    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::New));
    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::Running));

    // State remains Running
    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::Running);
}

// 6. Rejected transitions from Waiting state
TEST(OScopeProcessManagerTest, RejectsIllegalTransitionsFromWaiting) {
    oscope::ProcessManager manager;
    manager.register_process({1, 0, 5, 0});
    manager.transition_to(1, oscope::ProcessState::Ready);
    manager.transition_to(1, oscope::ProcessState::Running);
    manager.transition_to(1, oscope::ProcessState::Waiting);

    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::New));
    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::Waiting));
    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::Running));
    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::Terminated));

    // State remains Waiting
    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::Waiting);
}

// 7. Rejected transitions out of Terminated state
TEST(OScopeProcessManagerTest, RejectsAllTransitionsOutOfTerminated) {
    oscope::ProcessManager manager;
    manager.register_process({1, 0, 5, 0});
    manager.transition_to(1, oscope::ProcessState::Ready);
    manager.transition_to(1, oscope::ProcessState::Running);
    manager.transition_to(1, oscope::ProcessState::Terminated);

    // State is Terminated
    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::Terminated);

    // Any transition out of Terminated must be rejected
    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::New));
    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::Ready));
    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::Running));
    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::Waiting));
    EXPECT_FALSE(manager.transition_to(1, oscope::ProcessState::Terminated));

    // Process remains registered and in Terminated state
    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::Terminated);
    EXPECT_EQ(manager.process_count(), 1);
    EXPECT_TRUE(manager.has_process(1));
}

// 8. State remains unchanged after rejected transitions
TEST(OScopeProcessManagerTest, StateRemainsUnchangedAfterRejectedTransition) {
    oscope::ProcessManager manager;
    manager.register_process({10, 2, 4, 1});

    // In New, attempt jump to Running
    EXPECT_FALSE(manager.transition_to(10, oscope::ProcessState::Running));
    EXPECT_EQ(manager.get_state(10), oscope::ProcessState::New);

    // Advance to Ready
    EXPECT_TRUE(manager.transition_to(10, oscope::ProcessState::Ready));

    // In Ready, attempt jump to Terminated
    EXPECT_FALSE(manager.transition_to(10, oscope::ProcessState::Terminated));
    EXPECT_EQ(manager.get_state(10), oscope::ProcessState::Ready);

    // Advance to Running
    EXPECT_TRUE(manager.transition_to(10, oscope::ProcessState::Running));

    // In Running, attempt jump to New
    EXPECT_FALSE(manager.transition_to(10, oscope::ProcessState::New));
    EXPECT_EQ(manager.get_state(10), oscope::ProcessState::Running);
}

// 9. Duplicate PIDs are rejected
TEST(OScopeProcessManagerTest, RejectsDuplicatePids) {
    oscope::ProcessManager manager;

    EXPECT_TRUE(manager.register_process({1, 0, 5, 0}));
    EXPECT_EQ(manager.process_count(), 1);

    // Duplicate registration attempt
    EXPECT_FALSE(manager.register_process({1, 2, 8, 3}));
    EXPECT_EQ(manager.process_count(), 1);

    // Verify original process attributes remain intact
    auto proc = manager.get_process(1);
    ASSERT_TRUE(proc.has_value());
    EXPECT_EQ(proc->arrival_time, 0);
    EXPECT_EQ(proc->burst_time, 5);
}

// 10. Unknown PIDs are rejected
TEST(OScopeProcessManagerTest, RejectsUnknownPids) {
    oscope::ProcessManager manager;
    manager.register_process({1, 0, 5, 0});

    EXPECT_FALSE(manager.has_process(999));
    EXPECT_EQ(manager.get_state(999), std::nullopt);
    EXPECT_EQ(manager.get_process(999), std::nullopt);
    EXPECT_FALSE(manager.transition_to(999, oscope::ProcessState::Ready));
}

// 11. Invalid process data: PID, arrival time, burst time
TEST(OScopeProcessManagerTest, RejectsInvalidProcessData) {
    oscope::ProcessManager manager;

    // PID must be positive (> 0)
    EXPECT_FALSE(manager.register_process({0, 0, 5, 0}));
    EXPECT_FALSE(manager.register_process({-1, 0, 5, 0}));
    EXPECT_FALSE(manager.register_process({-100, 0, 5, 0}));

    // Arrival time must be non-negative (>= 0)
    EXPECT_FALSE(manager.register_process({1, -1, 5, 0}));
    EXPECT_FALSE(manager.register_process({2, -10, 5, 0}));

    // Burst time must be positive (> 0)
    EXPECT_FALSE(manager.register_process({3, 0, 0, 0}));
    EXPECT_FALSE(manager.register_process({4, 0, -5, 0}));

    // None should have been registered
    EXPECT_EQ(manager.process_count(), 0);
    EXPECT_TRUE(manager.empty());

    // Valid process with boundary values (PID=1, arrival=0, burst=1) succeeds
    EXPECT_TRUE(manager.register_process({1, 0, 1, 0}));
    EXPECT_EQ(manager.process_count(), 1);
}

// 12. Process count, multiple processes, and state lookup
TEST(OScopeProcessManagerTest, TracksMultipleProcessesAndCountsCorrectly) {
    oscope::ProcessManager manager;

    EXPECT_EQ(manager.process_count(), 0);
    EXPECT_TRUE(manager.empty());

    EXPECT_TRUE(manager.register_process({1, 0, 4, 1}));
    EXPECT_TRUE(manager.register_process({2, 1, 3, 2}));
    EXPECT_TRUE(manager.register_process({3, 2, 2, 3}));

    EXPECT_EQ(manager.process_count(), 3);
    EXPECT_FALSE(manager.empty());

    // Transition P1: New -> Ready -> Running
    EXPECT_TRUE(manager.transition_to(1, oscope::ProcessState::Ready));
    EXPECT_TRUE(manager.transition_to(1, oscope::ProcessState::Running));

    // Transition P2: New -> Ready
    EXPECT_TRUE(manager.transition_to(2, oscope::ProcessState::Ready));

    // P3 stays in New

    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::Running);
    EXPECT_EQ(manager.get_state(2), oscope::ProcessState::Ready);
    EXPECT_EQ(manager.get_state(3), oscope::ProcessState::New);

    // Transition P1: Running -> Terminated
    EXPECT_TRUE(manager.transition_to(1, oscope::ProcessState::Terminated));

    // Terminated process is still registered and count remains 3
    EXPECT_EQ(manager.process_count(), 3);
    EXPECT_EQ(manager.get_state(1), oscope::ProcessState::Terminated);

    // Clear manager
    manager.clear();
    EXPECT_EQ(manager.process_count(), 0);
    EXPECT_TRUE(manager.empty());
    EXPECT_FALSE(manager.has_process(1));
}
