#ifndef OSCOPE_REPORTING_EXPERIMENT_REPORTER_HPP
#define OSCOPE_REPORTING_EXPERIMENT_REPORTER_HPP

#include <string>
#include <string_view>

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

} // namespace oscope::reporting

#endif // OSCOPE_REPORTING_EXPERIMENT_REPORTER_HPP
