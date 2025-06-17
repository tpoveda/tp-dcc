from __future__ import annotations

import os
import sys
import cmd
import json
import shlex
import inspect
import readline
import traceback
from typing import Any, Optional, List, Dict

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from loguru import logger

from tp.libs.rpc.api.interface import (
    call_remote_function,
    describe_remote_function,
)
from tp.libs.rpc.hooks.registry import get_supported_dccs
from tp.libs.rpc.core.instances import list_instances


class RPCConsole(cmd.Cmd):
    """Interactive console for testing RPC functions."""

    intro = "Welcome to the TP DCC RPC Console. Type help or ? to list commands.\n"
    prompt = "(rpc) "

    def __init__(self, dcc_type: str = None, instance_name: str = None):
        """Initialize the console.

        Args:
            dcc_type: Optional DCC type to connect to
            instance_name: Optional instance name to connect to
        """
        super().__init__()
        self.dcc_type = dcc_type
        self.instance_name = instance_name
        self.output_format = "plain"
        self.history_file = os.path.expanduser("~/.tp_dcc_rpc_history")

        # Load command history if available
        try:
            readline.read_history_file(self.history_file)
        except FileNotFoundError:
            pass

        # Update prompt if DCC is selected
        self._update_prompt()

    def _update_prompt(self):
        """Update the prompt based on current connection."""
        if self.dcc_type:
            instance_part = f"/{self.instance_name}" if self.instance_name else ""
            self.prompt = f"({self.dcc_type}{instance_part}) "
        else:
            self.prompt = "(rpc) "

    def _format_output(self, data: Any) -> str:
        """Format output based on current output format.

        Args:
            data: Data to format

        Returns:
            Formatted string
        """
        if self.output_format == "json":
            return json.dumps(data, indent=2)
        elif self.output_format == "yaml" and YAML_AVAILABLE:
            return yaml.dump(data, sort_keys=False)
        else:
            return str(data)

    def emptyline(self):
        """Do nothing on empty line."""
        pass

    def do_connect(self, arg):
        """Connect to a specific DCC instance.

        Usage: connect <dcc_type> [instance_name]
        """
        args = shlex.split(arg)
        if not args:
            print("Error: DCC type is required")
            return

        dcc_type = args[0]
        instance_name = args[1] if len(args) > 1 else None

        # Verify DCC type exists
        instances = list_instances()
        if dcc_type not in instances:
            print(f"Error: DCC type '{dcc_type}' not found")
            return

        # If instance name is provided, verify it exists
        if instance_name and instance_name not in instances.get(dcc_type, {}):
            print(f"Error: Instance '{instance_name}' not found for DCC '{dcc_type}'")
            return

        self.dcc_type = dcc_type
        self.instance_name = instance_name
        self._update_prompt()
        print(
            f"Connected to {dcc_type}" + (f"/{instance_name}" if instance_name else "")
        )

    def do_disconnect(self, arg):
        """Disconnect from the current DCC instance."""
        self.dcc_type = None
        self.instance_name = None
        self._update_prompt()
        print("Disconnected")

    def do_list(self, arg):
        """List all registered DCC instances."""
        instances = list_instances()
        if not instances:
            print("No DCC instances currently registered.")
            return

        print("Registered DCC Instances:")
        for dcc_type, dcc_map in instances.items():
            for instance, data in dcc_map.items():
                uri = data["uri"]
                print(f" - {dcc_type}/{instance}: {uri}")

    def do_dccs(self, arg):
        """List all supported DCC types."""
        dccs = get_supported_dccs()
        print("Supported DCC Types:")
        for key, meta in dccs.items():
            print(f" - {key}: {meta['label']} (headless={meta['headless']})")

    def do_functions(self, arg):
        """List all registered functions for the current DCC.

        Usage: functions [--verbose]
        """
        if not self.dcc_type:
            print("Error: Not connected to any DCC. Use 'connect' first.")
            return

        verbose = "--verbose" in arg

        try:
            funcs = call_remote_function(
                dcc_type=self.dcc_type,
                instance_name=self.instance_name,
                function_name="list_registered_functions",
                verbose=verbose,
            )

            if verbose:
                print(f"Registered functions ({len(funcs)}):")
                for entry in funcs:
                    print(f" • {entry['signature']}")
                    if entry["doc"]:
                        print(f"    ↪ {entry['doc']}")
            else:
                print(f"Registered functions ({len(funcs)}):")
                for name in funcs:
                    print(f" • {name}")

        except Exception as e:
            print(f"Error: {e}")

    def do_describe(self, arg):
        """Describe a remote function (signature + doc).

        Usage: describe <function_name>
        """
        if not self.dcc_type:
            print("Error: Not connected to any DCC. Use 'connect' first.")
            return

        args = shlex.split(arg)
        if not args:
            print("Error: Function name is required")
            return

        func_name = args[0]

        try:
            info = describe_remote_function(
                name=func_name, dcc_type=self.dcc_type, instance_name=self.instance_name
            )

            if not info.get("found"):
                print(f"Function '{func_name}' not found.")
                return

            print(f"{info['signature']}")
            if info.get("doc"):
                print(f"\n{info['doc']}")
            print("\nArguments:")
            for arg in info.get("args", []):
                line = f" - {arg['name']}"
                if arg["type"]:
                    line += f" ({arg['type']})"
                if arg["default"] is not None:
                    line += f" = {arg['default']}"
                print(line)
            if info.get("return_type"):
                print(f"\n↩Returns: {info['return_type']}")

        except Exception as e:
            print(f"Error: {e}")

    def do_call(self, arg):
        """Call a remote function.

        Usage: call <function_name> [arg1 arg2 ...] [key1=value1 key2=value2 ...]
        """
        if not self.dcc_type:
            print("Error: Not connected to any DCC. Use 'connect' first.")
            return

        args = shlex.split(arg)
        if not args:
            print("Error: Function name is required")
            return

        func_name = args[0]
        pos_args = []
        kw_args = {}

        # Parse arguments
        for arg in args[1:]:
            if "=" in arg:
                key, val = arg.split("=", 1)
                kw_args[key] = val
            else:
                pos_args.append(arg)

        try:
            result = call_remote_function(
                dcc_type=self.dcc_type,
                instance_name=self.instance_name,
                function_name=func_name,
                *pos_args,
                **kw_args,
            )

            print(f"Result: {self._format_output(result)}")

        except Exception as e:
            print(f"Error: {e}")

    def do_format(self, arg):
        """Set the output format.

        Usage: format [plain|json|yaml]
        """
        args = shlex.split(arg)
        if not args:
            print(f"Current format: {self.output_format}")
            return

        format_type = args[0].lower()
        if format_type not in ["plain", "json", "yaml"]:
            print("Error: Format must be one of: plain, json, yaml")
            return

        if format_type == "yaml" and not YAML_AVAILABLE:
            print("Warning: PyYAML not installed. Falling back to plain format.")
            self.output_format = "plain"
        else:
            self.output_format = format_type

        print(f"Output format set to: {self.output_format}")

    def do_progress(self, arg):
        """Monitor progress of a task.

        Usage: progress <task_id>
        """
        if not self.dcc_type:
            print("Error: Not connected to any DCC. Use 'connect' first.")
            return

        args = shlex.split(arg)
        if not args:
            print("Error: Task ID is required")
            return

        task_id = args[0]

        try:
            print(f"Monitoring progress of task {task_id}...")
            print("Press Ctrl+C to stop monitoring")

            while True:
                status = call_remote_function(
                    dcc_type=self.dcc_type,
                    instance_name=self.instance_name,
                    function_name="get_task_status",
                    task_id=task_id,
                )

                progress = call_remote_function(
                    dcc_type=self.dcc_type,
                    instance_name=self.instance_name,
                    function_name="get_task_progress",
                    task_id=task_id,
                )

                progress_value, progress_message = progress
                progress_bar = "=" * int(progress_value * 20)
                print(
                    f"\r[{progress_bar:<20}] {progress_value:.0%} - {status} - {progress_message}",
                    end="",
                )

                if status in ["done", "failed", "canceled"]:
                    print()  # Add newline
                    if status == "done":
                        result = call_remote_function(
                            dcc_type=self.dcc_type,
                            instance_name=self.instance_name,
                            function_name="get_task_result",
                            task_id=task_id,
                        )
                        print(f"Result: {self._format_output(result)}")
                    break

                import time

                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\nMonitoring stopped")
        except Exception as e:
            print(f"\nError: {e}")

    def do_tasks(self, arg):
        """List all tasks for the current DCC.

        Usage: tasks
        """
        if not self.dcc_type:
            print("Error: Not connected to any DCC. Use 'connect' first.")
            return

        try:
            tasks = call_remote_function(
                dcc_type=self.dcc_type,
                instance_name=self.instance_name,
                function_name="list_tasks",
            )

            print(f"Tasks ({len(tasks)}):")
            for task in tasks:
                progress = f"{task['progress']:.0%}" if "progress" in task else "N/A"
                message = f" - {task['message']}" if "message" in task else ""
                print(
                    f" • {task['id']} [{task['status']}] {progress} - {task['function']}{message}"
                )

        except Exception as e:
            print(f"Error: {e}")

    def do_exit(self, arg):
        """Exit the console."""
        print("Goodbye!")
        # Save command history
        try:
            readline.write_history_file(self.history_file)
        except Exception:
            pass
        return True

    def do_quit(self, arg):
        """Exit the console."""
        return self.do_exit(arg)

    def do_EOF(self, arg):
        """Exit on Ctrl-D."""
        print()  # Add newline
        return self.do_exit(arg)


def start_console(dcc_type: str = None, instance_name: str = None):
    """Start the interactive console.

    Args:
        dcc_type: Optional DCC type to connect to
        instance_name: Optional instance name to connect to
    """
    console = RPCConsole(dcc_type, instance_name)
    try:
        console.cmdloop()
    except KeyboardInterrupt:
        print("\nGoodbye!")
