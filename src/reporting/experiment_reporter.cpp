#include "oscope/reporting/experiment_reporter.hpp"
#include "oscope/disk/disk_scheduler.hpp"

#include <string_view>

namespace oscope::reporting {

namespace {

std::string_view to_string_view(experiments::ProcessExperimentStatus status) noexcept {
    switch (status) {
        case experiments::ProcessExperimentStatus::Success:
            return "success";
        case experiments::ProcessExperimentStatus::ForkFailed:
            return "fork_failed";
        case experiments::ProcessExperimentStatus::WaitFailed:
            return "wait_failed";
        case experiments::ProcessExperimentStatus::AbnormalTermination:
            return "abnormal_termination";
        case experiments::ProcessExperimentStatus::UnexpectedExitCode:
            return "unexpected_exit_code";
    }
    return "unknown";
}

std::string_view to_string_view(experiments::PipeIpcStatus status) noexcept {
    switch (status) {
        case experiments::PipeIpcStatus::Success:
            return "success";
        case experiments::PipeIpcStatus::PipeCreationFailed:
            return "pipe_creation_failed";
        case experiments::PipeIpcStatus::ForkFailed:
            return "fork_failed";
        case experiments::PipeIpcStatus::WriteFailed:
            return "write_failed";
        case experiments::PipeIpcStatus::ReadFailed:
            return "read_failed";
        case experiments::PipeIpcStatus::WaitFailed:
            return "wait_failed";
        case experiments::PipeIpcStatus::MessageMismatch:
            return "message_mismatch";
        case experiments::PipeIpcStatus::ChildTerminatedAbnormally:
            return "child_terminated_abnormally";
        case experiments::PipeIpcStatus::ChildReportedError:
            return "child_reported_error";
    }
    return "unknown";
}

} // namespace

JsonValue to_json(const experiments::ProcessExperimentResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string(kLinuxExperimentCategory));
    root.set("experiment", JsonValue::string("process_creation"));
    root.set("status", JsonValue::string(result.is_success() ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.is_success()));

    JsonValue details = JsonValue::object();
    details.set("parent_pid", JsonValue::integer(result.parent_pid));
    details.set("child_pid", result.child_pid > 0 ? JsonValue::integer(result.child_pid) : JsonValue::null());
    details.set("child_exited_normally", JsonValue::boolean(result.exited_normally));
    details.set("child_exit_code", result.exited_normally ? JsonValue::integer(result.exit_code) : JsonValue::null());
    details.set("child_termination_signal", result.termination_signal >= 0 ? JsonValue::integer(result.termination_signal) : JsonValue::null());
    details.set("status_code", JsonValue::string(to_string_view(result.status)));
    details.set("message", JsonValue::string(result.message));
    root.set("result", std::move(details));

    if (result.is_success()) {
        root.set("error", JsonValue::null());
    } else {
        JsonValue error_obj = JsonValue::object();
        error_obj.set("status_code", JsonValue::string(to_string_view(result.status)));
        error_obj.set("message", JsonValue::string(result.message));
        root.set("error", std::move(error_obj));
    }

    return root;
}

JsonValue to_json(const experiments::ThreadExperimentResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string(kLinuxExperimentCategory));
    root.set("experiment", JsonValue::string("thread_creation"));
    root.set("status", JsonValue::string(result.success ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.success));

    JsonValue details = JsonValue::object();
    details.set("requested_threads", JsonValue::unsigned_integer(result.requested_threads));
    details.set("started_threads", JsonValue::unsigned_integer(result.started_threads));
    details.set("completed_threads", JsonValue::unsigned_integer(result.completed_threads));

    JsonValue results_arr = JsonValue::array();
    for (int r : result.worker_results) {
        results_arr.push_back(JsonValue::integer(r));
    }
    details.set("worker_results", std::move(results_arr));
    root.set("result", std::move(details));

    if (result.success) {
        root.set("error", JsonValue::null());
    } else {
        JsonValue error_obj = JsonValue::object();
        error_obj.set("message", JsonValue::string(result.error_message));
        root.set("error", std::move(error_obj));
    }

    return root;
}

JsonValue to_json(const experiments::SynchronizationExperimentResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string(kLinuxExperimentCategory));
    root.set("experiment", JsonValue::string("thread_synchronization"));
    root.set("status", JsonValue::string(result.success ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.success));

    JsonValue details = JsonValue::object();
    details.set("num_threads", JsonValue::unsigned_integer(result.num_threads));
    details.set("iterations_per_thread", JsonValue::unsigned_integer(result.iterations_per_thread));
    details.set("threads_completed", JsonValue::unsigned_integer(result.threads_completed));
    details.set("expected_counter", JsonValue::unsigned_integer(result.expected_counter));
    details.set("actual_counter", JsonValue::unsigned_integer(result.actual_counter));
    details.set("counter_match", JsonValue::boolean(result.expected_counter == result.actual_counter));
    root.set("result", std::move(details));

    if (result.success) {
        root.set("error", JsonValue::null());
    } else {
        JsonValue error_obj = JsonValue::object();
        error_obj.set("message", JsonValue::string(result.error_message));
        root.set("error", std::move(error_obj));
    }

    return root;
}

JsonValue to_json(const experiments::PipeIpcExperimentResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string(kLinuxExperimentCategory));
    root.set("experiment", JsonValue::string("pipe_ipc"));
    root.set("status", JsonValue::string(result.is_success() ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.is_success()));

    JsonValue details = JsonValue::object();
    details.set("direction", JsonValue::string("child_to_parent"));
    details.set("parent_pid", JsonValue::integer(result.parent_pid));
    details.set("child_pid", result.child_pid > 0 ? JsonValue::integer(result.child_pid) : JsonValue::null());
    details.set("child_exited_normally", JsonValue::boolean(result.child_exited_normally));
    details.set("child_exit_code", result.child_exited_normally ? JsonValue::integer(result.child_exit_code) : JsonValue::null());
    details.set("child_termination_signal", result.child_termination_signal >= 0 ? JsonValue::integer(result.child_termination_signal) : JsonValue::null());
    details.set("sent_message", JsonValue::string(result.sent_message));
    details.set("received_message", JsonValue::string(result.received_message));
    details.set("messages_match", JsonValue::boolean(result.sent_message == result.received_message));
    details.set("status_code", JsonValue::string(to_string_view(result.status)));
    root.set("result", std::move(details));

    if (result.is_success()) {
        root.set("error", JsonValue::null());
    } else {
        JsonValue error_obj = JsonValue::object();
        error_obj.set("status_code", JsonValue::string(to_string_view(result.status)));
        error_obj.set("message", JsonValue::string(result.error_message));
        root.set("error", std::move(error_obj));
    }

    return root;
}

std::string serialize_result(const experiments::ProcessExperimentResult& result, bool pretty) {
    return to_json(result).serialize(pretty);
}

std::string serialize_result(const experiments::ThreadExperimentResult& result, bool pretty) {
    return to_json(result).serialize(pretty);
}

std::string serialize_result(const experiments::SynchronizationExperimentResult& result, bool pretty) {
    return to_json(result).serialize(pretty);
}

std::string serialize_result(const experiments::PipeIpcExperimentResult& result, bool pretty) {
    return to_json(result).serialize(pretty);
}

JsonValue to_json(const deadlock::SafetyResult& result, const deadlock::DeadlockState& state) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string(kDeadlockCategory));
    root.set("experiment", JsonValue::string("bankers_safety"));
    root.set("status", JsonValue::string(result.is_safe ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.is_safe));

    JsonValue details = JsonValue::object();
    details.set("is_safe", JsonValue::boolean(result.is_safe));
    details.set("num_processes", JsonValue::integer(state.num_processes));
    details.set("num_resources", JsonValue::integer(state.num_resources));

    JsonValue seq_arr = JsonValue::array();
    for (int p : result.safe_sequence) {
        seq_arr.push_back(JsonValue::integer(p));
    }
    details.set("safe_sequence", std::move(seq_arr));

    JsonValue blocked_arr = JsonValue::array();
    for (int p : result.blocked_processes) {
        blocked_arr.push_back(JsonValue::integer(p));
    }
    details.set("blocked_processes", std::move(blocked_arr));
    details.set("message", JsonValue::string(result.message));
    root.set("result", std::move(details));

    if (result.is_safe) {
        root.set("error", JsonValue::null());
    } else {
        JsonValue error_obj = JsonValue::object();
        error_obj.set("status_code", JsonValue::string("unsafe_state"));
        error_obj.set("message", JsonValue::string(result.message));
        root.set("error", std::move(error_obj));
    }

    return root;
}

JsonValue to_json(const deadlock::ResourceRequestResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string(kDeadlockCategory));
    root.set("experiment", JsonValue::string("resource_request"));
    root.set("status", JsonValue::string(result.granted ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.granted));

    JsonValue details = JsonValue::object();
    details.set("granted", JsonValue::boolean(result.granted));
    details.set("process_id", JsonValue::integer(result.process_id));

    JsonValue req_arr = JsonValue::array();
    for (int r : result.request) {
        req_arr.push_back(JsonValue::integer(r));
    }
    details.set("request", std::move(req_arr));

    std::string_view status_str;
    switch (result.status) {
        case deadlock::RequestStatus::Granted: status_str = "granted"; break;
        case deadlock::RequestStatus::DeniedExceedsNeed: status_str = "denied_exceeds_need"; break;
        case deadlock::RequestStatus::DeniedExceedsAvailable: status_str = "denied_exceeds_available"; break;
        case deadlock::RequestStatus::DeniedUnsafeState: status_str = "denied_unsafe_state"; break;
        case deadlock::RequestStatus::InvalidRequest: status_str = "invalid_request"; break;
    }
    details.set("status_code", JsonValue::string(status_str));

    if (result.granted) {
        JsonValue seq_arr = JsonValue::array();
        for (int p : result.safe_sequence) {
            seq_arr.push_back(JsonValue::integer(p));
        }
        details.set("safe_sequence", std::move(seq_arr));
    } else {
        details.set("safe_sequence", JsonValue::null());
    }
    details.set("message", JsonValue::string(result.message));
    root.set("result", std::move(details));

    if (result.granted) {
        root.set("error", JsonValue::null());
    } else {
        JsonValue error_obj = JsonValue::object();
        error_obj.set("status_code", JsonValue::string(status_str));
        error_obj.set("message", JsonValue::string(result.message));
        root.set("error", std::move(error_obj));
    }

    return root;
}

JsonValue to_json(const deadlock::DetectionResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string(kDeadlockCategory));
    root.set("experiment", JsonValue::string("deadlock_detection"));
    root.set("status", JsonValue::string((!result.is_deadlocked && result.is_valid) ? "success" : "failure"));
    root.set("success", JsonValue::boolean(!result.is_deadlocked && result.is_valid));

    JsonValue details = JsonValue::object();
    details.set("is_deadlocked", JsonValue::boolean(result.is_deadlocked));

    JsonValue dl_arr = JsonValue::array();
    for (int p : result.deadlocked_processes) {
        dl_arr.push_back(JsonValue::integer(p));
    }
    details.set("deadlocked_processes", std::move(dl_arr));

    JsonValue fin_arr = JsonValue::array();
    for (int p : result.finished_processes) {
        fin_arr.push_back(JsonValue::integer(p));
    }
    details.set("finished_processes", std::move(fin_arr));
    details.set("message", JsonValue::string(result.message));
    root.set("result", std::move(details));

    if (!result.is_deadlocked && result.is_valid) {
        root.set("error", JsonValue::null());
    } else {
        JsonValue error_obj = JsonValue::object();
        error_obj.set("status_code", JsonValue::string(result.is_deadlocked ? "deadlock_detected" : "invalid_input"));
        error_obj.set("message", JsonValue::string(result.message));
        root.set("error", std::move(error_obj));
    }

    return root;
}

JsonValue to_json(const disk::DiskSchedulingResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string(kDiskCategory));
    root.set("experiment", JsonValue::string("disk_scheduling"));
    root.set("status", JsonValue::string(result.success ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.success));

    JsonValue details = JsonValue::object();
    details.set("algorithm", JsonValue::string(result.algorithm_name));

    JsonValue srv_arr = JsonValue::array();
    for (int r : result.serviced_requests) {
        srv_arr.push_back(JsonValue::integer(r));
    }
    details.set("serviced_requests", std::move(srv_arr));

    JsonValue path_arr = JsonValue::array();
    for (int p : result.head_path) {
        path_arr.push_back(JsonValue::integer(p));
    }
    details.set("head_path", std::move(path_arr));

    details.set("total_head_movement", JsonValue::integer(result.total_head_movement));
    details.set("wraparound_movement", JsonValue::integer(result.wraparound_movement));
    details.set("average_head_movement", JsonValue::string(std::to_string(result.average_head_movement)));
    details.set("initial_head_position", JsonValue::integer(result.initial_head_position));
    details.set("final_head_position", JsonValue::integer(result.final_head_position));
    details.set("message", JsonValue::string(result.message));
    root.set("result", std::move(details));

    if (result.success) {
        root.set("error", JsonValue::null());
    } else {
        JsonValue error_obj = JsonValue::object();
        error_obj.set("status_code", JsonValue::string("scheduling_failed"));
        error_obj.set("message", JsonValue::string(result.message));
        root.set("error", std::move(error_obj));
    }

    return root;
}

JsonValue to_json(const disk::DiskComparisonResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string(kDiskCategory));
    root.set("experiment", JsonValue::string("disk_comparison"));
    root.set("status", JsonValue::string("success"));
    root.set("success", JsonValue::boolean(true));

    JsonValue details = JsonValue::object();
    JsonValue req_arr = JsonValue::array();
    for (int r : result.original_requests) {
        req_arr.push_back(JsonValue::integer(r));
    }
    details.set("original_requests", std::move(req_arr));
    details.set("min_cylinder", JsonValue::integer(result.config.min_cylinder));
    details.set("max_cylinder", JsonValue::integer(result.config.max_cylinder));
    details.set("initial_head", JsonValue::integer(result.config.initial_head));
    details.set("direction", JsonValue::string(oscope::disk::to_string(result.config.direction)));

    JsonValue algo_arr = JsonValue::array();
    for (const auto& item : result.results) {
        JsonValue item_obj = JsonValue::object();
        item_obj.set("algorithm", JsonValue::string(item.algorithm_name));
        item_obj.set("total_head_movement", JsonValue::integer(item.total_head_movement));
        item_obj.set("wraparound_movement", JsonValue::integer(item.wraparound_movement));
        item_obj.set("average_head_movement", JsonValue::string(std::to_string(item.average_head_movement)));
        item_obj.set("final_head_position", JsonValue::integer(item.final_head_position));
        algo_arr.push_back(std::move(item_obj));
    }
    details.set("algorithms", std::move(algo_arr));
    root.set("result", std::move(details));
    root.set("error", JsonValue::null());

    return root;
}

std::string serialize_result(const deadlock::SafetyResult& result, const deadlock::DeadlockState& state, bool pretty) {
    return to_json(result, state).serialize(pretty);
}

std::string serialize_result(const deadlock::ResourceRequestResult& result, bool pretty) {
    return to_json(result).serialize(pretty);
}

std::string serialize_result(const deadlock::DetectionResult& result, bool pretty) {
    return to_json(result).serialize(pretty);
}

std::string serialize_result(const disk::DiskSchedulingResult& result, bool pretty) {
    return to_json(result).serialize(pretty);
}

std::string serialize_result(const disk::DiskComparisonResult& result, bool pretty) {
    return to_json(result).serialize(pretty);
}

JsonValue to_json(const paging::TranslationResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string("paging_virtual_memory"));
    root.set("experiment", JsonValue::string("address_translation"));
    root.set("status", JsonValue::string(result.page_fault ? "page_fault" : "success"));
    root.set("success", JsonValue::boolean(!result.page_fault));

    JsonValue details = JsonValue::object();
    details.set("virtual_address", JsonValue::unsigned_integer(result.virtual_address));
    details.set("page_number", JsonValue::unsigned_integer(result.page_number));
    details.set("offset", JsonValue::unsigned_integer(result.offset));
    details.set("page_fault", JsonValue::boolean(result.page_fault));
    details.set("frame_number", result.page_fault ? JsonValue::null() : JsonValue::integer(result.frame_number));
    details.set("physical_address", result.page_fault ? JsonValue::null() : JsonValue::unsigned_integer(result.physical_address));
    details.set("message", JsonValue::string(result.message));
    root.set("result", std::move(details));
    root.set("error", result.page_fault ? JsonValue::string(result.message) : JsonValue::null());
    return root;
}

JsonValue to_json(const paging::DemandPagingResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string("paging_virtual_memory"));
    root.set("experiment", JsonValue::string("demand_paging"));
    root.set("status", JsonValue::string("success"));
    root.set("success", JsonValue::boolean(true));

    JsonValue details = JsonValue::object();
    details.set("page_size", JsonValue::unsigned_integer(result.page_size));
    details.set("total_frames", JsonValue::integer(result.total_frames));
    details.set("total_accesses", JsonValue::integer(result.total_accesses));
    details.set("page_faults", JsonValue::integer(result.page_faults));
    details.set("page_hits", JsonValue::integer(result.page_hits));
    details.set("fault_rate", JsonValue::string(std::to_string(result.fault_rate)));
    root.set("result", std::move(details));
    root.set("error", JsonValue::null());
    return root;
}

JsonValue to_json(const synchronization::PetersonSimulationResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string("synchronization"));
    root.set("experiment", JsonValue::string("petersons_algorithm"));
    root.set("status", JsonValue::string(result.mutual_exclusion_maintained ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.mutual_exclusion_maintained));

    JsonValue details = JsonValue::object();
    details.set("mutual_exclusion_maintained", JsonValue::boolean(result.mutual_exclusion_maintained));
    details.set("p0_critical_entries", JsonValue::integer(result.p0_critical_entries));
    details.set("p1_critical_entries", JsonValue::integer(result.p1_critical_entries));
    details.set("total_steps", JsonValue::integer(result.total_steps));
    details.set("explanation", JsonValue::string(result.explanation));
    root.set("result", std::move(details));
    root.set("error", JsonValue::null());
    return root;
}

JsonValue to_json(const deadlock::CoffmanConditionReport& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string(kDeadlockCategory));
    root.set("experiment", JsonValue::string("coffman_conditions"));
    root.set("status", JsonValue::string("success"));
    root.set("success", JsonValue::boolean(true));

    JsonValue details = JsonValue::object();
    details.set("mutual_exclusion", JsonValue::boolean(result.mutual_exclusion));
    details.set("hold_and_wait", JsonValue::boolean(result.hold_and_wait));
    details.set("no_preemption", JsonValue::boolean(result.no_preemption));
    details.set("circular_wait", JsonValue::boolean(result.circular_wait));
    details.set("deadlock_possible", JsonValue::boolean(result.deadlock_possible));
    details.set("summary", JsonValue::string(result.summary));
    root.set("result", std::move(details));
    root.set("error", JsonValue::null());
    return root;
}

JsonValue to_json(const monitoring::HostMonitoringSnapshot& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string("linux_monitoring"));
    root.set("experiment", JsonValue::string("host_observation"));
    root.set("status", JsonValue::string(result.success ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.success));

    JsonValue details = JsonValue::object();
    details.set("source", JsonValue::string(result.source));
    details.set("timestamp", JsonValue::string(result.timestamp));
    details.set("cpu_usage_percent", JsonValue::string(std::to_string(result.cpu.total_cpu_usage_percent)));
    details.set("memory_total_kb", JsonValue::unsigned_integer(result.memory.total_kb));
    details.set("memory_used_kb", JsonValue::unsigned_integer(result.memory.used_kb));
    details.set("memory_used_percent", JsonValue::string(std::to_string(result.memory.used_percent)));
    details.set("self_pid", JsonValue::integer(result.self_process.pid));
    details.set("self_state", JsonValue::string(std::string(1, result.self_process.state)));
    details.set("self_rss_kb", JsonValue::unsigned_integer(result.self_process.rss_kb));
    root.set("result", std::move(details));
    root.set("error", result.success ? JsonValue::null() : JsonValue::string(result.error_message));
    return root;
}

JsonValue to_json(const filesystem::FilesystemStatus& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string("filesystem_simulation"));
    root.set("experiment", JsonValue::string("simple_filesystem"));
    root.set("status", JsonValue::string("success"));
    root.set("success", JsonValue::boolean(true));

    JsonValue details = JsonValue::object();
    details.set("total_blocks", JsonValue::integer(result.total_blocks));
    details.set("block_size", JsonValue::integer(result.block_size));
    details.set("used_blocks", JsonValue::integer(result.used_blocks));
    details.set("free_blocks", JsonValue::integer(result.free_blocks));
    details.set("file_count", JsonValue::integer(result.file_count));
    details.set("directory_count", JsonValue::integer(result.directory_count));
    root.set("result", std::move(details));
    root.set("error", JsonValue::null());
    return root;
}

JsonValue to_json(const experiments::FifoExperimentResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string(kLinuxExperimentCategory));
    root.set("experiment", JsonValue::string("fifo_ipc"));
    root.set("status", JsonValue::string(result.success ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.success));

    JsonValue details = JsonValue::object();
    details.set("fifo_path", JsonValue::string(result.fifo_path));
    details.set("message_sent", JsonValue::string(result.message_sent));
    details.set("message_received", JsonValue::string(result.message_received));
    details.set("details", JsonValue::string(result.details));
    root.set("result", std::move(details));
    root.set("error", result.success ? JsonValue::null() : JsonValue::string(result.error_message));
    return root;
}

JsonValue to_json(const experiments::SharedMemoryExperimentResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string(kLinuxExperimentCategory));
    root.set("experiment", JsonValue::string("shared_memory_ipc"));
    root.set("status", JsonValue::string(result.success ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.success));

    JsonValue details = JsonValue::object();
    details.set("segment_name", JsonValue::string(result.segment_name));
    details.set("size_bytes", JsonValue::unsigned_integer(result.size_bytes));
    details.set("message_written", JsonValue::string(result.message_written));
    details.set("message_read", JsonValue::string(result.message_read));
    details.set("details", JsonValue::string(result.details));
    root.set("result", std::move(details));
    root.set("error", result.success ? JsonValue::null() : JsonValue::string(result.error_message));
    return root;
}

JsonValue to_json(const experiments::ZombieDemonstrationResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string(kLinuxExperimentCategory));
    root.set("experiment", JsonValue::string("zombie_demonstration"));
    root.set("status", JsonValue::string(result.reaped_successfully ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.reaped_successfully));

    JsonValue details = JsonValue::object();
    details.set("child_pid", JsonValue::integer(result.child_pid));
    details.set("observed_state", JsonValue::string(std::string(1, result.observed_state)));
    details.set("zombie_observed", JsonValue::boolean(result.zombie_observed));
    details.set("reaped_successfully", JsonValue::boolean(result.reaped_successfully));
    details.set("details", JsonValue::string(result.details));
    root.set("result", std::move(details));
    root.set("error", JsonValue::null());
    return root;
}

JsonValue to_json(const experiments::OrphanDemonstrationResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string(kLinuxExperimentCategory));
    root.set("experiment", JsonValue::string("orphan_demonstration"));
    root.set("status", JsonValue::string(result.reparented_to_init_or_subreaper ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.reparented_to_init_or_subreaper));

    JsonValue details = JsonValue::object();
    details.set("child_pid", JsonValue::integer(result.child_pid));
    details.set("initial_parent_pid", JsonValue::integer(result.initial_parent_pid));
    details.set("adopted_parent_pid", JsonValue::integer(result.adopted_parent_pid));
    details.set("reparented_to_init_or_subreaper", JsonValue::boolean(result.reparented_to_init_or_subreaper));
    details.set("details", JsonValue::string(result.details));
    root.set("result", std::move(details));
    root.set("error", JsonValue::null());
    return root;
}

JsonValue to_json(const experiments::MessageQueueExperimentResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string(kLinuxExperimentCategory));
    root.set("experiment", JsonValue::string("message_queue_ipc"));
    root.set("status", JsonValue::string(result.success ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.success));

    JsonValue details = JsonValue::object();
    details.set("queue_name", JsonValue::string(result.queue_name));
    details.set("messages_sent", JsonValue::integer(result.messages_sent));
    details.set("messages_received", JsonValue::integer(result.messages_received));
    details.set("message_content", JsonValue::string(result.message_content));
    details.set("details", JsonValue::string(result.details));
    root.set("result", std::move(details));
    root.set("error", result.success ? JsonValue::null() : JsonValue::string(result.error_message));
    return root;
}

JsonValue to_json(const experiments::ProcessExecResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string(kLinuxExperimentCategory));
    root.set("experiment", JsonValue::string("process_exec"));
    root.set("status", JsonValue::string(result.success ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.success));

    JsonValue details = JsonValue::object();
    details.set("child_pid", JsonValue::integer(result.child_pid));
    details.set("program_executed", JsonValue::string(result.program_executed));
    details.set("image_replaced", JsonValue::boolean(result.image_replaced));
    details.set("captured_output", JsonValue::string(result.captured_output));
    details.set("child_exit_code", JsonValue::integer(result.child_exit_code));
    details.set("details", JsonValue::string(result.details));
    root.set("result", std::move(details));
    root.set("error", result.success ? JsonValue::null() : JsonValue::string(result.error_message));
    return root;
}

JsonValue to_json(const synchronization::SemaphoreExperimentResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string("synchronization"));
    root.set("experiment", JsonValue::string("posix_semaphore"));
    root.set("status", JsonValue::string(result.success ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.success));

    JsonValue details = JsonValue::object();
    details.set("num_threads", JsonValue::unsigned_integer(result.num_threads));
    details.set("iterations_per_thread", JsonValue::unsigned_integer(result.iterations_per_thread));
    details.set("threads_completed", JsonValue::unsigned_integer(result.threads_completed));
    details.set("expected_counter", JsonValue::unsigned_integer(result.expected_counter));
    details.set("actual_counter", JsonValue::unsigned_integer(result.actual_counter));
    details.set("counter_match", JsonValue::boolean(result.expected_counter == result.actual_counter));
    details.set("initial_value", JsonValue::unsigned_integer(result.initial_value));
    root.set("result", std::move(details));
    root.set("error", result.success ? JsonValue::null() : JsonValue::string(result.error_message));
    return root;
}

JsonValue to_json(const synchronization::ProducerConsumerResult& result) {
    JsonValue root = JsonValue::object();
    root.set("schema_version", JsonValue::string(kSchemaVersion));
    root.set("category", JsonValue::string("synchronization"));
    root.set("experiment", JsonValue::string("producer_consumer"));
    root.set("status", JsonValue::string(result.success ? "success" : "failure"));
    root.set("success", JsonValue::boolean(result.success));

    JsonValue details = JsonValue::object();
    details.set("buffer_capacity", JsonValue::unsigned_integer(result.buffer_capacity));
    details.set("total_items", JsonValue::unsigned_integer(result.total_items));
    details.set("num_producers", JsonValue::unsigned_integer(result.num_producers));
    details.set("num_consumers", JsonValue::unsigned_integer(result.num_consumers));
    details.set("items_produced", JsonValue::unsigned_integer(result.items_produced));
    details.set("items_consumed", JsonValue::unsigned_integer(result.items_consumed));
    details.set("items_preserved", JsonValue::boolean(result.items_preserved));
    details.set("max_buffer_occupancy_observed", JsonValue::unsigned_integer(result.max_buffer_occupancy_observed));
    root.set("result", std::move(details));
    root.set("error", result.success ? JsonValue::null() : JsonValue::string(result.error_message));
    return root;
}

} // namespace oscope::reporting
