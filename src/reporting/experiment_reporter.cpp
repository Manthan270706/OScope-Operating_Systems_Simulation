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

} // namespace oscope::reporting
