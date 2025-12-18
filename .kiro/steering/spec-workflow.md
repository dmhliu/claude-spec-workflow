# Spec-Driven Workflow - Detailed Rules

This document provides detailed rules for maintaining spec consistency during development.

## Spec File Consistency

### When to Update Specs

| Event | Action |
|-------|--------|
| Implementation reveals missing requirement | Add to requirements.md, update design.md |
| Bug found during testing | Check if requirement was missing, update if needed |
| User requests change during implementation | Pause, update spec, get approval, resume |
| Correctness property cannot be satisfied | Major drift - full spec revision |

### Spec Update Process

1. **Identify the change scope**
   - Single requirement affected → Minor update
   - Multiple requirements affected → Medium update
   - Architecture affected → Major update (requires user approval)

2. **Update in order**: requirements.md → design.md → tasks.md

3. **Add revision notes**:
   ```markdown
   ## Revision History
   - YYYY-MM-DD: <description of change and rationale>
   ```

4. **Re-validate correctness properties** after any design change

## Correctness Properties

### What Makes a Good Property

A correctness property should be:
- **Testable**: Can be verified with automated tests
- **Linked**: References specific requirement(s)
- **Universal**: Uses "for any" language (property-based)
- **Precise**: No ambiguity in expected behavior

### Property Format

```markdown
**Property N: <Short name>**
*For any* <input/condition>, <the system should> <expected behavior>
**Validates: Requirements X.Y, Z.W**
```

### Property Categories

1. **Input validation** - What inputs are accepted/rejected
2. **Output format** - What the response looks like
3. **State transitions** - How system state changes
4. **Error handling** - How errors are reported
5. **Invariants** - What's always true

## Parallel Implementation

### Identifying Parallelizable Tasks

Tasks are parallelizable when:
- No shared state mutations
- No file conflicts (different files)
- No dependency ordering (A doesn't need B's output)

### Task Grouping Strategy

```
Group 1: Infrastructure/Configuration
  - External system setup (NetSuite saved searches, etc.)
  - Configuration files
  - Environment variables

Group 2: Core Implementation
  - Handler modules
  - Business logic
  - Data models

Group 3: Integration
  - Tool registration
  - Routing changes
  - API endpoint updates

Group 4: Testing
  - Unit tests
  - Property-based tests
  - Integration tests
```

### Agent Coordination

When spawning parallel agents:

1. **Pass full context**: Include paths to all three spec files
2. **Assign specific tasks**: List exact tasks from tasks.md
3. **Define boundaries**: Specify which files the agent should modify
4. **Set completion criteria**: How to know when done

**Agent prompt template:**
```
Implement the following tasks from .kiro/specs/<feature>/tasks.md:
- [ ] Task 1
- [ ] Task 2

Context:
- Read requirements: .kiro/specs/<feature>/requirements.md
- Read design: .kiro/specs/<feature>/design.md

Boundaries:
- Only modify files in: <list of files>
- Do not modify: <protected files>

When complete:
- Mark tasks as done in tasks.md
- Report any spec drift encountered
```

## Interview Techniques

### Requirements Interview

**Opening questions:**
- "What problem does this feature solve?"
- "Who will use this feature?"
- "What should happen when X?"

**Probing questions:**
- "What if the user provides invalid input?"
- "What happens if the external service is unavailable?"
- "How should this interact with existing feature Y?"

**Confirmation:**
- Summarize understanding
- List any assumptions made
- Ask "Is there anything I'm missing?"

### Design Interview

**Architecture questions:**
- "Should this be a new component or extend existing?"
- "What data needs to flow between components?"
- "What are the failure modes?"

**Trade-off questions:**
- Present 2-3 options with pros/cons
- Ask user preference
- Document rationale for chosen approach

**Validation questions:**
- "Does this design satisfy requirement X?"
- "Can you think of a case where this would break?"

## Quality Gates

### Before Exiting Requirements Phase
- [ ] All user stories have acceptance criteria
- [ ] Edge cases are documented
- [ ] User has explicitly approved requirements

### Before Exiting Design Phase
- [ ] Architecture diagram exists
- [ ] All data models defined
- [ ] Correctness properties cover all requirements
- [ ] Error handling strategy documented
- [ ] User has explicitly approved design

### Before Starting Implementation
- [ ] Tasks are broken into parallelizable groups
- [ ] Each task links to requirements/properties
- [ ] User has approved task breakdown

### Before Marking Feature Complete
- [ ] All tasks checked off
- [ ] Tests exist for all correctness properties
- [ ] Spec drift has been reconciled
- [ ] User has verified implementation
