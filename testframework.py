import unittest
import threading
import socket
import time
import sys
import client_app
import server_app
import filecmp

timeout=100
winsize=100
inputfile = "input.jpeg"
outputfile = "output.jpeg"
intf="lo"
netem_add="sudo tc qdisc add dev {} root netem".format(intf)
netem_change="sudo tc qdisc change dev {} root netem {}".format(intf,"{}")
netem_del="sudo tc qdisc del dev {} root netem".format(intf)

"""run command and retrieve output"""
def run_command_with_output(command, input=None, cwd=None, shell=True):
    import subprocess
    try:
      process = subprocess.Popen(command, cwd=cwd, shell=shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    except Exception as inst:
      print("problem running command : \n   ", str(command))

    [stdoutdata, stderrdata]=process.communicate(input)  # no pipes set for stdin/stdout/stdout streams so does effectively only just wait for process ends  (same as process.wait()

    if process.returncode:
      print(stderrdata)
      print("problem running command : \n   ", str(command), " ",process.returncode)

    return stdoutdata

"""run command with no output piping"""
def run_command(command,cwd=None, shell=True):
    import subprocess
    process = None
    try:
        process = subprocess.Popen(command, shell=shell, cwd=cwd)
        print(str(process))
    except Exception as inst:
        print("1. problem running command : \n   ", str(command), "\n problem : ", str(inst))

    process.communicate()  # wait for the process to end
    if process.returncode:
        print("2. problem running command : \n   ", str(command), " ", process.returncode)
        


class TestbTCPFramework(unittest.TestCase):
    """Test cases for bTCP"""
    
    def setUp(self):
        """Prepare for testing"""
        # default netem rule (does nothing)
        run_command(netem_add)
        print("testing: ", self._testMethodName)
        
    def tearDown(self):
        """Clean up after testing"""
        run_command(netem_del)
        # clean the environment
        
    def test_ideal_network(self):
        """reliability over an ideal framework"""
        stopServer = threading.Event()
        server = threading.Thread(target=server_app.main, args=(False, stopServer, winsize, timeout, outputfile))
        server.start()
        client_app.main(False, timeout= 100, input = inputfile)
        stopServer.set()
        
        self.assertTrue(filecmp.cmp(inputfile, outputfile))
    
    def test_flipping_network(self):
        """reliability over network with bit flips 
        (which sometimes results in lower layer packet loss)"""
        run_command(netem_change.format("corrupt 1%"))
    
        stopServer = threading.Event()
        server = threading.Thread(target=server_app.main, args=(False, stopServer, winsize, timeout, outputfile))
        server.start()
        client_app.main(False, timeout= 100, input = inputfile)
        stopServer.set()

        self.assertTrue(filecmp.cmp(inputfile, outputfile))

    def test_duplicates_network(self):
        """reliability over network with duplicate packets"""
        run_command(netem_change.format("duplicate 50%"))

        stopServer = threading.Event()
        server = threading.Thread(target=server_app.main, args=(False, stopServer, winsize, timeout, outputfile))
        server.start()
        client_app.main(False, timeout= 100, input = inputfile)
        stopServer.set()

        self.assertTrue(filecmp.cmp(inputfile, outputfile))

    def test_lossy_network(self):
        """reliability over network with packet loss"""
        run_command(netem_change.format("loss 1%"))
        
        stopServer = threading.Event()
        server = threading.Thread(target=server_app.main, args=(False, stopServer, winsize, timeout, outputfile))
        server.start()
        client_app.main(False, timeout= 100, input = inputfile)
        stopServer.set()
        
        self.assertTrue(filecmp.cmp(inputfile, outputfile))

    def test_reordering_network(self):
        """reliability over network with packet reordering"""    
        run_command(netem_change.format("delay 200ms reorder 50% 50%"))
        
        stopServer = threading.Event()
        server = threading.Thread(target=server_app.main, args=(False, stopServer, winsize, timeout, outputfile))
        server.start()
        client_app.main(False, timeout= 100, input = inputfile)
        stopServer.set()

        self.assertTrue(filecmp.cmp(inputfile, outputfile))
        
    def test_delayed_network(self):
        """reliability over network with delay relative to the timeout value"""
        run_command(netem_change.format("delay "+str(0.5 * timeout)+"ms 20ms"))
        
        stopServer = threading.Event()
        server = threading.Thread(target=server_app.main, args=(False, stopServer, winsize, timeout, outputfile))
        server.start()
        client_app.main(False, timeout= 100, input = inputfile)
        stopServer.set()

        self.assertTrue(filecmp.cmp(inputfile, outputfile))
    
    def test_allbad_network(self):
        """reliability over network with all of the above problems"""

        #run_command(netem_change.format("corrupt 1% duplicate 10% loss 10% 25% delay 20ms reorder 25% 50%"))
        run_command(netem_change.format("corrupt 1% duplicate 10% loss 10% 25% delay 1ms reorder 25% 50%"))
        stopServer = threading.Event()
        server = threading.Thread(target=server_app.main, args=(False, stopServer, winsize, timeout, outputfile))
        server.start()
        client_app.main(False, timeout= 100, input = inputfile)
        stopServer.set()
         
        self.assertTrue(filecmp.cmp(inputfile, outputfile))

  
#    def test_command(self):
#        #command=['dir','.']
#        out = run_command_with_output("dir .")
#        print(out)
        

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="bTCP tests")
    parser.add_argument("-w", "--window", help="Define bTCP window size used", type=int, default=100)
    parser.add_argument("-t", "--timeout", help="Define the timeout value used (ms)", type=int, default=timeout)
    args, extra = parser.parse_known_args()
    timeout = args.timeout
    winsize = args.window
    
    # Pass the extra arguments to unittest
    sys.argv[1:] = extra

    # Start test suite
    unittest.main()
