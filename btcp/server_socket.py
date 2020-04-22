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
        self._buffer_not_empty = threading.Event()

    # Called by the lossy layer from another thread whenever a segment arrives
    def lossy_layer_input(self, segment):
        super().print_segment(segment[0])
        if(len(self._buffer) < self._window):
            self._buffer.append(segment[0])
            self._buffer_not_empty.set()

    # Wait for the client to initiate a three-way handshake
    def accept(self):
        thread = threading.Thread(target=self.accepting)
        thread.start()

    #The function that does the actual accepting
    def accepting(self):
        isAccepted = False
        while(not isAccepted):
            self._buffer_not_empty.wait()
            segment = self._buffer.pop(0)
            if(self._buffer == []):
                self._buffer_not_empty.clear()
            seqnum, acknum, ACK, SYN, FIN, windowsize, datalength, cksum, data = super().breakdown_segment(segment)
            if(SYN and (not FIN) and (not ACK)): 
                randomSeqNum = random.randint(0, MAX_16BITS)
                newsegment = self.buildsegment(randomSeqNum, seqnum+1 % MAX_16BITS, ACK = True, SYN = True)
                self._lossy_layer.send_segment(newsegment)


            
            

    # Send any incoming data to the application layer
    def recv(self):
        pass

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
