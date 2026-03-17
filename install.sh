#!/usr/bin/env bash
set -euo pipefail

# SprintPlanner installer — copies pipeline into ~/.claude/
# Usage: ./install.sh [--uninstall] [--version]

VERSION="1.3.2"

CLAUDE_DIR="$HOME/.claude"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="$CLAUDE_DIR/backups/sprint-planner-$(date +%Y%m%d-%H%M%S)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# --- Version ---
if [[ "${1:-}" == "--version" || "${1:-}" == "-v" ]]; then
  echo "SprintPlanner v${VERSION}"
  exit 0
fi

# --- Uninstall ---
if [[ "${1:-}" == "--uninstall" ]]; then
  echo -e "${YELLOW}Uninstalling SprintPlanner...${NC}"

  # Remove skills
  for skill_dir in "$SCRIPT_DIR"/skills/*/; do
    skill_name=$(basename "$skill_dir")
    target="$CLAUDE_DIR/skills/$skill_name"
    if [[ -d "$target" ]]; then
      rm -rf "$target"
      echo "  Removed skill: $skill_name"
    fi
  done

  # Remove agents
  for agent_file in "$SCRIPT_DIR"/agents/*.md; do
    agent_name=$(basename "$agent_file")
    target="$CLAUDE_DIR/agents/$agent_name"
    if [[ -f "$target" ]]; then
      rm "$target"
      echo "  Removed agent: $agent_name"
    fi
  done

  # Remove hooks
  for hook_file in "$SCRIPT_DIR"/hooks/*.py; do
    hook_name=$(basename "$hook_file")
    target="$CLAUDE_DIR/hooks/$hook_name"
    if [[ -f "$target" ]]; then
      rm "$target"
      echo "  Removed hook: $hook_name"
    fi
  done

  echo -e "${YELLOW}Note: settings.json hook entry not removed (edit manually if needed).${NC}"
  echo -e "${GREEN}Uninstall complete.${NC}"
  exit 0
fi

# --- Install ---
echo -e "${GREEN}Installing SprintPlanner into $CLAUDE_DIR${NC}"
echo ""

# Check Python + PyYAML
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}Error: python3 is required but not found.${NC}"
  exit 1
fi

if ! python3 -c "import yaml" 2>/dev/null; then
  echo -e "${YELLOW}PyYAML not found. Installing...${NC}"
  pip3 install pyyaml --quiet
fi

# Create directories
mkdir -p "$CLAUDE_DIR"/{skills,agents,hooks,backups}

# Backup existing files that would be overwritten
backup_needed=false
for skill_dir in "$SCRIPT_DIR"/skills/*/; do
  skill_name=$(basename "$skill_dir")
  if [[ -d "$CLAUDE_DIR/skills/$skill_name" ]]; then
    backup_needed=true
    break
  fi
done

if [[ "$backup_needed" == true ]]; then
  echo -e "${YELLOW}Backing up existing files to $BACKUP_DIR${NC}"
  mkdir -p "$BACKUP_DIR"/{skills,agents,hooks}

  for skill_dir in "$SCRIPT_DIR"/skills/*/; do
    skill_name=$(basename "$skill_dir")
    if [[ -d "$CLAUDE_DIR/skills/$skill_name" ]]; then
      cp -r "$CLAUDE_DIR/skills/$skill_name" "$BACKUP_DIR/skills/"
    fi
  done

  for agent_file in "$SCRIPT_DIR"/agents/*.md; do
    agent_name=$(basename "$agent_file")
    if [[ -f "$CLAUDE_DIR/agents/$agent_name" ]]; then
      cp "$CLAUDE_DIR/agents/$agent_name" "$BACKUP_DIR/agents/"
    fi
  done

  for hook_file in "$SCRIPT_DIR"/hooks/*.py; do
    hook_name=$(basename "$hook_file")
    if [[ -f "$CLAUDE_DIR/hooks/$hook_name" ]]; then
      cp "$CLAUDE_DIR/hooks/$hook_name" "$BACKUP_DIR/hooks/"
    fi
  done
fi

# Copy skills
echo "Installing skills..."
for skill_dir in "$SCRIPT_DIR"/skills/*/; do
  skill_name=$(basename "$skill_dir")
  mkdir -p "$CLAUDE_DIR/skills/$skill_name"
  cp "$skill_dir"SKILL.md "$CLAUDE_DIR/skills/$skill_name/SKILL.md"
  echo "  + $skill_name"
done

# Copy agents
echo "Installing agents..."
for agent_file in "$SCRIPT_DIR"/agents/*.md; do
  agent_name=$(basename "$agent_file")
  cp "$agent_file" "$CLAUDE_DIR/agents/$agent_name"
  echo "  + $agent_name"
done

# Copy hooks
echo "Installing hooks..."
for hook_file in "$SCRIPT_DIR"/hooks/*.py; do
  hook_name=$(basename "$hook_file")
  cp "$hook_file" "$CLAUDE_DIR/hooks/$hook_name"
  chmod +x "$CLAUDE_DIR/hooks/$hook_name"
  echo "  + $hook_name"
done

# Copy config templates (don't overwrite existing user config)
if [[ ! -f "$CLAUDE_DIR/jira_config.yaml" ]]; then
  cp "$SCRIPT_DIR/jira_config.template.yaml" "$CLAUDE_DIR/jira_config.yaml"
  echo "  + jira_config.yaml (template — edit with your Jira project details)"
fi
if [[ ! -f "$CLAUDE_DIR/personal-project-config.md" ]]; then
  cp "$SCRIPT_DIR/personal-project-config.template.md" "$CLAUDE_DIR/personal-project-config.md"
  echo "  + personal-project-config.md (template — edit with your team details)"
fi
echo ""

# Configure settings.json hook (PostToolUse on Write)
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
HOOK_CMD="python3 $CLAUDE_DIR/hooks/validate_artifact.py"

if [[ -f "$SETTINGS_FILE" ]]; then
  # Check if hook already exists
  if python3 -c "
import json, sys
with open('$SETTINGS_FILE') as f:
    data = json.load(f)
hooks = data.get('hooks', {}).get('PostToolUse', [])
for h in hooks:
    if h.get('matcher') == 'Write':
        for sub in h.get('hooks', []):
            if 'validate_artifact' in sub.get('command', ''):
                sys.exit(0)
sys.exit(1)
" 2>/dev/null; then
    echo -e "${GREEN}Hook already configured in settings.json${NC}"
  else
    echo -e "${YELLOW}Adding PostToolUse hook to settings.json...${NC}"
    python3 -c "
import json
with open('$SETTINGS_FILE') as f:
    data = json.load(f)
if 'hooks' not in data:
    data['hooks'] = {}
if 'PostToolUse' not in data['hooks']:
    data['hooks']['PostToolUse'] = []
# Check if Write matcher exists
write_hook = None
for h in data['hooks']['PostToolUse']:
    if h.get('matcher') == 'Write':
        write_hook = h
        break
if not write_hook:
    data['hooks']['PostToolUse'].append({
        'matcher': 'Write',
        'hooks': [{
            'type': 'command',
            'command': '$HOOK_CMD',
            'timeout': 30
        }]
    })
else:
    write_hook.setdefault('hooks', []).append({
        'type': 'command',
        'command': '$HOOK_CMD',
        'timeout': 30
    })
with open('$SETTINGS_FILE', 'w') as f:
    json.dump(data, f, indent=2)
print('  Hook added.')
"
  fi
else
  echo "Creating settings.json with hook..."
  cat > "$SETTINGS_FILE" << 'SETTINGS_EOF'
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 HOOK_PATH/validate_artifact.py",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
SETTINGS_EOF
  # Replace placeholder with actual path (cross-platform sed)
  if [[ "$(uname)" == "Darwin" ]]; then
    sed -i '' "s|HOOK_PATH|$CLAUDE_DIR/hooks|g" "$SETTINGS_FILE"
  else
    sed -i "s|HOOK_PATH|$CLAUDE_DIR/hooks|g" "$SETTINGS_FILE"
  fi
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  SprintPlanner v${VERSION} installed successfully  ${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Installed:"
echo "  - $(ls "$SCRIPT_DIR"/skills/ | wc -l | tr -d ' ') skills"
echo "  - $(ls "$SCRIPT_DIR"/agents/*.md | wc -l | tr -d ' ') agents"
echo "  - $(ls "$SCRIPT_DIR"/hooks/*.py | wc -l | tr -d ' ') hooks"
echo "  - PostToolUse validation hook"

# Check optional MCP dependencies
echo ""
echo "Optional MCP servers (checked at runtime, not required for local repos):"

# GitHub MCP — needed for remote repo scanning
if claude mcp list 2>/dev/null | grep -qi "github"; then
  echo -e "  ${GREEN}[installed]${NC} GitHub MCP — remote repo scanning"
else
  echo -e "  ${YELLOW}[not found]${NC} GitHub MCP — needed for scanning GitHub repos without cloning"
  echo "              Install: claude mcp add github -- npx -y @anthropic-ai/github-mcp"
fi

# Figma MCP — needed for design analysis
if claude mcp list 2>/dev/null | grep -qi "figma"; then
  echo -e "  ${GREEN}[installed]${NC} Figma MCP — design analysis"
else
  echo -e "  ${YELLOW}[not found]${NC} Figma MCP — needed for analyzing Figma designs"
  echo "              Install: claude mcp add figma -- npx -y @anthropic-ai/figma-mcp"
fi

echo ""
echo "Usage: Open Claude Code in any project and run:"
echo "  /run-pipeline"
echo ""
echo "To uninstall:"
echo "  ./install.sh --uninstall"
