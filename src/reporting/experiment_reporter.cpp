#include "oscope/reporting/experiment_reporter.hpp"

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

} // namespace oscope::reporting
