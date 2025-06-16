from __future__ import annotations

import base64
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, Any

from .compression import compress_data, decompress_data
from .task_manager import get_task_manager
from .registry import register_function


class FileTransferError(Exception):
    """Exception raised for errors during file transfer operations."""

    pass


def calculate_file_hash(file_path: str | Path) -> str:
    """Calculate MD5 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        MD5 hash of the file

    Raises:
        FileTransferError: If the file cannot be read
    """
    try:
        with open(file_path, "rb") as f:
            file_hash = hashlib.md5()
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                file_hash.update(chunk)
            return file_hash.hexdigest()
    except Exception as e:
        raise FileTransferError(f"Failed to calculate file hash: {e}")


def encode_file(
    file_path: str | Path, compress: bool = True, report_progress: callable = None
) -> Dict[str, Any]:
    """Encode a file for transfer.

    Args:
        file_path: Path to the file
        compress: Whether to compress the file data
        report_progress: Optional progress reporting callback

    Returns:
        Dictionary with encoded file data and metadata

    Raises:
        FileTransferError: If the file cannot be read or encoded
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileTransferError(f"File not found: {file_path}")

        file_size = file_path.stat().st_size
        file_name = file_path.name

        if report_progress:
            report_progress(0.1, f"Reading file: {file_name}")

        # Read file in binary mode
        with open(file_path, "rb") as f:
            file_data = f.read()

        if report_progress:
            report_progress(0.4, "Calculating hash")

        file_hash = hashlib.md5(file_data).hexdigest()

        if report_progress:
            report_progress(0.5, "Encoding data")

        # Base64 encode the data
        encoded_data = base64.b64encode(file_data).decode("utf-8")

        if compress and file_size > 1024:  # Only compress files larger than 1KB
            if report_progress:
                report_progress(0.7, "Compressing data")
            compressed_data = compress_data(encoded_data)
            data = compressed_data
            is_compressed = True
        else:
            data = encoded_data
            is_compressed = False

        if report_progress:
            report_progress(0.9, "Preparing transfer package")

        # Create transfer package
        transfer_package = {
            "file_name": file_name,
            "file_size": file_size,
            "file_hash": file_hash,
            "is_compressed": is_compressed,
            "data": data,
        }

        if report_progress:
            report_progress(1.0, "File encoded successfully")

        return transfer_package

    except Exception as e:
        raise FileTransferError(f"Failed to encode file: {e}")


def decode_file(
    transfer_package: Dict[str, Any],
    output_dir: str | Path = None,
    output_file: str | Path = None,
    report_progress: callable = None,
) -> str:
    """Decode a file from a transfer package.

    Args:
        transfer_package: Dictionary with encoded file data and metadata
        output_dir: Directory to save the file to (default: temp directory)
        output_file: Specific file path to save to (overrides output_dir)
        report_progress: Optional progress reporting callback

    Returns:
        Path to the decoded file

    Raises:
        FileTransferError: If the file cannot be decoded or written
    """
    try:
        if report_progress:
            report_progress(0.1, "Validating transfer package")

        # Validate transfer package
        required_keys = ["file_name", "file_size", "file_hash", "is_compressed", "data"]
        for key in required_keys:
            if key not in transfer_package:
                raise FileTransferError(f"Invalid transfer package: missing '{key}'")

        file_name = transfer_package["file_name"]
        is_compressed = transfer_package["is_compressed"]
        data = (
            transfer_package["file_data"]
            if "file_data" in transfer_package
            else transfer_package["data"]
        )

        if report_progress:
            report_progress(0.3, "Decoding data")

        # Decompress if needed
        if is_compressed:
            if report_progress:
                report_progress(0.4, "Decompressing data")
            decoded_data = decompress_data(data)
        else:
            decoded_data = data

        if report_progress:
            report_progress(0.6, "Decoding base64")

        # Decode base64
        file_data = base64.b64decode(decoded_data)

        if report_progress:
            report_progress(0.7, "Verifying file integrity")

        # Verify hash
        calculated_hash = hashlib.md5(file_data).hexdigest()
        if calculated_hash != transfer_package["file_hash"]:
            raise FileTransferError(
                f"File integrity check failed: hash mismatch "
                f"(expected: {transfer_package['file_hash']}, got: {calculated_hash})"
            )

        if report_progress:
            report_progress(0.8, "Writing file to disk")

        # Determine output path
        if output_file:
            output_path = Path(output_file)
        else:
            if output_dir:
                output_dir = Path(output_dir)
                if not output_dir.exists():
                    output_dir.mkdir(parents=True)
            else:
                output_dir = Path(tempfile.gettempdir())

            output_path = output_dir / file_name

        # Write file
        with open(output_path, "wb") as f:
            f.write(file_data)

        if report_progress:
            report_progress(1.0, f"File saved to {output_path}")

        return str(output_path)

    except Exception as e:
        raise FileTransferError(f"Failed to decode file: {e}")


def send_file_to_dcc(
    file_path: str | Path,
    dcc_type: str,
    instance_name: str = None,
    remote_dir: str = None,
    compress: bool = True,
) -> Dict[str, Any]:
    """Send a file to a remote DCC.

    Args:
        file_path: Path to the file to send
        dcc_type: Target DCC type
        instance_name: Target instance name
        remote_dir: Directory on the remote system to save the file to
        compress: Whether to compress the file data

    Returns:
        Dictionary with transfer result information

    Raises:
        FileTransferError: If the file cannot be sent
    """
    from tp.libs.rpc.api.interface import call_remote_function

    try:
        # Submit as a background task to show progress
        task_manager = get_task_manager()
        task_id = task_manager.submit(encode_file, file_path, compress)

        # Wait for encoding to complete
        while task_manager.get_status(task_id) not in ["done", "failed", "canceled"]:
            import time

            time.sleep(0.1)

        if task_manager.get_status(task_id) != "done":
            raise FileTransferError("File encoding failed")

        # Get the encoded file
        transfer_package = task_manager.get_result(task_id)

        # Send to remote DCC
        result = call_remote_function(
            dcc_type=dcc_type,
            instance_name=instance_name,
            function_name="receive_file",
            transfer_package=transfer_package,
            output_dir=remote_dir,
        )

        return {
            "success": True,
            "remote_path": result,
            "file_name": transfer_package["file_name"],
            "file_size": transfer_package["file_size"],
            "file_hash": transfer_package["file_hash"],
        }

    except Exception as e:
        raise FileTransferError(f"Failed to send file: {e}")


@register_function()
def receive_file(transfer_package: Dict[str, Any], output_dir: str = None) -> str:
    """Receive a file from a transfer package.

    This function is meant to be registered as an RPC function.

    Args:
        transfer_package: Dictionary with encoded file data and metadata
        output_dir: Directory to save the file to

    Returns:
        Path to the saved file

    Raises:
        FileTransferError: If the file cannot be received
    """
    try:
        # Submit as a background task to show progress
        task_manager = get_task_manager()
        task_id = task_manager.submit(decode_file, transfer_package, output_dir)

        # Wait for decoding to complete
        while task_manager.get_status(task_id) not in ["done", "failed", "canceled"]:
            import time

            time.sleep(0.1)

        if task_manager.get_status(task_id) != "done":
            raise FileTransferError("File decoding failed")

        # Get the decoded file path
        file_path = task_manager.get_result(task_id)

        return file_path

    except Exception as e:
        raise FileTransferError(f"Failed to receive file: {e}")


def get_file_from_dcc(
    remote_file_path: str,
    dcc_type: str,
    instance_name: str = None,
    output_dir: str = None,
    output_file: str = None,
) -> Dict[str, Any]:
    """Get a file from a remote DCC.

    Args:
        remote_file_path: Path to the file on the remote system
        dcc_type: Source DCC type
        instance_name: Source instance name
        output_dir: Directory to save the file to
        output_file: Specific file path to save to

    Returns:
        Dictionary with transfer result information

    Raises:
        FileTransferError: If the file cannot be retrieved
    """
    from tp.libs.rpc.api.interface import call_remote_function

    try:
        # Request the file from the remote DCC
        transfer_package = call_remote_function(
            dcc_type=dcc_type,
            instance_name=instance_name,
            function_name="prepare_file_for_transfer",
            file_path=remote_file_path,
        )

        # Submit decoding as a background task to show progress
        task_manager = get_task_manager()
        task_id = task_manager.submit(
            decode_file, transfer_package, output_dir, output_file
        )

        # Wait for decoding to complete
        while task_manager.get_status(task_id) not in ["done", "failed", "canceled"]:
            import time

            time.sleep(0.1)

        if task_manager.get_status(task_id) != "done":
            raise FileTransferError("File decoding failed")

        # Get the decoded file path
        file_path = task_manager.get_result(task_id)

        return {
            "success": True,
            "local_path": file_path,
            "file_name": transfer_package["file_name"],
            "file_size": transfer_package["file_size"],
            "file_hash": transfer_package["file_hash"],
        }

    except Exception as e:
        raise FileTransferError(f"Failed to get file: {e}")


@register_function()
def prepare_file_for_transfer(file_path: str) -> Dict[str, Any]:
    """Prepare a file for transfer.

    This function is meant to be registered as an RPC function.

    Args:
        file_path: Path to the file to prepare

    Returns:
        Transfer package with encoded file data

    Raises:
        FileTransferError: If the file cannot be prepared
    """
    try:
        # Submit as a background task to show progress
        task_manager = get_task_manager()
        task_id = task_manager.submit(encode_file, file_path, True)

        # Wait for encoding to complete
        while task_manager.get_status(task_id) not in ["done", "failed", "canceled"]:
            import time

            time.sleep(0.1)

        if task_manager.get_status(task_id) != "done":
            raise FileTransferError("File encoding failed")

        # Get the encoded file
        transfer_package = task_manager.get_result(task_id)

        return transfer_package

    except Exception as e:
        raise FileTransferError(f"Failed to prepare file: {e}")


@register_function()
def get_task_progress(task_id: str) -> tuple[float, str]:
    """Get the progress of a task.

    Args:
        task_id: ID of the task

    Returns:
        Tuple of (progress_value, progress_message)

    Raises:
        ValueError: If the task ID is invalid
    """
    task_manager = get_task_manager()
    return task_manager.get_progress(task_id)
