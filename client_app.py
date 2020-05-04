#!/usr/local/bin/python3

import argparse
from btcp.client_socket import BTCPClientSocket


def main(printSegments,window = 100, timeout = 100, input = "input.file"):
    # Create a bTCP client socket with the given window size and timeout value
    s = BTCPClientSocket(window, timeout, printSegments)
    # TODO Write your file transfer clientcode using your implementation of BTCPClientSocket's connect, send, and disconnect methods.
    s.connect()
    s.send("groetjes")
    # Clean up any state
    s.close()
    #return s._currentSeqNum
