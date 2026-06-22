#!/usr/bin/env python3
"""
V6.0 Ticket Lock — PreToolUse hook for Edit/Write operations.
Checks .claude/synergy_locks/ for a valid .ticket before allowing writes.
Blocked operations exit with code 1, which causes Claude Code to abort the tool call.

Usage (registered in settings.json PreToolUse hooks):
    python check_synergy_ticket.py <ToolName> <FilePath>
"""
import sys, os, logging

# ── Configuration ──────────────────────────────────────────────────────────
SOURCE_EXTS = {'.py', '.vue', '.cpp', '.c', '.js', '.ts', '.h', '.cs',
               '.java', '.go', '.rs', '.swift', '.kt', '.rb', '.php'}
LOCK_DIR_NAME = '.claude'
LOCK_SUBDIR = 'synergy_locks'

# ── Logging (stderr to avoid interfering with hook output) ─────────────────
logging.basicConfig(
    level=logging.WARNING,
    format='[TicketLock] %(levelname)s: %(message)s',
    stream=sys.stderr,
)


def resolve_lock_dir() -> str:
    """Resolve the synergy_locks directory relative to cwd."""
    cwd = os.getcwd()
    return os.path.join(cwd, LOCK_DIR_NAME, LOCK_SUBDIR)


def check_ticket(tool_name: str, file_path: str) -> int:
    """
    Check if a .ticket exists for the given file.
    Returns 0 if allowed, 1 if blocked.
    """
    # ── Only intercept Edit and Write ──
    if tool_name not in ('Write', 'Edit'):
        return 0

    # ── Only intercept source code files ──
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SOURCE_EXTS:
        return 0

    # ── Resolve ticket path ──
    base = os.path.basename(file_path)
    lock_dir = resolve_lock_dir()
    ticket = os.path.join(lock_dir, f"{base}.ticket")

    # ── Check ticket ──
    try:
        if os.path.exists(ticket):
            print(f"  [TicketLock] {base} -> verified", file=sys.stderr)
            return 0
    except OSError as e:
        logging.error("Failed to access lock dir %s: %s", lock_dir, e)
        # On access failure, allow the operation (fail-open to avoid blocking
        # legitimate work due to filesystem issues)
        return 0

    # ── Block: no ticket ──
    print("", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"  [BLOCKED] {base} -> NO SYNERGY TICKET", file=sys.stderr)
    print("", file=sys.stderr)
    print("  This file requires tri-party review before modification.", file=sys.stderr)
    print("  Run the synergy router with --ticket-for:", file=sys.stderr)
    print(f"    python ~/.claude/scripts/dashscope_router.py code --ticket-for {file_path} ...", file=sys.stderr)
    print("", file=sys.stderr)
    print("  Do NOT bypass this check.", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    return 1


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(0)
    try:
        exit_code = check_ticket(sys.argv[1], sys.argv[2])
        sys.exit(exit_code)
    except Exception as exc:
        logging.error("Unexpected error: %s", exc)
        sys.exit(0)  # Fail-open on unexpected errors
