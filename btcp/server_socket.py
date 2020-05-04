import socket
import random
import threading
from btcp.lossy_layer import LossyLayer
from btcp.btcp_socket import BTCPSocket
from btcp.constants import *


# The bTCP server socket
# A server application makes use of the services provided by bTCP by calling accept, recv, and close
class BTCPServerSocket(BTCPSocket):
    def __init__(self, window, timeout, printSegments):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, SERVER_IP, SERVER_PORT, CLIENT_IP, CLIENT_PORT)
        self._printSegments = printSegments
        self._buffer = []
        self._currentState = "unconnected"
        self._connected = threading.Event()
        self._bufferNotEmpty = threading.Event()
        self._bufferlock = threading.Lock()

    # Called by the lossy layer from another thread whenever a segment arrives
    def lossy_layer_input(self, segment):
        if self._printSegments:
            print("The server has received:")
            super().print_segment(segment[0])
        seqnum, acknum, ACK, SYN, FIN, windowsize, cksumHasSucceeded, data = super().breakdown_segment(segment[0])
        if(not cksumHasSucceeded):
            return
        if(SYN and (not FIN) and (not ACK) and self._currentState == "waiting for SYN"): 
            randomSeqNum = random.randint(0, MAX_16BITS)
            self._timer = threading.Timer(self._timeout / 1000, self.accept)
            self._timer.start()
            self.sendSegment(randomSeqNum, seqnum + 1, ACK = True, SYN = True)
            self._currentState = "waiting for ACK"
        elif((not SYN) and (not FIN) and ACK and self._currentState == "waiting for ACK"):
            self._currentState = "connected"
            print("the server has connected with acknum: ", acknum, "and seqnum: ", seqnum)
            self._exptectedNextSeqNum = seqnum + 1
            self._timer.cancel()
            self._connected.set()
            self._bufferlock.acquire()
            self._buffer.append(data)
            self._bufferlock.release()
        elif((not SYN) and (not FIN) and (not ACK) and self._currentState == "connected"):
            if(seqnum == self._exptectedNextSeqNum ):
                self._bufferlock.acquire()
                self._buffer.append(data)
                self._bufferlock.release()
                self._exptectedNextSeqNum  += 1
                self._bufferNotEmpty.set()
            self.sendSegment(acknum = self._exptectedNextSeqNum - 1, ACK = True)
            
    
    # Wait for the client to initiate a three-way handshake
    def accept(self):
        self._currentState = "waiting for SYN"
        self._connected.wait() # wait until the connection is established to return to the app

    def sendSegment(self, seqnum = 0, acknum = 0, ACK = False, SYN = False, FIN = False, windowsize = 100, data:bytes = b''):
        newsegment = self.buildsegment(seqnum % MAX_16BITS, acknum % MAX_16BITS, ACK = ACK, SYN = SYN, FIN = FIN, windowsize = windowsize, data = data)
        if self._printSegments:
            print("The server has sent a segment with ACK ", acknum)
        self._lossy_layer.send_segment(newsegment)

    # Send any incoming data to the application layer
    def recv(self):
        file = []
        fileCompleted = False
        while(not fileCompleted):
            self._bufferNotEmpty.wait()
            self._bufferlock.acquire()
            data = self._buffer.pop(0)
            if(len(self._buffer) == 0):
                self._bufferNotEmpty.clear()
            self._bufferlock.release()
            data = data.decode()
            file.append(data)
            if(len(file) == 20):
                fileCompleted = True
        return file
            

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
