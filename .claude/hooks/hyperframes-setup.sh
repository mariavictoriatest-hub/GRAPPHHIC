#!/bin/bash
# Reinstalls HyperFrames skills and its headless Chrome at the start of each
# cloud session, because the cloud computer starts empty every time.
set -uo pipefail

# Only needed on the cloud computer; on a personal machine it stays installed.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Skills go to ~/.claude/skills, so Claude Code can use them in any project.
npx -y hyperframes@latest skills update >/dev/null 2>&1 \
  || echo "HyperFrames: could not install skills" >&2

# Chrome Headless Shell: the browser HyperFrames uses to capture each frame.
npx -y hyperframes@latest browser ensure >/dev/null 2>&1 \
  || echo "HyperFrames: could not install Chrome" >&2

exit 0
