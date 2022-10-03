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


class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        """Hang."""
        while True:
            time.sleep(60)


def func(host, port):
    """Create the server, binding to host and port."""
    with socketserver.TCPServer((host, port), MyTCPHandler) as server:
        server.serve_forever()


def run(port):
    """Start the TCP server."""
    proc = Process(target=func, args=('localhost', port))
    proc.start()
    return proc
