#include <gtest/gtest.h>

#include "oscope/deadlock/bankers_algorithm.hpp"
#include "oscope/deadlock/deadlock_detector.hpp"
#include "oscope/deadlock/deadlock_types.hpp"
#include "oscope/reporting/experiment_reporter.hpp"

namespace {

using namespace oscope::deadlock;

// Standard Silberschatz textbook Banker's algorithm benchmark state
DeadlockState create_textbook_benchmark_state() {
    DeadlockState state;
    state.num_processes = 5;
    state.num_resources = 3;
    state.available = {3, 3, 2};

    state.allocation = {
        {0, 1, 0}, // P0
        {2, 0, 0}, // P1
        {3, 0, 2}, // P2
        {2, 1, 1}, // P3
        {0, 0, 2}  // P4
    };

    state.max = {
        {7, 5, 3}, // P0
        {3, 2, 2}, // P1
        {9, 0, 2}, // P2
        {2, 2, 2}, // P3
        {4, 3, 3}  // P4
    };

    state.compute_need();
    return state;
}

// ============================================================================
// 1. Banker's Safety Algorithm Tests
// ============================================================================

TEST(BankersSafetyTest, CorrectlyIdentifiesSafeStateAndProducesSafeSequence) {
    DeadlockState state = create_textbook_benchmark_state();
    SafetyResult result = check_safety(state);

    EXPECT_TRUE(result.is_valid);
    EXPECT_TRUE(result.is_safe);
    ASSERT_EQ(result.safe_sequence.size(), 5u);

    // Textbook benchmark safe sequence with deterministic lowest-index preference: P1 -> P3 -> P0 -> P2 -> P4
    EXPECT_EQ(result.safe_sequence[0], 1);
    EXPECT_EQ(result.safe_sequence[1], 3);
    EXPECT_EQ(result.safe_sequence[2], 0);
    EXPECT_EQ(result.safe_sequence[3], 2);
    EXPECT_EQ(result.safe_sequence[4], 4);

    EXPECT_TRUE(result.blocked_processes.empty());
    EXPECT_NE(result.message.find("safe state"), std::string::npos);
}

TEST(BankersSafetyTest, CorrectlyIdentifiesUnsafeStateAndReportsBlockedProcesses) {
    DeadlockState state = create_textbook_benchmark_state();
    // Reduce available resources to 0 so no process can start
    state.available = {0, 0, 0};

    SafetyResult result = check_safety(state);

    EXPECT_TRUE(result.is_valid);
    EXPECT_FALSE(result.is_safe);
    EXPECT_EQ(result.safe_sequence.size(), 0u);
    EXPECT_EQ(result.blocked_processes.size(), 5u);
    EXPECT_NE(result.message.find("unsafe state"), std::string::npos);
}

TEST(BankersSafetyTest, RejectsInvalidStateWithMismatchedDimensionsOrNegativeValues) {
    // Negative available
    DeadlockState neg_avail = create_textbook_benchmark_state();
    neg_avail.available[1] = -1;
    EXPECT_FALSE(check_safety(neg_avail).is_valid);

    // Allocation exceeds Max
    DeadlockState invalid_alloc = create_textbook_benchmark_state();
    invalid_alloc.allocation[0][0] = 10; // Max is 7
    EXPECT_FALSE(check_safety(invalid_alloc).is_valid);

    // Wrong process count
    DeadlockState wrong_p = create_textbook_benchmark_state();
    wrong_p.num_processes = 0;
    EXPECT_FALSE(check_safety(wrong_p).is_valid);

    // Wrong matrix dimensions
    DeadlockState wrong_dim = create_textbook_benchmark_state();
    wrong_dim.allocation.pop_back();
    EXPECT_FALSE(check_safety(wrong_dim).is_valid);
}

// ============================================================================
// 2. Resource-Request Algorithm Tests
// ============================================================================

TEST(BankersRequestTest, GrantsEligibleRequestAndLeavesSystemInSafeState) {
    DeadlockState state = create_textbook_benchmark_state();

    // P1 requests [1, 0, 2]
    std::vector<int> req = {1, 0, 2};
    ResourceRequestResult result = request_resources(state, 1, req);

    EXPECT_EQ(result.status, RequestStatus::Granted);
    EXPECT_TRUE(result.granted);
    EXPECT_EQ(result.process_id, 1);
    ASSERT_EQ(result.safe_sequence.size(), 5u);

    // Verify resulting state reflects committed allocation
    EXPECT_EQ(result.resulting_state.available[0], 2);
    EXPECT_EQ(result.resulting_state.available[1], 3);
    EXPECT_EQ(result.resulting_state.available[2], 0);

    EXPECT_EQ(result.resulting_state.allocation[1][0], 3);
    EXPECT_EQ(result.resulting_state.allocation[1][1], 0);
    EXPECT_EQ(result.resulting_state.allocation[1][2], 2);

    EXPECT_EQ(result.resulting_state.need[1][0], 0);
    EXPECT_EQ(result.resulting_state.need[1][1], 2);
    EXPECT_EQ(result.resulting_state.need[1][2], 0);
}

TEST(BankersRequestTest, RejectsRequestExceedingMaximumNeedWithoutStateCorruption) {
    DeadlockState state = create_textbook_benchmark_state();

    // P1 need is [1, 2, 2]; request [2, 0, 0] exceeds need
    std::vector<int> req = {2, 0, 0};
    ResourceRequestResult result = request_resources(state, 1, req);

    EXPECT_EQ(result.status, RequestStatus::DeniedExceedsNeed);
    EXPECT_FALSE(result.granted);
    EXPECT_NE(result.message.find("exceeds its maximum declared need"), std::string::npos);

    // Original state must remain untouched
    EXPECT_EQ(state.available[0], 3);
    EXPECT_EQ(state.allocation[1][0], 2);
    EXPECT_EQ(result.resulting_state.available[0], 3);
}

TEST(BankersRequestTest, RejectsRequestExceedingAvailableWithoutStateCorruption) {
    DeadlockState state = create_textbook_benchmark_state();

    // P0 requests [4, 4, 3], but Available is only [3, 3, 2]
    std::vector<int> req = {4, 4, 3};
    ResourceRequestResult result = request_resources(state, 0, req);

    EXPECT_EQ(result.status, RequestStatus::DeniedExceedsAvailable);
    EXPECT_FALSE(result.granted);
    EXPECT_NE(result.message.find("must wait"), std::string::npos);

    // Original state untouched
    EXPECT_EQ(state.available, (std::vector<int>{3, 3, 2}));
}

TEST(BankersRequestTest, DeniesRequestThatWouldLeadToUnsafeStateWithoutStateCorruption) {
    DeadlockState state = create_textbook_benchmark_state();

    // From benchmark state, P4 (need [4, 3, 1]) requesting [3, 3, 0] leaves Available [0, 0, 2],
    // which leaves the system in an unsafe state (no process can satisfy its remaining need).
    std::vector<int> req = {3, 3, 0};
    ResourceRequestResult result = request_resources(state, 4, req);

    EXPECT_EQ(result.status, RequestStatus::DeniedUnsafeState);
    EXPECT_FALSE(result.granted);
    EXPECT_NE(result.message.find("unsafe state"), std::string::npos);

    // Verify rollback: state remains unchanged
    EXPECT_EQ(result.resulting_state.available, (std::vector<int>{3, 3, 2}));
    EXPECT_EQ(result.resulting_state.allocation[4], (std::vector<int>{0, 0, 2}));
}

TEST(BankersRequestTest, HandlesZeroResourceRequestGracefully) {
    DeadlockState state = create_textbook_benchmark_state();
    std::vector<int> zero_req = {0, 0, 0};

    ResourceRequestResult result = request_resources(state, 2, zero_req);

    EXPECT_EQ(result.status, RequestStatus::Granted);
    EXPECT_TRUE(result.granted);
    EXPECT_EQ(result.resulting_state.available, state.available);
}

TEST(BankersRequestTest, RejectsInvalidProcessIdOrNegativeRequest) {
    DeadlockState state = create_textbook_benchmark_state();

    // Invalid process ID
    EXPECT_EQ(request_resources(state, -1, {1, 0, 0}).status, RequestStatus::InvalidRequest);
    EXPECT_EQ(request_resources(state, 99, {1, 0, 0}).status, RequestStatus::InvalidRequest);

    // Negative request quantity
    EXPECT_EQ(request_resources(state, 0, {-1, 0, 0}).status, RequestStatus::InvalidRequest);

    // Wrong vector size
    EXPECT_EQ(request_resources(state, 0, {1, 0}).status, RequestStatus::InvalidRequest);
}

// ============================================================================
// 3. Deadlock Detection Algorithm Tests
// ============================================================================

TEST(DeadlockDetectionTest, DetectsDeadlockAndAccuratelyReportsDeadlockedProcesses) {
    int num_p = 5;
    int num_r = 3;
    std::vector<int> avail = {0, 0, 0};

    std::vector<std::vector<int>> alloc = {
        {0, 1, 0}, // P0
        {2, 0, 0}, // P1
        {3, 0, 3}, // P2
        {2, 1, 1}, // P3
        {0, 0, 2}  // P4
    };

    std::vector<std::vector<int>> req = {
        {0, 0, 0}, // P0 needs nothing
        {2, 0, 2}, // P1 needs resources held by P2 & P4
        {0, 0, 0}, // P2 needs nothing
        {1, 0, 0}, // P3
        {0, 0, 2}  // P4
    };

    // Make P2 request resources that cannot be satisfied
    req[2] = {0, 0, 1};

    DetectionResult result = detect_deadlock(num_p, num_r, avail, alloc, req);

    EXPECT_TRUE(result.is_valid);
    // P0 finishes (req=0), releasing {0, 1, 0}. Work={0, 1, 0}.
    // No other process can finish -> Deadlock detected!
    EXPECT_TRUE(result.is_deadlocked);
    EXPECT_FALSE(result.deadlocked_processes.empty());
    EXPECT_NE(result.message.find("Deadlock detected"), std::string::npos);
}

TEST(DeadlockDetectionTest, AccuratelyReportsNoDeadlockWhenAllProcessesCanFinish) {
    int num_p = 3;
    int num_r = 2;
    std::vector<int> avail = {1, 1};

    std::vector<std::vector<int>> alloc = {
        {1, 0}, // P0
        {0, 1}, // P1
        {1, 1}  // P2
    };

    std::vector<std::vector<int>> req = {
        {0, 1}, // P0 can finish once P1 finishes
        {1, 0}, // P1 can finish immediately with avail {1, 1}
        {0, 0}  // P2 needs nothing
    };

    DetectionResult result = detect_deadlock(num_p, num_r, avail, alloc, req);

    EXPECT_TRUE(result.is_valid);
    EXPECT_FALSE(result.is_deadlocked);
    EXPECT_TRUE(result.deadlocked_processes.empty());
    EXPECT_EQ(result.finished_processes.size(), 3u);
    EXPECT_NE(result.message.find("No deadlock detected"), std::string::npos);
}

TEST(DeadlockDetectionTest, HandlesProcessesWithNoAllocationsGracefully) {
    int num_p = 3;
    int num_r = 2;
    std::vector<int> avail = {0, 0};

    std::vector<std::vector<int>> alloc = {
        {0, 0}, // P0 holds no resources
        {1, 0}, // P1
        {0, 1}  // P2
    };

    std::vector<std::vector<int>> req = {
        {1, 1}, // P0 requests resources
        {0, 1}, // P1 requests resource held by P2
        {1, 0}  // P2 requests resource held by P1
    };

    DetectionResult result = detect_deadlock(num_p, num_r, avail, alloc, req);

    EXPECT_TRUE(result.is_valid);
    // P0 holds no resources, so it cannot be part of the deadlock cycle
    EXPECT_TRUE(result.is_deadlocked);
    // Deadlocked processes are P1 and P2
    EXPECT_EQ(result.deadlocked_processes.size(), 2u);
    EXPECT_EQ(result.deadlocked_processes[0], 1);
    EXPECT_EQ(result.deadlocked_processes[1], 2);
}

TEST(DeadlockDetectionTest, RejectsInvalidDetectionInputs) {
    EXPECT_FALSE(detect_deadlock(0, 2, {1, 1}, {}, {}).is_valid);
    EXPECT_FALSE(detect_deadlock(2, 0, {}, {}, {}).is_valid);
    EXPECT_FALSE(detect_deadlock(2, 2, {-1, 1}, {{0, 0}, {0, 0}}, {{0, 0}, {0, 0}}).is_valid);
}

// ============================================================================
// 4. JSON Serialization Tests
// ============================================================================

TEST(DeadlockReportingTest, SerializesSafetyResultCorrectly) {
    DeadlockState state = create_textbook_benchmark_state();
    SafetyResult result = check_safety(state);

    std::string json_str = oscope::reporting::serialize_result(result, state, false);
    EXPECT_NE(json_str.find("\"category\": \"deadlock_management\""), std::string::npos);
    EXPECT_NE(json_str.find("\"experiment\": \"bankers_safety\""), std::string::npos);
    EXPECT_NE(json_str.find("\"status\": \"success\""), std::string::npos);
    EXPECT_NE(json_str.find("\"safe_sequence\": [1, 3, 0, 2, 4]"), std::string::npos);
}

TEST(DeadlockReportingTest, SerializesResourceRequestResultCorrectly) {
    DeadlockState state = create_textbook_benchmark_state();
    ResourceRequestResult result = request_resources(state, 1, {1, 0, 2});

    std::string json_str = oscope::reporting::serialize_result(result, false);
    EXPECT_NE(json_str.find("\"category\": \"deadlock_management\""), std::string::npos);
    EXPECT_NE(json_str.find("\"experiment\": \"resource_request\""), std::string::npos);
    EXPECT_NE(json_str.find("\"granted\": true"), std::string::npos);
    EXPECT_NE(json_str.find("\"process_id\": 1"), std::string::npos);
}

TEST(DeadlockReportingTest, SerializesDetectionResultCorrectly) {
    DetectionResult result = detect_deadlock(2, 1, {0}, {{1}, {1}}, {{1}, {1}});
    std::string json_str = oscope::reporting::serialize_result(result, false);

    EXPECT_NE(json_str.find("\"category\": \"deadlock_management\""), std::string::npos);
    EXPECT_NE(json_str.find("\"experiment\": \"deadlock_detection\""), std::string::npos);
    EXPECT_NE(json_str.find("\"is_deadlocked\": true"), std::string::npos);
    EXPECT_NE(json_str.find("\"deadlocked_processes\": [0, 1]"), std::string::npos);
}

} // namespace
