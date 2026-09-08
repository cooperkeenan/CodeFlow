import random
import socket
import struct
from pathlib import Path

from naming.models import DnsAnswer

RECORD_NS = 2
RECORD_A = 1

_FALLBACK_SERVERS = ("1.1.1.1", "8.8.8.8", "9.9.9.9")
_RESOLV_CONF = Path("/etc/resolv.conf")
_HEADER = ">HHHHHH"


class DnsResolver:
    def __init__(self, servers: tuple[str, ...] = (), timeout_s: float = 4.0) -> None:
        self._servers = servers or self._system_servers()
        self._timeout_s = timeout_s

    def query(self, name: str, record_type: int) -> DnsAnswer:
        last_error = "no nameserver configured"
        for server in self._servers:
            try:
                return self._ask(server, name, record_type)
            except (OSError, struct.error) as error:
                last_error = f"{server}: {type(error).__name__}: {error}"
        return DnsAnswer(rcode=-1, answers=0, ok=False, error=last_error)

    def _ask(self, server: str, name: str, record_type: int) -> DnsAnswer:
        transaction_id = random.randint(0, 0xFFFF)
        packet = self._build(transaction_id, name, record_type)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.settimeout(self._timeout_s)
            sock.sendto(packet, (server, 53))
            payload, _ = sock.recvfrom(4096)
        finally:
            sock.close()
        return self._parse(transaction_id, payload)

    def _build(self, transaction_id: int, name: str, record_type: int) -> bytes:
        header = struct.pack(_HEADER, transaction_id, 0x0100, 1, 0, 0, 0)
        labels = b"".join(
            bytes([len(part)]) + part.encode("idna") for part in name.strip(".").split(".")
        )
        return header + labels + b"\x00" + struct.pack(">HH", record_type, 1)

    def _parse(self, transaction_id: int, payload: bytes) -> DnsAnswer:
        if len(payload) < 12:
            return DnsAnswer(rcode=-1, answers=0, ok=False, error="short response")
        fields = struct.unpack(_HEADER, payload[:12])
        if fields[0] != transaction_id:
            return DnsAnswer(rcode=-1, answers=0, ok=False, error="transaction id mismatch")
        return DnsAnswer(rcode=fields[1] & 0xF, answers=fields[3], ok=True)

    def _system_servers(self) -> tuple[str, ...]:
        found: list[str] = []
        try:
            for line in _RESOLV_CONF.read_text(encoding="utf-8").splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[0] == "nameserver" and ":" not in parts[1]:
                    found.append(parts[1])
        except OSError:
            found = []
        return tuple(found) or _FALLBACK_SERVERS
