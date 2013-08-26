#!/usr/bin/env python
#########################################################################################################################
# This software belongs to Adtran, Inc.
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

"""
TODO: Refactor to remove Curl and use requests
"""

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



import inspect
import json
import logging
import re
import sys
import telnetlib
import time
import timing

from subprocess import call as syscall
from sys import exit
from time import sleep

#Requires requests which is not a standard module
try:
  import requests
  from requests.auth import HTTPDigestAuth as digest
except Exception:
  print "This library requires the installation of requests!  /n (debian package: python-requests)"
  exit()


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
BC_RESPONSE=re.compile(r".*fxo\s(.*) - 0x(\d+)\s\((.*)\)\s\((.*)\).*\((.*)\)")
PROMPT=""

#just so I can avoid quotes in all my keys
BC="BC"
name="name"
IP="IP"
number="number"
port="port"
analog="analog"
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

#Add SIP Phone disctionaries
SIP_A={type:IP, name:"Maynard Keenan", IP:"10.10.10.101", number:"5551111", port:"0/1"}
SIP_B={type:IP, name:"Roger Daltry", IP:"10.10.10.102", number:"5551112", port:"0/2"}
SIP_C={type:IP, name:"Getty Lee", IP:"10.10.10.103", number:"5551113", port:"0/3"}
SIP_D={type:IP, name:"Freddie Mercury", IP:"10.10.10.104", number:"555114", port:False}

#Add Bulk Caller Phone Dictionaries
BC_A={type:BC, name:"John Bonham", IP:False, number:"555114", port:"0/7"}
BC_B={type:BC, name:"Neil Pert", IP:False, number:"5561012", port:"0/8"}

BULK_CALLER="10.10.10.50"

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

def isRinging(A, con):
  """
  Returns True if phone has incoming call, else False
  """
  state=sendPoll(A)
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if A[type]==IP:
    try: 
      line=(state["LineState"])
    except:
      log.warn('No headers returned from poll')
      return False
    try:
      result=(state["CallState"]=="Offering")
      log.debug('%s returned from %s'% (result, (getFunctionName())))
      return result
    except:
      if line=='Inactive':
        log.warn('Line is inctive')
        return False
      else:
        log.warn('Unknown error: %s', state)
        return False
  elif A[type]==BC:
    #this is kind of kludgy, but there is no way to poll for state yet, so I must make an assumption then test it
    #I'll go off hook and expect "to Connected".  "Wrong State" means it is not ringing
    goOffHook(A,con)

def isConnected(A, con):
  """
  Returns True if line state is Active, else False
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if A[type]==IP:  
    state=sendPoll(A)
    try:
      result=(state["CallState"]=="Connected" or state["CallState"]=="CallConference")
      log.debug('%s returned from %s'% (result, (getFunctionName())))
      return result
    except Exception:
      log.error(Exception)
      return False
  elif A[type]==BC:
    #this is kind of kludgy, but there is no way to poll for state yet.  I'll go off hook and expect " to Connected".
    #Whether current state is ringing or connected, the BC will return "<STATE> to Connected"
    #Any other response means it is not connected
    goOffHook(A,con)

def call(A, B, inHeadsetMode):
  """
  TODO:  Add functionality to initiate from BC
  A calls B and if A is not in headeset mode, goes to headset mode
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  URL=constructPushURL(A)
  PAYLOAD=(PAYLOAD_A + "tel:\\"+B[number]+ PAYLOAD_B)
  result=sendCurl(PAYLOAD, URL)
  if not inHeadsetMode:
    pressHeadset(A)
  sleep(1)
  
def connect(A, con):
  """
  sends a push to press the headset button if SIP phone
  OR
  sends a command to BC to go off-hook
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if A[type]==IP:
    pressHeadset(A)
  elif A[type]==BC:
    goOffHook(A,con)
    
def disconnect(A, con):
  """
  sends a push to press the headset button if SIP phone
  OR
  sends a command to BC to go on-hook
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if A[type]==IP:
    state=sendPoll(A)
    try:
      if state['CallState']=="Connected":
        pressHeadset(A)
    except Exception:
      pass
  elif A[type]==BC:
    goOnHook(A,con)

def attendedTransfer(A, C, con):
  """
  TODO:  Add functionality to initiate from BC
  From connected call (A-B), performs attended transfer resulting in (B-C)
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if isConnected(A):
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    URL=constructPushURL(A)
    sendCurl(PAYLOAD, URL)
    call(A,C, True)
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
  TODO:  Add functionality to initiate from BC
  From connected call (A-B), performs unattended transfer resulting in (B-C)
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if isConnected(A):
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    URL=constructPushURL(A)
    sendCurl(PAYLOAD, URL)
    call(A, C, True)
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    URL=constructPushURL(A)
    sendCurl(PAYLOAD, URL)
    while not isRinging(C):
      sleep(1)
    sleep(1)
    connect(C)

def blindTransfer(A, C):
  """
  From connected call (A-B), performs blind transfer resulting in (B-C)
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if isConnected(A):
    URL=constructPushURL(A)
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
    URL=constructPushURL(A)
    PAYLOAD=(PAYLOAD_A+"Key:Softkey3"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
    initializeCall(A, C, 'blind transfer BC', log, True)

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

def pressHeadset(A):
    URL=constructPushURL(A)
    PAYLOAD=(PAYLOAD_A+"Key:Headset"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)

def goOffHook(A, con):
  con.write("script-manager fxo %s off-hook\n" % (A[port],))
  con.expect([BC_RESPONSE,],5)
  con.read_until(PROMPT)

def goOnHook(A, con):
  con.write("script-manager fxo %s on-hook\n" % (A[port],))
  con.expect([BC_RESPONSE,],5)
  con.read_until(PROMPT)

def telnet(address):
  log=setLogging(__name__)
  try:
    con = telnetlib.Telnet(address,23,10)
    return con
  except:
    log.error( "Error connecting to %s:" %(address))
    log.error(sys.exc_info()[0])
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

def initializePort(con, port):
  """
  Takes connection and FXO port number (string)
  as arguments and sets the given port into Idle state
  """
  baseCommand="script-manager fxo %s " % (port,)
  # results in Offline state
  cmd=baseCommand + on
  con.write(cmd)
  con.expect([''], 2)
  con.read_until(PROMPT)  
  # results in Idle state
  cmd=baseCommand + db
  con.write(cmd)
  con.expect(['to Idle'], 2)
  con.read_until(PROMPT)  

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
  con.read_until(PROMPT)
  time.sleep(1)
  #results in Dialtone state
  cmd=baseCommand + seize
  con.write(cmd)
  con.expect(['Dialtone'], 2)
  con.read_until(PROMPT)
  time.sleep(1)
  #results in Connected state
  cmd=baseCommand + flash
  con.write(cmd)
  con.expect(['Connected'], 2)
  con.read_until(PROMPT)

def listenForTones(con, port, time='10000', tones='1'):
  """
  Takes a port in Connected State and
  listens for $time MS for $tones tones
  """
  cmd="script-manager fxo %s listen %s %s\n" % (port, time, tones)
  con.write(cmd)

def verifyTalkPath(A, B, con, callType):
  """
  verifies bidirectional talk path
  returns success percentage as a string tuple
  """
  count=0.0
  successAB=0.0
  successBA=0.0
  failed=0
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  #bulk caller calls will already be in connected state, initiallize the ports on BC for SIP phones
  if A[type]==IP:
    initializeSIP(con, A[port])
  if B[type]==IP:
    initializeSIP(con, B[port])
  while count<4.0:
    count +=1
    time.sleep(4)
    tonesA='333'
    tonesB='444'
    listenForTones(con, A[port])
    time.sleep(3)
    log.info("Listening for a %s on fxo %s"%(tonesA[0], B[port]))
    sendKeyPress(B, tonesA)
    result=con.expect([RESPONSE,], 10)
    con.read_until(PROMPT)
    log.info("%s received %s from %s" %(result.group(4), B[name], A[name]))
    if result.group(2)=="5000":
      successBA+=1
    else:
      log.error("Error: %s, received (%s) from %s" %(result.group(3), result.group(4), B[name]))
    sleep(10)
    listenForTones(con, B[port])
    time.sleep(3)
    log.info("Listening for a %s on fxo %s"%(tonesB[0], A[port]))
    sendKeyPress(A, tonesB)
    result=con.expect([RESPONSE,], 15)
    con.read_until(PROMPT)
    log.info("%s received %s from %s" %(result.group(4), B[name], A[name]))
    if result.group=="5000":
      successAB+=1
    else:
      log.error("Error: %s, received (%s) from %s" %(result.group(3), result.group(4), B[name]))
    successRateAB="{0:.0%}".format(successAB/count)
    successRateBA="{0:.0%}".format(successBA/count)
  sleep(2)
  return (successRateAB, successRateBA)

def verifyCallPath(A, B, con, callType):
  """
  takes existing calls and telnet connection as arguments
  if phone is sip:
    verifies connection
    maxes headset volumes
  verifies talk path in both directions
  logs results
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  sleep(1)
  agood=False
  bgood=False
  while not (agood and bgood):
    agood=isConnected(A)
    bgood=isConnected(B)
  if (agood and bgood):
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
  log.info('initiating talk path verification between %s and %s during %s'% (A[name], B[name], callType))
  (successRateAB, successRateBA)=verifyTalkPath(A,B,con, callType)
  log.info('%s success rate from %s to %s in %s'%(successRateAB,A[name], B[name], callType))  
  log.info('%s success rate from %s to %s in %s'%(successRateBA,B[name], A[name], callType))
  log.info('%s test complete'%(callType, ))
  return (successRateAB, successRateBA)

def initializeCall(A, B, callType, log, inHeadsetMode):
  """
  initializes a call of callType between A and B
  waits for B to start ringing and then connects
  """
  call(A,B, inHeadsetMode)
  log.info('initiallizing %s between %s and %s' %(callType, A[name], B[name]))
  while not isRinging(B):
    sleep(1)
  connect(B)

def normalCall(A, B, con):
  """
  places call between A and B,
  verifies talk path in both directions,
  logs results and hangs up
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  initializeCall(A, B, 'normal call', log, False)
  verifyCallPath(A, B, con, 'normal call')
  disconnect(A)
  
def conferenceCall(A, B, C, con):
  """
  creates conference call between A,B, and C
  does NOT validate A-B talkpath before conferencing
  verifies talk path in between all three participants
  logs results and hangs up
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  initializeCall(A,B,'conference call AB', log, False)
  verifyCallPath(A, B, con, 'conference call leg AB')
  pressConference(A)
  initializeCall(A,C,'conference call AC', log, True)
  verifyCallPath(A, B, con, 'conference call leg AC')
  pressConference(A)
  sleep(2)
  log.info("connecting conference call legs AB->AC")
  verifyCallPath(A, B, con, 'conference call ABC')
  verifyCallPath(A, C, con, 'conference call ABC')
  verifyCallPath(B, C, con, 'conference call ABC')
  disconnect(A)
  disconnect(B)
  disconnect(C)
  
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
  initializeCall(A, B, 'attended transfer call', log, False)
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
  initializeCall(A, B, 'unattended transfer AB', log, False)
  verifyCallPath(A, B, con, 'unattended transfer AB')
  unattendedTransfer(A, C)
  verifyCallPath(C, B, con, 'unattended transfer BC')
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
  initializeCall(A, B, 'blind transfer call', log, False)
  verifyCallPath(A, B, con, 'blind transfer AB')
  blindTransfer(A, C)
  verifyCallPath(C, B, con, 'blind transfer  BC')
  disconnect(B)
  
def setupLogging(level):
  #setup basic logging configuration for INFO
  #format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',  !!!leaving outmodule name since it will always be the same
  logging.basicConfig(level=level,
                      format='%(asctime)s %(levelname)-8s %(message)s',
                      datefmt='%m-%d %H:%M',
                      filename='AutoCallPathVerify.log',
                      filemode='w')
  #set requests logging to WARNING
  requests_log = logging.getLogger("requests")
  requests_log.setLevel(logging.WARNING)
  
def initializeTest(ip, level):
  """
  sets up logging and creates connection to bulk caller
  returns telnet connection
  """
  global PROMPT
  setupLogging(level)
  con=telnet(ip)
  if con==-1:
    exit()
  PROMPT=login(con)
  return (con)






def test():
  """
  Unit testing of automation script
  """
  con=initializeTest(BULK_CALLER, INFO)
  log=setLogging(__name__)
  

  
  """
  Completed unit tests down here
  """
  #disconnect(A[IP])
  normalCall(A,B,con) #good
  #normalCall(A,C,con) #good
  #normalCall(B,C,con) #good
  #attendedTransferCall(A,B,C,con)   #good 
  #unattendedTransferCall(A,B,C,con) #good
  #blindTransferCall(A,B,C,con) #good
  #conferenceCall(A,B,C,con) #good
  
 


if __name__=="__main__":
  test()

