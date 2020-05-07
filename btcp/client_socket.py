import random
import threading
import time
from btcp.btcp_socket import BTCPSocket
from btcp.lossy_layer import LossyLayer
from btcp.constants import *

# bTCP client socket
# A client application makes use of the services provided by bTCP by calling connect, send, disconnect, and close
class BTCPClientSocket(BTCPSocket):
    def __init__(self, window, timeout, printSegments, maxRetries):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, CLIENT_IP, CLIENT_PORT, SERVER_IP, SERVER_PORT)
        self._printSegments = printSegments
        self._currentState = "waiting"
        self._timeout = timeout
        self._maxRetries = maxRetries
        self._NextSeqNum = 0
        self._AckNum = 0
        self._numberOfRetries = 0
        self._connected = threading.Event()
        self._entireFileAcknowledged = threading.Event()
        self._sendBase = 0
        self._initialSequenceNumber = 0
        self._timerLock = threading.Lock()
        self._sendtimer = 0
        self._disconnectingtimer = 0
        self._disconnected = threading.Event()


    # Called by the lossy layer from another thread whenever a segment arrives. 
    def lossy_layer_input(self, segment):
        if self._printSegments:
            print("Client has received: ")
            super().print_segment(segment[0])
        seqnum, acknum, ACK, SYN, FIN, windowsize, cksumHasSucceeded, data = super().breakdown_segment(segment[0])
        if(not cksumHasSucceeded):
            return
        self._window = windowsize #to make sure we do not have a window size of 0
        if(self._window == 0):
            self._window = 1 
        if((SYN and (not FIN) and ACK) and self._currentState == "waiting for SYN and ACK" and acknum == self._NextSeqNum + 1): 
                self._currentState = "connected"
                self._NextSeqNum = acknum
                self._AckNum = seqnum + 1
                self._sendBase = acknum
                self._timer.cancel()
                self._connected.set()
        elif((not SYN) and (not FIN) and ACK and self._currentState == "connected"):
            #an ACK has been received
            if(acknum == self._lastSegment):
                self._entireFileAcknowledged.set()
                self._sendtimer.cancel()
                self._sendBase = acknum + 1
            elif(acknum >= self._sendBase):
                self._sendBase = acknum + 1
                self.startTimer(self.timeout)
            self.sendSegmentsInWindow() 
        elif((not SYN) and FIN and ACK and self._currentState == "waiting for ACK and FIN"):
            self._disconnectingtimer.cancel()
            self._disconnected.set()

    # Perform a three-way handshake to establish a connection
    def connect(self):
        if(self._numberOfRetries > self._maxRetries):
            self._disconnected.set()
        self._numberOfRetries += 1
        randomSeqNum = random.randint(0, MAX_16BITS) # Creating a random 16 bit value for the sequence number
        self._NextSeqNum = randomSeqNum
        self._currentState = "waiting for SYN and ACK"
        self._timer = threading.Timer(self._timeout / 1000, self.connect)
        self._timer.start()
        self.sendSegment(randomSeqNum,0, SYN=True)
        self._connected.wait() # wait until the connection is established to return to the app
        self._numberOfRetries = 0
        return self._currentState == "connected" # return if the connection establishment succeeded

    def sendSegment(self, seqnum = 0, acknum = 0, ACK = False, SYN = False, FIN = False, windowsize = 0, data:bytes = b''):
        newsegment = self.buildsegment(seqnum % MAX_16BITS, acknum % MAX_16BITS, ACK = ACK, SYN = SYN, FIN = FIN, windowsize = windowsize, data = data)
        if self._printSegments:
            print("The client has sent a segment with SEQ ", seqnum)
        self._lossy_layer.send_segment(newsegment)

    # Send data originating from the application in a reliable way to the server
    def send(self, data):
        self._sendPackets = []
        for i in range(0, len(data), 1008): #splits it in parts of 1008 bytes
            self._sendPackets.append(data[i:i + 1008])
        self._lastSegment = self._sendBase + len(self._sendPackets) - 1
        self._initialSequenceNumber = self._sendBase
        self.startTimer(self.timeout)
        self.sendSegmentsInWindow()
        self._entireFileAcknowledged.wait()
    
    def startTimer(self, method):
        self._timerLock.acquire()
        if(self._sendtimer != 0):
            self._sendtimer.cancel()
        self._sendtimer = threading.Timer(self._timeout / 1000, method)
        self._sendtimer.start()
        self._timerLock.release()

    def sendSegmentsInWindow(self):
        while(self._NextSeqNum <= self._sendBase + self._window and self._NextSeqNum <= self._lastSegment):
            if(self._NextSeqNum == self._initialSequenceNumber):
                self.sendSegment(self._NextSeqNum, self._AckNum, ACK = True, data= self._sendPackets[self._NextSeqNum - self._initialSequenceNumber])
            else: 
                self.sendSegment(self._NextSeqNum, data= self._sendPackets[self._NextSeqNum - self._initialSequenceNumber])
            self._NextSeqNum += 1

    def timeout(self):
        if(self._printSegments):
            print("a timeout has occured, we restart with seqnum : ", self._sendBase, ', which is package number ', self._sendBase - self._initialSequenceNumber)
        self._NextSeqNum = self._sendBase
        self.sendSegmentsInWindow()
        self.startTimer(self.timeout)
        

    # Perform a handshake to terminate a connection
    def disconnect(self):
        if(self._numberOfRetries > self._maxRetries):
            self._disconnected.set()
        self._numberOfRetries += 1
        self._currentState = "waiting for ACK and FIN"
        self._disconnectingtimer = threading.Timer(self._timeout / 1000, self.disconnect)
        self._disconnectingtimer.start()
        self.sendSegment(self._NextSeqNum, FIN = True)
        self._disconnected.wait()


    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
