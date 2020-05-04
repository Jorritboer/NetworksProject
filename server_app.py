#!/usr/local/bin/python3

import argparse
from btcp.server_socket import BTCPServerSocket


def main(printSegments,window = 100, timeout = 100, output = "output.file"):
    # Create a bTCP server socket
    s = BTCPServerSocket(window, timeout, printSegments)
    # TODO Write your file transfer server code here using your BTCPServerSocket's accept, and recv methods.
    s.accept()
    file = s.recv()
    # Clean up any state
    s.close()
    return file
    #return s._currentSeqNum