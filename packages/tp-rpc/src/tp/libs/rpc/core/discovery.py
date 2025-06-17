from __future__ import annotations

import os
import time
import json
import socket
import threading

from loguru import logger

from .instances import register_instance

# Default multicast group and port for service discovery.
DEFAULT_MULTICAST_GROUP = "239.0.0.1"
DEFAULT_MULTICAST_PORT = 9999

# Service announcement interval in seconds.
ANNOUNCE_INTERVAL = 30

# Service timeout in seconds (how long before a service is considered offline).
SERVICE_TIMEOUT = 90


class ServiceDiscovery:
    """Service discovery using multicast for automatic RPC service
    detection.
    """

    def __init__(
        self,
        multicast_group: str = DEFAULT_MULTICAST_GROUP,
        multicast_port: int = DEFAULT_MULTICAST_PORT,
        announce_interval: float = ANNOUNCE_INTERVAL,
    ):
        """Initialize the service discovery.

        Args:
            multicast_group: Multicast group address
            multicast_port: Multicast port
            announce_interval: Interval between service announcements in seconds
        """

        self._multicast_group = multicast_group
        self._multicast_port = multicast_port
        self._announce_interval = announce_interval
        self._running = False
        self._listener_thread = None
        self._announcer_thread = None
        self._services: dict[
            str, dict
        ] = {}  # {service_id: {uri, dcc_type, instance_name, last_seen}}
        self._lock = threading.RLock()

        # Get the hostname for service identification
        self._hostname = socket.gethostname()

    def start_listener(self):
        """Start listening for service announcements."""

        if self._listener_thread and self._listener_thread.is_alive():
            return

        self._running = True
        self._listener_thread = threading.Thread(
            target=self._listen_for_announcements,
            daemon=True,
            name="ServiceDiscoveryListener",
        )
        self._listener_thread.start()
        logger.info(
            f"[tp-rpc][discovery] Started service discovery listener "
            f"on {self._multicast_group}:{self._multicast_port}"
        )

    def start_announcer(self, uri: str, dcc_type: str, instance_name: str):
        """Start announcing a service.

        Args:
            uri: The URI of the service
            dcc_type: The DCC type
            instance_name: The instance name
        """

        if self._announcer_thread and self._announcer_thread.is_alive():
            return

        self._running = True
        self._announcer_thread = threading.Thread(
            target=self._announce_service,
            args=(uri, dcc_type, instance_name),
            daemon=True,
            name="ServiceDiscoveryAnnouncer",
        )
        self._announcer_thread.start()
        logger.info(
            f"[tp-rpc][discovery] Started service announcer "
            f"for {dcc_type}/{instance_name}"
        )

    def stop(self):
        """Stop the service discovery."""

        self._running = False

        if self._listener_thread:
            self._listener_thread.join(timeout=2.0)
            self._listener_thread = None

        if self._announcer_thread:
            self._announcer_thread.join(timeout=2.0)
            self._announcer_thread = None

        logger.info("[tp-rpc][discovery] Stopped service discovery")

    def _listen_for_announcements(self):
        """Internal function that listens for service announcements on the
        multicast group.
        """

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind to the multicast port.
        sock.bind(("", self._multicast_port))

        # Join the multicast group.
        mreq = socket.inet_aton(self._multicast_group) + socket.inet_aton("0.0.0.0")
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        # Set a timeout so we can check if we should stop.
        sock.settimeout(1.0)

        while self._running:
            try:
                data, addr = sock.recvfrom(1024)
                self._handle_announcement(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"[tp-rpc][discovery] Error in listener: {e}")
                time.sleep(1.0)  # Avoid tight loop on error

    def _handle_announcement(self, data: bytes, addr: tuple[str, int]):
        """Internal function that handles a service announcement.

        Args:
            data: The announcement data
            addr: The sender address (ip, port)
        """

        try:
            announcement = json.loads(data.decode("utf-8"))

            uri = announcement.get("uri")
            dcc_type = announcement.get("dcc_type")
            instance_name = announcement.get("instance_name")
            hostname = announcement.get("hostname")

            if not all([uri, dcc_type, instance_name, hostname]):
                return

            # Create a unique service ID
            service_id = f"{hostname}/{dcc_type}/{instance_name}"

            with self._lock:
                if service_id in self._services:
                    # Update existing service
                    self._services[service_id].update(
                        {
                            "uri": uri,
                            "dcc_type": dcc_type,
                            "instance_name": instance_name,
                            "hostname": hostname,
                            "last_seen": time.time(),
                        }
                    )
                else:
                    # New service
                    self._services[service_id] = {
                        "uri": uri,
                        "dcc_type": dcc_type,
                        "instance_name": instance_name,
                        "hostname": hostname,
                        "last_seen": time.time(),
                        "address": addr[0],
                    }
                    logger.info(
                        f"[tp-rpc][discovery] Discovered new "
                        f"service: {service_id} at {uri}"
                    )

                    # Register the instance in our local registry
                    if (
                        hostname == self._hostname
                        or os.environ.get("TP_DCC_RPC_REGISTER_REMOTE", "0") == "1"
                    ):
                        try:
                            register_instance(dcc_type, uri, instance_name)
                            logger.info(
                                f"[tp-rpc][discovery] Registered remote "
                                f"instance: {dcc_type}/{instance_name}"
                            )
                        except Exception as e:
                            logger.error(
                                f"[tp-rpc][discovery] Error registering instance: {e}"
                            )

        except Exception as e:
            logger.error(f"[tp-rpc][discovery] Error handling announcement: {e}")

    def _announce_service(self, uri: str, dcc_type: str, instance_name: str):
        """Periodically announce a service.

        Args:
            uri: The URI of the service
            dcc_type: The DCC type
            instance_name: The instance name
        """

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        announcement = {
            "uri": uri,
            "dcc_type": dcc_type,
            "instance_name": instance_name,
            "hostname": self._hostname,
        }

        announcement_data = json.dumps(announcement).encode("utf-8")

        while self._running:
            try:
                sock.sendto(
                    announcement_data,
                    (self._multicast_group, self._multicast_port),
                )
                logger.debug(
                    f"[tp-rpc][discovery] Announced "
                    f"service: {dcc_type}/{instance_name}"
                )
            except Exception as e:
                logger.error(f"[tp-rpc][discovery] Error announcing service: {e}")

            # Sleep until next announcement.
            for _ in range(int(self._announce_interval * 2)):
                if not self._running:
                    break
                time.sleep(0.5)

    def cleanup_services(self):
        """Remove services that haven't been seen recently."""

        with self._lock:
            now = time.time()
            expired = []

            for service_id, service in list(self._services.items()):
                if now - service["last_seen"] > SERVICE_TIMEOUT:
                    expired.append(service_id)

            for service_id in expired:
                self._services.pop(service_id)
                logger.info(f"[tp-rpc][discovery] Service expired: {service_id}")

    def get_services(self, dcc_type: str | None = None) -> list[dict]:
        """Get all discovered services.

        Args:
            dcc_type: Optional filter by DCC type

        Returns:
            List of service dictionaries
        """

        self.cleanup_services()

        with self._lock:
            if dcc_type:
                return [s for s in self._services.values() if s["dcc_type"] == dcc_type]
            else:
                return list(self._services.values())


# Global service discovery instance
_service_discovery = ServiceDiscovery()


def get_service_discovery() -> ServiceDiscovery:
    """Get the global service discovery instance.

    Returns:
        The singleton ServiceDiscovery instance
    """
    return _service_discovery
