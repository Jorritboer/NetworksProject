from btcp.constants import *

class BTCPSocket:
    def __init__(self, window, timeout):
        self._window = window
        self._timeout = timeout
   
    # Return the Internet checksum of data
    @staticmethod
    def in_cksum(data):
        sum = 0
        for i in range(0, len(data), 2):
            twoBytes = int.from_bytes(data[i:i+2], byteorder='big', signed = False)
            sum += twoBytes
        sum = sum + (sum >> 16)
        sum = (~sum) & 0xffff
        sum = BTCPSocket.intToBytes(sum,2)
        return sum
    
    @staticmethod
    def buildsegment(seqnum = 0, acknum = 0, ACK = False, SYN = False, FIN = False, windowsize = 100, data:bytes = b''):
        segment = BTCPSocket.intToBytes(seqnum)
        segment += BTCPSocket.intToBytes(acknum)
        segment += BTCPSocket.intToBytes((ACK * 4 + SYN * 2 + FIN * 1), 1) #the last three bits represent respectively the state of the three flags
        segment += BTCPSocket.intToBytes(windowsize, 1)
        segment += BTCPSocket.intToBytes(len(data))
        check_segment = segment + BTCPSocket.intToBytes(0)
        padded_data = data + BTCPSocket.intToBytes(0,(PAYLOAD_SIZE - len(data))) 
        check_segment += padded_data  #here we have a temporary check segment with the checksum set to 0
        segment += BTCPSocket.in_cksum(check_segment)
        segment += padded_data   
        if(len(segment) != SEGMENT_SIZE):
            raise Exception("Segment size is larger than max segment size, your data was probably too large")
        return segment
    
    @staticmethod
    def intToBytes(number, noBytes = 2):
        return (number).to_bytes(noBytes, byteorder = 'big', signed = False)

    @staticmethod
    def breakdown_segment(segment):
        seqnum = int.from_bytes(segment[0:2], byteorder='big', signed = False)
        acknum = int.from_bytes(segment[2:4], byteorder='big', signed = False)
        flags = segment[4]
        ACK = bool(flags & 4)
        SYN = bool(flags & 2)
        FIN = bool(flags & 1)
        windowsize = segment[5] # when getting one byte you don't need to convert from bytes
        datalength = int.from_bytes(segment[6:8], byteorder='big', signed = False)
        cksumHasSucceeded = BTCPSocket.in_cksum(segment) == b'\x00\x00'
        data = segment[10:10+datalength]
        return seqnum, acknum, ACK, SYN, FIN, windowsize, cksumHasSucceeded, data

    @staticmethod
    def print_segment(segment):
        seqnum, acknum, ACK, SYN, FIN, windowsize, cksumHasSucceeded, data = BTCPSocket.breakdown_segment(segment)
        print('--------------------------------------------')
        print('Sequence number: ', seqnum)
        print('Acknowledgement number: ', acknum)
        print('ACK =', ACK, '    SYN =', SYN, '    FIN =', FIN)
        print('Window size: ', windowsize)
        print('Data length: ', len(data))
        print('Data: ', data)
        print("The checksum has succeeded:", cksumHasSucceeded)
        print('--------------------------------------------')