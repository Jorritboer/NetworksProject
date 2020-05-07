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
        self._currentState = "disconnected"
        self._maxRetries = maxRetries
        self._numberOfRetries = 0
        self._nextSeqNum = 0
        self._ackNum = 0
        self._sendBase = 0
        self._initialSequenceNumber = 0
        self._timer = 0
        self._timerLock = threading.Lock()
        self._disconnected = threading.Event()
        self._connected = threading.Event()
        self._entireFileAcknowledged = threading.Event()


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

        if (self._currentState == "connecting"):
            if (SYN and (not FIN) and ACK):
                self._currentState = "connected"
                self._nextSeqNum = acknum
                self._ackNum = seqnum + 1
                self._sendBase = acknum
                self.stopTimer()
                self._connected.set()
        elif (self._currentState == "connected"):
            if ((not SYN) and (not FIN) and ACK):
                #an ACK has been received
                if(acknum == self._lastSegment):
                    self._entireFileAcknowledged.set()
                    self.stopTimer()
                    self._sendBase = acknum + 1
                elif(acknum >= self._sendBase):
                    self._sendBase = acknum + 1
                    self.startTimer()
                self.sendSegmentsInWindow() 
        elif (self._currentState == "disconnecting"):
            if ((not SYN) and FIN and ACK):
                self.stopTimer()
                self._disconnected.set()

    # Perform a three-way handshake to establish a connection
    def connect(self):
        randomSeqNum = random.randint(0, MAX_16BITS) # Creating a random 16 bit value for the sequence number
        self._nextSeqNum = randomSeqNum
        self.sendSegment(randomSeqNum,0, SYN=True)
        self._currentState = "connecting"
        self._numberOfRetries = 1
        self.startTimer()
        self._connected.wait() # wait until the connection is established to return to the app
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
        self.startTimer()
        self.sendSegmentsInWindow()
        self._entireFileAcknowledged.wait()
    
    def startTimer(self):
        self.stopTimer() # in case a different timer is running currently, cancel it
        self._timerLock.acquire()
        self._timer = threading.Timer(self._timeout / 1000, self.timeout)
        self._timer.start()
        self._timerLock.release()

    def stopTimer(self):
        if (self._timer == 0): # timer has not yet been initialized
            return
        self._timerLock.acquire()
        self._timer.cancel()
        self._timerLock.release()

    def sendSegmentsInWindow(self):
        while(self._nextSeqNum <= self._sendBase + self._window and self._nextSeqNum <= self._lastSegment):
            if(self._nextSeqNum == self._initialSequenceNumber):
                self.sendSegment(self._nextSeqNum, self._ackNum, ACK = True, data= self._sendPackets[self._nextSeqNum - self._initialSequenceNumber])
            else: 
                self.sendSegment(self._nextSeqNum, data= self._sendPackets[self._nextSeqNum - self._initialSequenceNumber])
            self._nextSeqNum += 1

    def timeout(self):
        if (self._currentState == "connecting"):
            if(self._numberOfRetries > self._maxRetries):
                self._connected.set()
                return 
            self._numberOfRetries += 1
            randomSeqNum = random.randint(0, MAX_16BITS) # Creating a random 16 bit value for the sequence number
            self._nextSeqNum = randomSeqNum
            self.sendSegment(randomSeqNum,0, SYN=True)
        elif (self._currentState == "connected"):
            if(self._printSegments):
                print("a timeout has occured, we restart with seqnum : ", self._sendBase, ', which is package number ', self._sendBase - self._initialSequenceNumber)
            self._nextSeqNum = self._sendBase
            self.sendSegmentsInWindow()
        elif (self._currentState == "disconnecting"):
            if(self._numberOfRetries > self._maxRetries):
                self._disconnected.set()
            self._numberOfRetries += 1
            self.sendSegment(self._nextSeqNum, FIN = True)
        self.startTimer()

    # Perform a handshake to terminate a connection
    def disconnect(self):
        self._currentState = "disconnecting"
        self._numberOfRetries = 1
        self.startTimer()
        self.sendSegment(self._nextSeqNum, FIN = True)
        self._disconnected.wait()

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
