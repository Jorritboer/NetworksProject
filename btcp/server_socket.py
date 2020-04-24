import socket
import random
import threading
from btcp.lossy_layer import LossyLayer
from btcp.btcp_socket import BTCPSocket
from btcp.constants import *


# The bTCP server socket
# A server application makes use of the services provided by bTCP by calling accept, recv, and close
class BTCPServerSocket(BTCPSocket):
    def __init__(self, window, timeout):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, SERVER_IP, SERVER_PORT, CLIENT_IP, CLIENT_PORT)
        self._buffer = []
        self._currentState = "unconnected"

    # Called by the lossy layer from another thread whenever a segment arrives
    def lossy_layer_input(self, segment):
        super().print_segment(segment[0])
        seqnum, acknum, ACK, SYN, FIN, windowsize, datalength, cksum, data = super().breakdown_segment(segment[0])
        if(SYN and (not FIN) and (not ACK) and self._currentState == "waiting for SYN"): 
            randomSeqNum = random.randint(0, MAX_16BITS)
            self.sendSegment(randomSeqNum, seqnum + 1, ACK = True, SYN = True)
            self._currentState = "waiting for ACK"
        elif((not SYN) and (not FIN) and ACK and self._currentState == "waiting for ACK"):
            self._currentState = "connected"
            print("the client has connected with acknum: ", acknum, "and seqnum: ", seqnum)
    
    # Wait for the client to initiate a three-way handshake
    def accept(self):
        self._currentState = "waiting for SYN"

    def sendSegment(self, seqnum, acknum, ACK = False, SYN = False, FIN = False, windowsize = 100, data:bytes = b''):
        newsegment = self.buildsegment(seqnum % MAX_16BITS, acknum % MAX_16BITS, ACK = ACK, SYN = SYN, FIN = FIN, windowsize = windowsize, data = data)
        self._lossy_layer.send_segment(newsegment)

    # Send any incoming data to the application layer
    def recv(self):
        pass

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
