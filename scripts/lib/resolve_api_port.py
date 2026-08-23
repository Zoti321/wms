"""为本地开发选择可绑定的 API 端口（Windows Hyper-V 常保留 8000/8080）。"""

from __future__ import annotations

import socket
import sys
import unittest
from unittest.mock import MagicMock, patch

DEFAULT_CANDIDATES = (8000, 9000, 18000)


def can_bind(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def resolve(
    explicit: int | None = None,
    candidates: tuple[int, ...] = DEFAULT_CANDIDATES,
) -> int:
    if explicit is not None:
        if not can_bind(explicit):
            raise SystemExit(f"cannot bind WMS_API_PORT={explicit}")
        return explicit

    for port in candidates:
        if can_bind(port):
            return port

    joined = ", ".join(str(p) for p in candidates)
    raise SystemExit(f"cannot bind any candidate port: {joined}")


def main() -> None:
    explicit: int | None = None
    if len(sys.argv) > 1 and sys.argv[1].strip():
        explicit = int(sys.argv[1])
    port = resolve(explicit)
    print(port)


class ResolveApiPortTests(unittest.TestCase):
    def test_resolve_uses_first_bindable_candidate(self) -> None:
        mock_sock = MagicMock()
        bind_errors = {8000: OSError("reserved"), 8080: OSError("reserved")}

        def bind(addr: tuple[str, int]) -> None:
            port = addr[1]
            if port in bind_errors:
                raise bind_errors[port]

        mock_sock.bind.side_effect = bind

        with patch(f"{__name__}.socket.socket", return_value=mock_sock):
            port = resolve(candidates=(8000, 8080, 9000))
        self.assertEqual(port, 9000)

    def test_resolve_honors_explicit_port(self) -> None:
        with patch(f"{__name__}.can_bind", return_value=True):
            self.assertEqual(resolve(explicit=7777), 7777)

    def test_resolve_fails_when_explicit_port_unavailable(self) -> None:
        with patch(f"{__name__}.can_bind", return_value=False):
            with self.assertRaises(SystemExit):
                resolve(explicit=8000)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        unittest.main(argv=[sys.argv[0]])
    main()
