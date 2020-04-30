#!/usr/local/bin/python3

import argparse
from btcp.server_socket import BTCPServerSocket


def main(window = 100, timeout = 100, output = "output.file"):
    # Create a bTCP server socket
    s = BTCPServerSocket(window, timeout)
    # TODO Write your file transfer server code here using your BTCPServerSocket's accept, and recv methods.
    s.accept()
    s.recv()
    # Clean up any state
    s.close()
    #return s._currentSeqNum