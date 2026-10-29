#include "oscope/monitoring/host_monitor.hpp"

#include <chrono>
#include <ctime>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <unistd.h>
#if !defined(_WIN32)
#include <sys/statvfs.h>
#endif

namespace oscope::monitoring {

namespace {

std::string get_current_iso_timestamp() {
    auto now = std::chrono::system_clock::now();
    std::time_t tt = std::chrono::system_clock::to_time_t(now);
    std::tm tm_buf{};
#if defined(_WIN32)
    localtime_s(&tm_buf, &tt);
#else
    localtime_r(&tt, &tm_buf);
#endif
    std::ostringstream ss;
    ss << std::put_time(&tm_buf, "%Y-%m-%d %H:%M:%S");
    return ss.str();
}

} // namespace

HostCpuObservation HostMonitor::read_cpu_observation(const std::string& proc_stat_path) {
    HostCpuObservation obs;
    std::ifstream file(proc_stat_path);
    if (!file.is_open()) {
        obs.valid = false;
        return obs;
    }

    std::string line;
    if (std::getline(file, line)) {
        std::istringstream ss(line);
        std::string cpu_label;
        uint64_t user = 0, nice = 0, system = 0, idle = 0, iowait = 0, irq = 0, softirq = 0, steal = 0;
        if (ss >> cpu_label && cpu_label == "cpu") {
            ss >> user >> nice >> system >> idle >> iowait >> irq >> softirq >> steal;
            uint64_t total = user + nice + system + idle + iowait + irq + softirq + steal;
            uint64_t total_idle = idle + iowait;
            uint64_t active = (total >= total_idle) ? (total - total_idle) : 0;

            if (total > 0) {
                obs.user_percent = (static_cast<double>(user) / static_cast<double>(total)) * 100.0;
                obs.system_percent = (static_cast<double>(system) / static_cast<double>(total)) * 100.0;
                obs.idle_percent = (static_cast<double>(total_idle) / static_cast<double>(total)) * 100.0;
                obs.total_cpu_usage_percent = (static_cast<double>(active) / static_cast<double>(total)) * 100.0;
                obs.valid = true;
            }
        }
    }

    return obs;
}

HostMemoryObservation HostMonitor::read_memory_observation(const std::string& proc_meminfo_path) {
    HostMemoryObservation obs;
    std::ifstream file(proc_meminfo_path);
    if (!file.is_open()) {
        obs.valid = false;
        return obs;
    }

    std::string key;
    uint64_t value = 0;
    std::string unit;
    bool has_total = false;
    bool has_avail = false;

    while (file >> key >> value >> unit) {
        if (key == "MemTotal:") {
            obs.total_kb = value;
            has_total = true;
        } else if (key == "MemFree:") {
            obs.free_kb = value;
        } else if (key == "MemAvailable:") {
            obs.available_kb = value;
            has_avail = true;
        }
    }

    if (has_total) {
        if (has_avail && obs.total_kb >= obs.available_kb) {
            obs.used_kb = obs.total_kb - obs.available_kb;
        } else if (obs.total_kb >= obs.free_kb) {
            obs.used_kb = obs.total_kb - obs.free_kb;
        }

        if (obs.total_kb > 0) {
            obs.used_percent = (static_cast<double>(obs.used_kb) / static_cast<double>(obs.total_kb)) * 100.0;
            obs.valid = true;
        }
    }

    return obs;
}

ProcessObservation HostMonitor::read_process_observation(int pid, const std::string& proc_dir) {
    ProcessObservation obs;
    if (pid <= 0) {
        pid = static_cast<int>(::getpid());
    }
    obs.pid = pid;

    std::string stat_path = proc_dir + "/" + std::to_string(pid) + "/stat";
    std::ifstream file(stat_path);
    if (!file.is_open()) {
        obs.valid = false;
        return obs;
    }

    std::string content;
    if (!std::getline(file, content)) {
        obs.valid = false;
        return obs;
    }

    // Format: pid (comm) state ppid ...
    size_t lparen = content.find('(');
    size_t rparen = content.rfind(')');
    if (lparen == std::string::npos || rparen == std::string::npos || rparen <= lparen) {
        obs.valid = false;
        return obs;
    }

    obs.comm = content.substr(lparen + 1, rparen - lparen - 1);
    std::string rest = content.substr(rparen + 2);
    std::istringstream ss(rest);

    // After (comm):
    // 3: state
    // 4: ppid
    // 5: pgrp, 6: session, 7: tty_nr, 8: tpgid, 9: flags, 10: minflt, 11: cminflt, 12: majflt, 13: cmajflt
    // 14: utime, 15: stime, 16: cutime, 17: cstime, 18: priority, 19: nice, 20: num_threads, 21: itrealvalue, 22: starttime
    // 23: vsize, 24: rss
    char state = '?';
    int ppid = 0;
    ss >> state >> ppid;
    obs.state = state;
    obs.ppid = ppid;

    std::string dummy;
    for (int i = 5; i <= 13; ++i) {
        ss >> dummy;
    }
    ss >> obs.utime_ticks >> obs.stime_ticks;
    for (int i = 16; i <= 22; ++i) {
        ss >> dummy;
    }
    ss >> obs.vm_size_bytes >> obs.rss_pages;

    long page_size = ::sysconf(_SC_PAGESIZE);
    if (page_size <= 0) page_size = 4096;
    obs.rss_kb = (obs.rss_pages * static_cast<uint64_t>(page_size)) / 1024;
    obs.valid = true;

    return obs;
}

std::vector<HostDiskObservation> HostMonitor::read_disk_observations(const std::string& proc_diskstats_path) {
    std::vector<HostDiskObservation> observations;
    std::ifstream file(proc_diskstats_path);
    if (!file.is_open()) {
        return observations;
    }

    std::string line;
    while (std::getline(file, line)) {
        std::istringstream ss(line);
        int major = 0, minor = 0;
        std::string dev_name;
        uint64_t reads_comp = 0, reads_merged = 0, sec_read = 0;
        uint64_t time_reading = 0, writes_comp = 0, writes_merged = 0, sec_written = 0;

        if (ss >> major >> minor >> dev_name >> reads_comp >> reads_merged >> sec_read
               >> time_reading >> writes_comp >> writes_merged >> sec_written) {
            // Keep disks and ignore empty partitions or loop devices
            if (dev_name.rfind("loop", 0) == 0 && reads_comp == 0 && writes_comp == 0) {
                continue;
            }
            HostDiskObservation obs;
            obs.device_name = dev_name;
            obs.reads_completed = reads_comp;
            obs.sectors_read = sec_read;
            obs.writes_completed = writes_comp;
            obs.sectors_written = sec_written;
            obs.valid = true;
            observations.push_back(obs);
            if (observations.size() >= 10) break; // limit to 10 entries
        }
    }

    return observations;
}

HostSystemObservation HostMonitor::read_system_observation(const std::string& root_mount,
                                                          const std::string& proc_uptime_path,
                                                          const std::string& proc_loadavg_path) {
    HostSystemObservation obs;
    obs.root_mount = root_mount;

    // 1. /proc/uptime
    std::ifstream up_file(proc_uptime_path);
    if (up_file.is_open()) {
        double up = 0.0, idle = 0.0;
        if (up_file >> up >> idle) {
            obs.uptime_seconds = up;
            obs.valid = true;
        }
    }

    // 2. /proc/loadavg
    std::ifstream load_file(proc_loadavg_path);
    if (load_file.is_open()) {
        double l1 = 0.0, l5 = 0.0, l15 = 0.0;
        std::string proc_str;
        if (load_file >> l1 >> l5 >> l15 >> proc_str) {
            obs.load_1min = l1;
            obs.load_5min = l5;
            obs.load_15min = l15;
            size_t slash = proc_str.find('/');
            if (slash != std::string::npos) {
                try {
                    obs.running_processes = std::stoi(proc_str.substr(0, slash));
                    obs.total_processes = std::stoi(proc_str.substr(slash + 1));
                } catch (...) {}
            }
            obs.valid = true;
        }
    }

    // 3. Filesystem capacity via statvfs
#if !defined(_WIN32)
    struct statvfs vfs{};
    if (::statvfs(root_mount.c_str(), &vfs) == 0) {
        uint64_t total = static_cast<uint64_t>(vfs.f_blocks) * static_cast<uint64_t>(vfs.f_frsize);
        uint64_t free_b = static_cast<uint64_t>(vfs.f_bfree) * static_cast<uint64_t>(vfs.f_frsize);
        uint64_t avail = static_cast<uint64_t>(vfs.f_bavail) * static_cast<uint64_t>(vfs.f_frsize);
        uint64_t used = (total >= free_b) ? (total - free_b) : 0;
        obs.disk_total_bytes = total;
        obs.disk_used_bytes = used;
        obs.disk_available_bytes = avail;
        if (total > 0) {
            obs.disk_used_percent = (static_cast<double>(used) / static_cast<double>(total)) * 100.0;
        }
        obs.valid = true;
    }
#endif

    return obs;
}

HostMonitoringSnapshot HostMonitor::take_snapshot() {
    HostMonitoringSnapshot snap;
    snap.source = "real_linux_host";
    snap.timestamp = get_current_iso_timestamp();

    snap.cpu = read_cpu_observation();
    snap.memory = read_memory_observation();
    snap.self_process = read_process_observation(0);
    snap.disks = read_disk_observations();
    snap.system = read_system_observation();

    snap.success = snap.cpu.valid || snap.memory.valid || snap.self_process.valid || snap.system.valid;
    if (!snap.success) {
        snap.error_message = "Failed to access host /proc monitoring interfaces.";
    }

    return snap;
}

} // namespace oscope::monitoring
