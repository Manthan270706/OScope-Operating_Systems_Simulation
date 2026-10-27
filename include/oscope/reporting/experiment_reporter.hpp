#ifndef OSCOPE_REPORTING_EXPERIMENT_REPORTER_HPP
#define OSCOPE_REPORTING_EXPERIMENT_REPORTER_HPP

#include <string>
#include <string_view>

#include "oscope/deadlock/deadlock_types.hpp"
#include "oscope/disk/disk_types.hpp"
#include "oscope/experiments/pipe_ipc_experiment.hpp"
#include "oscope/experiments/process_experiment.hpp"
#include "oscope/experiments/synchronization_experiment.hpp"
#include "oscope/experiments/thread_experiment.hpp"
#include "oscope/reporting/json_value.hpp"

namespace oscope::reporting {

/// Documented version of the OScope Experiment JSON Schema.
inline constexpr std::string_view kSchemaVersion = "1.0.0";

/// Standard experiment category identifier for Linux/POSIX experiments.
inline constexpr std::string_view kLinuxExperimentCategory = "linux_posix_experiment";

/// Category identifier for Deadlock Management simulations.
inline constexpr std::string_view kDeadlockCategory = "deadlock_management";

/// Category identifier for Disk Scheduling simulations.
inline constexpr std::string_view kDiskCategory = "disk_scheduling";

/**
 * @brief Converts a ProcessExperimentResult into a structured JsonValue object.
 */
JsonValue to_json(const experiments::ProcessExperimentResult& result);

/**
 * @brief Converts a ThreadExperimentResult into a structured JsonValue object.
 */
JsonValue to_json(const experiments::ThreadExperimentResult& result);

/**
 * @brief Converts a SynchronizationExperimentResult into a structured JsonValue object.
 */
JsonValue to_json(const experiments::SynchronizationExperimentResult& result);

/**
 * @brief Converts a PipeIpcExperimentResult into a structured JsonValue object.
 */
JsonValue to_json(const experiments::PipeIpcExperimentResult& result);

/**
 * @brief Converts a Banker's SafetyResult into a structured JsonValue object.
 */
JsonValue to_json(const deadlock::SafetyResult& result, const deadlock::DeadlockState& state);

/**
 * @brief Converts a Banker's ResourceRequestResult into a structured JsonValue object.
 */
JsonValue to_json(const deadlock::ResourceRequestResult& result);

/**
 * @brief Converts a Deadlock DetectionResult into a structured JsonValue object.
 */
JsonValue to_json(const deadlock::DetectionResult& result);

/**
 * @brief Converts a DiskSchedulingResult into a structured JsonValue object.
 */
JsonValue to_json(const disk::DiskSchedulingResult& result);

/**
 * @brief Converts a DiskComparisonResult into a structured JsonValue object.
 */
JsonValue to_json(const disk::DiskComparisonResult& result);

/**
 * @brief Serializes a ProcessExperimentResult directly to a JSON string.
 */
std::string serialize_result(const experiments::ProcessExperimentResult& result, bool pretty = true);

/**
 * @brief Serializes a ThreadExperimentResult directly to a JSON string.
 */
std::string serialize_result(const experiments::ThreadExperimentResult& result, bool pretty = true);

/**
 * @brief Serializes a SynchronizationExperimentResult directly to a JSON string.
 */
std::string serialize_result(const experiments::SynchronizationExperimentResult& result, bool pretty = true);

/**
 * @brief Serializes a PipeIpcExperimentResult directly to a JSON string.
 */
std::string serialize_result(const experiments::PipeIpcExperimentResult& result, bool pretty = true);

/**
 * @brief Serializes a Banker's SafetyResult directly to a JSON string.
 */
std::string serialize_result(const deadlock::SafetyResult& result, const deadlock::DeadlockState& state, bool pretty = true);

/**
 * @brief Serializes a Banker's ResourceRequestResult directly to a JSON string.
 */
std::string serialize_result(const deadlock::ResourceRequestResult& result, bool pretty = true);

/**
 * @brief Serializes a Deadlock DetectionResult directly to a JSON string.
 */
std::string serialize_result(const deadlock::DetectionResult& result, bool pretty = true);

/**
 * @brief Serializes a DiskSchedulingResult directly to a JSON string.
 */
std::string serialize_result(const disk::DiskSchedulingResult& result, bool pretty = true);

/**
 * @brief Serializes a DiskComparisonResult directly to a JSON string.
 */
std::string serialize_result(const disk::DiskComparisonResult& result, bool pretty = true);

} // namespace oscope::reporting

#endif // OSCOPE_REPORTING_EXPERIMENT_REPORTER_HPP
