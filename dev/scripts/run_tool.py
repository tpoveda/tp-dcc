#!/usr/bin/env python
"""Script to run TP DCC tools from the command line using UV.

This script provides a simple way to launch tools by their ID from the command
line. It automatically detects if the current environment is standalone and
initializes a QApplication instance if necessary.

Usage:
    uv run python run_tool.py <tool_id>
    uv run python run_tool.py tp.rigging.rigbuilder

Requirements:
    - UV must be installed and accessible in the system PATH.
    - The tool must be registered in the TP DCC tools environment variable.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Set up the root directory environment variable before importing bootstrap.
# The script is located at: <root>/dev/scripts/run_tool.py
# So the root is two directories up from the script location.
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent
os.environ.setdefault("TP_DCC_PIPELINE_ROOT_DIRECTORY", str(_PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed command line arguments.
    """

    parser = argparse.ArgumentParser(
        description="Run a TP DCC tool by its ID.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_tool.py tp.rigging.rigbuilder
    python run_tool.py tp.animation.animexport --list
        """,
    )
    parser.add_argument(
        "tool_id",
        nargs="?",
        help="The ID of the tool to run (e.g., tp.rigging.rigbuilder).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available tool IDs.",
    )

    return parser.parse_args()


def list_tools():
    """List all available tool IDs."""

    from tp.managers.tools import ToolsManager

    tools_manager = ToolsManager()
    tool_ids = tools_manager.tool_ids()

    if not tool_ids:
        print("No tools found.")
        return

    print("Available tools:")
    for tool_id in sorted(tool_ids):
        print(f"  - {tool_id}")


def run_tool(tool_id: str):
    """Run a tool by its ID.

    Args:
        tool_id: The ID of the tool to run.
    """

    from tp.managers import tools

    tools.launch_tool(tool_id)


def main():
    """Main entry point for the script."""

    args = parse_args()

    # Initialize the bootstrap before doing anything else.
    from tp.bootstrap import init

    init()

    if args.list:
        list_tools()
        return

    if not args.tool_id:
        print("Error: tool_id is required. Use --list to see available tools.")
        sys.exit(1)

    run_tool(args.tool_id)


if __name__ == "__main__":
    main()
