# {{FEATURE_NAME}} - Implementation Tasks

## Task Groups

| Group | Description | Parallelizable |
|-------|-------------|----------------|
| Phase 1 | {{Description}} | No (must complete first) |
| Phase 2 | {{Description}} | Yes |
| Phase 3 | {{Description}} | Yes |
| Phase 4 | {{Description}} | No (depends on 2,3) |

## Phase 1: {{Phase Name}} (Sequential)

- [ ] {{Task description}}
  - [ ] {{Subtask if needed}}
  - [ ] {{Subtask if needed}}
  **Validates: Requirements {{X.Y}}, Property {{Z}}**

- [ ] {{Task description}}
  **Validates: Requirements {{X.Y}}**

## Phase 2: {{Phase Name}} (Parallel Group A)

- [ ] {{Task description}}
  **Validates: Requirements {{X.Y}}, Property {{Z}}**

- [ ] {{Task description}}
  **Validates: Requirements {{X.Y}}**

## Phase 3: {{Phase Name}} (Parallel Group B)

- [ ] {{Task description}}
  **Validates: Property {{Z}}**

- [ ] {{Task description}}

## Phase 4: {{Phase Name}} (Sequential - Integration)

- [ ] {{Integration task}}
- [ ] {{Verification task}}

## Implementation Notes

{{Any notes about implementation approach, dependencies, or gotchas}}

## Spec Drift Log

<!--
Log any deviations from the original design here:
- YYYY-MM-DD: [Task X] {{description of change}} - {{minor/medium/major}}
-->

## Completion Checklist

- [ ] All Phase 1 tasks complete
- [ ] All Phase 2 tasks complete
- [ ] All Phase 3 tasks complete
- [ ] All Phase 4 tasks complete
- [ ] All tests passing
- [ ] Spec drift reconciled (design.md updated if needed)
- [ ] User verification complete
