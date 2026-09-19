# OScope — Data Model and Result Schema

## 1. Purpose

This document defines the initial conceptual data model for workloads, events, metrics, and experiment results.

## 2. Workload

A workload is a deterministic description of an experiment's input.

Examples:

- process list;
- page reference string;
- memory requests;
- disk request queue;
- resource matrices.

## 3. Event

```text
Event
- event_id
- type
- simulation_time or relative_time
- actor
- payload
```

The timestamp field must identify whether it is simulated time or real elapsed time.

## 4. Metrics

```text
Metric
- name
- value
- unit
- source
- description
```

## 5. Experiment Metadata

```text
ExperimentMetadata
- experiment_id
- module
- algorithm
- mode
- created_at
- oscope_version
- seed
- environment
```

## 6. Result

```text
{
  "schema_version": "1.0",
  "experiment": {},
  "workload": {},
  "events": [],
  "metrics": {},
  "status": "success",
  "errors": []
}
```

## 7. Reproducibility Fields

For deterministic simulations:

- input;
- configuration;
- seed if applicable;
- algorithm version.

For Linux experiments:

- kernel/environment information where available;
- compiler/build version;
- host resource context where relevant.

## 8. Naming

Names should be stable, machine-readable, and documented. Avoid using presentation-only labels as schema identifiers.

## 9. Compatibility

Schema changes shall prefer additive evolution. Breaking changes require a version change and ADR.
