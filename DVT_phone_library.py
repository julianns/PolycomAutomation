#!/usr/bin/env python
#########################################################################################################################
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
# Author Jeffrey McAnarney from U.S. 7/26/2013
# 
#
#  Beautiful is better than ugly
#  Explicit is better than implicit
#  Simple is better than complex
#  Complex is better than complicated
#  Readability counts
#
##########################################################################################################################
#REFERENCE:  curl --digest -u Push:Push -d "<PolycomIPPhone><Data priority="all">tel:\\8500</Data></PolycomIPPhone>" /
#                 --header "Content-Type: application/x-com-polycom-spipx" http://10.17.220.17/push
#
#REFERENCE:  requests.post(r"http://10.17.220.10/push", auth=digest("Push", "Push"), verify=False, data=DATA,
#                          headers={"Content-Type":"application/x-com-polycom-spipx", "User-Agent":"Voice DVT Automation"})
#
#REFERENCE:  PAYLOAD=r"<PolycomIPPhone><Data priority=\"Critical\">tel:\\5552112</Data></PolycomIPPhone>"
#REFERENCE:  URL=r"http://10.17.220.10/push"
#
#TODO:  convert functions to OOP, the PHONE class, then when we add other phones we can inherit and override
#       the necessary functions if state machine differs
#
##########################################################################################################################


#########################   Bulk Caller API  #####################################################
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


#Define state machine transistions
"""
Outgoing call states: Dialtone, Setup, Ringback
Incoming call states: Offering
Outgoing/incoming call states: Connected, CallConference,
CallHold, CallHeld, CallConfHold, CallConfHeld
Line state: Active, Inactive
Shared line states: CallRemoteActive
Call type: Incoming, Outgoing
"""

###Requires requests : sudo apt-get install python-requests
import inspect
import json
import logging
import re
import requests
import sys
import telnetlib
import time
from requests.auth import HTTPDigestAuth as digest
from subprocess import call as syscall
from sys import exit
from time import sleep

#Set globals
username, password, enable = 'adtran\n', 'adtran\n', 'adtran\n'
USER='Push'
PWD='Push'
AUTH=digest(USER, PWD)
URL_A=r"http://"
URL_B=r"/push"
HEADERA="Content-Type: application/x-com-polycom-spipx"
HEADERB="User-Agent: DVT User Agent"
PAYLOAD_A="<PolycomIPPhone><Data priority=\"Critical\">"
PAYLOAD_B="</Data></PolycomIPPhone>"

#just so I can avoid quotes in all my keys
name="name"
IP="IP"
number="number"
port="port"
DEBUG=logging.DEBUG
INFO=logging.INFO

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

#All parameters modified with A, B, or C reference the three possible actors in calling scenarios
A={name:"Maynard Keenan", IP:"10.17.220.217", number:"5551111", port:"0/1"}
B={name:"Roger Daltry", IP:"10.17.220.218", number:"5551112", port:"0/2"}
C={name:"Getty Lee", IP:"10.17.220.219", number:"5552112", port:"0/3"}
D={name:"Freedie Mercury", IP:"10.17.220.220", number:"5552113", port:False}
BULK_CALLER="10.17.220.7"




def getFunctionName():
  return inspect.stack()[1][3]

def getCallingModuleName():
  return inspect.stack()[3][3]

def getArguments(frame):
  args, _, _, values = inspect.getargvalues(frame)
  return [(i, values[i]) for i in args]

def setLogging(name):
  log=logging.getLogger(name)
  #requests_log=logging.getLogger("requests").setLevel(logging.level)
  return log

def isActive(A):
  """
  Returns True if line state is Active, else False
  """
  log=setLogging(__name__)
  state=sendPoll(A)
  result=(state["LineState"]=="Active")
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  log.debug('%s returned from %s'% (result, (getFunctionName())))
  return result

def isRingback(A):
  """
  Returns True if call state is RingBack, else False
  """
  state=sendPoll(A)
  result=(state["CallState"]=="Ringback")
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  log.debug('%s returned from %s'% (result, (getFunctionName())))
  return result

def isRinging(A):
  """
  Returns True if phone has incoming call, else False
  """
  state=sendPoll(A)
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  try:
    result=(state["CallState"]=="Offering")
    log.debug('%s returned from %s'% (result, (getFunctionName())))
    return result
  except:
    log.warn('No headers returned from poll')
    return False

def isConnected(A):
  """
  Returns True if line state is Active, else False
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  state=sendPoll(A)
  try:
    result=state["CallState"]=="Connected"
    log.debug('%s returned from %s'% (result, (getFunctionName())))
    return result
  except Exception:
    log.error(Exception)
    return False

def call(A, B, hs=False):
  """
  IFF LineState?INACTIVE==>DIALTONE->SETUP->RINGBACK
  Given the ip address of the phone from which to call and a number to call
  calls number, and goes to headset mode
  TODO:  Returns -1 if no registered line is inactive or if push message rejected 
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  URL=constructPushURL(A)
  #command="Key:Softkey1\n"+constructDialPadString(number)+"Key:Softkey2"
  PAYLOAD=(PAYLOAD_A + "tel:\\"+B[number]+ PAYLOAD_B)
  if not isActive(A):
    #result=sendRequest(PAYLOAD, URL)
    result=sendCurl(PAYLOAD, URL)
  if hs:
    PAYLOAD=(PAYLOAD_A+"Key:Headset"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
  sleep(2)
  
def connect(A):
  """
  IFF isRinging(ip)?TRUE==>isActive(ip)
  STATE==OFFERING=>ACTIVE
  """
  callstate=""
  PAYLOAD=(PAYLOAD_A+"Key:Headset"+PAYLOAD_B)
  URL=constructPushURL(A)
  print "connecting to %s"%(A[IP],)
  sendCurl(PAYLOAD, URL)
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))

def disconnect(A):
  """
  IFF isConnected(ip)?TRUE==>isActive(ip)?FALSE
  STATE==CONNECTED=>INACTIVE
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  state=sendPoll(A)
  try:
    if state['CallState']=="Connected":
      PAYLOAD=(PAYLOAD_A+"Key:Softkey2"+PAYLOAD_B)
      URL=constructPushURL(A)
      sendCurl(PAYLOAD, URL)
  except Exception:
    pass
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))

def attendedTransfer(A,C, con):
  """
  From connected call (A-B), performs attended transfer resulting in (B-C)
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if isConnected(A):
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    URL=constructPushURL(A)
    sendCurl(PAYLOAD, URL)
    call(A,C)
    while not isRinging(C):
      sleep(1)
    connect(C)
    verifyCallPath(A, C, con, 'attended transfer call')
    sleep(3)
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    URL=constructPushURL(A)
    sendCurl(PAYLOAD, URL)    
    disconnect(A)
    
def unattendedTransfer(A, C):
  """
  From connected call (A-B), performs unattended transfer resulting in (B-C)
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if isConnected(A):
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    URL=constructPushURL(A)
    sendCurl(PAYLOAD, URL)
    call(A, C)
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    URL=constructPushURL(A)
    sendCurl(PAYLOAD, URL)
    disconnect(A)
    while not isRinging(C):
      sleep(1)
    connect(C)
    PAYLOAD=(PAYLOAD_A+"Key:Softkey3"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))

def blindTransfer(A, C):
  """
  From connected call (A-B), performs blind transfer resulting in (B-C)
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if isConnected:
    URL=constructPushURL(A)
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
    sleep(3)
    PAYLOAD=(PAYLOAD_A+"Key:Softkey4"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
    PAYLOAD=(PAYLOAD_A+"Key:Softkey1"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
    call(A, C)
    sleep(1)
    disconnect(A)
    sleep(1)
    connect(C)
    URL=constructPushURL(A)
    PAYLOAD=(PAYLOAD_A+"Key:Softkey3"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
  
def conference(A, B):
  """
  From connected call (A-B), performs conference resulting in (A-B-C)
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if isConnected:
    PAYLOAD=(PAYLOAD_A+"Key:Conference"+PAYLOAD_B)
    URL=constructPushURL(A)
    sendCurl(PAYLOAD, URL)
    call(A, B[number])
    sleep(3)
    while not isRinging(B):
      sleep(1)
    connect(B)
    #while not isConnected(B[IP]):
    #  sleep(1)
    sleep(3)
    PAYLOAD=(PAYLOAD_A+"Key:Conference"+PAYLOAD_B)
    URL=constructPushURL(A)
    sendCurl(PAYLOAD, URL)
 
def constructPushURL(A):
  """
  Given IP address returns properly constructed push URL
  """ 
  result=URL_A + A[IP] + URL_B
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  log.debug('%s returned from %s'% (result, (getFunctionName())))  
  return result

def constructDialPadString(number):
  dialPadString=""
  for n in str(number):
    dialPadString+="Key:Dialpad"+n+"\n"
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  log.debug('%s returned from %s'% (dialPadString, (getFunctionName())))
  return dialPadString
 
def sendCurl(payload, URL):
  global HEADERS
  global USER
  global PWD
  AUTH=USER+":"+PWD
  curl=['curl', '--digest', '-u', AUTH, '-d', payload, '--header', HEADERA , '--header', HEADERB , URL]
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  return syscall(curl)

def sendRequest(payload, URL):
  global HEADERS
  global AUTH
  DATA=json.dumps(payload)
  result=requests.post(URL, auth=AUTH, verify=False, data=DATA, headers=HEADERS)
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  log.debug('%s returned from %s'% (result.status_code, (getFunctionName())))
  return result
   
def sendPoll(A, pollType="callstate"):
  """
  The handlers Polycom offers are:
  polling/callStateHandler
  polling/deviceHandler
  polling/networkHandler

  """
  global AUTH
  global USER
  global PWD
  count=0
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  payload="http://" + A[IP] + "/polling/"+pollType+"Handler"
  result=requests.get(payload, auth=AUTH)
  while result.status_code!=200:
    if count>5:
      sys.exit()
    log.debug('%s returned from sendPoll; regenerating Authorization'%(result.status_code,))
    AUTH=digest(USER, PWD)
    result=requests.get(payload, auth=AUTH)
    count+=1
  XMLstring=result.text.splitlines()
  log.debug("Result of poll is %s" %(XMLstring,))
  pattern=re.compile(r".*<(.*)>(.*)<.*")
  state={}
  for line in XMLstring:
    log.debug("checking %s for XML" %(line))
    m=pattern.match(line)
    if m:
      log.debug("found match in %s" %(line,))
      log.debug("Adding key-value pair %s:%s" %(m.group(1),m.group(2)))
      state.update({m.group(1):m.group(2)})

  lineState=""
  while lineState not in ['Active', 'Inactive']:
    try:
      lineState=state["LineState"]
    except:
      log.warn('No headers returned from poll')
  log.debug('Valid poll response to %s at %s'% ((getFunctionName(), getArguments(inspect.currentframe()))))
  return state 

def sendKeyPress(A, number):
  payload=PAYLOAD_A+constructDialPadString(number)+PAYLOAD_B
  url=constructPushURL(A)
  sendCurl(payload, url)
  
def maxVolume(A):
  for i in range(10):
    payload=(PAYLOAD_A+"Key:VolUp"+PAYLOAD_B)
    url=constructPushURL(A)
    sendCurl(payload, url)
  
def pressConference(A):
  """
  IFF connected: conference with number
  From active call, presses conference softkey
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  state=sendPoll(A)
  callState=state["CallState"]
  
  if callState=="Connected":
    PAYLOAD=(PAYLOAD_A+"Key:Conference"+PAYLOAD_B)
    URL=constructPushURL(A)
    sendCurl(PAYLOAD, URL)

def telnet(address):
    try:
        con = telnetlib.Telnet(address,23,10)
        return con
    except:
        print "Error connecting to %s:" %(address)
        print sys.exc_info()[0]
        return -1

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
    !!!!Assumes any actual phones are in headset mode!!!
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

def initializeSIP(con, port):
    """
    Initiallizes a port connected to the
    headset on a polycom phone which is
    affilliated with an existing call and
    leaves it in connected mode
    """
    baseCommand="script-manager fxo %s " % (port,)
    # results in Idle state
    cmd=baseCommand + on
    con.write(cmd)
    con.expect(['Idle'], 2)
    time.sleep(1)
    #results in Dialtone state
    cmd=baseCommand + seize
    con.write(cmd)
    con.expect(['Dialtone'], 2)
    time.sleep(1)
    #results in Connected state
    cmd=baseCommand + flash
    con.write(cmd)
    con.expect(['Connected'], 2)

def listenForTones(con, port, time='18000', tones='1'):
    """
    Takes a port in Connected State and
    listens for $time MS for $tones tones
    """
    cmd="script-manager fxo %s listen %s %s\n" % (port, time, tones)
    con.write(cmd)

def verifyTalkPath(A, B, con, callType):
  """
  verifies talk path in one direction
  returns success percentage as a string
  """
  count=0.0
  success=0.0
  failed=0
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  initializeSIP(con, A[port])
  initializeSIP(con, B[port])
  while count<5.0:
    count +=1
    time.sleep(6)
    listenForTones(con, B[port])
    time.sleep(2)
    tones='23'
    sendKeyPress(A, tones)
    result=con.expect(["0x5000", "0x5001"], 15)
    log.debug("count %f result is %s"%(count,result))
    if result[0]!=0:
      success+=1
    else:
      log.error("Error verifying talk path from %s to %s during %s" %(A[name], B[name]), callType) 
  return "{0:.0%}".format(success/count)

def verifyCallPath(A,B,con, callType):
  """
  takes existing calls and telnet connection as arguments
  verifies connection
  maxes headset volumes
  verifies talk path in both directions
  logs results
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  sleep(1)
  agood=isConnected(A)
  bgood=isConnected(B)
  if agood and bgood:
    #crank up the headset volumes
    maxVolume(A)
    maxVolume(B)
    log.info('%s is connected to %s'% (A[name], B[name]))
  else:
    #should never ever get here...
    log.error('error connecting %s to %s'% (A[name], B[name]))
    if not agood:
      log.error("%s is not connected"%(A[name],))
    if not bgood:
      log.error("%s is not connected"%(B[name],))
  log.info('%s test initiated between %s and %s' %(callType, A[name], B[name]))
  #seize associated ports and get them into Connected state
  log.info('initiating talk path verification from %s to %s in %s'% (A[name], B[name], callType))
  successAB=verifyTalkPath(A,B,con, callType)
  log.info('%s success rate from %s to %s in %s'%(successAB,A[name], B[name], callType))  
  log.info('initiating talk path verification from %s to %s'% (B[name], A[name]))
  successBA=verifyTalkPath(B,A,con, callType)
  log.info('%s success rate from %s to %s in %s'%(successBA,B[name], A[name], callType))
  log.info('%s test complete'%(callType, ))
  return (successAB, successBA)
           
def initializeCall(A, B, callType, log):
  call(A,B, True)
  log.info('initiallizing %s between %s and %s' %(callType, A[name], B[name]))
  while not isRinging(B):
    sleep(1)
  connect(B)
  return True

def normalCall(A, B, con):
  """
  places call between A and B,
  verifies talk path in both directions,
  logs results and hangs up
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  initializeCall(A, B, 'normal call', log)
  verifyCallPath(A, B, con, 'normal call')
  disconnect(A)
  
def conferenceCall(A,B,C, con):
  """
  creates conference call between A,B, and C
  does NOT validate A-B talkpath before conferencing
  verifies talk path in between all three participants
  logs results and hangs up
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  connected=initializeCall(A,B,'conference call A', log)
  while not connected:
    sleep(1)
  pressConference(A)
  sleep(5)
  connected=initializeCall(A,C,'conference call B', log)
  while not connected:
    connected=initializeCall(A,C,'conference call B', log)
  pressConference(A)
  sleep(1)
  log.info("connecting conference calls B->A")
  verifyCallPath(A, B, con, 'conference call')
  verifyCallPath(A, C, con, 'conference call')
  verifyCallPath(B, C, con, 'conference call')
  disconnect(A)
  disconnect(B)
  
def attendedTransferCall(A, B, C, con):
  """
  places call between A and B,
  verifies talk path in both directions,
  attended transfer from A->C
  verifies talk path in both directions,
  logs results and hangs up
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  initializeCall(A, B, 'attended transfer call', log)
  #sleep(5)
  verifyCallPath(A, B, con, 'attended transfer call')
  attendedTransfer(A, C, con)
  #sleep(5)
  verifyCallPath(C, B, con, 'attended transfer call')
  disconnect(B)
  
def unattendedTransferCall(A, B, C, con):
  """
  places call between A and B,
  verifies talk path in both directions,
  unattended transfer from A->C
  verifies talk path in both directions,
  logs results and hangs up
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  initializeCall(A, B, 'normal call', log)
  verifyCallPath(A, B, con, 'unattended transfer call')
  unattendedTransfer(A, C)
  verifyCallPath(C, B, con, 'unattended transfer call')
  disconnect(B)
  
def blindTransferCall(A, B, C, con):
  """
  places call between A and B,
  verifies talk path in both directions,
  blind transfer from A->C
  verifies talk path in both directions,
  logs results and hangs up
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  initializeCall(A, B, 'blind transfer call', log)
  verifyCallPath(A, B, con, 'blind transfer call')
  blindTransfer(A[IP], C[number], C[IP])
  verifyCallPath(C, B, con, 'blind transfer call')
  disconnect(B[IP])
  
def setupLogging(level):
  #setup basic logging configuration for INFO
  logging.basicConfig(level=level,
                      format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                      datefmt='%m-%d %H:%M',
                      filename='AutoCallPathVerify.log',
                      filemode='w')
  #set requests logging to WARNING
  requests_log = logging.getLogger("requests")
  requests_log.setLevel(logging.WARNING)
  
def initialize(ip, level):
  """
  sets up logging and creates connection to bulk caller
  returns telnet connection
  """
  setupLogging(level)
  con=telnet(ip)
  prompt=login(con)
  return (con)






def test():
  """
  Unit testing of automation script
  """
  con=initialize(BULK_CALLER, INFO)
  log=setLogging(__name__)


  #conferenceCall(A,B,C,con)
  attendedTransferCall(A,B,C,con)
  #unattendedTransferCall(A,B,C,con)
  #blindTransferCall(A,B,C,con)
  
  
  #conferenceCall(A,B,C, con)


  
  
  """
  Old unit tests down here
  """
  #disconnect(A[IP])
  #normalCall(A,B,con)
  #normalCall(A,C,con)
  #normalCall(B,C,con)
  #initializeCall(A,B,'test', log)
  #pressConference(A[IP])
  #sleep(10)
  # call(A[IP], C[number])
  #sleep(1)
  #initializeCall(A,C,'test2',log)
  
  


  


if __name__=="__main__":
  test()

