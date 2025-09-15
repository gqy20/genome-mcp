#!/usr/bin/env python3
"""
Setup pre-commit hooks for the Genome MCP project.

This script installs pre-commit and sets up the hooks to run
automatically on each commit to ensure code quality.
"""

import subprocess
import sys


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"   Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"   Error: {e.stderr}")
        return False


def main():
    """Main setup function."""
    print("🚀 Setting up pre-commit hooks for Genome MCP")
    print("=" * 50)

    # Check if pre-commit is installed
    try:
        import pre_commit

        print("✅ pre-commit is already installed")
    except ImportError:
        print("📦 Installing pre-commit...")
        if not run_command(
            [sys.executable, "-m", "pip", "install", "pre-commit"], "Install pre-commit"
        ):
            print("❌ Failed to install pre-commit. Please install it manually:")
            print("   pip install pre-commit")
            return False

    # Install pre-commit hooks
    if not run_command(["pre-commit", "install"], "Install pre-commit hooks"):
        print("❌ Failed to install pre-commit hooks")
        return False

    # Run pre-commit on all files to check current status
    print("\n🔍 Running pre-commit on current files...")
    result = subprocess.run(
        ["pre-commit", "run", "--all-files"], capture_output=True, text=True
    )

    if result.returncode == 0:
        print("✅ All pre-commit checks passed!")
    else:
        print("⚠️  Some pre-commit checks failed:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        print("\n💡 You can fix these issues and commit again, or use:")
        print("   pre-commit run --all-files  # to run all checks manually")

    print("\n🎉 Pre-commit hooks setup complete!")
    print("\nFrom now on, these checks will run automatically on each commit:")
    print("  • Black code formatting")
    print("  • Import sorting with isort")
    print("  • Linting with ruff")
    print("  • Type checking with mypy")
    print("  • Security checking with bandit")
    print("  • Basic file checks")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
