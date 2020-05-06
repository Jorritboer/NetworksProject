#!/usr/local/bin/python3

import argparse
from btcp.server_socket import BTCPServerSocket


def main(printSegments, stopServer, window = 100, timeout = 100, output = "output.file"):
    # Create a bTCP server socket
    s = BTCPServerSocket(window, timeout, printSegments)
    # TODO Write your file transfer server code here using your BTCPServerSocket's accept, and recv methods.
    s.accept()
    open(output, 'w').close() #this makes sure the file is empty
    while(not stopServer.is_set()):
        data = s.recv() #write it to the output file
        f = open(output, 'ab')
        f.write(data)
        f.close()
    # Clean up any state
    s.close()
    #return s._currentSeqNum