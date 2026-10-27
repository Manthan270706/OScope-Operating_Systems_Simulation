#include <gtest/gtest.h>

#include <array>
#include <cstdio>
#include <cstdlib>
#include <sstream>
#include <string>
#include <sys/wait.h>

#include "oscope/cli.hpp"
#include "oscope/experiments/pipe_ipc_experiment.hpp"
#include "oscope/experiments/process_experiment.hpp"
#include "oscope/experiments/synchronization_experiment.hpp"
#include "oscope/experiments/thread_experiment.hpp"
#include "oscope/reporting/experiment_reporter.hpp"
#include "oscope/reporting/json_value.hpp"

namespace {

using namespace oscope::reporting;
using namespace oscope::experiments;

// ============================================================================
// 1. JSON String Escaping Tests
// ============================================================================

TEST(JsonValueTest, EscapesBasicCharactersAndQuotesCorrectly) {
    EXPECT_EQ(escape_json_string(""), "");
    EXPECT_EQ(escape_json_string("hello world"), "hello world");
    EXPECT_EQ(escape_json_string("quote: \"test\""), "quote: \\\"test\\\"");
    EXPECT_EQ(escape_json_string("slash: \\path\\to"), "slash: \\\\path\\\\to");
}

TEST(JsonValueTest, EscapesWhitespaceControlCharactersCorrectly) {
    EXPECT_EQ(escape_json_string("line1\nline2"), "line1\\nline2");
    EXPECT_EQ(escape_json_string("col1\tcol2"), "col1\\tcol2");
    EXPECT_EQ(escape_json_string("return\r"), "return\\r");
    EXPECT_EQ(escape_json_string("form\ffeed"), "form\\ffeed");
    EXPECT_EQ(escape_json_string("back\bspace"), "back\\bspace");
}

TEST(JsonValueTest, EscapesNonPrintableControlCharactersAsUnicodeHex) {
    // ASCII 0x01 (SOH) -> \u0001, ASCII 0x1B (ESC) -> \u001B
    std::string input;
    input += static_cast<char>(0x01);
    input += "alert";
    input += static_cast<char>(0x1B);

    EXPECT_EQ(escape_json_string(input), "\\u0001alert\\u001B");
}

// ============================================================================
// 2. JsonValue Primitive & Structured Serialization Tests
// ============================================================================

TEST(JsonValueTest, SerializesPrimitivesCorrectly) {
    EXPECT_EQ(JsonValue::null().serialize(false), "null");
    EXPECT_EQ(JsonValue::boolean(true).serialize(false), "true");
    EXPECT_EQ(JsonValue::boolean(false).serialize(false), "false");
    EXPECT_EQ(JsonValue::integer(-42).serialize(false), "-42");
    EXPECT_EQ(JsonValue::unsigned_integer(100ULL).serialize(false), "100");
    EXPECT_EQ(JsonValue::string("value").serialize(false), "\"value\"");
}

TEST(JsonValueTest, SerializesArraysCorrectly) {
    JsonValue empty_arr = JsonValue::array();
    EXPECT_EQ(empty_arr.serialize(false), "[]");

    JsonValue arr = JsonValue::array({
        JsonValue::integer(10),
        JsonValue::integer(20),
        JsonValue::integer(30)
    });
    EXPECT_EQ(arr.serialize(false), "[10, 20, 30]");

    std::string pretty = arr.serialize(true, 2);
    EXPECT_NE(pretty.find("[\n  10,\n  20,\n  30\n]"), std::string::npos);
}

TEST(JsonValueTest, SerializesObjectsCorrectlyAndPreservesKeyOrder) {
    JsonValue empty_obj = JsonValue::object();
    EXPECT_EQ(empty_obj.serialize(false), "{}");

    JsonValue obj = JsonValue::object({
        {"name", JsonValue::string("OScope")},
        {"version", JsonValue::integer(1)},
        {"active", JsonValue::boolean(true)}
    });

    EXPECT_EQ(obj.serialize(false), "{\"name\": \"OScope\", \"version\": 1, \"active\": true}");

    // Updating existing key
    obj.set("version", JsonValue::integer(2));
    EXPECT_EQ(obj.find("version")->as_int64(), 2);

    // Finding non-existent key
    EXPECT_EQ(obj.find("non_existent"), nullptr);
}

// ============================================================================
// 3. Process Creation Experiment Serialization Tests
// ============================================================================

TEST(ExperimentReportingTest, SerializesSuccessfulProcessExperiment) {
    ProcessExperimentResult res;
    res.status = ProcessExperimentStatus::Success;
    res.parent_pid = 1000;
    res.child_pid = 1001;
    res.exited_normally = true;
    res.exit_code = 42;
    res.termination_signal = -1;
    res.message = "Child process exited normally with expected exit code 42.";

    std::string json_str = serialize_result(res, false);
    JsonValue json = to_json(res);

    EXPECT_EQ(json.find("schema_version")->as_string(), "1.0.0");
    EXPECT_EQ(json.find("category")->as_string(), "linux_posix_experiment");
    EXPECT_EQ(json.find("experiment")->as_string(), "process_creation");
    EXPECT_EQ(json.find("status")->as_string(), "success");
    EXPECT_TRUE(json.find("success")->as_bool());
    EXPECT_TRUE(json.find("error")->is_null());

    const JsonValue* result_obj = json.find("result");
    ASSERT_NE(result_obj, nullptr);
    EXPECT_EQ(result_obj->find("parent_pid")->as_int64(), 1000);
    EXPECT_EQ(result_obj->find("child_pid")->as_int64(), 1001);
    EXPECT_TRUE(result_obj->find("child_exited_normally")->as_bool());
    EXPECT_EQ(result_obj->find("child_exit_code")->as_int64(), 42);
    EXPECT_TRUE(result_obj->find("child_termination_signal")->is_null());
    EXPECT_EQ(result_obj->find("status_code")->as_string(), "success");

    EXPECT_NE(json_str.find("\"status\": \"success\""), std::string::npos);
    EXPECT_NE(json_str.find("\"child_exit_code\": 42"), std::string::npos);
}

TEST(ExperimentReportingTest, SerializesFailedOrSignaledProcessExperiment) {
    ProcessExperimentResult res;
    res.status = ProcessExperimentStatus::AbnormalTermination;
    res.parent_pid = 2000;
    res.child_pid = 2001;
    res.exited_normally = false;
    res.exit_code = -1;
    res.termination_signal = 9;
    res.message = "Child process terminated abnormally by signal 9.";

    JsonValue json = to_json(res);

    EXPECT_EQ(json.find("status")->as_string(), "failure");
    EXPECT_FALSE(json.find("success")->as_bool());

    const JsonValue* result_obj = json.find("result");
    ASSERT_NE(result_obj, nullptr);
    EXPECT_FALSE(result_obj->find("child_exited_normally")->as_bool());
    EXPECT_TRUE(result_obj->find("child_exit_code")->is_null());
    EXPECT_EQ(result_obj->find("child_termination_signal")->as_int64(), 9);
    EXPECT_EQ(result_obj->find("status_code")->as_string(), "abnormal_termination");

    const JsonValue* error_obj = json.find("error");
    ASSERT_NE(error_obj, nullptr);
    EXPECT_EQ(error_obj->find("status_code")->as_string(), "abnormal_termination");
    EXPECT_EQ(error_obj->find("message")->as_string(), res.message);
}

TEST(ExperimentReportingTest, SerializesForkFailedProcessExperiment) {
    ProcessExperimentResult res;
    res.status = ProcessExperimentStatus::ForkFailed;
    res.parent_pid = 3000;
    res.child_pid = -1;
    res.exited_normally = false;
    res.exit_code = -1;
    res.termination_signal = -1;
    res.message = "fork() failed: Cannot allocate memory";

    JsonValue json = to_json(res);

    EXPECT_EQ(json.find("status")->as_string(), "failure");
    const JsonValue* result_obj = json.find("result");
    ASSERT_NE(result_obj, nullptr);
    EXPECT_TRUE(result_obj->find("child_pid")->is_null());
    EXPECT_EQ(result_obj->find("status_code")->as_string(), "fork_failed");

    const JsonValue* error_obj = json.find("error");
    ASSERT_NE(error_obj, nullptr);
    EXPECT_EQ(error_obj->find("status_code")->as_string(), "fork_failed");
}

// ============================================================================
// 4. Thread Creation Experiment Serialization Tests
// ============================================================================

TEST(ExperimentReportingTest, SerializesSuccessfulThreadExperiment) {
    ThreadExperimentResult res;
    res.success = true;
    res.requested_threads = 4;
    res.started_threads = 4;
    res.completed_threads = 4;
    res.worker_results = {100, 200, 300, 400};

    std::string json_str = serialize_result(res, true);
    JsonValue json = to_json(res);

    EXPECT_EQ(json.find("schema_version")->as_string(), "1.0.0");
    EXPECT_EQ(json.find("experiment")->as_string(), "thread_creation");
    EXPECT_EQ(json.find("status")->as_string(), "success");
    EXPECT_TRUE(json.find("success")->as_bool());
    EXPECT_TRUE(json.find("error")->is_null());

    const JsonValue* result_obj = json.find("result");
    ASSERT_NE(result_obj, nullptr);
    EXPECT_EQ(result_obj->find("requested_threads")->as_uint64(), 4);
    EXPECT_EQ(result_obj->find("started_threads")->as_uint64(), 4);
    EXPECT_EQ(result_obj->find("completed_threads")->as_uint64(), 4);

    const JsonValue* results_arr = result_obj->find("worker_results");
    ASSERT_NE(results_arr, nullptr);
    EXPECT_EQ(results_arr->as_array().size(), 4);
    EXPECT_EQ(results_arr->as_array()[0].as_int64(), 100);
    EXPECT_EQ(results_arr->as_array()[3].as_int64(), 400);

    EXPECT_NE(json_str.find("\"requested_threads\": 4"), std::string::npos);
}

TEST(ExperimentReportingTest, SerializesFailedThreadExperiment) {
    ThreadExperimentResult res;
    res.success = false;
    res.requested_threads = 2000;
    res.started_threads = 0;
    res.completed_threads = 0;
    res.error_message = "Requested thread count (2000) exceeds maximum supported limit of 1024.";

    JsonValue json = to_json(res);

    EXPECT_EQ(json.find("status")->as_string(), "failure");
    EXPECT_FALSE(json.find("success")->as_bool());

    const JsonValue* error_obj = json.find("error");
    ASSERT_NE(error_obj, nullptr);
    EXPECT_NE(error_obj->find("message")->as_string().find("exceeds maximum supported limit"), std::string::npos);
}

// ============================================================================
// 5. Thread Synchronization Experiment Serialization Tests
// ============================================================================

TEST(ExperimentReportingTest, SerializesSuccessfulSynchronizationExperiment) {
    SynchronizationExperimentResult res;
    res.success = true;
    res.num_threads = 4;
    res.iterations_per_thread = 10000;
    res.threads_completed = 4;
    res.expected_counter = 40000;
    res.actual_counter = 40000;

    std::string json_str = serialize_result(res, true);
    JsonValue json = to_json(res);

    EXPECT_EQ(json.find("schema_version")->as_string(), "1.0.0");
    EXPECT_EQ(json.find("experiment")->as_string(), "thread_synchronization");
    EXPECT_EQ(json.find("status")->as_string(), "success");
    EXPECT_TRUE(json.find("success")->as_bool());
    EXPECT_TRUE(json.find("error")->is_null());

    const JsonValue* result_obj = json.find("result");
    ASSERT_NE(result_obj, nullptr);
    EXPECT_EQ(result_obj->find("num_threads")->as_uint64(), 4);
    EXPECT_EQ(result_obj->find("iterations_per_thread")->as_uint64(), 10000);
    EXPECT_EQ(result_obj->find("threads_completed")->as_uint64(), 4);
    EXPECT_EQ(result_obj->find("expected_counter")->as_uint64(), 40000);
    EXPECT_EQ(result_obj->find("actual_counter")->as_uint64(), 40000);
    EXPECT_TRUE(result_obj->find("counter_match")->as_bool());

    EXPECT_NE(json_str.find("\"counter_match\": true"), std::string::npos);
}

TEST(ExperimentReportingTest, SerializesFailedSynchronizationExperiment) {
    SynchronizationExperimentResult res;
    res.success = false;
    res.num_threads = 10;
    res.iterations_per_thread = 1000;
    res.threads_completed = 8;
    res.expected_counter = 10000;
    res.actual_counter = 8000;
    res.error_message = "Only 8 out of 10 threads completed.";

    JsonValue json = to_json(res);

    EXPECT_EQ(json.find("status")->as_string(), "failure");
    EXPECT_FALSE(json.find("success")->as_bool());

    const JsonValue* result_obj = json.find("result");
    ASSERT_NE(result_obj, nullptr);
    EXPECT_FALSE(result_obj->find("counter_match")->as_bool());

    const JsonValue* error_obj = json.find("error");
    ASSERT_NE(error_obj, nullptr);
    EXPECT_EQ(error_obj->find("message")->as_string(), res.error_message);
}

// ============================================================================
// 6. Pipe IPC Experiment Serialization Tests
// ============================================================================

TEST(ExperimentReportingTest, SerializesSuccessfulPipeIpcExperiment) {
    PipeIpcExperimentResult res;
    res.status = PipeIpcStatus::Success;
    res.parent_pid = 4000;
    res.child_pid = 4001;
    res.child_exited_normally = true;
    res.child_exit_code = 0;
    res.child_termination_signal = -1;
    res.sent_message = "Hello from OScope child process via POSIX pipe!";
    res.received_message = "Hello from OScope child process via POSIX pipe!";

    std::string json_str = serialize_result(res, true);
    JsonValue json = to_json(res);

    EXPECT_EQ(json.find("schema_version")->as_string(), "1.0.0");
    EXPECT_EQ(json.find("experiment")->as_string(), "pipe_ipc");
    EXPECT_EQ(json.find("status")->as_string(), "success");
    EXPECT_TRUE(json.find("success")->as_bool());
    EXPECT_TRUE(json.find("error")->is_null());

    const JsonValue* result_obj = json.find("result");
    ASSERT_NE(result_obj, nullptr);
    EXPECT_EQ(result_obj->find("direction")->as_string(), "child_to_parent");
    EXPECT_EQ(result_obj->find("parent_pid")->as_int64(), 4000);
    EXPECT_EQ(result_obj->find("child_pid")->as_int64(), 4001);
    EXPECT_TRUE(result_obj->find("child_exited_normally")->as_bool());
    EXPECT_EQ(result_obj->find("child_exit_code")->as_int64(), 0);
    EXPECT_TRUE(result_obj->find("child_termination_signal")->is_null());
    EXPECT_EQ(result_obj->find("sent_message")->as_string(), res.sent_message);
    EXPECT_EQ(result_obj->find("received_message")->as_string(), res.received_message);
    EXPECT_TRUE(result_obj->find("messages_match")->as_bool());
    EXPECT_EQ(result_obj->find("status_code")->as_string(), "success");

    EXPECT_NE(json_str.find("\"direction\": \"child_to_parent\""), std::string::npos);
}

TEST(ExperimentReportingTest, SerializesPipeIpcWithSpecialCharactersAndNewlines) {
    PipeIpcExperimentResult res;
    res.status = PipeIpcStatus::Success;
    res.parent_pid = 5000;
    res.child_pid = 5001;
    res.child_exited_normally = true;
    res.child_exit_code = 0;
    res.sent_message = "Line 1\nLine 2\t\"quoted\" \\path\\";
    res.received_message = "Line 1\nLine 2\t\"quoted\" \\path\\";

    std::string json_str = serialize_result(res, false);

    // Verify string in JSON is properly escaped
    EXPECT_NE(json_str.find("Line 1\\nLine 2\\t\\\"quoted\\\" \\\\path\\\\"), std::string::npos);
}

TEST(ExperimentReportingTest, SerializesFailedPipeIpcExperiment) {
    PipeIpcExperimentResult res;
    res.status = PipeIpcStatus::ChildReportedError;
    res.parent_pid = 6000;
    res.child_pid = 6001;
    res.child_exited_normally = true;
    res.child_exit_code = 101;
    res.child_termination_signal = -1;
    res.error_message = "Child process exited with error code 101.";

    JsonValue json = to_json(res);

    EXPECT_EQ(json.find("status")->as_string(), "failure");
    EXPECT_FALSE(json.find("success")->as_bool());

    const JsonValue* result_obj = json.find("result");
    ASSERT_NE(result_obj, nullptr);
    EXPECT_EQ(result_obj->find("status_code")->as_string(), "child_reported_error");

    const JsonValue* error_obj = json.find("error");
    ASSERT_NE(error_obj, nullptr);
    EXPECT_EQ(error_obj->find("status_code")->as_string(), "child_reported_error");
    EXPECT_EQ(error_obj->find("message")->as_string(), res.error_message);
}

// ============================================================================
// 7. CLI Integration with OutputFormat::Json Tests
// ============================================================================

TEST(ExperimentReportingTest, RunsProcessCreationExperimentViaCLIWithJsonFormat) {
    // 10 (Experiments), 1 (Process Creation), 5 (Return), 13 (Exit)
    std::istringstream in("10\n1\n5\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out, oscope::OutputFormat::Json);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();

    // Verify stdout is a JSON array and contains no menu/prompt/exit text
    ASSERT_FALSE(s.empty());
    EXPECT_EQ(s.front(), '[');
    EXPECT_EQ(s.find("OScope - Operating Systems Learning Toolkit"), std::string::npos);
    EXPECT_EQ(s.find("Enter your choice:"), std::string::npos);
    EXPECT_EQ(s.find("Exiting OScope. Goodbye!"), std::string::npos);

    // Verify JSON structure output
    EXPECT_NE(s.find("\"schema_version\": \"1.0.0\""), std::string::npos);
    EXPECT_NE(s.find("\"experiment\": \"process_creation\""), std::string::npos);
    EXPECT_NE(s.find("\"status\": \"success\""), std::string::npos);
    EXPECT_NE(s.find("\"child_exit_code\": 42"), std::string::npos);
}

TEST(ExperimentReportingTest, RunsThreadCreationExperimentViaCLIWithJsonFormat) {
    // 10 (Experiments), 2 (Thread Creation), 5 (Return), 13 (Exit)
    std::istringstream in("10\n2\n5\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out, oscope::OutputFormat::Json);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();

    ASSERT_FALSE(s.empty());
    EXPECT_EQ(s.front(), '[');
    EXPECT_EQ(s.find("OScope - Operating Systems Learning Toolkit"), std::string::npos);
    EXPECT_EQ(s.find("Enter your choice:"), std::string::npos);

    EXPECT_NE(s.find("\"schema_version\": \"1.0.0\""), std::string::npos);
    EXPECT_NE(s.find("\"experiment\": \"thread_creation\""), std::string::npos);
    EXPECT_NE(s.find("\"status\": \"success\""), std::string::npos);
    EXPECT_NE(s.find("\"requested_threads\": 4"), std::string::npos);
    EXPECT_NE(s.find("\"completed_threads\": 4"), std::string::npos);
}

TEST(ExperimentReportingTest, RunsSynchronizationExperimentViaCLIWithJsonFormat) {
    // 10 (Experiments), 3 (Thread Synchronization), 5 (Return), 13 (Exit)
    std::istringstream in("10\n3\n5\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out, oscope::OutputFormat::Json);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();

    ASSERT_FALSE(s.empty());
    EXPECT_EQ(s.front(), '[');
    EXPECT_EQ(s.find("OScope - Operating Systems Learning Toolkit"), std::string::npos);
    EXPECT_EQ(s.find("Enter your choice:"), std::string::npos);

    EXPECT_NE(s.find("\"schema_version\": \"1.0.0\""), std::string::npos);
    EXPECT_NE(s.find("\"experiment\": \"thread_synchronization\""), std::string::npos);
    EXPECT_NE(s.find("\"status\": \"success\""), std::string::npos);
    EXPECT_NE(s.find("\"counter_match\": true"), std::string::npos);
    EXPECT_NE(s.find("\"expected_counter\": 40000"), std::string::npos);
}

TEST(ExperimentReportingTest, RunsPipeIpcExperimentViaCLIWithJsonFormat) {
    // 10 (Experiments), 4 (Pipe-based IPC), 5 (Return), 13 (Exit)
    std::istringstream in("10\n4\n5\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out, oscope::OutputFormat::Json);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();

    ASSERT_FALSE(s.empty());
    EXPECT_EQ(s.front(), '[');
    EXPECT_EQ(s.find("OScope - Operating Systems Learning Toolkit"), std::string::npos);
    EXPECT_EQ(s.find("Enter your choice:"), std::string::npos);

    EXPECT_NE(s.find("\"schema_version\": \"1.0.0\""), std::string::npos);
    EXPECT_NE(s.find("\"experiment\": \"pipe_ipc\""), std::string::npos);
    EXPECT_NE(s.find("\"status\": \"success\""), std::string::npos);
    EXPECT_NE(s.find("\"direction\": \"child_to_parent\""), std::string::npos);
    EXPECT_NE(s.find("\"messages_match\": true"), std::string::npos);
}

TEST(ExperimentReportingTest, DirectDisplayFunctionWithJsonFormatOutputsValidJson) {
    ProcessExperimentResult res;
    res.status = ProcessExperimentStatus::Success;
    res.parent_pid = 777;
    res.child_pid = 888;
    res.exited_normally = true;
    res.exit_code = 42;
    res.message = "OK";

    std::ostringstream out;
    oscope::display_process_experiment_result(out, res, oscope::OutputFormat::Json);

    const std::string s = out.str();
    EXPECT_NE(s.find("\"schema_version\": \"1.0.0\""), std::string::npos);
    EXPECT_NE(s.find("\"parent_pid\": 777"), std::string::npos);
    EXPECT_NE(s.find("\"child_pid\": 888"), std::string::npos);
    EXPECT_NE(s.find("\"child_exit_code\": 42"), std::string::npos);
}

// ============================================================================
// 8. End-to-End Executable Regression Tests
// ============================================================================

#ifdef OSCOPE_EXECUTABLE_PATH

namespace {

std::string run_executable_e2e(const std::string& input, int& exit_code) {
    std::string cmd = "printf '" + input + "' | \"" + std::string(OSCOPE_EXECUTABLE_PATH) + "\" --json";
    std::array<char, 512> buffer;
    std::string output;

    FILE* pipe = popen(cmd.c_str(), "r");
    if (!pipe) {
        exit_code = -1;
        return "";
    }
    while (fgets(buffer.data(), buffer.size(), pipe) != nullptr) {
        output += buffer.data();
    }
    int status = pclose(pipe);
    exit_code = (status != -1 && WIFEXITED(status)) ? WEXITSTATUS(status) : -1;
    return output;
}

int run_shell_command(const std::string& cmd) {
    int status = std::system(cmd.c_str());
    return (status != -1 && WIFEXITED(status)) ? WEXITSTATUS(status) : -1;
}

} // namespace

TEST(ExperimentReportingEndToEndTest, CompleteExecutableOutputsValidJsonArrayWithAllFourExperiments) {
    int exit_code = -1;
    // 10 (Experiments), 1 (Process), 2 (Thread), 3 (Sync), 4 (IPC), 5 (Return), 13 (Exit)
    std::string stdout_output = run_executable_e2e("10\\n1\\n2\\n3\\n4\\n5\\n11\\n", exit_code);

    EXPECT_EQ(exit_code, 0);
    ASSERT_FALSE(stdout_output.empty());

    // Verify stdout contains ONLY valid JSON and no interactive UI artifacts
    EXPECT_EQ(stdout_output.front(), '[');
    EXPECT_EQ(stdout_output.find("========================================"), std::string::npos);
    EXPECT_EQ(stdout_output.find("CPU Scheduling & Paging Platform"), std::string::npos);
    EXPECT_EQ(stdout_output.find("Enter your choice:"), std::string::npos);
    EXPECT_EQ(stdout_output.find("Goodbye!"), std::string::npos);

    // Verify parsing with python3 -c
    std::string py_cmd =
        "printf '10\\n1\\n2\\n3\\n4\\n5\\n11\\n' | \"" + std::string(OSCOPE_EXECUTABLE_PATH) +
        "\" --json | python3 -c \"import json, sys; data = json.load(sys.stdin); "
        "assert isinstance(data, list); assert len(data) == 4; "
        "exps = [d['experiment'] for d in data]; "
        "assert exps == ['process_creation', 'thread_creation', 'thread_synchronization', 'pipe_ipc']; "
        "assert all(d['schema_version'] == '1.0.0' for d in data); "
        "assert all(d['status'] == 'success' for d in data)\"";

    EXPECT_EQ(run_shell_command(py_cmd), 0);
}

TEST(ExperimentReportingEndToEndTest, EmptySessionOutputsValidEmptyJsonArray) {
    int exit_code = -1;
    // 13 (Exit immediately)
    std::string stdout_output = run_executable_e2e("11\\n", exit_code);

    EXPECT_EQ(exit_code, 0);
    ASSERT_FALSE(stdout_output.empty());
    EXPECT_EQ(stdout_output.find("========================================"), std::string::npos);
    EXPECT_EQ(stdout_output.find("CPU Scheduling & Paging Platform"), std::string::npos);
    EXPECT_EQ(stdout_output.find("Enter your choice:"), std::string::npos);

    std::string py_cmd =
        "printf '11\\n' | \"" + std::string(OSCOPE_EXECUTABLE_PATH) +
        "\" --json | python3 -c \"import json, sys; data = json.load(sys.stdin); assert isinstance(data, list); assert len(data) == 0\"";

    EXPECT_EQ(run_shell_command(py_cmd), 0);
}

TEST(ExperimentReportingEndToEndTest, SingleExperimentWithSubmenuReturnOutputsValidJsonArray) {
    int exit_code = -1;
    // 10 (Experiments), 1 (Process Creation), 5 (Return to main), 13 (Exit)
    std::string stdout_output = run_executable_e2e("10\\n1\\n5\\n11\\n", exit_code);

    EXPECT_EQ(exit_code, 0);
    ASSERT_FALSE(stdout_output.empty());
    EXPECT_EQ(stdout_output.find("========================================"), std::string::npos);
    EXPECT_EQ(stdout_output.find("CPU Scheduling & Paging Platform"), std::string::npos);
    EXPECT_EQ(stdout_output.find("Enter your choice:"), std::string::npos);

    std::string py_cmd =
        "printf '10\\n1\\n5\\n11\\n' | \"" + std::string(OSCOPE_EXECUTABLE_PATH) +
        "\" --json | python3 -c \"import json, sys; data = json.load(sys.stdin); "
        "assert isinstance(data, list); assert len(data) == 1; "
        "assert data[0]['experiment'] == 'process_creation'; "
        "assert data[0]['status'] == 'success'\"";

    EXPECT_EQ(run_shell_command(py_cmd), 0);
}

#endif

} // namespace
