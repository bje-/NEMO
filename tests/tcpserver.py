# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""A simple TCP server for testing TCP timeouts."""

import socketserver
import time
from multiprocessing import Process


class HTTP400Handler(socketserver.BaseRequestHandler):
    """A socket server that returns HTTP error 400."""

    def handle(self):
        """Send error 400 and quit."""
        self.request.recv(1024)
        self.request.sendall(b'HTTP/1.1 400 Bad Request\n')


class BlockingTCPHandler(socketserver.BaseRequestHandler):
    """A socket server that just blocks."""

    def handle(self):
        """Just block."""
        while True:
            time.sleep(60)


def func(host, port, action):
    """Create the server, binding to host and port."""
    if action == 'block':
        with socketserver.TCPServer((host, port),
                                    BlockingTCPHandler) as server:
            server.serve_forever()
    elif action == 'http400':
        with socketserver.TCPServer((host, port),
                                    HTTP400Handler) as server:
            server.serve_forever()


def run(port, action):
    """Start the TCP server."""
    proc = Process(target=func, args=('localhost', port, action))
    proc.start()
    return proc
