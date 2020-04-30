import random
import threading
import time
from btcp.btcp_socket import BTCPSocket
from btcp.lossy_layer import LossyLayer
from btcp.constants import *

# bTCP client socket
# A client application makes use of the services provided by bTCP by calling connect, send, disconnect, and close
class BTCPClientSocket(BTCPSocket):
    def __init__(self, window, timeout):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, CLIENT_IP, CLIENT_PORT, SERVER_IP, SERVER_PORT)
        self._currentState = "waiting"
        self._timeout = timeout
        self._NextSeqNum = 0
        self._AckNum = 0
        self._numberOfRetries = 0
        self._connected = threading.Event()
        self._entireFileAcknowledged = threading.Event()


    # Called by the lossy layer from another thread whenever a segment arrives. 
    def lossy_layer_input(self, segment):
        print("Client has received: ")
        super().print_segment(segment[0])
        seqnum, acknum, ACK, SYN, FIN, windowsize, datalength, cksum, data = super().breakdown_segment(segment[0])
        if((SYN and (not FIN) and ACK) and self._currentState == "waiting for SYN and ACK" and acknum == self._NextSeqNum + 1): 
                self._currentState = "connected"
                print("the client has connected with acknum: ", acknum, "and seqnum: ", seqnum + 1)
                self._NextSeqNum = acknum
                self._AckNum = seqnum + 1
                self._timer.cancel()
                self._connected.set()
        elif((not SYN) and (not FIN) and ACK and self._currentState == "connected"):
            #an ACK has been received
            if(acknum == self._lastSegment):
                self._entireFileAcknowledged.set()

    # Perform a three-way handshake to establish a connection
    def connect(self):
        randomSeqNum = random.randint(0, MAX_16BITS) # Creating a random 16 bit value for the sequence number
        self._NextSeqNum = randomSeqNum
        self._currentState = "waiting for SYN and ACK"
        self._timer = threading.Timer(self._timeout / 1000, self.connect)
        self._timer.start()
        self.sendSegment(randomSeqNum,0, SYN=True)
        self._connected.wait() # wait until the connection is established to return to the app

    def sendSegment(self, seqnum = 0, acknum = 0, ACK = False, SYN = False, FIN = False, windowsize = 100, data:bytes = b''):
        newsegment = self.buildsegment(seqnum % MAX_16BITS, acknum % MAX_16BITS, ACK = ACK, SYN = SYN, FIN = FIN, windowsize = windowsize, data = data)
        print("The client sent a segment")
        self._lossy_layer.send_segment(newsegment)


    # Send data originating from the application in a reliable way to the server
    def send(self, data):
        self._lastSegment = self._NextSeqNum + 4
        self.sendSegment(self._NextSeqNum, self._AckNum, ACK = True, data = "pakketje1".encode())
        self.sendSegment(self._NextSeqNum + 1, data = "pakketje2".encode())
        self.sendSegment(self._NextSeqNum + 2, data = "pakketje3".encode())
        #self.sendSegment(self._NextSeqNum + 3, data = "pakketje4".encode())
        self.sendSegment(self._NextSeqNum + 4, data = "pakketje5".encode())
        self._entireFileAcknowledged.wait()



    # Perform a handshake to terminate a connection
    def disconnect(self):
        pass

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
