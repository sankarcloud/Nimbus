#!/usr/bin/env python

# configure these paths:
import ConfigParser
	
try:
	t = open('/etc/nimbus/nimbus_manager.conf')
	t.close()
except: 
	print "File /etc/nimbus/nimbus_manager.conf not found !"
	sys.exit(1)

configd = ConfigParser.ConfigParser()
configd.read("/etc/nimbus/nimbus_manager.conf")

LOGFILE = configd.get("PATH","log")
PIDFILE = configd.get("PATH","pid")
USER = configd.get("SYSTEM","uid")
GROUP = configd.get("SYSTEM","gid")
# and let USERPROG be the main function of your project
import NimbusManager
USERPROG = NimbusManager.main

#based on Jurgen Hermanns http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
import sys
import os

class Log:
    """file like for writes with auto flush after each write
    to ensure that everything is logged, even during an
    unexpected exit."""
    def __init__(self, f):
        self.f = f
    def write(self, s):
        self.f.write(s)
        self.f.flush()

def main():
    #change to data directory if needed
    #os.chdir("/root/data")
    #redirect outputs to a logfile
    sys.stdout = sys.stderr = Log(open(LOGFILE, 'a+'))
    #ensure the that the daemon runs a normal user
    #os.setegid(int(GROUP))  #set group first "pydaemon"
    #os.seteuid(int(USER))     #set user "pydaemon"
    #start the user program here:
    USERPROG()

if __name__ == "__main__":
    # do the UNIX double-fork magic, see Stevens' "Advanced
    # Programming in the UNIX Environment" for details (ISBN 0201563177)
    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
    except OSError, e:
        print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    # decouple from parent environment
    os.chdir("/")   #don't prevent unmounting....
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent, print eventual PID before
            #print "Daemon PID %d" % pid
            open(PIDFILE,'w').write("%d"%pid)
            sys.exit(0)
    except OSError, e:
        print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    # start the daemon main loop
    main()