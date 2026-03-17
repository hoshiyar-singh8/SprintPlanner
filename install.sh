#!/usr/bin/env bash
set -euo pipefail

# FeaturePlanner installer — copies pipeline into ~/.claude/
# Usage: ./install.sh [--uninstall] [--update] [--check] [--setup-mcps] [--version]

VERSION="1.4.3"

CLAUDE_DIR="$HOME/.claude"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="$CLAUDE_DIR/backups/sprint-planner-$(date +%Y%m%d-%H%M%S)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# --- Version ---
if [[ "${1:-}" == "--version" || "${1:-}" == "-v" ]]; then
  echo "FeaturePlanner v${VERSION}"
  exit 0
fi

# --- Check for updates ---
if [[ "${1:-}" == "--check" ]]; then
  cd "$SCRIPT_DIR"
  echo "Checking for updates..."
  git fetch origin main --quiet 2>/dev/null || { echo -e "${RED}Failed to fetch from remote.${NC}"; exit 1; }
  LOCAL=$(git rev-parse HEAD)
  REMOTE=$(git rev-parse origin/main)
  if [[ "$LOCAL" == "$REMOTE" ]]; then
    echo -e "${GREEN}You're on the latest version (v${VERSION})${NC}"
  else
    REMOTE_VER=$(git show origin/main:install.sh | grep '^VERSION=' | head -1 | tr -d '"' | cut -d= -f2)
    echo -e "${YELLOW}Update available: v${VERSION} -> v${REMOTE_VER}${NC}"
    echo "  Run: ./install.sh --update"
  fi
  exit 0
fi

# --- Update (git pull + reinstall) ---
if [[ "${1:-}" == "--update" ]]; then
  echo -e "${GREEN}Updating FeaturePlanner...${NC}"
  cd "$SCRIPT_DIR"
  BEFORE=$VERSION
  git pull origin main --quiet || { echo -e "${RED}Failed to pull from remote.${NC}"; exit 1; }
  # Re-read version from the (potentially updated) install.sh
  AFTER=$(grep '^VERSION=' "$SCRIPT_DIR/install.sh" | head -1 | tr -d '"' | cut -d= -f2)
  if [[ "$BEFORE" == "$AFTER" ]]; then
    echo "Already up to date (v${BEFORE})"
  else
    echo -e "Updated: v${BEFORE} -> v${AFTER}"
  fi
  echo "Reinstalling..."
  # Run install, skipping MCP setup (MCPs are already configured)
  SKIP_MCP_SETUP=true exec "$SCRIPT_DIR/install.sh"
fi

# --- Setup MCPs only ---
if [[ "${1:-}" == "--setup-mcps" ]]; then
  SKIP_MCP_SETUP=false
  # Jump to MCP section handled below — we set a flag and fall through
  RUN_MCP_ONLY=true
fi

# --- Uninstall ---
if [[ "${1:-}" == "--uninstall" ]]; then
  echo -e "${YELLOW}Uninstalling FeaturePlanner...${NC}"

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

  # Remove version tracking file
  rm -f "$CLAUDE_DIR/.sprint-planner-version"
  echo "  Removed version tracking file"

  echo -e "${YELLOW}Note: settings.json hook entry not removed (edit manually if needed).${NC}"
  echo -e "${GREEN}Uninstall complete.${NC}"
  exit 0
fi

# --- Setup MCPs only (skip install) ---
if [[ "${RUN_MCP_ONLY:-}" == "true" ]]; then
  echo -e "${GREEN}Running MCP setup...${NC}"
  echo ""
  # Jump past install section — MCP section is at the bottom
  # We need the helpers, so skip to MCP directly below
fi

# --- Install ---
if [[ "${RUN_MCP_ONLY:-}" != "true" ]]; then

echo -e "${GREEN}Installing FeaturePlanner into $CLAUDE_DIR${NC}"

# Show upgrade/reinstall info
if [[ -f "$CLAUDE_DIR/.sprint-planner-version" ]]; then
  INSTALLED_VER=$(grep '^version=' "$CLAUDE_DIR/.sprint-planner-version" | cut -d= -f2)
  if [[ "$INSTALLED_VER" == "$VERSION" ]]; then
    echo -e "  Current version: v${INSTALLED_VER} (reinstalling)"
  else
    echo -e "  Upgrading: v${INSTALLED_VER} -> v${VERSION}"
  fi
fi
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
echo -e "${GREEN}  FeaturePlanner v${VERSION} installed successfully  ${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Installed:"
echo "  - $(ls "$SCRIPT_DIR"/skills/ | wc -l | tr -d ' ') skills"
echo "  - $(ls "$SCRIPT_DIR"/agents/*.md | wc -l | tr -d ' ') agents"
echo "  - $(ls "$SCRIPT_DIR"/hooks/*.py | wc -l | tr -d ' ') hooks"
echo "  - PostToolUse validation hook"

# Write version tracking file
cat > "$CLAUDE_DIR/.sprint-planner-version" << VEOF
version=$VERSION
installed_from=$SCRIPT_DIR
installed_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VEOF

fi  # end of if [[ "${RUN_MCP_ONLY:-}" != "true" ]]

# --- MCP Server Setup ---
if [[ "${SKIP_MCP_SETUP:-}" != "true" ]]; then
echo ""
echo "MCP Server Setup"
echo "━━━━━━━━━━━━━━━━"
echo "FeaturePlanner uses 3 optional MCP servers. I'll check each one"
echo "and offer to install any that are missing."
echo ""

# Check prerequisites for MCP installation
HAS_CLAUDE=false
HAS_NPX=false
if command -v claude &>/dev/null; then HAS_CLAUDE=true; fi
if command -v npx &>/dev/null; then HAS_NPX=true; fi

if [[ "$HAS_CLAUDE" == false ]]; then
  echo -e "${YELLOW}Claude CLI not found — skipping MCP setup.${NC}"
  echo "  Install Claude Code first, then re-run ./install.sh to set up MCPs."
elif [[ "$HAS_NPX" == false ]]; then
  echo -e "${YELLOW}npx not found — skipping MCP setup.${NC}"
  echo "  Install Node.js (https://nodejs.org), then re-run ./install.sh to set up MCPs."
else

  # Helper: check if an MCP is already installed
  mcp_installed() {
    claude mcp list 2>/dev/null | grep -qi "$1"
  }

  # Helper: case-insensitive yes check (works on macOS bash 3)
  is_yes() {
    case "$(echo "$1" | tr '[:upper:]' '[:lower:]')" in
      y|yes) return 0 ;; *) return 1 ;;
    esac
  }

  MCPS_INSTALLED=0
  MCPS_SKIPPED=0

  # ── 1. GitHub MCP ──────────────────────────────────────────────
  echo -e "1/3 ${GREEN}GitHub MCP${NC} — scan remote repos without cloning"
  if mcp_installed "github"; then
    echo -e "     ${GREEN}[already installed]${NC}"
    MCPS_INSTALLED=$((MCPS_INSTALLED + 1))
  else
    echo -n "     Install? (y/n): "
    read -r ans
    if is_yes "$ans"; then
      echo -n "     GitHub Personal Access Token (create at https://github.com/settings/tokens): "
      read -rs gh_token
      echo ""
      if [[ -n "$gh_token" ]]; then
        claude mcp add github -s user -e GITHUB_PERSONAL_ACCESS_TOKEN="$gh_token" -- npx -y @modelcontextprotocol/server-github 2>&1 | sed 's/^/     /'
        echo -e "     ${GREEN}[installed]${NC}"
        MCPS_INSTALLED=$((MCPS_INSTALLED + 1))
      else
        echo -e "     ${YELLOW}[skipped — no token provided]${NC}"
        MCPS_SKIPPED=$((MCPS_SKIPPED + 1))
      fi
    else
      echo -e "     ${YELLOW}[skipped]${NC}"
      MCPS_SKIPPED=$((MCPS_SKIPPED + 1))
    fi
  fi
  echo ""

  # ── 2. Figma MCP ───────────────────────────────────────────────
  echo -e "2/3 ${GREEN}Figma MCP${NC} — analyze Figma designs for UI tasks"
  if mcp_installed "figma"; then
    echo -e "     ${GREEN}[already installed]${NC}"
    MCPS_INSTALLED=$((MCPS_INSTALLED + 1))
  else
    echo -n "     Install? (y/n): "
    read -r ans
    if is_yes "$ans"; then
      echo -n "     Figma API Key (create at https://www.figma.com/developers/api#access-tokens): "
      read -rs figma_key
      echo ""
      if [[ -n "$figma_key" ]]; then
        claude mcp add figma -s user -- npx -y figma-developer-mcp --figma-api-key="$figma_key" --stdio 2>&1 | sed 's/^/     /'
        echo -e "     ${GREEN}[installed]${NC}"
        MCPS_INSTALLED=$((MCPS_INSTALLED + 1))
      else
        echo -e "     ${YELLOW}[skipped — no key provided]${NC}"
        MCPS_SKIPPED=$((MCPS_SKIPPED + 1))
      fi
    else
      echo -e "     ${YELLOW}[skipped]${NC}"
      MCPS_SKIPPED=$((MCPS_SKIPPED + 1))
    fi
  fi
  echo ""

  # ── 3. Atlassian MCP ───────────────────────────────────────────
  echo -e "3/3 ${GREEN}Atlassian MCP${NC} — read/create Jira tickets and Confluence pages"
  if mcp_installed "atlassian"; then
    echo -e "     ${GREEN}[already installed]${NC}"
    MCPS_INSTALLED=$((MCPS_INSTALLED + 1))
  else
    echo -n "     Install? (y/n): "
    read -r ans
    if is_yes "$ans"; then
      echo -n "     Atlassian Site URL (e.g., https://your-org.atlassian.net): "
      read -r atl_url
      echo -n "     Atlassian Email: "
      read -r atl_email
      echo -n "     Atlassian API Token (create at https://id.atlassian.net/manage-profile/security/api-tokens): "
      read -rs atl_token
      echo ""
      if [[ -n "$atl_url" && -n "$atl_email" && -n "$atl_token" ]]; then
        claude mcp add atlassian -s user \
          -e ATLASSIAN_SITE_URL="$atl_url" \
          -e ATLASSIAN_USER_EMAIL="$atl_email" \
          -e ATLASSIAN_API_TOKEN="$atl_token" \
          -- npx -y atlassian-mcp --stdio 2>&1 | sed 's/^/     /'
        echo -e "     ${GREEN}[installed]${NC}"
        MCPS_INSTALLED=$((MCPS_INSTALLED + 1))
      else
        echo -e "     ${YELLOW}[skipped — missing credentials]${NC}"
        MCPS_SKIPPED=$((MCPS_SKIPPED + 1))
      fi
    else
      echo -e "     ${YELLOW}[skipped]${NC}"
      MCPS_SKIPPED=$((MCPS_SKIPPED + 1))
    fi
  fi

  echo ""
  echo "MCP setup: ${MCPS_INSTALLED} installed, ${MCPS_SKIPPED} skipped"
  if [[ "$MCPS_SKIPPED" -gt 0 ]]; then
    echo "  Re-run ./install.sh --setup-mcps anytime to set up skipped MCPs."
  fi
fi

fi  # end of SKIP_MCP_SETUP check

if [[ "${RUN_MCP_ONLY:-}" == "true" ]]; then
  echo ""
  echo "MCP setup complete."
  exit 0
fi

echo ""
echo "Usage: Open Claude Code in any project and run:"
echo "  /run-pipeline"
echo ""
echo "To uninstall:"
echo "  ./install.sh --uninstall"
