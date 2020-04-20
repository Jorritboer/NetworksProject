from btcp.constants import *

class BTCPSocket:
    def __init__(self, window, timeout):
        self._window = window
        self._timeout = timeout
   
    # Return the Internet checksum of data
    @staticmethod
    def in_cksum(data):
        return BTCPSocket.intToBytes(0,2)
    
    @staticmethod
    def buildsegment(seqnum, acknum, ACK = False, SYN = False, FIN = False, windowsize = 100, data:bytes = b''):
        segment = BTCPSocket.intToBytes(seqnum)
        segment += BTCPSocket.intToBytes(acknum)
        segment += BTCPSocket.intToBytes((ACK * 4 + SYN * 2 + FIN * 1), 1) #the last three bits represent respectively the state of the three flags
        segment += BTCPSocket.intToBytes(windowsize, 1)
        segment += BTCPSocket.intToBytes(len(data))
        check_segment = BTCPSocket.intToBytes(0)
        padded_data = data + BTCPSocket.intToBytes(0,(PAYLOAD_SIZE - len(data))) 
        check_segment += padded_data  #here we have a temporary check segment with the checksum set to 0
        segment += BTCPSocket.in_cksum(check_segment)
        segment += padded_data   
        if(len(segment) != SEGMENT_SIZE):
            raise Exception("Segment size is larger than max segment size, your data was probably too large")
        return segment
    
    @staticmethod
    def intToBytes(number, noBytes = 2):
        return (number).to_bytes(noBytes, byteorder = 'big')



    