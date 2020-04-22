import random
from btcp.btcp_socket import BTCPSocket
from btcp.lossy_layer import LossyLayer
from btcp.constants import *

# bTCP client socket
# A client application makes use of the services provided by bTCP by calling connect, send, disconnect, and close
class BTCPClientSocket(BTCPSocket):
    def __init__(self, window, timeout):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, CLIENT_IP, CLIENT_PORT, SERVER_IP, SERVER_PORT)

    # Called by the lossy layer from another thread whenever a segment arrives. 
    def lossy_layer_input(self, segment):
        super().print_segment(segment[0])

    # Perform a three-way handshake to establish a connection
    def connect(self):
        randomSeqNum = random.randint(0, MAX_16BITS) # Creating a random 16 bit value for the sequence number
        print(randomSeqNum)
        segment = super().buildsegment(randomSeqNum,0, SYN=True)
        self._lossy_layer.send_segment(segment)
        #print(super().buildsegment(14,15))

    # Send data originating from the application in a reliable way to the server
    def send(self, data):
        pass

    # Perform a handshake to terminate a connection
    def disconnect(self):
        pass

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
