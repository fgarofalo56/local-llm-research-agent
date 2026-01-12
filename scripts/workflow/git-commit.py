#!/usr/bin/env python3
"""
Smart Git Commit Helper

Analyzes staged changes and generates a detailed commit message.
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def get_staged_files() -> list[str]:
    """Get list of staged files."""
    _, stdout, _ = run_command(["git", "diff", "--name-only", "--cached"])
    return [f.strip() for f in stdout.split("\n") if f.strip()]


def get_git_status() -> str:
    """Get git status."""
    _, stdout, _ = run_command(["git", "status", "--short"])
    return stdout


def get_diff_stats() -> str:
    """Get diff statistics."""
    _, stdout, _ = run_command(["git", "diff", "--cached", "--stat"])
    return stdout


def generate_commit_message(files: list[str]) -> str:
    """Generate a commit message based on changed files."""
    if not files:
        return ""

    # Categorize changes
    docs = [f for f in files if f.startswith("docs/") or f.endswith(".md")]
    tests = [f for f in files if "test" in f.lower()]
    src = [f for f in files if f.startswith("src/")]
    scripts = [f for f in files if f.endswith((".bat", ".sh", ".py")) and not f.startswith("src/")]
    
    # Determine primary type
    if "streamlit_app.py" in str(files):
        commit_type = "fix"
        scope = "streamlit"
        subject = "Add MCP session management to chat interface"
    elif docs:
        commit_type = "docs"
        scope = "streamlit"
        subject = "Add comprehensive testing guide and fix documentation"
    elif scripts:
        commit_type = "chore"
        scope = "scripts"
        subject = "Add automated testing scripts"
    elif tests:
        commit_type = "test"
        scope = ""
        subject = "Add/update tests"
    else:
        commit_type = "feat"
        scope = ""
        subject = "Update implementation"

    # Build commit message
    header = f"{commit_type}"
    if scope:
        header += f"({scope})"
    header += f": {subject}"

    body_parts = []
    
    # Add context
    if "streamlit_app.py" in str(files):
        body_parts.append(
            "Streamlit chat was failing due to missing MCP server session management.\n"
            "Fixed by wrapping agent calls in 'async with agent:' context manager,\n"
            "matching the CLI implementation pattern."
        )
    
    # List changes
    if src:
        body_parts.append(f"\nModified:\n" + "\n".join(f"- {f}" for f in src))
    if docs:
        body_parts.append(f"\nDocumentation:\n" + "\n".join(f"- {f}" for f in docs))
    if scripts:
        body_parts.append(f"\nScripts:\n" + "\n".join(f"- {f}" for f in scripts))
    
    body = "\n".join(body_parts)
    
    footer = "\nTask: 494cdf28-4e58-49ba-ad7a-4e9ed2cde284"
    
    return f"{header}\n\n{body}{footer}"


def main():
    """Main function."""
    print("=" * 60)
    print("Smart Git Commit Helper")
    print("=" * 60)
    print()
    
    # Check if there are staged changes
    staged = get_staged_files()
    if not staged:
        print("❌ No staged changes found.")
        print("\nRun: git add <files>")
        print("Or run: git-add.bat to stage all changes")
        sys.exit(1)
    
    print("📝 Staged files:")
    for f in staged:
        print(f"  - {f}")
    print()
    
    # Show diff stats
    print("📊 Changes:")
    print(get_diff_stats())
    
    # Generate commit message
    message = generate_commit_message(staged)
    
    print("=" * 60)
    print("Suggested commit message:")
    print("=" * 60)
    print(message)
    print("=" * 60)
    print()
    
    # Ask for confirmation
    response = input("Commit with this message? [Y/n/e(dit)]: ").strip().lower()
    
    if response in ("", "y", "yes"):
        # Commit
        returncode, stdout, stderr = run_command(["git", "commit", "-m", message])
        if returncode == 0:
            print("\n✅ Committed successfully!")
            print(stdout)
        else:
            print("\n❌ Commit failed:")
            print(stderr)
            sys.exit(1)
    elif response in ("e", "edit"):
        # Open editor for message
        print("\n📝 Opening editor...")
        # Write message to temp file
        msg_file = Path(".git/COMMIT_EDITMSG_TEMP")
        msg_file.write_text(message)
        # Commit with editor
        returncode, stdout, stderr = run_command(["git", "commit", "-e", "-F", str(msg_file)])
        if returncode == 0:
            print("\n✅ Committed successfully!")
        else:
            print("\n❌ Commit cancelled or failed")
            sys.exit(1)
    else:
        print("\n❌ Commit cancelled")
        sys.exit(0)


if __name__ == "__main__":
    main()
