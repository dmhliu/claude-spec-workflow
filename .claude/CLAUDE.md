# Claude Code Spec-Driven Workflow

This project uses a spec-driven development workflow inspired by Kiro. Before implementing new features, Claude should guide the user through creating specifications that ensure thorough design and traceable implementation.

## Workflow Overview

```
Request → Detect → [Spec Mode] → Requirements → Design → Tasks → Implement (Parallel)
```

## When to Enter Spec Mode

### Auto-Detection Heuristics

**Score the request using these signals:**

| Signal | Score |
|--------|-------|
| Keywords: "add", "implement", "create", "build", "new feature" | +2 |
| Multiple components/files likely affected | +2 |
| Requires new data models, schemas, or APIs | +2 |
| Involves external integrations | +2 |
| User uncertain about approach ("how should we...", "what's the best way") | +1 |
| Cross-cutting concerns (auth, logging, error handling) | +1 |

| Signal | Score |
|--------|-------|
| Keywords: "fix", "tweak", "update", "change" (existing) | -2 |
| Single file or known location mentioned | -2 |
| Bug fix with clear reproduction | -2 |
| Documentation/comment only | -3 |
| Refactoring (same behavior) | -1 |

**Decision:**
- Score ≥ 3: Suggest spec mode with: "This looks like a new feature. Would you like to use the spec workflow to plan it first?"
- Score 1-2: Ask: "This could benefit from spec planning. Your preference?"
- Score ≤ 0: Proceed normally without spec mode

### User Can Always Override
- User says "use spec workflow" or runs `/spec` → Enter spec mode
- User says "just do it" or "skip spec" → Proceed without spec

## Spec Mode Phases

### Phase 1: Requirements Interview

**Goal:** Capture user stories and acceptance criteria through conversation.

**Interview approach:**
1. Ask about the primary purpose/goal
2. Ask about specific capabilities needed
3. Ask about edge cases and error handling
4. Ask about integration points with existing system
5. Summarize and confirm understanding

**Output:** Write `.kiro/specs/<feature-name>/requirements.md`

**Format:**
```markdown
# <Feature Name> Requirements

## Introduction
<Brief description and context>

## Glossary
<Key terms defined>

## Requirements

### Requirement 1
**User Story:** As a <role>, I want <capability>, so that <benefit>.

#### Acceptance Criteria
1. WHEN <condition>, THE system SHALL <behavior>
2. ...
```

### Phase 2: Design Interview

**Goal:** Define architecture, data models, and correctness properties.

**Interview approach:**
1. Discuss high-level architecture and component integration
2. Define data models (request/response structures)
3. Discuss error handling strategy
4. Identify correctness properties (formal statements that bridge requirements to tests)
5. Review and confirm design decisions

**Output:** Write `.kiro/specs/<feature-name>/design.md`

**Key sections:**
- Architecture (with Mermaid diagrams)
- Components and Interfaces
- Data Models
- Correctness Properties (numbered, linked to requirements)
- Error Handling
- Testing Strategy

### Phase 3: Tasks Review

**Goal:** Create implementation checklist with clear task breakdown.

**Approach:**
1. Generate tasks from design document
2. Group by phase (infrastructure, implementation, testing, deployment)
3. Link tasks to requirements and properties
4. Identify parallelizable task groups
5. Present to user for approval

**Output:** Write `.kiro/specs/<feature-name>/tasks.md`

**Format:**
```markdown
# <Feature Name> - Implementation Tasks

## Phase 1: <Phase Name>
- [ ] Task description
  **Validates: Requirements X.Y, Property Z**
```

### Phase 4: Parallel Implementation

**After tasks.md is approved:**

1. Identify independent task groups that can run in parallel
2. Spawn Task agents for each group:
   - Use `subagent_type: "general-purpose"`
   - Pass the spec files as context
   - Assign specific tasks from tasks.md
3. Main thread coordinates and handles integration tasks
4. Mark tasks complete in tasks.md as they finish

**Example parallel groups:**
- Infrastructure/configuration tasks
- Core implementation tasks
- Test creation tasks

## Spec Drift Handling

### During Implementation

**Minor drift** (variable names, small adjustments):
- Note in tasks.md under the task
- Continue implementation

**Medium drift** (new parameter, additional error case):
- Update relevant section in design.md
- Add note: `## Design Revision - <date>: <description>`
- Continue implementation

**Major drift** (architecture change, requirement invalidated):
1. Stop current implementation
2. Mark task as `blocked: design change required`
3. Update design.md with revision section explaining what changed and why
4. Update affected correctness properties
5. Regenerate affected tasks in tasks.md
6. Ask user to approve changes before resuming

**Triggers for "Major" drift:**
- Implementation would invalidate a correctness property
- New requirement contradicts existing requirement
- Interface change affects multiple components
- User explicitly says current approach won't work

## File Locations

```
.kiro/
├── specs/
│   └── <feature-name>/
│       ├── requirements.md
│       ├── design.md
│       └── tasks.md
├── steering/
│   └── spec-workflow.md (detailed rules)
└── templates/
    ├── requirements.template.md
    ├── design.template.md
    └── tasks.template.md
```

## Integration with Claude Code Tools

- **TodoWrite**: Track current phase and task progress
- **AskUserQuestion**: Conduct interviews during requirements/design phases
- **Task (agents)**: Spawn parallel implementation agents
- **Read/Write**: Create and update spec files
- **Plan mode**: Can be used during design phase for complex architectures

## Quick Reference

| Phase | Key Questions | Output |
|-------|--------------|--------|
| Requirements | What? Who? Why? Edge cases? | requirements.md |
| Design | How? What components? What data? What properties? | design.md |
| Tasks | What steps? What order? What's parallel? | tasks.md |
| Implement | Execute tasks, handle drift, coordinate agents | Code changes |
