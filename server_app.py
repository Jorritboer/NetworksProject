#!/usr/local/bin/python3

from btcp.server_socket import BTCPServerSocket


def main(printSegments, stopServer, window = 100, timeout = 100, output = "output.file"):
    # Create a bTCP server socket
    s = BTCPServerSocket(window, timeout, printSegments)

    s.accept()
    open(output, 'w').close() #this makes sure the file is empty
    while(not stopServer.is_set()):
        data = s.recv() 
        f = open(output, 'ab')
        f.write(data) #write it to the output file
        f.close()
    # Clean up any state
    s.close()