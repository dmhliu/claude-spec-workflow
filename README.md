# Claude Spec Workflow

A spec-driven development workflow for Claude Code, inspired by [Kiro](https://kiro.dev).

## Why?

Kiro's best feature is its **spec-driven workflow**: Requirements → Design → Tasks → Implementation. This ensures:

- **Thorough planning** before coding
- **Traceable implementation** (requirements → properties → tests)
- **Reduced rework** from missed requirements
- **Better collaboration** through explicit specs

Claude Code has strengths Kiro lacks:
- **Large context window** with automatic summarization
- **Parallel agents** for concurrent implementation
- **Flexible tooling** (TodoWrite, AskUserQuestion, Task agents)

This project brings Kiro's workflow discipline to Claude Code's capabilities.

## Installation

### Option 1: Clone and Install

```bash
git clone https://github.com/your-repo/claude-spec-workflow.git
cd claude-spec-workflow
./install.sh /path/to/your/project
```

### Option 2: Manual Copy

Copy these directories to your project:
- `.claude/` → Your project's `.claude/`
- `.kiro/steering/` → Your project's `.kiro/steering/`
- `.kiro/templates/` → Your project's `.kiro/templates/`

## Usage

### Explicit Trigger

```
/spec my-new-feature
```

Claude will guide you through:
1. **Requirements interview** → Creates `requirements.md`
2. **Design interview** → Creates `design.md`
3. **Task generation** → Creates `tasks.md`
4. **Parallel implementation** → Spawns agents for independent tasks

### Auto-Detection

When you describe a new feature, Claude will detect it and ask:

> "This looks like a new feature. Would you like to use the spec workflow to plan it first?"

Say yes to enter spec mode, or "just do it" to proceed without specs.

## Workflow Phases

### 1. Requirements Phase

Claude interviews you to capture:
- User stories ("As a X, I want Y, so that Z")
- Acceptance criteria (WHEN/THEN format)
- Edge cases and error handling
- Integration points

Output: `.kiro/specs/<feature>/requirements.md`

### 2. Design Phase

Claude interviews you to define:
- Architecture (with Mermaid diagrams)
- Data models
- Correctness properties (bridge requirements to tests)
- Error handling strategy

Output: `.kiro/specs/<feature>/design.md`

### 3. Tasks Phase

Claude generates:
- Implementation checklist
- Parallel task groups
- Links to requirements and properties

Output: `.kiro/specs/<feature>/tasks.md`

### 4. Implementation Phase

After you approve tasks:
- Claude identifies parallelizable work
- Spawns agents for independent task groups
- Tracks progress via TodoWrite
- Handles spec drift appropriately

## Spec Drift

When implementation reveals design issues:

| Drift Level | Example | Action |
|-------------|---------|--------|
| Minor | Variable name change | Note in tasks.md |
| Medium | New error case | Update design.md section |
| Major | Architecture change | Pause, revise spec, get approval |

## File Structure

```
your-project/
├── .claude/
│   ├── CLAUDE.md              # Steering document (workflow rules)
│   └── commands/
│       └── spec.md            # Slash command
└── .kiro/
    ├── specs/
    │   └── <feature-name>/
    │       ├── requirements.md
    │       ├── design.md
    │       └── tasks.md
    ├── steering/
    │   └── spec-workflow.md   # Detailed workflow rules
    └── templates/
        ├── requirements.template.md
        ├── design.template.md
        └── tasks.template.md
```

## Customization

### Modifying Detection Heuristics

Edit `.claude/CLAUDE.md` to adjust the scoring signals that determine when to suggest spec mode.

### Adding Project-Specific Rules

Add to `.kiro/steering/spec-workflow.md` or create additional steering documents.

### Custom Templates

Modify templates in `.kiro/templates/` to match your project's conventions.

## Comparison with Kiro

| Feature | Kiro | Claude Spec Workflow |
|---------|------|---------------------|
| Spec-driven workflow | ✅ | ✅ |
| Requirements → Design → Tasks | ✅ | ✅ |
| Correctness properties | ✅ | ✅ |
| Large context | ❌ | ✅ |
| Parallel implementation | ❌ | ✅ |
| Flexible tooling | ❌ | ✅ |
| Spec drift handling | Limited | ✅ Explicit rules |

## License

MIT
