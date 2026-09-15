import socket

WHOIS_SERVERS: dict[str, str] = {
    "com": "whois.verisign-grs.com",
    "net": "whois.verisign-grs.com",
    "io": "whois.nic.io",
    "dev": "whois.nic.google",
    "app": "whois.nic.google",
    "co": "whois.nic.co",
    "org": "whois.pir.org",
    "ai": "whois.nic.ai",
    "sh": "whois.nic.sh",
    "xyz": "whois.nic.xyz",
}

IANA_SERVER = "whois.iana.org"


class WhoisClient:
    def __init__(self, timeout_s: float = 10.0, port: int = 43) -> None:
        self._timeout_s = timeout_s
        self._port = port

    def server_for(self, tld: str) -> str:
        return WHOIS_SERVERS.get(tld, IANA_SERVER)

    def query(self, domain: str, server: str) -> str:
        address = socket.gethostbyname(server)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self._timeout_s)
        try:
            sock.connect((address, self._port))
            sock.sendall(f"{domain}\r\n".encode())
            chunks: list[bytes] = []
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            sock.close()
        return b"".join(chunks).decode("utf-8", errors="replace")
