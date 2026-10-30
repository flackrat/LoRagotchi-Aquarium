"""The openHop companion transport, tested against a fake companion on loopback."""
import socket
import threading

import pytest

from tank.protocol import StreamFrames, frame
from tank.transport import OpenHopCompanionTransport, open_transport


def _fake_companion(replies):
    """Accept one client, read its '<' frames, and send back the given '>' replies."""
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    received = []

    def run():
        sock, _ = server.accept()
        parser = StreamFrames(b"<")
        with sock:
            sock.settimeout(2)
            while len(received) < 1:
                try:
                    data = sock.recv(1024)
                except socket.timeout:
                    break
                if not data:
                    break
                received.extend(parser.feed(data))
            for payload in replies:
                sock.sendall(frame(payload, direction=b">"))
        server.close()

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    return server.getsockname()[1], received, worker


def test_frames_out_and_replies_in_over_real_tcp():
    port, received, worker = _fake_companion([b"\x05hello"])
    transport = OpenHopCompanionTransport("127.0.0.1", port)
    transport.send(b"\x01\x03      mesh")
    reply = transport.receive(timeout=3)
    worker.join(3)
    transport.close()
    assert received == [b"\x01\x03      mesh"]
    assert reply == b"\x05hello"


def test_open_transport_reads_the_openhop_uri():
    port, _, worker = _fake_companion([])
    transport = open_transport(f"openhop:127.0.0.1:{port}")
    assert isinstance(transport, OpenHopCompanionTransport)
    transport.close()
    worker.join(3)


def test_bad_uri_names_the_new_option():
    with pytest.raises(ValueError) as err:
        open_transport("nonsense:1")
    assert "openhop:HOST:PORT" in str(err.value)


def test_refused_connection_raises_promptly():
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    with pytest.raises(OSError):
        OpenHopCompanionTransport("127.0.0.1", port)
