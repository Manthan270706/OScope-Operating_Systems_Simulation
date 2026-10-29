#ifndef OSCOPE_MONITORING_HOST_MONITOR_HPP
#define OSCOPE_MONITORING_HOST_MONITOR_HPP

#include <cstdint>
#include <string>
#include <vector>

namespace oscope::monitoring {

struct HostCpuObservation {
    double user_percent{0.0};
    double system_percent{0.0};
    double idle_percent{0.0};
    double total_cpu_usage_percent{0.0};
    std::string unit{"% (real Linux host)"};
    bool valid{false};
};

struct HostMemoryObservation {
    uint64_t total_kb{0};
    uint64_t free_kb{0};
    uint64_t available_kb{0};
    uint64_t used_kb{0};
    double used_percent{0.0};
    std::string unit{"kB (real Linux host)"};
    bool valid{false};
};

struct ProcessObservation {
    int pid{0};
    int ppid{0};
    std::string comm;
    char state{'?'};
    uint64_t utime_ticks{0};
    uint64_t stime_ticks{0};
    uint64_t vm_size_bytes{0};
    uint64_t rss_pages{0};
    uint64_t rss_kb{0};
    bool valid{false};
};

struct HostDiskObservation {
    std::string device_name;
    uint64_t reads_completed{0};
    uint64_t sectors_read{0};
    uint64_t writes_completed{0};
    uint64_t sectors_written{0};
    bool valid{false};
};

struct HostSystemObservation {
    double uptime_seconds{0.0};
    double load_1min{0.0};
    double load_5min{0.0};
    double load_15min{0.0};
    int total_processes{0};
    int running_processes{0};
    uint64_t disk_total_bytes{0};
    uint64_t disk_used_bytes{0};
    uint64_t disk_available_bytes{0};
    double disk_used_percent{0.0};
    std::string root_mount{"/"};
    bool valid{false};
};

struct HostMonitoringSnapshot {
    std::string source{"real_linux_host"};
    HostCpuObservation cpu;
    HostMemoryObservation memory;
    ProcessObservation self_process;
    std::vector<HostDiskObservation> disks;
    HostSystemObservation system;
    std::string timestamp;
    bool success{false};
    std::string error_message;
};

class HostMonitor {
public:
    static HostCpuObservation read_cpu_observation(const std::string& proc_stat_path = "/proc/stat");
    static HostMemoryObservation read_memory_observation(const std::string& proc_meminfo_path = "/proc/meminfo");
    static ProcessObservation read_process_observation(int pid = 0, const std::string& proc_dir = "/proc");
    static std::vector<HostDiskObservation> read_disk_observations(const std::string& proc_diskstats_path = "/proc/diskstats");
    static HostSystemObservation read_system_observation(const std::string& root_mount = "/",
                                                        const std::string& proc_uptime_path = "/proc/uptime",
                                                        const std::string& proc_loadavg_path = "/proc/loadavg");

    /**
     * @brief Takes a complete snapshot of host CPU, memory, self-process, and disk I/O.
     */
    static HostMonitoringSnapshot take_snapshot();
};

} // namespace oscope::monitoring

#endif // OSCOPE_MONITORING_HOST_MONITOR_HPP
