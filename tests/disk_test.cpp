#include <gtest/gtest.h>

#include "oscope/disk/disk_scheduler.hpp"
#include "oscope/disk/disk_types.hpp"
#include "oscope/reporting/experiment_reporter.hpp"

namespace {

using namespace oscope::disk;

const std::vector<int> kTextbookRequests = {98, 183, 37, 122, 14, 124, 65, 67};

DiskConfig create_standard_config(Direction dir = Direction::Increasing) {
    DiskConfig config;
    config.min_cylinder = 0;
    config.max_cylinder = 199;
    config.initial_head = 53;
    config.direction = dir;
    return config;
}

// ============================================================================
// 1. FCFS Disk Scheduling Tests
// ============================================================================

TEST(DiskSchedulingTest, FCFSServicesInArrivalOrderWithExactMovement) {
    DiskConfig config = create_standard_config();
    DiskSchedulingResult res = schedule_fcfs(kTextbookRequests, config);

    EXPECT_TRUE(res.success);
    EXPECT_EQ(res.serviced_requests, kTextbookRequests);

    // Textbook: Total movement for FCFS = 640 cylinders, average = 80.0
    EXPECT_EQ(res.total_head_movement, 640);
    EXPECT_DOUBLE_EQ(res.average_head_movement, 80.0);
    EXPECT_EQ(res.initial_head_position, 53);
    EXPECT_EQ(res.final_head_position, 67);
}

// ============================================================================
// 2. SSTF Disk Scheduling Tests
// ============================================================================

TEST(DiskSchedulingTest, SSTFChoosesClosestCylinderWithExactMovement) {
    DiskConfig config = create_standard_config();
    DiskSchedulingResult res = schedule_sstf(kTextbookRequests, config);

    EXPECT_TRUE(res.success);
    // Textbook SSTF sequence: 65, 67, 37, 14, 98, 122, 124, 183
    std::vector<int> expected_order = {65, 67, 37, 14, 98, 122, 124, 183};
    EXPECT_EQ(res.serviced_requests, expected_order);

    // Textbook: Total movement for SSTF = 236 cylinders
    EXPECT_EQ(res.total_head_movement, 236);
    EXPECT_DOUBLE_EQ(res.average_head_movement, 236.0 / 8.0);
    EXPECT_EQ(res.final_head_position, 183);
}

// ============================================================================
// 3. SCAN (Elevator) Tests
// ============================================================================

TEST(DiskSchedulingTest, SCANMovesToDiskBoundaryAndReversesAccurately) {
    DiskConfig config = create_standard_config(Direction::Increasing);
    DiskSchedulingResult res = schedule_scan(kTextbookRequests, config);

    EXPECT_TRUE(res.success);
    // Serviced order: 65, 67, 98, 122, 124, 183, then 37, 14
    std::vector<int> expected_order = {65, 67, 98, 122, 124, 183, 37, 14};
    EXPECT_EQ(res.serviced_requests, expected_order);

    // Full head path MUST include max_cylinder (199), and end at min_cylinder (0)
    std::vector<int> expected_path = {53, 65, 67, 98, 122, 124, 183, 199, 37, 14, 0};
    EXPECT_EQ(res.head_path, expected_path);

    // Explicit path arithmetic:
    // (199 - 53) + (199 - 0) = 146 + 199 = 345 cylinders
    EXPECT_EQ(res.total_head_movement, 345);
    EXPECT_EQ(res.final_head_position, 0);
}

TEST(DiskSchedulingTest, SCANDownwardReachesMinBoundaryAndReverses) {
    DiskConfig config = create_standard_config(Direction::Decreasing);
    DiskSchedulingResult res = schedule_scan(kTextbookRequests, config);

    EXPECT_TRUE(res.success);
    // Serviced order: 37, 14, then 65, 67, 98, 122, 124, 183
    std::vector<int> expected_order = {37, 14, 65, 67, 98, 122, 124, 183};
    EXPECT_EQ(res.serviced_requests, expected_order);

    // Full path reaches min_cylinder (0) and completes travel to max_cylinder (199)
    std::vector<int> expected_path = {53, 37, 14, 0, 65, 67, 98, 122, 124, 183, 199};
    EXPECT_EQ(res.head_path, expected_path);

    // Explicit path arithmetic:
    // (53 - 0) + (199 - 0) = 53 + 199 = 252? Wait: |53 - 0| + |199 - 0| = 53 + 199 = 252 cylinders
    EXPECT_EQ(res.total_head_movement, 252);
    EXPECT_EQ(res.final_head_position, 199);
}

// ============================================================================
// 4. C-SCAN Tests
// ============================================================================

TEST(DiskSchedulingTest, CSCANWrapsAroundToOppositeBoundaryAccurately) {
    DiskConfig config = create_standard_config(Direction::Increasing);
    DiskSchedulingResult res = schedule_cscan(kTextbookRequests, config);

    EXPECT_TRUE(res.success);
    // Serviced order: 65, 67, 98, 122, 124, 183, then 14, 37
    std::vector<int> expected_order = {65, 67, 98, 122, 124, 183, 14, 37};
    EXPECT_EQ(res.serviced_requests, expected_order);

    // Full head path visits 199, then jumps to 0
    std::vector<int> expected_path = {53, 65, 67, 98, 122, 124, 183, 199, 0, 14, 37};
    EXPECT_EQ(res.head_path, expected_path);

    // Circular jump: 199 -> 0 = 199
    EXPECT_EQ(res.wraparound_movement, 199);
    // Textbook: (199 - 53) + (199 - 0) + (37 - 0) = 146 + 199 + 37 = 382 cylinders
    EXPECT_EQ(res.total_head_movement, 382);
    EXPECT_EQ(res.final_head_position, 37);
}

// ============================================================================
// 5. LOOK Tests
// ============================================================================

TEST(DiskSchedulingTest, LOOKReversesWithoutTravelingToDiskBoundary) {
    DiskConfig config = create_standard_config(Direction::Increasing);
    DiskSchedulingResult res = schedule_look(kTextbookRequests, config);

    EXPECT_TRUE(res.success);
    // Serviced order: 65, 67, 98, 122, 124, 183, then 37, 14
    std::vector<int> expected_order = {65, 67, 98, 122, 124, 183, 37, 14};
    EXPECT_EQ(res.serviced_requests, expected_order);

    // Head path stops at 183 and does NOT include 199
    std::vector<int> expected_path = {53, 65, 67, 98, 122, 124, 183, 37, 14};
    EXPECT_EQ(res.head_path, expected_path);

    // Textbook LOOK movement: (183 - 53) + (183 - 14) = 130 + 169 = 299 cylinders
    EXPECT_EQ(res.total_head_movement, 299);
    EXPECT_EQ(res.final_head_position, 14);
}

// ============================================================================
// 6. C-LOOK Tests
// ============================================================================

TEST(DiskSchedulingTest, CLOOKJumpsDirectlyToSmallestRequestWithoutVisitingBoundaries) {
    DiskConfig config = create_standard_config(Direction::Increasing);
    DiskSchedulingResult res = schedule_clook(kTextbookRequests, config);

    EXPECT_TRUE(res.success);
    // Serviced order: 65, 67, 98, 122, 124, 183, then 14, 37
    std::vector<int> expected_order = {65, 67, 98, 122, 124, 183, 14, 37};
    EXPECT_EQ(res.serviced_requests, expected_order);

    // Head path jumps directly from 183 to 14 (no 199 or 0!)
    std::vector<int> expected_path = {53, 65, 67, 98, 122, 124, 183, 14, 37};
    EXPECT_EQ(res.head_path, expected_path);

    // Jump from 183 to 14: 169
    EXPECT_EQ(res.wraparound_movement, 169);
    // Textbook C-LOOK movement: (183 - 53) + (183 - 14) + (37 - 14) = 130 + 169 + 23 = 322 cylinders
    EXPECT_EQ(res.total_head_movement, 322);
    EXPECT_EQ(res.final_head_position, 37);
}

// ============================================================================
// 7. Edge Cases & Validation Tests
// ============================================================================

TEST(DiskSchedulingTest, HandlesEmptyRequestWorkloadSafely) {
    DiskConfig config = create_standard_config();
    std::vector<int> empty_requests;

    for (DiskAlgorithm algo : {DiskAlgorithm::FCFS, DiskAlgorithm::SSTF, DiskAlgorithm::SCAN,
                               DiskAlgorithm::CSCAN, DiskAlgorithm::LOOK, DiskAlgorithm::CLOOK, DiskAlgorithm::LIFO}) {
        DiskSchedulingResult res = schedule_disk(algo, empty_requests, config);
        EXPECT_TRUE(res.success);
        EXPECT_TRUE(res.serviced_requests.empty());
        EXPECT_EQ(res.total_head_movement, 0);
        EXPECT_DOUBLE_EQ(res.average_head_movement, 0.0);
        EXPECT_EQ(res.final_head_position, config.initial_head);
    }
}

TEST(DiskSchedulingTest, HandlesSingleRequestAndRequestsAtHeadSafely) {
    DiskConfig config = create_standard_config();

    // Single request away from head
    DiskSchedulingResult res1 = schedule_fcfs({100}, config);
    EXPECT_EQ(res1.total_head_movement, 47); // |100 - 53|
    EXPECT_EQ(res1.final_head_position, 100);

    // Request exactly at current head
    DiskSchedulingResult res2 = schedule_fcfs({53}, config);
    EXPECT_EQ(res2.total_head_movement, 0);
    EXPECT_EQ(res2.final_head_position, 53);
}

TEST(DiskSchedulingTest, RejectsOutOfRangeRequestsAndInvalidConfig) {
    DiskConfig config = create_standard_config();

    // Request above max_cylinder
    EXPECT_FALSE(schedule_fcfs({200}, config).success);

    // Negative request
    EXPECT_FALSE(schedule_fcfs({-5}, config).success);

    // Initial head out of range
    DiskConfig bad_head = config;
    bad_head.initial_head = 500;
    EXPECT_FALSE(schedule_fcfs({100}, bad_head).success);

    // Inverted cylinder bounds
    DiskConfig bad_range = config;
    bad_range.min_cylinder = 200;
    bad_range.max_cylinder = 100;
    EXPECT_FALSE(schedule_fcfs({150}, bad_range).success);
}

TEST(DiskSchedulingTest, HandlesDuplicateRequestsAndRequestsAtHeadConsistently) {
    DiskConfig config = create_standard_config(Direction::Increasing);
    // Workload with duplicates and requests at head: {53, 65, 53, 98, 65}
    std::vector<int> dups = {53, 65, 53, 98, 65};

    for (DiskAlgorithm algo : {DiskAlgorithm::FCFS, DiskAlgorithm::SSTF, DiskAlgorithm::SCAN,
                               DiskAlgorithm::CSCAN, DiskAlgorithm::LOOK, DiskAlgorithm::CLOOK, DiskAlgorithm::LIFO}) {
        DiskSchedulingResult res = schedule_disk(algo, dups, config);
        EXPECT_TRUE(res.success);
        EXPECT_EQ(res.serviced_requests.size(), 5u);

        // Verify total movement equals sum of absolute differences in recorded head path
        int64_t manual_sum = 0;
        for (size_t i = 1; i < res.head_path.size(); ++i) {
            manual_sum += std::abs(res.head_path[i] - res.head_path[i - 1]);
        }
        EXPECT_EQ(res.total_head_movement, manual_sum);
        EXPECT_DOUBLE_EQ(res.average_head_movement, static_cast<double>(manual_sum) / 5.0);
    }
}

TEST(DiskSchedulingTest, HandlesRequestsAtMinAndMaxCylinderBoundaries) {
    DiskConfig config = create_standard_config(Direction::Increasing);
    std::vector<int> boundary_reqs = {0, 199};

    // LOOK should reach 199, then reverse to 0 without extra boundary travel
    DiskSchedulingResult look_res = schedule_look(boundary_reqs, config);
    EXPECT_TRUE(look_res.success);
    std::vector<int> expected_look_path = {53, 199, 0};
    EXPECT_EQ(look_res.head_path, expected_look_path);
    EXPECT_EQ(look_res.total_head_movement, (199 - 53) + (199 - 0)); // 146 + 199 = 345

    // C-LOOK jumps from 199 to 0: total movement is |199-53| + |199-0| = 146 + 199 = 345
    DiskSchedulingResult clook_res = schedule_clook(boundary_reqs, config);
    EXPECT_TRUE(clook_res.success);
    EXPECT_EQ(clook_res.total_head_movement, 345);
}

TEST(DiskSchedulingTest, DownwardDirectionBenchmarkVerifiesAllAlgorithms) {
    DiskConfig config = create_standard_config(Direction::Decreasing);

    // LOOK Downward: Reverses at lowest request (14) directly to highest (183) without hitting 0 or 199
    // Path: 53 -> 37 -> 14 -> 65 -> 67 -> 98 -> 122 -> 124 -> 183
    // Movement: (53 - 14) + (183 - 14) = 39 + 169 = 208 cylinders
    DiskSchedulingResult look_down = schedule_look(kTextbookRequests, config);
    EXPECT_TRUE(look_down.success);
    std::vector<int> expected_look_path = {53, 37, 14, 65, 67, 98, 122, 124, 183};
    EXPECT_EQ(look_down.head_path, expected_look_path);
    EXPECT_EQ(look_down.total_head_movement, 208);

    // C-LOOK Downward: Head moves down servicing {37, 14}, jumps to highest {183}, and moves down servicing {124, 122, 98, 67, 65}
    // Path: 53 -> 37 -> 14 -> 183 -> 124 -> 122 -> 98 -> 67 -> 65
    // Movement: (53 - 14) + (183 - 14) + (183 - 65) = 39 + 169 + 118 = 326 cylinders
    DiskSchedulingResult clook_down = schedule_clook(kTextbookRequests, config);
    EXPECT_TRUE(clook_down.success);
    std::vector<int> expected_clook_path = {53, 37, 14, 183, 124, 122, 98, 67, 65};
    EXPECT_EQ(clook_down.head_path, expected_clook_path);
    EXPECT_EQ(clook_down.total_head_movement, 326);

    // C-SCAN Downward: Head moves down servicing {37, 14}, visits boundary 0, jumps to 199, moves down servicing {183, 124, 122, 98, 67, 65}
    // Path: 53 -> 37 -> 14 -> 0 -> 199 -> 183 -> 124 -> 122 -> 98 -> 67 -> 65
    // Movement: (53 - 0) + (199 - 0) + (199 - 65) = 53 + 199 + 134 = 386 cylinders
    DiskSchedulingResult cscan_down = schedule_cscan(kTextbookRequests, config);
    EXPECT_TRUE(cscan_down.success);
    std::vector<int> expected_cscan_path = {53, 37, 14, 0, 199, 183, 124, 122, 98, 67, 65};
    EXPECT_EQ(cscan_down.head_path, expected_cscan_path);
    EXPECT_EQ(cscan_down.total_head_movement, 386);
}

TEST(DiskSchedulingTest, ComparesAllAlgorithmsWithoutMutatingInput) {
    DiskConfig config = create_standard_config();
    std::vector<int> input_copy = kTextbookRequests;

    DiskComparisonResult comparison = compare_all_disk(input_copy, config);

    // Verify input vector was not mutated
    EXPECT_EQ(input_copy, kTextbookRequests);
    EXPECT_EQ(comparison.results.size(), 7u);

    // Check algorithm names and metrics in comparison
    EXPECT_EQ(comparison.results[0].algorithm, DiskAlgorithm::FCFS);
    EXPECT_EQ(comparison.results[0].total_head_movement, 640);

    EXPECT_EQ(comparison.results[1].algorithm, DiskAlgorithm::SSTF);
    EXPECT_EQ(comparison.results[1].total_head_movement, 236);

    EXPECT_EQ(comparison.results[2].algorithm, DiskAlgorithm::SCAN);
    EXPECT_EQ(comparison.results[2].total_head_movement, 345);

    EXPECT_EQ(comparison.results[3].algorithm, DiskAlgorithm::CSCAN);
    EXPECT_EQ(comparison.results[3].total_head_movement, 382);

    EXPECT_EQ(comparison.results[4].algorithm, DiskAlgorithm::LOOK);
    EXPECT_EQ(comparison.results[4].total_head_movement, 299);

    EXPECT_EQ(comparison.results[5].algorithm, DiskAlgorithm::CLOOK);
    EXPECT_EQ(comparison.results[5].total_head_movement, 322);

    EXPECT_EQ(comparison.results[6].algorithm, DiskAlgorithm::LIFO);
    EXPECT_EQ(comparison.results[6].total_head_movement, 609);
}

// ============================================================================
// 7. LIFO Disk Scheduling Tests
// ============================================================================

TEST(DiskSchedulingTest, LIFOServicesInReverseArrivalOrderWithExactMovement) {
    DiskConfig config = create_standard_config();
    DiskSchedulingResult res = schedule_lifo(kTextbookRequests, config);

    EXPECT_TRUE(res.success);
    // Reverse arrival order: 67, 65, 124, 14, 122, 37, 183, 98
    std::vector<int> expected_order = {67, 65, 124, 14, 122, 37, 183, 98};
    EXPECT_EQ(res.serviced_requests, expected_order);

    // Path: 53 -> 67 -> 65 -> 124 -> 14 -> 122 -> 37 -> 183 -> 98
    // Total movement: |67-53| + |65-67| + |124-65| + |14-124| + |122-14| + |37-122| + |183-37| + |98-183|
    //               = 14 + 2 + 59 + 110 + 108 + 85 + 146 + 85 = 609 cylinders
    EXPECT_EQ(res.total_head_movement, 609);
    EXPECT_DOUBLE_EQ(res.average_head_movement, 609.0 / 8.0);
    EXPECT_EQ(res.initial_head_position, 53);
    EXPECT_EQ(res.final_head_position, 98);
}

// ============================================================================
// 8. JSON Serialization Tests
// ============================================================================

TEST(DiskReportingTest, SerializesDiskResultCorrectly) {
    DiskConfig config = create_standard_config();
    DiskSchedulingResult res = schedule_fcfs(kTextbookRequests, config);

    std::string json_str = oscope::reporting::serialize_result(res, false);
    EXPECT_NE(json_str.find("\"category\": \"disk_scheduling\""), std::string::npos);
    EXPECT_NE(json_str.find("\"experiment\": \"disk_scheduling\""), std::string::npos);
    EXPECT_NE(json_str.find("\"total_head_movement\": 640"), std::string::npos);
    EXPECT_NE(json_str.find("\"final_head_position\": 67"), std::string::npos);
}

TEST(DiskReportingTest, SerializesDiskComparisonCorrectly) {
    DiskConfig config = create_standard_config();
    DiskComparisonResult comp = compare_all_disk(kTextbookRequests, config);

    std::string json_str = oscope::reporting::serialize_result(comp, false);
    EXPECT_NE(json_str.find("\"category\": \"disk_scheduling\""), std::string::npos);
    EXPECT_NE(json_str.find("\"experiment\": \"disk_comparison\""), std::string::npos);
    EXPECT_NE(json_str.find("\"algorithms\": ["), std::string::npos);
    EXPECT_NE(json_str.find("First-Come, First-Served (FCFS)"), std::string::npos);
}

} // namespace
