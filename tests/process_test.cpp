#include <gtest/gtest.h>

#include "oscope/process.hpp"

TEST(OScopeProcessTest, CreatesProcess) {
    oscope::Process process{1, 0, 5, 2};

    EXPECT_EQ(process.pid, 1);
    EXPECT_EQ(process.arrival_time, 0);
    EXPECT_EQ(process.burst_time, 5);
    EXPECT_EQ(process.priority, 2);
}
