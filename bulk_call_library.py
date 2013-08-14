#!/usr/bin/env python
###############################################################################
# This program is free software; you can redistribute it and/or modify it 
# under the terms of the GNU public license as published by the Free Software
# Foundation.
# 
# This program is distributed in the hopes that it will be useful but without 
# any warranty, even implied, of merchantability or fitness for a particular
# purpose.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Author Jeffrey McAnarney from U.S. 8/8/2013
# 
#
#  Beautiful is better than ugly
#  Explicit is better than implicit
#  Simple is better than complex
#  Complex is better than complicated
#  Readability counts
#
###############################################################################

#####################################################################################################
# <COMMANDS>                <PURPOSE>                                   <ARGUMENTS>
# script-manager         - parent command                               (fxo <slot/port>)
#########CHILDREN########
# detect-battery         - Check for battery.                           (none)
# flash                  - Perform a hook flash.                        (none) 
# listen                 - Listen for DTMF path confirmation tones.     (wait (MS), #expected digits)
# off-hook               - Answer an inbound call.                      (none)
# on-hook                - Go on hook.                                  (none)
# seize                  - Go off hook and detect dialtone.             (none)
# send-digits            - Send DTMF digits.                            (phone #)
# send-tones             - Send path confirmation tones.                (digits to send)                
# supervision            - Set the supervision of an FXO port.          (loop-start, ground-start)
######################################################################################################
#  import library modules
import sys
import re
import telnetlib
import time
from sys import exit
from polycom_library import isRinging

username, password, enable = 'adtran\n', 'adtran\n', 'adtran\n'

#just because I hate strings in code
db=" detect-battery\n"      
flash=" flash 10\n"                 
listen6=" listen 8000 6"
off=" off-hook\n"              
on=" on-hook\n"               
seize=" seize\n"                 
dial=" send-digits "          
send=" send-tones 123456\n"                      
sls=" supervision loop-start\n"    

#takes an IP address (string) as argument, returns Telnet object
def connect(address):
    try:
        con = telnetlib.Telnet(address,23,10)
        return con
    except:
        print "Error connecting to %s:" %(address)
        print sys.exc_info()[0]
        return -1
#takes Telnet object as argument, uses global user/pass/enable, returns prompt
def login(con):
    global username
    global password
    global enable
    
    temp=con.expect(['Username:'], 2)
    if temp[0] == -1:
        print temp
        exit()
    con.write(username)
    temp=con.expect(['Password:'], 2)
    if temp[0] == -1:
        print temp
        exit()
    con.write(password)
    con.expect(['>'], 2)
    if temp[0] == -1:
        print temp
        exit()
    con.write("en\n")
    con.expect(['Password:'], 2)
    if temp[0] == -1:
        print temp
        exit()
    con.write(enable)
    con.expect(['#'], 2)
    if temp[0] == -1:
        print temp
        exit()
    con.write('\n')
    prompt=con.read_until('#')
    con.write("terminal length 0\n")
    if temp[0] == -1:
        print temp
        exit()
    con.expect([prompt])
    return prompt
def initialize(con, port):
    """
    Takes connection and FXO port number (string)
    as arguments and sets the given port into Idle state
    """
    baseCommand="script-manager fxo %s " % (port,)
    # results in Offline state
    cmd=baseCommand + on
    con.write(cmd)
    con.expect([''], 2)
    # results in Idle state
    cmd=baseCommand + db
    con.write(cmd)
    con.expect(['to Idle'], 2)
def callStart(con, portA, portB, number):
    """
    Initiates call between A-B
    """
    #puts ports into Idle state
    initialize(con, portA)
    initialize(con, portB)
    baseA="script-manager fxo %s " % (portA,)
    baseB="script-manager fxo %s " % (portB,)
    # does not change state of portA
    cmd=baseA + sls
    con.write(cmd)
    con.expect(['#'], 2)
    # does not change state portB
    cmd=baseB + sls
    con.write(cmd)
    con.expect(['#'], 2)
    #results in Dialtone portA
    cmd=baseA + seize
    con.write(cmd)
    con.expect(['Dialtone'], 2)
    #results in Connecting portA, portB ringing
    print "calling %s" %(number,)
    cmd=baseA + dial + " " + number +"\n"
    con.write(cmd)
    con.expect(['Connecting'], 2)
def confirmPath(con, portA, portB):
    """
    !!!!Assumes portB is ringing!!!
    Confirms talk path from A->B
    by setting B to listen and then sending
    tones from A->B and confirming receipt
    and decodability
    """
    baseA="script-manager fxo %s " % (portA,)
    baseB="script-manager fxo %s " % (portB,)
    #results in Dialtone portB
    cmd=baseB + seize
    con.write(cmd)
    con.expect(['#'], 2)
    #results in Connected portB
    cmd=baseB + flash
    con.write(cmd)
    con.expect(['Connected'], 2)
    #results in Connected portB
    cmd=baseB + listen6
    print "Sending tones"
    con.write(cmd)
    con.expect(['#'], 2)
    cmd=baseA + send
    con.write(cmd)
    con.expect(['123456'], 2)
    result=""
def main():
    portA='0/7'
    portB='0/3'
    con=connect("10.17.220.7")
    prompt=login(con)
    callStart(con, portA, portB, '5552112')
    time.sleep(10)
    #confirmPath(con, portA, portB)

if __name__ == '__main__':
	main()


