from __future__ import annotations

import time
import json
import argparse
import importlib.util
from pathlib import Path
from types import FunctionType
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    yaml = None

from tp.libs.rpc.hooks.loader import (
    load_and_initialize,
    discover_plugins,
    reload_plugin,
)
from tp.libs.rpc.hooks.registry import get_supported_dccs
from tp.libs.rpc.core.instances import (
    list_instances,
    get_uri,
    unregister_instance,
    cleanup_registry,
)
from tp.libs.rpc.api.interface import (
    register_function_remotely,
    call_remote_function,
    describe_remote_function,
)
from tp.libs.rpc.console import start_console

from loguru import logger


def main():
    """Command line interface for starting an RPC server."""

    parser = argparse.ArgumentParser(description="tp-dcc-rpc CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Start an RPC server
    start_parser = subparsers.add_parser("start", help="Start an RPC server")
    start_parser.add_argument(
        "--dcc", required=True, help="DCC type (maya, unreal, etc.)"
    )
    start_parser.add_argument("--host", default="localhost", help="Bind address")
    start_parser.add_argument(
        "--port", type=int, default=0, help="Port to use (0 = auto)"
    )
    start_parser.add_argument("--instance-name", help="Optional name (e.g., maya_qa)")

    # List all registered instances
    list_parser = subparsers.add_parser(
        "list", help="List all registered DCC instances"
    )

    # List all supported DCC types
    dccs_parser = subparsers.add_parser("dccs", help="List all supported DCC types")

    # Unregister an instance
    unregister_parser = subparsers.add_parser(
        "unregister", help="Remove a registered instance"
    )
    unregister_parser.add_argument("--dcc", required=True, help="DCC type")
    unregister_parser.add_argument(
        "--instance-name", required=True, help="Name of instance to remove"
    )

    # Cleanup unreachable instances
    cleanup_parser = subparsers.add_parser(
        "clean", help="Cleanup unreachable instances"
    )

    # register commands
    reg_parser = subparsers.add_parser(
        "register", help="Register a Python function remotely"
    )
    reg_parser.add_argument(
        "path",
        type=str,
        help="Path to the Python file containing the function",
    )
    reg_parser.add_argument(
        "--func", type=str, help="Function name to register (optional)"
    )
    reg_parser.add_argument(
        "--dcc", type=str, required=True, help="DCC type (e.g., maya, unreal)"
    )
    reg_parser.add_argument("--instance", type=str, help="Specific instance name")
    reg_parser.add_argument(
        "--globals", action="store_true", help="Include global variables"
    )
    reg_parser.add_argument(
        "--no-imports",
        action="store_true",
        help="Do not auto-detect import paths",
    )
    reg_parser.add_argument(
        "--run",
        action="store_true",
        help="Call the function after registering",
    )
    reg_parser.add_argument("--args", nargs="*", help="Positional args for function")
    reg_parser.add_argument("--kwargs", nargs="*", help="Keyword args: key=value")
    reg_parser.add_argument(
        "--output",
        choices=["plain", "json", "yaml"],
        default="plain",
        help="Output format for function result if --run is used (default: plain)",
    )
    reg_parser.add_argument(
        "--background",
        action="store_true",
        help="Run the function as a background task instead of blocking",
    )
    reg_parser.add_argument(
        "--watch",
        action="store_true",
        help="Wait and print result of a background task after submission",
    )

    # list-functions
    list_parser = subparsers.add_parser(
        "list-functions", help="List all registered remote functions"
    )
    list_parser.add_argument("--dcc", required=True, help="DCC type (e.g., maya)")
    list_parser.add_argument("--instance", help="Instance name (optional)")
    list_parser.add_argument(
        "--output",
        choices=["plain", "json", "yaml"],
        default="plain",
        help="Output format",
    )
    list_parser.add_argument(
        "--verbose", action="store_true", help="Show signature and docstring"
    )

    # describe
    desc_parser = subparsers.add_parser(
        "describe", help="Describe a remote function (signature + doc)"
    )
    desc_parser.add_argument(
        "--func", required=True, help="Name of function to describe"
    )
    desc_parser.add_argument("--dcc", required=True, help="DCC type (e.g., maya)")
    desc_parser.add_argument("--instance", help="Instance name (optional)")
    desc_parser.add_argument(
        "--output",
        choices=["plain", "json", "yaml"],
        default="plain",
        help="Output format",
    )

    # call
    call_parser = subparsers.add_parser(
        "call", help="Call a registered remote function"
    )
    call_parser.add_argument(
        "--func", required=True, help="Name of the registered function to call"
    )
    call_parser.add_argument("--dcc", required=True, help="DCC type (e.g., maya)")
    call_parser.add_argument("--instance", help="Instance name (optional)")
    call_parser.add_argument("--args", nargs="*", help="Positional args")
    call_parser.add_argument("--kwargs", nargs="*", help="Keyword args: key=value")
    call_parser.add_argument(
        "--output",
        choices=["plain", "json", "yaml"],
        default="plain",
        help="Output format",
    )

    # tasks group
    task_parser = subparsers.add_parser("tasks", help="Manage remote background tasks")
    task_subparsers = task_parser.add_subparsers(dest="subcommand", required=True)

    # tasks list
    task_list = task_subparsers.add_parser("list", help="List all tasks")
    task_list.add_argument("--dcc", required=True)
    task_list.add_argument("--instance")

    # tasks get
    task_get = task_subparsers.add_parser("get", help="Get task status or result")
    task_get.add_argument("--dcc", required=True)
    task_get.add_argument("--instance")
    task_get.add_argument("--task-id", required=True)
    task_get.add_argument(
        "--result",
        action="store_true",
        help="Fetch result instead of just status",
    )

    # tasks cancel
    task_cancel = task_subparsers.add_parser("cancel", help="Cancel a running task")
    task_cancel.add_argument("--dcc", required=True)
    task_cancel.add_argument("--instance")
    task_cancel.add_argument("--task-id", required=True)

    status_parser = subparsers.add_parser(
        "status", help="Check status of registered DCC instances"
    )
    status_parser.add_argument(
        "--max-age",
        type=int,
        default=60,
        help="Max age in seconds before considering an instance offline",
    )
    status_parser.add_argument("--output", choices=["plain", "json"], default="plain")
    status_parser.add_argument(
        "--clean",
        action="store_true",
        help="Automatically unregister stale/offline instances",
    )

    reload_parser = subparsers.add_parser("reload", help="Reload a plugin module")
    reload_parser.add_argument("--dcc", required=True)
    reload_parser.add_argument("--port", type=int, default=0)
    reload_parser.add_argument("--instance-name", default="default")

    # Interactive console
    console_parser = subparsers.add_parser(
        "console", help="Start an interactive console for testing RPC functions"
    )
    console_parser.add_argument("--dcc", help="DCC type to connect to")
    console_parser.add_argument("--instance", help="Instance name to connect to")

    # File transfer commands
    file_parser = subparsers.add_parser("file", help="File transfer operations")
    file_subparsers = file_parser.add_subparsers(dest="subcommand", required=True)

    # Send file
    send_parser = file_subparsers.add_parser("send", help="Send a file to a remote DCC")
    send_parser.add_argument("file", help="Path to the file to send")
    send_parser.add_argument("--dcc", required=True, help="Target DCC type")
    send_parser.add_argument("--instance", help="Target instance name")
    send_parser.add_argument(
        "--remote-dir", help="Remote directory to save the file to"
    )
    send_parser.add_argument(
        "--no-compress", action="store_true", help="Disable compression"
    )

    # Get file
    get_parser = file_subparsers.add_parser("get", help="Get a file from a remote DCC")
    get_parser.add_argument("remote_file", help="Path to the file on the remote system")
    get_parser.add_argument("--dcc", required=True, help="Source DCC type")
    get_parser.add_argument("--instance", help="Source instance name")
    get_parser.add_argument("--output-dir", help="Directory to save the file to")
    get_parser.add_argument("--output-file", help="Specific file path to save to")

    args = parser.parse_args()

    # --start
    if args.command == "start":
        load_and_initialize(
            dcc_type=args.dcc,
            host=args.host,
            port=args.port,
            instance_name=args.instance_name,
        )

    # --list
    elif args.command == "list":
        instances = list_instances()
        if not instances:
            logger.info("No DCC instances currently registered.")
            return
        logger.info("Registered DCC Instances:")
        for dcc_type, dcc_map in instances.items():
            for instance, uri in dcc_map.items():
                logger.info(f" - {dcc_type}/{instance}: {uri}")

    # --dccs
    elif args.command == "dccs":
        dccs = get_supported_dccs()
        logger.info("Supported DCC Types:")
        for key, meta in dccs.items():
            logger.info(f" - {key}: {meta['label']} (headless={meta['headless']})")

        plugins = discover_plugins()
        if not plugins:
            logger.warning("No DCC plugins found.")
        else:
            logger.info("Supported DCC Types:")
            for name, meta in plugins.items():
                line = f" - {name}: {meta['doc']}"
                line += f" (headless={meta.get('headless')})"
                if meta.get("source") != "builtin":
                    line += f" [external from {meta['source']}]"
                logger.info(line)

    # --unregister
    elif args.command == "unregister":
        uri = get_uri(args.dcc, args.instance_name)
        if not uri:
            logger.info(f"Instance not found: {args.dcc}/{args.instance_name}")
            return
        unregister_instance(args.dcc, args.instance_name)
        logger.info(f"Unregistered {args.dcc}/{args.instance_name}")

    # --cleanup
    elif args.command == "clean":
        removed = cleanup_registry()
        if removed:
            logger.info("Removed unreachable instances:")
            for path in removed:
                logger.info(f" - {path}")
        else:
            logger.info("Registry is clean. No unreachable instances.")

    # --register
    elif args.command == "register":
        file_path = Path(args.path)
        if not file_path.exists():
            logger.info(f"File not found: {file_path}")
            return

        mod_name = file_path.stem
        spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # If function name is not given, use first function found.
        if args.func:
            func = getattr(mod, args.func, None)
        else:
            func = next(
                (v for v in vars(mod).values() if isinstance(v, FunctionType)),
                None,
            )

        if not func:
            logger.info("No function found to register.")
            return

        # Build optional globals
        gvars = vars(mod) if args.globals else {}

        logger.info(f"📡 Registering function '{func.__name__}' to {args.dcc}...")

        resp = register_function_remotely(
            func=func,
            dcc_type=args.dcc,
            instance_name=args.instance,
            inject_globals=gvars,
            detect_import_paths=not args.no_imports,
        )

        logger.info(
            f"{resp['message']}"
            if resp["status"] == "success"
            else f"{resp['message']}"
        )

        if args.run and resp["status"] == "success":
            pos_args = args.args or []
            kw_args = {}

            for pair in args.kwargs or []:
                if "=" not in pair:
                    logger.warning(f"Skipping invalid kwarg: {pair}")
                    continue
                key, val = pair.split("=", 1)
                kw_args[key] = val

            if args.background:
                logger.info(f"Submitting {func.__name__} as background task...")
                task_id = call_remote_function(
                    dcc_type=args.dcc,
                    instance_name=args.instance,
                    function_name="submit_task",
                    function_name_=func.__name__,  # avoid conflict
                    *pos_args,
                    **kw_args,
                )
                logger.info("Task submitted. ID:", task_id)

                if args.watch:
                    logger.info("👀 Watching for completion...")

                    try:
                        while True:
                            status = call_remote_function(
                                dcc_type=args.dcc,
                                instance_name=args.instance,
                                function_name="get_task_status",
                                task_id=task_id,
                            )
                            if status in ("done", "failed"):
                                break
                            logger.info(f" ⏳ {status}...")
                            time.sleep(1.0)

                        result = call_remote_function(
                            dcc_type=args.dcc,
                            instance_name=args.instance,
                            function_name="get_task_result",
                            task_id=task_id,
                        )

                        logger.info("Task completed. Result:")
                        if args.output == "json":
                            logger.info(json.dumps(result, indent=2))
                        elif args.output == "yaml" and yaml:
                            logger.info(yaml.dump(result, sort_keys=False))
                        else:
                            logger.info(result)

                    except KeyboardInterrupt:
                        logger.info("Watch interrupted.")
                    except Exception as e:
                        logger.info("Task failed:", e)

            else:
                logger.info(f"Calling {func.__name__} on {args.dcc}...")
                try:
                    result = call_remote_function(
                        dcc_type=args.dcc,
                        instance_name=args.instance,
                        function_name=func.__name__,
                        *pos_args,
                        **kw_args,
                    )
                    if args.output == "json":
                        logger.info(json.dumps(result, indent=2))
                    elif args.output == "yaml":
                        if not yaml:
                            logger.warning(
                                "PyYAML not installed. Falling back to plain output."
                            )
                            logger.info(result)
                        else:
                            logger.info(yaml.dump(result, sort_keys=False))
                    else:
                        logger.info("Result:", result)
                except Exception as e:
                    logger.exception("Call failed:", e)

    elif args.command == "list-functions":
        try:
            funcs = call_remote_function(
                dcc_type=args.dcc,
                instance_name=args.instance,
                function_name="list_registered_functions",
                verbose=args.verbose,
            )

            if args.output == "json":
                logger.info(json.dumps(funcs, indent=2))
            elif args.output == "yaml":
                if yaml:
                    logger.info(yaml.dump(funcs, sort_keys=False))
                else:
                    logger.warning("PyYAML not installed. Falling back to plain.")
                    for entry in funcs:
                        logger.info("-", entry["name"] if args.verbose else entry)
            else:
                if args.verbose:
                    logger.info(f"Registered functions ({len(funcs)}):")
                    for entry in funcs:
                        logger.info(f" • {entry['signature']}")
                        if entry["doc"]:
                            logger.info(f"    ↪ {entry['doc']}")
                else:
                    logger.info(f"Registered functions ({len(funcs)}):")
                    for name in funcs:
                        logger.info(" •", name)

        except Exception as e:
            logger.error("Failed to retrieve registered functions:", e)

    elif args.command == "describe":
        try:
            info = describe_remote_function(
                name=args.func, dcc_type=args.dcc, instance_name=args.instance
            )

            if not info.get("found"):
                logger.error(f"Function '{args.func}' not found.")
                return

            if args.output == "json":
                logger.info(json.dumps(info, indent=2))

            elif args.output == "yaml":
                if yaml:
                    logger.info(yaml.dump(info, sort_keys=False))
                else:
                    logger.warning(
                        "PyYAML not installed. Falling back to plain output."
                    )
                    logger.info(info)

            else:
                logger.info(f"{info['signature']}")
                if info.get("doc"):
                    logger.info(f"\n{info['doc']}")
                logger.info("\nArguments:")
                for arg in info.get("args", []):
                    line = f" - {arg['name']}"
                    if arg["type"]:
                        line += f" ({arg['type']})"
                    if arg["default"] is not None:
                        line += f" = {arg['default']}"
                    logger.info(line)
                if info.get("return_type"):
                    logger.info(f"\n↩Returns: {info['return_type']}")

        except Exception as e:
            logger.error("Describe failed:", e)

    elif args.command == "call":
        pos_args = args.args or []
        kw_args = {}

        for pair in args.kwargs or []:
            if "=" not in pair:
                logger.warning(f"Skipping invalid kwarg: {pair}")
                continue
            key, val = pair.split("=", 1)
            kw_args[key] = val

        logger.info(f"Calling {args.func} on {args.dcc}...")

        try:
            result = call_remote_function(
                dcc_type=args.dcc,
                instance_name=args.instance,
                function_name=args.func,
                *pos_args,
                **kw_args,
            )

            if args.output == "json":
                logger.info(json.dumps(result, indent=2))
            elif args.output == "yaml":
                if yaml:
                    logger.info(yaml.dump(result, sort_keys=False))
                else:
                    logger.warning("PyYAML not installed. Showing raw output.")
                    logger.info(result)
            else:
                logger.info("Result:", result)

        except Exception as e:
            logger.error("Remote call failed:", e)

    elif args.command == "tasks":
        if args.subcommand == "list":
            tasks = call_remote_function(
                args.dcc, "list_tasks", instance_name=args.instance
            )
            logger.info(f"🗂 {len(tasks)} task(s) found:")
            for t in tasks:
                logger.info(f" • {t['id']} [{t['status']}] - {t['function']}")

        elif args.subcommand == "get":
            if args.result:
                try:
                    result = call_remote_function(
                        args.dcc,
                        "get_task_result",
                        task_id=args.task_id,
                        instance_name=args.instance,
                    )
                    logger.info("Task result:\n", result)
                except Exception as e:
                    logger.error(f"Error fetching result: {e}")
            else:
                status = call_remote_function(
                    args.dcc,
                    "get_task_status",
                    task_id=args.task_id,
                    instance_name=args.instance,
                )
                logger.info(f"Task {args.task_id} status: {status}")

        elif args.subcommand == "cancel":
            success = call_remote_function(
                args.dcc,
                "cancel_task",
                task_id=args.task_id,
                instance_name=args.instance,
            )
            logger.info("Task cancelled." if success else "Unable to cancel task.")

    elif args.command == "status":
        now = datetime.now(timezone.utc)
        max_age = args.max_age
        registry = list_instances()

        results = []
        for dcc_type, instances in registry.items():
            for name, data in instances.items():
                uri = data["uri"]
                last_hb = data.get("last_heartbeat")
                try:
                    dt = datetime.fromisoformat(last_hb)
                    delta = (now - dt).total_seconds()
                    alive = delta < max_age
                except Exception:
                    dt = None
                    delta = None
                    alive = False

                if args.clean and not alive:
                    unregister_instance(dcc_type, name)
                    status_msg = "cleaned"
                else:
                    status_msg = "alive" if alive else "offline"

                results.append(
                    {
                        "dcc": dcc_type,
                        "instance": name,
                        "uri": uri,
                        "last_seen": last_hb,
                        "age_sec": delta,
                        "status": status_msg,
                    }
                )

        if args.output == "json":
            logger.info(json.dumps(results, indent=2))
        else:
            logger.info(
                f"{'DCC':<10} {'Instance':<20} {'Status':<8} {'Age':>6}s  {'URI'}"
            )
            for r in results:
                age = f"{int(r['age_sec'])}" if r["age_sec"] is not None else "??"
                logger.info(
                    f"{r['dcc']:<10} {r['instance']:<20} {r['status']:<8} {age:>6}s  {r['uri']}"
                )
    elif args.command == "reload":
        reload_plugin(args.dcc, port=args.port, instance_name=args.instance_name)
        logger.info(f"Reloaded plugin: {args.dcc}")
    elif args.command == "console":
        logger.info("Starting interactive console...")
        start_console(dcc_type=args.dcc, instance_name=args.instance)
    elif args.command == "file":
        from tp.libs.rpc.core.file_transfer import send_file_to_dcc, get_file_from_dcc

        if args.subcommand == "send":
            logger.info(f"Sending file {args.file} to {args.dcc}...")
            try:
                result = send_file_to_dcc(
                    file_path=args.file,
                    dcc_type=args.dcc,
                    instance_name=args.instance,
                    remote_dir=args.remote_dir,
                    compress=not args.no_compress,
                )
                logger.info(f"File sent successfully to {result['remote_path']}")
                logger.info(
                    f"File: {result['file_name']}, Size: {result['file_size']} bytes, Hash: {result['file_hash']}"
                )
            except Exception as e:
                logger.error(f"Failed to send file: {e}")

        elif args.subcommand == "get":
            logger.info(f"Getting file {args.remote_file} from {args.dcc}...")
            try:
                result = get_file_from_dcc(
                    remote_file_path=args.remote_file,
                    dcc_type=args.dcc,
                    instance_name=args.instance,
                    output_dir=args.output_dir,
                    output_file=args.output_file,
                )
                logger.info(f"File received successfully at {result['local_path']}")
                logger.info(
                    f"File: {result['file_name']}, Size: {result['file_size']} bytes, Hash: {result['file_hash']}"
                )
            except Exception as e:
                logger.error(f"Failed to get file: {e}")
    else:
        parser.print_help()
