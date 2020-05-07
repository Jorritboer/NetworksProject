#!/usr/local/bin/python3

from btcp.client_socket import BTCPClientSocket
import time


def main(printSegments,window = 100, timeout = 100, input = "input.file", maxRetries = 100):
    # Create a bTCP client socket with the given window size and timeout value
    s = BTCPClientSocket(window, timeout, printSegments, maxRetries)

    while not s.connect(): # if no connection can be established, wait 10*timeout and try again
        time.sleep((10 * timeout) / 1000)
    f = open(input, 'rb')
    data = f.read()
    f.close()
    s.send(data)
    s.disconnect()
    # Clean up any state
    s.close()
    