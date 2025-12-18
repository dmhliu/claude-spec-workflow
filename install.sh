#!/bin/bash
# Claude Spec Workflow - Install Script
# Installs spec-driven workflow files into the current project

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-.}"

echo "Installing Claude Spec Workflow to: $TARGET_DIR"

# Create directories
mkdir -p "$TARGET_DIR/.claude/commands"
mkdir -p "$TARGET_DIR/.kiro/steering"
mkdir -p "$TARGET_DIR/.kiro/templates"
mkdir -p "$TARGET_DIR/.kiro/specs"

# Copy .claude files
if [ -f "$TARGET_DIR/.claude/CLAUDE.md" ]; then
    echo "Warning: .claude/CLAUDE.md already exists"
    read -p "Overwrite? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Skipping CLAUDE.md"
    else
        cp "$SCRIPT_DIR/.claude/CLAUDE.md" "$TARGET_DIR/.claude/CLAUDE.md"
        echo "Copied: .claude/CLAUDE.md"
    fi
else
    cp "$SCRIPT_DIR/.claude/CLAUDE.md" "$TARGET_DIR/.claude/CLAUDE.md"
    echo "Copied: .claude/CLAUDE.md"
fi

# Copy slash command
cp "$SCRIPT_DIR/.claude/commands/spec.md" "$TARGET_DIR/.claude/commands/spec.md"
echo "Copied: .claude/commands/spec.md"

# Copy .kiro files
cp "$SCRIPT_DIR/.kiro/steering/spec-workflow.md" "$TARGET_DIR/.kiro/steering/spec-workflow.md"
echo "Copied: .kiro/steering/spec-workflow.md"

cp "$SCRIPT_DIR/.kiro/templates/requirements.template.md" "$TARGET_DIR/.kiro/templates/requirements.template.md"
cp "$SCRIPT_DIR/.kiro/templates/design.template.md" "$TARGET_DIR/.kiro/templates/design.template.md"
cp "$SCRIPT_DIR/.kiro/templates/tasks.template.md" "$TARGET_DIR/.kiro/templates/tasks.template.md"
echo "Copied: .kiro/templates/*.template.md"

echo ""
echo "Installation complete!"
echo ""
echo "Usage:"
echo "  1. Start Claude Code in your project"
echo "  2. Run: /spec <feature-name>"
echo "  3. Follow the interview prompts"
echo ""
echo "Or Claude will auto-detect new feature requests and offer spec mode."
