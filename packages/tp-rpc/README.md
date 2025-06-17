
# tp-rpc

A powerful, flexible RPC (Remote Procedure Call) system for Digital Content Creation (DCC) tools, built on Pyro5.

## Overview

tp-rpc enables seamless communication between different DCC applications like Maya, Unreal Engine, Blender, Houdini, MotionBuilder, and Substance Designer/Painter. It allows you to:

- Call functions remotely between different applications
- Register Python functions dynamically at runtime
- Execute code in a DCC's main thread from a background thread
- Manage connections with automatic discovery and heartbeat monitoring
- Optimize performance with connection pooling and batch operations
- Ensure security with authentication and authorization controls

## Quick Start

### Starting a Server in Maya

```python
from tp.libs.rpc.hooks.plugins import maya_plugin

# Start the RPC server in Maya
instance_name = maya_plugin.initialize(port=9090)
print(f"Maya RPC server started with instance name: {instance_name}")
```

### Calling Maya from Unreal Engine

```python
from tp.libs.rpc.api.interface import call_remote_function

# Create a polygon cube in Maya from Unreal
result = call_remote_function(
    dcc_type="maya",
    function_name="cmds.polyCube",
    width=2, height=2, depth=2
)
print(f"Created cube in Maya: {result}")
```

### Registering a Custom Function

```python
from tp.libs.rpc.api.decorators import register_function

@register_function()
def add_numbers(a, b):
    """Add two numbers together."""
    return a + b

# This function is now available for remote calls
```

## Architecture

tp-rpc is built on a client-server architecture using Pyro5 for network communication:

- **Server**: Runs inside a DCC application and exposes functions for remote calling
- **Client**: Connects to servers and invokes remote functions
- **Registry**: Tracks available DCC instances and their URIs
- **Plugins**: Provides DCC-specific integration (Maya, Unreal, etc.)

The system uses a persistent registry file to track running instances, allowing clients to discover and connect to servers without knowing their exact network location.

## Basic Usage

### Starting Servers

Each DCC has a dedicated plugin module that handles initialization:

```python
# In Maya
from tp.libs.rpc.hooks.plugins import maya_plugin
maya_plugin.initialize()

# In Unreal Engine
from tp.libs.rpc.hooks.plugins import unreal_plugin
unreal_plugin.initialize()

# In Blender
from tp.libs.rpc.hooks.plugins import blender_plugin
blender_plugin.initialize()
```

### Auto-Starting with Bootstrap

tp-rpc can automatically detect and initialize the appropriate server based on the current DCC environment:

```python
# This will detect the current DCC and start the appropriate server
import tp.libs.rpc.bootstrap
```

### Making Remote Calls

There are several ways to call remote functions:

```python
from tp.libs.rpc.api.interface import call_remote_function

# Call by DCC type and instance name
result = call_remote_function(
    dcc_type="maya",
    instance_name="maya-1",  # Optional, uses first instance if omitted
    function_name="cmds.ls",
    selection=True
)

# Call by direct URI
result = call_remote_function(
    uri="PYRO:rpc.service@localhost:9090",
    function_name="cmds.ls",
    selection=True
)
```

### Listing Available Instances

```python
from tp.libs.rpc.core.instances import list_instances

# List all instances
all_instances = list_instances()
print(all_instances)

# List instances of a specific DCC
maya_instances = list_instances("maya")
print(maya_instances)
```

### Registering Remote Functions

You can register functions that will be available for remote calling:

```python
from tp.libs.rpc.api.decorators import register_function

@register_function()
def calculate_distance(point1, point2):
    """Calculate the distance between two 3D points."""
    import math
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(point1, point2)))
```

You can also register functions remotely at runtime:

```python
from tp.libs.rpc.api.interface import register_function_remotely

def transform_object(object_name, translation):
    """Move an object by the specified translation vector."""
    import maya.cmds as cmds
    cmds.move(translation[0], translation[1], translation[2], object_name, relative=True)
    return cmds.xform(object_name, query=True, translation=True)

# Register this function in a remote Maya instance
register_function_remotely(
    func=transform_object,
    dcc_type="maya",
    instance_name="maya-1"
)

# Now you can call it remotely
from tp.libs.rpc.api.interface import call_remote_function
result = call_remote_function(
    dcc_type="maya",
    function_name="transform_object",
    object_name="pCube1",
    translation=[1, 0, 0]
)
```

## Advanced Features

### Progress Reporting

For long-running operations, you can report progress back to the caller:

```python
from tp.libs.rpc.api.decorators import register_function

@register_function()
def process_large_dataset(dataset_path, report_progress=None):
    """Process a large dataset with progress reporting."""
    import time

    # The report_progress parameter is automatically injected by the task manager
    # when the function is called as a background task

    # Load dataset
    if report_progress:
        report_progress(0.1, "Loading dataset...")
    time.sleep(1)  # Simulate loading

    # Process data
    if report_progress:
        report_progress(0.5, "Processing data...")
    time.sleep(2)  # Simulate processing

    # Finalize
    if report_progress:
        report_progress(0.9, "Finalizing results...")
    time.sleep(0.5)  # Simulate finalization

    return "Processing complete"

# To call this function and monitor progress:
from tp.libs.rpc.api.interface import call_remote_function

# Submit as a background task
task_id = call_remote_function(
    dcc_type="maya",
    function_name="submit_task",
    function_name_="process_large_dataset",  # Actual function to run
    dataset_path="/path/to/data"
)

# Monitor progress
while True:
    status = call_remote_function(
        dcc_type="maya",
        function_name="get_task_status",
        task_id=task_id
    )

    progress = call_remote_function(
        dcc_type="maya",
        function_name="get_task_progress",
        task_id=task_id
    )

    progress_value, progress_message = progress
    print(f"Progress: {progress_value:.0%} - {progress_message}")

    if status in ["done", "failed", "canceled"]:
        break

    import time
    time.sleep(0.5)

# Get the result when done
if status == "done":
    result = call_remote_function(
        dcc_type="maya",
        function_name="get_task_result",
        task_id=task_id
    )
    print(f"Result: {result}")
```

### Interactive Console

tp-rpc includes an interactive console for testing and debugging:

```bash
# Start the console
python -m tp.libs.rpc.cli console

# Connect to a specific DCC
python -m tp.libs.rpc.cli console --dcc maya --instance maya-main
```

Console commands:
- `connect <dcc_type> [instance_name]`: Connect to a DCC instance
- `functions`: List available remote functions
- `describe <function_name>`: Show function signature and documentation
- `call <function_name> [args] [key=value]`: Call a remote function
- `progress <task_id>`: Monitor progress of a background task
- `tasks`: List all running and completed tasks
- `format [plain|json|yaml]`: Set output format
- `help`: Show available commands

### Cross-Platform File Transfer

Transfer files between different DCC applications:

```python
# Send a file from the current application to Maya
from tp.libs.rpc.core.file_transfer import send_file_to_dcc

result = send_file_to_dcc(
    file_path="C:/path/to/local/file.ma",
    dcc_type="maya",
    instance_name="maya-main",
    remote_dir="/path/on/maya/machine"
)
print(f"File sent to: {result['remote_path']}")

# Get a file from Unreal Engine
from tp.libs.rpc.core.file_transfer import get_file_from_dcc

result = get_file_from_dcc(
    remote_file_path="/path/on/unreal/machine/asset.uasset",
    dcc_type="unreal",
    instance_name="unreal-main",
    output_dir="C:/local/download/folder"
)
print(f"File received at: {result['local_path']}")
```

Using the command line:

```bash
# Send a file
python -m tp.libs.rpc.cli file send C:/path/to/file.ma --dcc maya --remote-dir /maya/path

# Get a file
python -m tp.libs.rpc.cli file get /unreal/path/asset.uasset --dcc unreal --output-dir C:/downloads
```

### Plugin Hot-Reloading

Reload plugins without restarting the server:

```python
from tp.libs.rpc.hooks.loader import reload_plugin

# Reload a specific plugin
reload_plugin(
    dcc_type="maya",
    port=9090,
    instance_name="maya-main"
)
```

Using the command line:

```bash
python -m tp.libs.rpc.cli reload --dcc maya --instance-name maya-main
```

### Dependency Injection

Use dependency injection to provide services to your functions:

```python
from tp.libs.rpc.core.di import inject, provide
from tp.libs.rpc.api.decorators import register_function

# Define a service
class LoggingService:
    def log(self, message):
        print(f"[LOG] {message}")

# Register the service in the DI container
provide("logging", LoggingService())

# Use the service in a remote function
@register_function()
@inject("logging")
def process_with_logging(data, logging=None):
    """Process data with logging."""
    logging.log(f"Processing data: {data}")
    # Process the data...
    logging.log("Processing complete")
    return "Done"

# The function can now be called remotely without needing to pass the logging service
```

### Callback Systems

Register callbacks for events:

```python
from tp.libs.rpc.core.events import get_event_bus, Event

# Get the event bus
event_bus = get_event_bus()

# Subscribe to events
def on_task_progress(event):
    print(f"Task {event.data['task_id']} progress: {event.data['progress']:.0%} - {event.data['message']}")

# Subscribe to task progress events
unsubscribe = event_bus.subscribe("task_progress", on_task_progress)

# Later, unsubscribe when no longer needed
unsubscribe()

# Subscribe to task completion
def on_task_completed(event):
    print(f"Task {event.data['task_id']} completed with status: {event.data['status']}")

event_bus.subscribe("task_completed", on_task_completed)

# You can also publish custom events
event_bus.publish(Event("custom_event", {"message": "Something happened"}))
```

### Main Thread Execution

Many DCC applications require certain operations to be performed on the main thread. tp-rpc handles this automatically:

```python
from tp.libs.rpc.api.interface import call_remote_function

# This will be executed on Maya's main thread, even if called from a background thread
result = call_remote_function(
    dcc_type="maya",
    function_name="cmds.playblast",
    filename="/path/to/output.mp4",
    format="mp4",
    quality=100
)
```

### Asynchronous Tasks

For long-running operations, you can use the task manager:

```python
from tp.libs.rpc.api.interface import call_remote_function

# Submit a task to run asynchronously
task_id = call_remote_function(
    dcc_type="maya",
    function_name="submit_task",
    output_path="/path/to/render"
)

# Check task status
status = call_remote_function(
    dcc_type="maya",
    function_name="get_task_status",
    task_id=task_id
)

# Get task result when complete
if status == "done":
    result = call_remote_function(
        dcc_type="maya",
        function_name="get_task_result",
        task_id=task_id
    )
```

### Batch Operations

For better performance when making multiple calls:

```python
from tp.libs.rpc.core.client import RPCClient
from tp.libs.rpc.core.instances import get_uri

# Get the URI for a Maya instance
uri = get_uri("maya", "maya-1")

# Create a client
client = RPCClient(uri)

try:
    # Prepare batch calls
    calls = [
        {"function": "cmds.polyCube", "args": [], "kwargs": {"name": "cube1"}},
        {"function": "cmds.polySphere", "args": [], "kwargs": {"name": "sphere1"}},
        {"function": "cmds.polyCylinder", "args": [], "kwargs": {"name": "cylinder1"}}
    ]

    # Execute batch call
    results = client.batch_call(calls)

    # Process results
    for i, result in enumerate(results):
        if result["status"] == "success":
            print(f"Call {i} succeeded: {result['result']}")
        else:
            print(f"Call {i} failed: {result['error']}")
finally:
    client.close()
```

### Health Monitoring

Monitor the health of RPC instances:

```python
from tp.libs.rpc.core.health import get_health_monitor

# Get the health monitor
monitor = get_health_monitor()

# Start monitoring
monitor.start()

# Register a callback for health status changes
def on_health_change(dcc_type, instance_name, is_healthy):
    if not is_healthy:
        print(f"Warning: {dcc_type}/{instance_name} is not responding!")

monitor.register_callback(on_health_change)

# Get current status
status = monitor.get_status()
print(status)

# Stop monitoring when done
monitor.stop()
```

## DCC Integration

tp-rpc provides specialized plugins for various DCC applications:

### Maya

```python
from tp.libs.rpc.hooks.plugins import maya_plugin

# Start the server
maya_plugin.initialize(port=9090)

# Register a Maya-specific function
from tp.libs.rpc.api.decorators import register_function

@register_function()
def create_basic_rig(character_name):
    import maya.cmds as cmds
    # Create a simple character rig
    # ...
    return f"Created rig for {character_name}"
```

### Unreal Engine

```python
from tp.libs.rpc.hooks.plugins import unreal_plugin

# Start the server
unreal_plugin.initialize(port=9091)

# Register an Unreal-specific function
from tp.libs.rpc.api.decorators import register_function

@register_function()
def spawn_actor(actor_class, location, rotation):
    import unreal
    # Spawn an actor in the level
    # ...
    return "Actor spawned successfully"
```

### Blender

```python
from tp.libs.rpc.hooks.plugins import blender_plugin

# Start the server
blender_plugin.initialize(port=9092)

# Register a Blender-specific function
from tp.libs.rpc.api.decorators import register_function

@register_function()
def create_material(name, base_color):
    import bpy
    # Create a new material
    # ...
    return f"Created material: {name}"
```

## Security

### Authentication

Enable authentication for secure remote calls:

```python
# Set a strong secret key in the environment
import os
os.environ["TP_DCC_RPC_SECRET"] = "your-strong-secret-key"
os.environ["TP_DCC_RPC_REQUIRE_AUTH"] = "1"

# When making authenticated calls
from tp.libs.rpc.api.interface import call_remote_function
from tp.libs.rpc.core.security import generate_auth_token

# Generate an auth token for the function
function_name = "secure_function"
auth_token = generate_auth_token(function_name)

# Make the authenticated call
result = call_remote_function(
    dcc_type="maya",
    function_name=function_name,
    _auth_token=auth_token,
    # Other arguments...
)
```

### Access Control

Restrict which clients can call specific functions:

```python
from tp.libs.rpc.core.security import register_function_acl

# Only allow Maya instances to call this function
register_function_acl("export_animation", ["maya-.*"])

# Only allow specific instances to call this function
register_function_acl("render_scene", ["maya-main", "unreal-master"])
```

### Environment Controls

Control whether remote operations can modify the environment:

```python
# Disable remote environment control
import os
os.environ["TP_DCC_RPC_ALLOW_ENV_CONTROL"] = "0"

# Disable remote control operations (shutdown, kill, etc.)
os.environ["TP_DCC_RPC_ALLOW_REMOTE_CONTROL"] = "0"
```

## Performance Optimization

### Connection Pooling

Reuse connections for better performance:

```python
from tp.libs.rpc.core.client import RPCClient

# Create a client with connection pooling enabled
client = RPCClient(
    uri="PYRO:rpc.service@localhost:9090",
    use_pooling=True,
    max_connections=5
)

# Make multiple calls with the same client
for i in range(100):
    result = client.call("some_function", i)
    print(result)

client.close()
```

### Compression

Enable compression for large data transfers:

```python
import os

# Enable compression
os.environ["TP_DCC_RPC_ENABLE_COMPRESSION"] = "1"

# Set compression threshold (in bytes)
os.environ["TP_DCC_RPC_COMPRESSION_THRESHOLD"] = "1024"  # 1KB
```

### Serialization Format

Choose the most efficient serialization format:

```python
import os

# Use msgpack for faster serialization (default is pickle)
os.environ["TP_DCC_RPC_SERIALIZATION_FORMAT"] = "msgpack"
```

## Error Handling

### Retry Mechanism

tp-rpc includes automatic retry for network errors:

```python
from tp.libs.rpc.core.client import RPCClient

# Create a client with retry enabled
client = RPCClient(
    uri="PYRO:rpc.service@localhost:9090",
    retry_enabled=True,
    max_attempts=3
)

# This call will automatically retry up to 3 times if network errors occur
result = client.call("function_name")
```

### Custom Error Handling

Use the error handling decorator for standardized error handling:

```python
from tp.libs.rpc.core.errors import handle_rpc_errors, InvalidArgumentError

@handle_rpc_errors({ValueError: InvalidArgumentError})
def process_data(data):
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    # Process the data...
    return "Processed successfully"
```

## Configuration

tp-rpc can be configured through environment variables or the configuration system:

```python
from tp.libs.rpc.core.config import get_config

# Get the configuration manager
config = get_config()

# Get configuration values
host = config.get("server", "host")
port = config.get("server", "default_port")

# Set configuration values
config.set("server", "host", "0.0.0.0")  # Listen on all interfaces
config.set("security", "require_authentication", True)
```

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure the server is running and the port is not blocked by a firewall.

2. **Function Not Found**: Verify that the function is registered on the server using `list_remote_functions()`.

3. **Authentication Errors**: Check that the secret key matches between client and server.

4. **Thread Errors**: Some DCC operations must run on the main thread. Use the main thread execution mechanism.

### Debugging

Enable detailed logging:

```python
import logging
import os

# Set log level
os.environ["TP_DCC_RPC_LOG_LEVEL"] = "DEBUG"

# Log to file
os.environ["TP_DCC_RPC_LOG_FILE"] = "/path/to/log.txt"
```

## API Reference

### Core Modules

- `tp.libs.rpc.api.interface`: High-level interface for remote calls
- `tp.libs.rpc.api.decorators`: Function decorators for registration
- `tp.libs.rpc.core.client`: Client implementation
- `tp.libs.rpc.core.server`: Server implementation
- `tp.libs.rpc.core.instances`: Instance registry management
- `tp.libs.rpc.core.registry`: Function registry
- `tp.libs.rpc.core.security`: Authentication and authorization
- `tp.libs.rpc.core.config`: Configuration management
- `tp.libs.rpc.core.health`: Health monitoring
- `tp.libs.rpc.core.task_manager`: Asynchronous task management
- `tp.libs.rpc.core.events`: Event bus for callbacks and notifications
- `tp.libs.rpc.core.file_transfer`: Cross-platform file transfer utilities
- `tp.libs.rpc.core.di`: Dependency injection system
- `tp.libs.rpc.console`: Interactive console for testing and debugging

### DCC Plugins

- `tp.libs.rpc.hooks.plugins.maya_plugin`: Maya integration
- `tp.libs.rpc.hooks.plugins.unreal_plugin`: Unreal Engine integration
- `tp.libs.rpc.hooks.plugins.blender_plugin`: Blender integration
- `tp.libs.rpc.hooks.plugins.houdini_plugin`: Houdini integration
- `tp.libs.rpc.hooks.plugins.mobu_plugin`: MotionBuilder integration
- `tp.libs.rpc.hooks.plugins.substancedesigner_plugin`: Substance Designer integration
- `tp.libs.rpc.hooks.plugins.substancepainter_plugin`: Substance Painter integration
