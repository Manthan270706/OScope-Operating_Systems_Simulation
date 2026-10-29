#include <gtest/gtest.h>
#include <unistd.h>

#include "oscope/monitoring/host_monitor.hpp"

using namespace oscope::monitoring;

TEST(HostMonitorTest, ReadsHostSnapshotOnLinuxEnvironment) {
    auto snapshot = HostMonitor::take_snapshot();

    EXPECT_EQ(snapshot.source, "real_linux_host");
    EXPECT_FALSE(snapshot.timestamp.empty());

    // In a real Linux / WSL environment, /proc files exist
    if (snapshot.success) {
        EXPECT_TRUE(snapshot.cpu.valid);
        EXPECT_GE(snapshot.cpu.total_cpu_usage_percent, 0.0);
        EXPECT_LE(snapshot.cpu.total_cpu_usage_percent, 100.0);

        EXPECT_TRUE(snapshot.memory.valid);
        EXPECT_GT(snapshot.memory.total_kb, 0u);
        EXPECT_GE(snapshot.memory.used_percent, 0.0);
        EXPECT_LE(snapshot.memory.used_percent, 100.0);

        EXPECT_TRUE(snapshot.self_process.valid);
        EXPECT_EQ(snapshot.self_process.pid, static_cast<int>(::getpid()));
        EXPECT_NE(snapshot.self_process.state, '?');
        EXPECT_GT(snapshot.self_process.vm_size_bytes, 0u);
    }
}

TEST(HostMonitorTest, HandlesNonExistentProcPathsSafely) {
    auto cpu = HostMonitor::read_cpu_observation("/nonexistent/proc/stat");
    EXPECT_FALSE(cpu.valid);

    auto mem = HostMonitor::read_memory_observation("/nonexistent/proc/meminfo");
    EXPECT_FALSE(mem.valid);

    auto proc = HostMonitor::read_process_observation(9999999, "/nonexistent/proc");
    EXPECT_FALSE(proc.valid);

    auto disks = HostMonitor::read_disk_observations("/nonexistent/proc/diskstats");
    EXPECT_TRUE(disks.empty());
}
