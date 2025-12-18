# Spec Workflow Command

Start the spec-driven development workflow for a new feature.

## Instructions

You are entering **spec mode** for the feature: $ARGUMENTS

Follow the spec-driven workflow defined in CLAUDE.md:

### Step 1: Requirements Interview

Interview the user to gather requirements. Ask about:
1. Primary purpose and goals
2. Specific capabilities needed (use AskUserQuestion with options when appropriate)
3. Edge cases and error scenarios
4. Integration with existing system components
5. Any constraints or preferences

After gathering requirements, write `.kiro/specs/$ARGUMENTS/requirements.md` using the template format:
- Introduction and glossary
- Numbered requirements with user stories
- Acceptance criteria in WHEN/THEN format

Ask the user to confirm requirements before proceeding.

### Step 2: Design Interview

Interview the user about design decisions:
1. Architecture approach (show options if multiple valid approaches)
2. Data models and schemas
3. Error handling strategy
4. Identify correctness properties that bridge requirements to tests

Write `.kiro/specs/$ARGUMENTS/design.md` with:
- Architecture diagram (Mermaid)
- Components and interfaces
- Data models
- Correctness properties (numbered, linked to requirements)
- Error handling
- Testing strategy

Ask the user to confirm design before proceeding.

### Step 3: Generate Tasks

Generate `.kiro/specs/$ARGUMENTS/tasks.md`:
- Break down implementation into phases
- Create checkbox tasks linked to requirements and properties
- Identify which tasks can run in parallel
- Present task list for user approval

### Step 4: Implementation

After tasks are approved:
1. Identify independent task groups
2. Offer to spawn parallel agents for implementation
3. Track progress using TodoWrite
4. Handle any spec drift per CLAUDE.md guidelines

## Important

- Use AskUserQuestion for multi-choice decisions during interviews
- Write spec files incrementally (don't wait until end)
- Get explicit user approval before moving between phases
- If $ARGUMENTS is empty, ask the user for a feature name first
