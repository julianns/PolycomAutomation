#!/usr/bin/env python
#########################################################################################################################
# This software belongs to Adtran, Inc.
# Author Jeffrey McAnarney from U.S. 7/26/2013
# 			 Julian Sy	10/11/2013
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
#import timing
import atexit

from subprocess import call as syscall
from sys import exit

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
RESULTS=[]
con=telnetlib.Telnet()
con2=telnetlib.Telnet()


#just so I can avoid quotes in all my keys
pType="pYtpe"
BC="BC"
name="name"
IP="IP"
number="number"
port="port"
alias="alias"
log_filename = 'AutoCallPathVerify.log'
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
tn="telnet "                      
sls=" supervision loop-start\n"
spi="show power inline "

#Add SIP Phone dictionaries

#VVX300
SIP_300={pType:IP, name:"POLYCOM VVX300", IP:"10.10.10.101", number:"5551111", alias:"1111", port:"0/1"}
#VVX310
SIP_310={pType:IP, name:"POLYCOM VVX310", IP:"10.10.10.102", number:"5551112", alias:"1112", port:"0/2"}
#VVX40
SIP_400={pType:IP, name:"POLYCOM VVX400", IP:"10.10.10.103", number:"5551113", alias:"1113", port:"0/3"}
#VVX410
SIP_410={pType:IP, name:"POLYCOM VVX410", IP:"10.10.10.104", number:"5551114", alias:"1114", port:"0/4"}
#VVX500
SIP_500={pType:IP, name:"POLYCOM VVX500", IP:"10.10.10.105", number:"5551115", alias:"1115", port:"0/5"}


NV7100_SIP_400={pType:IP, name:"NV7100 POLYCOM VVX400 THROUGH SIP TRUNK", IP:"10.17.235.71:111", number:"5552221", port:"0/0 at BC2"}

#Add Bulk Caller Phone Dictionaries
BC_A={pType:BC, name:"NEO ANALOG FXS 0/1", IP:False, number:"5551011", port:"0/7"}
BC_B={pType:BC, name:"NEO ANALOG FXS 0/2", IP:False, number:"5551012", port:"0/6"}

#Add 
PRI2FXO_A={pType:BC, name:"ATLAS ANALOG THROUGH PRI", IP:False, number:"5581011", port:"0/8"}
#Calling Analog
NEO2FXO_A={pType:BC, name:"ATLAS ANALOG THROUGH NEO TRUNK T10", IP:False, number:"5591011", port:"0/8"}
NEO2FXO_B={pType:BC, name:"ATLAS ANALOG THROUGH NEO TRUNK T02", IP:False, number:"5592011", port:"0/8"}
NEO2FXO_C={pType:BC, name:"ATLAS ANALOG THROUGH NEO TRUNK T03", IP:False, number:"5593011", port:"0/8"}
NEO2FXO_D={pType:BC, name:"ATLAS ANALOG THROUGH NEO TRUNK T04", IP:False, number:"5594011", port:"0/8"}
NEO2FXO_E={pType:BC, name:"ATLAS ANALOG THROUGH NEO TRUNK T05", IP:False, number:"5595011", port:"0/8"}
NEO2FXO_F={pType:BC, name:"ATLAS ANALOG THROUGH NEO TRUNK T06", IP:False, number:"5596011", port:"0/8"}

NEO_01={pType:IP, name:"VVX300 THROUGH FXO 0/1 T10", IP:"10.10.10.101", number:"5561011", port:"0/1"} 
NEO_02={pType:IP, name:"VVX310 THROUGH FXO 0/2 T02", IP:"10.10.10.102", number:"5562011", port:"0/2"} 
NEO_03={pType:IP, name:"VVX400 through FXO 0/3 T03", IP:"10.10.10.103", number:"5563011", port:"0/3"} 
NEO_04={pType:IP, name:"VVX410 THROUGH FXO 0/4 T04", IP:"10.10.10.104", number:"5564011", port:"0/4"} 
NEO_05={pType:IP, name:"VVX500 THROUGH FXO 0/5 T05", IP:"10.10.10.105", number:"5565011", port:"0/5"} 
#NEO_06={pType:IP, name:"VVX500 THROUGH FXO 0/6 T06", IP:"10.10.10.105", number:"5566011", port:"0/5"}
NEO_06={pType:BC, name:"NEO ANALOG FXS 0/1 THROUGH FXO 0/6 T06", IP:False, number:"5566011", port:"0/7"}

#Tuples of Phones
SIP_LOCAL=(SIP_300,SIP_310,SIP_400,SIP_410,SIP_500)
ANALOG_LOCAL=(BC_A, BC_B)
LOCAL_PHONES=SIP_LOCAL+ANALOG_LOCAL
ATLAS_ANALOG_NUM=(PRI2FXO_A, NEO2FXO_A, NEO2FXO_B, NEO2FXO_C, NEO2FXO_D, NEO2FXO_E, NEO2FXO_F)
NEO_TRUNK_NUM=(NEO_01, NEO_02, NEO_03, NEO_04, NEO_05, NEO_06)

#Ports and addresses
DoorRelayPort="0/24" #NV6355 Port

ROUTER="10.17.235.254"
BULK_CALLER="10.10.10.16"
BULK_CALLER_2="10.10.10.17"
NV6355="10.10.10.55"
NEO="10.10.10.254"

log=logging.getLogger('AutoVerify')
#hdlr=logging.FileHandler('auto.log')
#formatter=logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
#hdlr.setFormatter(formatter)
#log.addHandler(hdlr)
#log.setLevel(logging.INFO)

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

def isRinging(A):
  """
  Returns True if phone has incoming call, else False
  """
  
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  count=0
  if A[pType]==IP:
    try:
      state=sendPoll(A)
      line=(state["LineState"])
    except:
      log.warn('No headers returned from poll')
      return False
    try:
      result=(state["CallState"]=="Offering")
      ##log.debug('%s returned from %s'% (result, (getFunctionName())))
      return result
    except:
      count+=1
      if count>2:
        if line=='Inactive':
          ##log.debug('Line is inactive')
          return False
      else:
        ##log.debug('Unknown error: %s', state)
        return False
  elif A[pType]==BC:
    #this is kind of kludgy, but there is no way to poll for state yet, so I must make an assumption then test it
    #I'll go off hook and expect "to Connected".  "Wrong State" means it is not ringing
    ringing=goOffHook(A)
    return ringing

def isConnected(A):
  """
  Returns True if line state is Active, else False
  """
  ##log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if A[pType]==IP:  
    state=sendPoll(A)
    try:
      result=(state["CallState"]=="Connected" or state["CallState"]=="CallConference")
      ##log.debug('%s returned from %s'% (result, (getFunctionName())))
      return result
    except Exception:
      log.error(Exception)
      return False
  elif A[pType]==BC:
    #this is kind of kludgy, but there is no way to poll for state yet.  I'll go off hook and expect " to Connected".
    #Whether current state is ringing or connected, the BC will return "<STATE> to Connected"
    #Any other response means it is not connected
    connected= goOffHook(A)
    return connected

def call(A, B, inHeadsetMode):
  """
  TODO:  Add functionality to initiate from BC
  A calls B and if A is not in headeset mode, goes to headset mode
  """
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if A[pType]==IP:
    URL=constructPushURL(A)
    PAYLOAD=(PAYLOAD_A + "tel:\\"+B[number]+ PAYLOAD_B)
    result=sendCurl(PAYLOAD, URL)
    if not inHeadsetMode:
      pressHeadset(A)
  elif A[pType]==BC: #will only be in BULK_CALLER 
    baseCommand="script-manager fxo %s " % (A[port],)
    #cmd=baseCommand + db
    #con.write(cmd)
    #time.sleep(1)
    #cmd=baseCommand + on
    #con.write(cmd)
    #time.sleep(1)
    cmd=baseCommand + seize
    con.write(cmd)
    time.sleep(1)
    cmd=baseCommand + dial + B[number] + '\n'
    con.write(cmd)
    time.sleep(1)
  else :
	log.error("Unknown pType %s" %A[pType])
	exit()
  
def connect(A):
  """
  sends a push to press the headset button if SIP phone
  OR
  sends a command to BC to go off-hook
  """
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if A[pType]==IP:
    pressHeadset(A)
  elif A[pType]==BC:
    goOffHook(A)
    
def disconnect(A):
  """
  sends a push to press the headset button if SIP phone
  OR
  sends a command to BC to go on-hook
  """
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if A[pType]==IP:
    state=sendPoll(A)
    try:
      if state['CallState']=="Connected":
        pressEndCall(A)
    except Exception:
      pass
  elif A[pType]==BC:
    goOnHook(A)

def attendedTransfer(A, C):
  """
  TODO:  Add functionality to initiate from BC
  From connected call (A-B), performs attended transfer resulting in (B-C)
  """
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if isConnected(A):
    if A[pType] == IP:
      PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
      URL=constructPushURL(A)
      sendCurl(PAYLOAD, URL)
    else:
      baseCommand="script-manager fxo %s " % (port,)
      cmd=baseCommand + flash
    call(A,C, True)
    while not isRinging(C):
      time.sleep(1)
    connect(C)
    verifyCallPath(A, C, 'attended transfer call AC')
    time.sleep(3)
    if A[pType] == IP:
      PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
      URL=constructPushURL(A)
      sendCurl(PAYLOAD, URL)
    disconnect(A)

def unattendedTransfer(A, C):
  """
  TODO:  Add functionality to initiate from BC
  From connected call (A-B), performs unattended transfer resulting in (B-C)
  """
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if isConnected(A):
    if A[pType] == IP:
      PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
      URL=constructPushURL(A)
      sendCurl(PAYLOAD, URL)
    else:
      baseCommand="script-manager fxo %s " % (port,)
      cmd=baseCommand + flash
    call(A, C, True)
    while not isRinging(C):
      time.sleep(1)
    if A[pType] == IP:
      PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
      URL=constructPushURL(A)
      sendCurl(PAYLOAD, URL)
    while not isRinging(C):
      time.sleep(1)
    time.sleep(1)
    connect(C)

def blindTransfer(A, C):
  """
  From connected call (A-B), performs blind transfer resulting in (B-C)
  """
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if isConnected(A):
    URL=constructPushURL(A)
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
    URL=constructPushURL(A)
    PAYLOAD=(PAYLOAD_A+"Key:Softkey3"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
    initializeCall(A, C, 'blind transfer call leg BC', log, True)

def constructPushURL(A):
  """
  Given IP address returns properly constructed push URL
  """ 
  result=URL_A + A[IP] + URL_B
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  #log.debug('%s returned from %s'% (result, (getFunctionName())))  
  return result

def constructDialPadString(number):
  dialPadString=""
  for n in str(number):
    dialPadString+="Key:Dialpad"+n+"\n"
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  #log.debug('%s returned from %s'% (dialPadString, (getFunctionName())))
  return dialPadString
 
def sendCurl(payload, URL):
  global HEADERS
  global USER
  global PWD
  AUTH=USER+":"+PWD
  curl=['curl', '--digest', '-u', AUTH, '-d', payload, '--header', HEADERA , '--header', HEADERB , URL]
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  return syscall(curl)

def sendRequest(payload, URL):
  global HEADERS
  global AUTH
  DATA=json.dumps(payload)
  result=requests.post(URL, auth=AUTH, verify=False, data=DATA, headers=HEADERS)
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  #log.debug('%s returned from %s'% (result.status_code, (getFunctionName())))
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
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  payload="http://" + A[IP] + "/polling/"+pollType+"Handler"
  result=requests.get(payload, auth=AUTH)
  while result.status_code!=200:
    if count>5:
      sys.exit()
    ##log.debug('%s returned from sendPoll; regenerating Authorization'%(result.status_code,))
    AUTH=digest(USER, PWD)
    result=requests.get(payload, auth=AUTH)
    count+=1
  XMLstring=result.text.splitlines()
  #log.debug("Result of poll is %s" %(XMLstring,))
  pattern=re.compile(r".*<(.*)>(.*)<.*")
  state={}
  for line in XMLstring:
    #log.debug("checking %s for XML" %(line))
    m=pattern.match(line)
    if m:
      #log.debug("found match in %s" %(line,))
      #log.debug("Adding key-value pair %s:%s" %(m.group(1),m.group(2)))
      state.update({m.group(1):m.group(2)})

  lineState=""
  while lineState not in ['Active', 'Inactive']:
    try:
      lineState=state["LineState"]
    except:
      log.warn('No headers returned from poll')
  #log.debug('Valid poll response to %s at %s'% ((getFunctionName(), getArguments(inspect.currentframe()))))
  return state 

def sendKeyPress(A, number):
  payload=PAYLOAD_A+constructDialPadString(number)+PAYLOAD_B
  url=constructPushURL(A)
  sendCurl(payload, url)
 
def sendTones(A, number):
  BC2found = bool(A[port].find("BC2")+1)
  if BC2found:
    telnetCon=con2 # Log in to Bulk Caller 2
  else:
    telnetCon=con # Log in to Bulk Caller 1
  cmd="script-manager fxo %s send-tones %s\n" % (A[port][0:3], number)
  telnetCon.write(cmd)

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
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
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

def pressEndCall(A):
    URL=constructPushURL(A)
    PAYLOAD=(PAYLOAD_A+"Key:Softkey2"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)

def goOffHook(A):
  success="to Connected"
  temp=con.read_eager()
  con.write("script-manager fxo %s off-hook\n" % (A[port],))
  result=con.expect([BC_RESPONSE, "to Connected"],5)
 
  #THIS IS UGLY
  try:
    if success in result[1].group(2):
      return True
  except Exception:
    pass
  if result[0]==1:
    return True
  else:
    return False
  #con.read_until(PROMPT)

def goOnHook(A):
  con.write("script-manager fxo %s on-hook\n" % (A[port],))
  con.expect([BC_RESPONSE,],5)
  #con.read_until(PROMPT)

def telnet(address):
  try:
    con = telnetlib.Telnet(address,23,10)
    return con
  except:
    log.error( "Error connecting to %s:" %(address))
    log.error(sys.exc_info()[0])
    return -1

def login(telnetCon=0):
  global username
  global password
  global enable
  if telnetCon == 0:
    telnetCon=con #if no argument, use global con object
  temp=telnetCon.expect(['Username:'], 5)
  if temp[0] == -1:
      print temp
      exit()
  telnetCon.write(username)
  temp=telnetCon.expect(['Password:'], 2)
  if temp[0] == -1:
      print temp
      exit()
  telnetCon.write(password)
  telnetCon.expect(['>'], 2)
  if temp[0] == -1:
      print temp
      exit()
  telnetCon.write("en\n")
  telnetCon.expect(['Password:'], 2)
  if temp[0] == -1:
      print temp
      exit()
  telnetCon.write(enable)
  telnetCon.expect(['#'], 2)
  if temp[0] == -1:
      print temp
      exit()
  telnetCon.write('\n')
  prompt=telnetCon.read_until('#')
  telnetCon.write("terminal length 0\n")
  if temp[0] == -1:
      print temp
      exit()
  telnetCon.expect([prompt])
  return prompt

def initializePort(port):
  """
  Takes connection and FXO port number (string)
  as arguments and sets the given port into Idle state
  """
  BC2found = bool(port.find("BC2")+1)
  if BC2found:
    telnetCon=con2 # Log in to Bulk Caller 2
  else:
    telnetCon=con # Log in to Bulk Caller 1
  baseCommand="script-manager fxo %s " % (port[0:3],) # Do not read 'at BC' if found
  # results in Offline state
  cmd=baseCommand + on
  telnetCon.write(cmd)
  telnetCon.expect([''], 2)
  telnetCon.read_until(PROMPT, 5)
  # results in Idle state
  cmd=baseCommand + db
  telnetCon.write(cmd)
  telnetCon.expect(['to Idle'], 2)
  telnetCon.read_until(PROMPT, 5)

def initializeSIP(port):
  """
  Initiallizes a port connected to the
  headset on a polycom phone which is
  affilliated with an existing call and
  leaves it in connected mode
  """
  BC2found = bool(port.find("BC2")+1)
  if BC2found:
    telnetCon=con2 # Log in to Bulk Caller 2
  else:
    telnetCon=con # Log in to Bulk Caller 1
  baseCommand="script-manager fxo %s " % (port[0:3],)
  # results in Idle state
  cmd=baseCommand + on
  telnetCon.write(cmd)
  telnetCon.expect(['Idle'], 2)
  #con.read_until(PROMPT)
  time.sleep(1)
  #results in Dialtone state
  cmd=baseCommand + seize
  telnetCon.write(cmd)
  telnetCon.expect(['Dialtone'], 2)
  #con.read_until(PROMPT)
  time.sleep(1)
  #results in Connected state
  cmd=baseCommand + flash
  telnetCon.write(cmd)
  telnetCon.expect(['Connected'], 2)
  #con.read_until(PROMPT)

def listenForTones(port, time='10000', tones='1'):
  """
  Takes a port in Connected State and
  listens for $time MS for $tones tones
  """
  BC2found = bool(port.find("BC2")+1)
  if BC2found:
    telnetCon=con2 # Log in to Bulk Caller 2
  else:
    telnetCon=con # Log in to Bulk Caller 1
  cmd="script-manager fxo %s listen %s %s\n" % (port[0:3], time, tones)
  telnetCon.write(cmd)

def verifyTalkPath(A, B, callType):
  """
  verifies bidirectional talk path
  returns success percentage as a string tuple
  """
  count=0.0
  successAB=0.0
  successBA=0.0
  failed=0
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  #bulk caller calls will already be in connected state, initialize the ports on BC for SIP phones
  if A[pType]==IP:
    initializeSIP(A[port])
  if B[pType]==IP:
    initializeSIP(B[port])

  while count<1.0:
    count +=1
    tonesA='333'
    tonesB='444'
    if B[pType]==BC:
      listenForTones(A[port], time=12000)
    else:
      listenForTones(A[port])
    time.sleep(2)#pause for BC
    log.info("Listening for a %s on fxo %s: %s -> %s"%(tonesA[0], A[port], B[name], A[name]))
    sendTones(B, tonesA)
    BC2foundA = bool(A[port].find("BC2")+1)
    if BC2foundA:
      telnetCon=con2 # Log in to Bulk Caller 2
    else:
      telnetCon=con # Log in to Bulk Caller 1
    result=telnetCon.expect([BC_RESPONSE,], 10)
    try:
      while result[1].group(2) not in ['5000', '5001']:
        result=telnetCon.expect([BC_RESPONSE,], 15)
      log.info("%s: received (%s) on fxo %s" %(result[1].group(2), result[1].group(4), A[port]))
      if result[1].group(2)=="5001":
        successBA+=1
      else:
        log.error("Error: %s: (%s)" %result[1].group(3). result[1].group(4))
    except:
      log.error("Error: unknown return value")

    time.sleep(5)

    if A[pType]==BC:
      listenForTones(B[port], time=12000)
    else:
      listenForTones(B[port])
    time.sleep(2)#pause for BC
    log.info("Listening for a %s on fxo %s: %s -> %s"%(tonesB[0], B[port], A[name], B[name]))
    sendTones(A, tonesB)
    BC2foundB = bool(B[port].find("BC2")+1)
    if BC2foundB:
      telnetCon=con2 # Log in to Bulk Caller 2
    else:
      telnetCon=con # Log in to Bulk Caller 1
    result=telnetCon.expect([BC_RESPONSE,], 10)
    try:
      while result[1].group(2) not in ['5000', '5001']:
        result=telnetCon.expect([BC_RESPONSE,], 15)
      log.info("%s: received (%s) on fxo %s" %(result[1].group(2), result[1].group(4), B[port]))
      if result[1].group(2)=="5001":
        successAB+=1
      else:
        log.error("Error: %s: (%s)" %result[1].group(3). result[1].group(4))
    except:
      log.error("Error: unknown return value")
    time.sleep(10) #peridoic tests
  successRateBA="{0:.0%}".format(successBA/count)
  successRateAB="{0:.0%}".format(successAB/count)
  return (successRateAB, successRateBA)

def verifyCallPath(A, B, callType):
  """
  takes existing calls and telnet connection as arguments
  if phone is sip:
    verifies connection
    maxes headset volumes
  verifies talk path in both directions
  #logs results
  """
  global RESULTS
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  time.sleep(1)
  agood=False
  bgood=False
  attempts=0
  while not (agood and bgood):
    attempts+=1
    agood=isConnected(A)
    bgood=isConnected(B)
    if attempts==20:
     log.error("Unable to determine connection between %s and %s" %(A[name], B[name]))
     #RESULTS.append('Unable to verify connection from %s to %s in %s'%(B[name], A[name], callType))
     #RESULTS.append('Unable to verify connection from %s to %s in %s'%(A[name], B[name], callType))    
     return False
  if (agood and bgood):
    #crank up the headset volumes
    if A[pType]==IP:
      maxVolume(A)
    if B[pType]==IP:
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
  log.info('initializing talk path verification between %s and %s during %s'% (A[name], B[name], callType))
  (successRateAB, successRateBA)=verifyTalkPath(A, B, callType)
  log.info('%s success rate from %s to %s in %s'%(successRateBA,B[name], A[name], callType))
  log.info('%s success rate from %s to %s in %s'%(successRateAB,A[name], B[name], callType))  
  #RESULTS.append('%s success rate from %s to %s in %s'%(successRateBA,B[name], A[name], callType))
  #RESULTS.append('%s success rate from %s to %s in %s'%(successRateAB,A[name], B[name], callType))
  log.info('%s test complete\n\n'%(callType, ))
  return (int(successRateAB[:-1]) and int(successRateBA[:-1]))

def initializeCall(A, B, callType, log, inHeadsetMode):
  """
  initializes a call of callType between A and B
  waits for B to start ringing and then connects
  """
  if B[port]:
      initializePort(B[port])      
  if A[port]:
      initializePort(A[port])   

  time.sleep(6)
  call(A,B, inHeadsetMode)
  log.info('initializing %s from %s to %s' %(callType, A[name], B[name]))
  count = 0
  while not isRinging(B):
    time.sleep(1)
    count += 1
    if count == 20:
      log.error('Call failed from %s to %s\n' %(A[name], B[name]))
      #RESULTS.append('Call failed from %s to %s' %(A[name], B[name]))
      return False
  connect(B)
  return True

def normalCall(A, B, callID=False):
  """
  places call between A and B,
  verifies talk path in both directions,
  #logs results and hangs up
  """
  passed = True
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if (initializeCall(A, B, 'normal call', log, False)):
    if callID==True:
      passed = callerIDtest(B)
    else:
      passed = verifyCallPath(A, B, 'normal call')
  else:
    passed = False
  disconnect(A)
  disconnect(B)
  return passed
  
def conferenceCall(A, B, C):
  """
  creates conference call between A,B, and C
  does NOT validate A-B talkpath before conferencing
  verifies talk path in between all three participants
  #logs results and hangs up
  """
  passed = True
  ##log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if (initializeCall(A,B,'conference call AB', log, False)):
    passed = verifyCallPath(A, B, 'conference call leg AB')
    pressConference(A)
    if(initializeCall(A,C,'conference call AC', log, True)):
      passed = verifyCallPath(A, C, 'conference call leg AC')
      pressConference(A)
      time.sleep(2)
      log.info("connecting conference call legs AB->AC")
      passed = verifyCallPath(A, B, 'conference call ABC')
      passed = verifyCallPath(A, C, 'conference call ABC')
      passed = verifyCallPath(B, C, 'conference call ABC')
    else:
      passed = False
  else:
    passed = False
  disconnect(A)
  disconnect(B)
  disconnect(C)
  return passed
  
def attendedTransferCall(A, B, C):
  """
  places call between A and B,
  verifies talk path in both directions,
  attended transfer from A->C
  verifies talk path in both directions,
  #logs results and hangs up
  """
  passed = True
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if(initializeCall(A, B, 'attended transfer call leg AB', log, False)):
    #time.sleep(5)
    passed = verifyCallPath(A, B, 'attended transfer call leg AB')
    attendedTransfer(A, C)
    #time.sleep(5)
    passed = verifyCallPath(C, B, 'attended transfer call leg BC')
  else :
    passed = False
  disconnect(B)
  disconnect(C)
  return passed
  
def unattendedTransferCall(A, B, C):
  """
  places call between A and B,
  verifies talk path in both directions,
  unattended transfer from A->C
  verifies talk path in both directions,
  #logs results and hangs up
  """
  passed = True
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if(initializeCall(A, B, 'unattended transfer call leg AB', log, False)):
    passed = verifyCallPath(A, B, 'unattended transfer call leg AB')
    time.sleep(10)
    unattendedTransfer(A, C)
    passed = verifyCallPath(C, B, 'unattended transfer call leg BC')
  else :
    passed = False
  disconnect(B)
  disconnect(C)
  return passed
  
def blindTransferCall(A, B, C):
  """
  places call between A and B,
  verifies talk path in both directions,
  blind transfer from A->C
  verifies talk path in both directions,
  #logs results and hangs up
  """
  passed = True
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if(initializeCall(A, B, 'blind transfer call leg AB', log, False)):
    passed = verifyCallPath(A, B, 'blind transfer call leg AB')
    blindTransfer(A, C)
    passed = verifyCallPath(C, B, 'blind transfer call leg BC')
  else :
    passed = False
  disconnect(B)
  disconnect(C)
  return passed
  
def setupLogging(level):
  log=logging.getLogger('AutoVerify')
  hdlr=logging.FileHandler(log_filename)
  formatter=logging.Formatter('%(asctime)s %(levelname)-5s %(message)s')
  hdlr.setFormatter(formatter)
  log.addHandler(hdlr)
  log.setLevel(level)
  #set requests logging to WARNING
  requests_log = logging.getLogger("requests")
  requests_log.setLevel(logging.WARNING)

def callerIDtest(A):
  state = sendPoll(A)
  passed=True
  caller=(state["CallingPartyName"])
  callerNum=(state["CallingPartyDirNum"])
  log.info("Calling Party: %s - %s"%(caller, callerNum))
  if (callerNum.find("Unknown")+1):
    passed=False
  return passed
   
def initializeTest(ipA, ipB, level, testType):
  """
  creates connection to bulk caller
  returns telnet connection
  """
  global PROMPT
  global con
  global con2
  con=telnet(ipA) # telnet to first bulk caller
  #~ setupLogging(level)
  log.info('\n\nCreating %s...\n' %(testType))
  if con==-1:
    log.error("No connection to device")
    exit()
  PROMPT=login(con)
  for i in ('1','2','3','4','5','6','7','8'):
    port="0/"+i
    initializePort(port)
  con2=telnet(ipB) # telnet to second bulk caller through first bulk caller's  CLI
  if con2==-1:
    log.error("No connection to device")
    exit()
  PROMPT=login(con2)
  for i in ('0'):
    port="0/"+i
    initializePort(port)
  
def finalizeTest():
  log.info('\n\n#### TEST RESULTS #####\n\n')
  #~ for result in RESULTS:
    #~ log.info(result)
  log_file = open(log_filename)
  log_output = log_file.read()
  result_file = open("Test_Results_Phone_Calls.log", 'w')
  result_file.write('#### TEST RESULTS #####\n\n')
  for result in RESULTS:
    result_file.write(result + '\n')
  print(log_output)
  result_file.write(log_output)
  log_file.close()
  result_file.close()

def passFailCheck(passed):
  if passed:
     return "PASS"
  else:
     return "FAIL"

def test():
  """
  Unit testing of automation script
  """
#Set up logger
  setupLogging(INFO)
#Clearing old logfile
  open(log_filename, 'w').close()
  log.info("Neo Phone Calls Verification Test")
  runs = 1
  RESULTS.append("Neo Phone Calls Verification Test")

#Phone Calls Testing
  initializeTest(BULK_CALLER, BULK_CALLER_2, INFO, "Neo Telnet Connection")
  for i in range(runs):
    log.info("CALLER ID VERIFICATION#################################")
    passed = normalCall(SIP_500,SIP_300, True)
    passed = normalCall(NV7100_SIP_400,SIP_310, True)
    passed = normalCall(PRI2FXO_A,SIP_400, True)
    passed = normalCall(PRI2FXO_A,NEO_04, True)
    RESULTS.append("CALLER ID VERIFICATION----------------------------%s"%(passFailCheck(passed)))

  for i in range(runs):
    log.info("NORMAL CALL LOCAL SIP-SIP VERIFICATION#################################")
    passed = normalCall(SIP_300,SIP_310)
    RESULTS.append("NORMAL CALL LOCAL SIP-SIP VERIFICATION----------------------------%s"%(passFailCheck(passed)))

  for i in range(runs):
    log.info("NORMAL CALL LOCAL SIP-ANALOG VERIFICATION#############################")
    passedA = normalCall(SIP_400,BC_A)
    passedB = normalCall(BC_B,SIP_410)
    passed = passedA and passedB
    RESULTS.append("NORMAL CALL LOCAL SIP-ANALOG VERIFICATION------------------------%s"%(passFailCheck(passed)))

  for i in range(runs):
    log.info("NORMAL CALL THROUGH SIP TRUNK VERIFICATION##############################\n")
    passedA = normalCall(SIP_500,NV7100_SIP_400)
    passedB = normalCall(NV7100_SIP_400,SIP_300)
    passed = passedA and passedB
    RESULTS.append("NORMAL CALL THROUGH SIP TRUNK VERIFICATION-------------------------%s"%(passFailCheck(passed)))

  for i in range(runs):
    log.info("NORMAL CALL THROUGH T1/PRI VERIFICATION#############################")
    passedA = normalCall(SIP_500,PRI2FXO_A)
    passedB = normalCall(PRI2FXO_A,SIP_300)
    passed = passedA and passedB
    RESULTS.append("NORMAL CALL LOCAL THROUGH T1/PRI VERIFICATION------------------------%s"%(passFailCheck(passed)))

  #time.sleep(10)
  for i in range(runs):
    log.info("NORMAL CALL THROUGH FXO PORTS OUTBOUND CALL VERIFICATION##############################\n")
    for j in ATLAS_ANALOG_NUM:
      passed += int(not(normalCall(SIP_310,j)))
    RESULTS.append("NORMAL CALL THROUGH FXO PORTS OUTBOUND CALL VERIFICATION-------------------------%s"%(passFailCheck(passed)))

  for i in range(runs):
    log.info("NORMAL CALL THROUGH FXO PORTS INBOUND CALL VERIFICATION##############################\n")
    for j in NEO_TRUNK_NUM:
      passed += int(not(normalCall(PRI2FXO_A,j)))
    RESULTS.append("NORMAL CALL THROUGH FXO PORTS INBOUND CALL VERIFICATION-------------------------%s"%(passFailCheck(passed)))

  for i in range(runs):
    log.info("ATTENDED CALL TRANSFER LOCAL VERIFICATION#################################")
    passed = attendedTransferCall(SIP_400,SIP_410,SIP_500)
    RESULTS.append("ATTENDED CALL TRANSFER LOCAL VERIFICATION----------------------------%s"%(passFailCheck(passed)))

  for i in range(runs):
    log.info("ATTENDED CALL TRANSFER SIP TRUNK VERIFICATION#################################")
    passed = attendedTransferCall(SIP_300,NV7100_SIP_400,SIP_400)
    RESULTS.append("ATTENDED CALL TRANSFER SIP TRUNK VERIFICATION----------------------------%s"%(passFailCheck(passed)))

  for i in range(runs):
    log.info("ATTENDED CALL TRANSFER T1/PRI VERIFICATION#################################")
    passed = attendedTransferCall(SIP_300,PRI2FXO_A,SIP_310)
    RESULTS.append("ATTENDED CALL TRANSFER T1/PRI VERIFICATION----------------------------%s"%(passFailCheck(passed)))

  for i in range(runs):
    log.info("ATTENDED CALL TRANSFER FXO VERIFICATION#################################")
    for j in ATLAS_ANALOG_NUM:
      passed += int(not(attendedTransferCall(SIP_400,j,SIP_410)))
    RESULTS.append("ATTENDED CALL TRANSFER FXO VERIFICATION----------------------------%s"%(passFailCheck(passed)))

#CAUSES NEO TO REBOOT
  #~ for i in range(runs):
    #~ log.info("UNATTENDED CALL TRANSFER LOCAL VERIFICATION#################################")
    #~ passed = unattendedTransferCall(SIP_400,SIP_410,SIP_500)
    #~ RESULTS.append("UNATTENDED CALL TRANSFER LOCAL VERIFICATION----------------------------%s"%(passFailCheck(passed)))

  #~ for i in range(runs):
    #~ log.info("UNATTENDED CALL TRANSFER SIP TRUNK VERIFICATION#################################")
    #~ passed = unattendedTransferCall(SIP_300,NV7100_SIP_400,SIP_310)
    #~ RESULTS.append("UNATTENDED CALL TRANSFER SIP TRUNK VERIFICATION----------------------------%s"%(passFailCheck(passed)))
#~ 
  #~ for i in range(runs):
    #~ log.info("UNATTENDED CALL TRANSFER T1/PRI VERIFICATION#################################")
    #~ passed = unattendedTransferCall(SIP_300,PRI2FXO_A,SIP_310)
    #~ RESULTS.append("UNATTENDED CALL TRANSFER T1/PRI VERIFICATION----------------------------%s"%(passFailCheck(passed)))
#~ 
  #~ for i in range(runs):
    #~ log.info("UNATTENDED CALL TRANSFER FXO VERIFICATION#################################")
    #~ for j in ATLAS_ANALOG_NUM:
      #~ passed += int(not(unattendedTransferCall(SIP_400,j,SIP_410)))
    #~ RESULTS.append("UNATTENDED CALL TRANSFER FXO VERIFICATION----------------------------%s"%(passFailCheck(passed)))
#~ 
  #~ for i in range(runs):
    #~ log.info("BLIND CALL TRANSFER LOCAL VERIFICATION#################################")
    #~ passed = blindTransferCall(SIP_400,SIP_410,SIP_500)
    #~ RESULTS.append("BLIND CALL TRANSFER LOCAL VERIFICATION----------------------------%s"%(passFailCheck(passed)))
#~ 
  #~ for i in range(runs):
    #~ log.info("BLIND CALL TRANSFER SIP TRUNK VERIFICATION#################################")
    #~ passed = blindTransferCall(SIP_300,NV7100_SIP_400,SIP_310)
    #~ RESULTS.append("BLIND CALL TRANSFER SIP TRUNK VERIFICATION----------------------------%s"%(passFailCheck(passed)))
#~ 
  #~ for i in range(runs):
    #~ log.info("BLIND CALL TRANSFER T1/PRI VERIFICATION#################################")
    #~ passed = blindTransferCall(SIP_300,PRI2FXO_A,SIP_310)
    #~ RESULTS.append("BLIND CALL TRANSFER T1/PRI VERIFICATION----------------------------%s"%(passFailCheck(passed)))
#~ 
  #~ for i in range(runs):
    #~ log.info("BLIND CALL TRANSFER FXO VERIFICATION#################################")
    #~ for j in ATLAS_ANALOG_NUM:
      #~ passed += int(not(blindTransferCall(SIP_400,j,SIP_410)))
    #~ RESULTS.append("BLIND CALL TRANSFER FXO VERIFICATION----------------------------%s"%(passFailCheck(passed)))
#~ 
  #~ for i in range(runs):
    #~ log.info("CONFERENCE CALL LOCAL VERIFICATION#################################")
    #~ passed = conferenceCall(SIP_400,SIP_410,SIP_500)
    #~ RESULTS.append("CONFERENCE CALL LOCAL VERIFICATION----------------------------%s"%(passFailCheck(passed)))
#~ 
  #~ for i in range(runs):
    #~ log.info("CONFERENCE CALL SIP TRUNK VERIFICATION#################################")
    #~ passed = conferenceCall(SIP_300,NV7100_SIP_400,SIP_310)
    #~ RESULTS.append("CONFERENCE CALL SIP TRUNK VERIFICATION----------------------------%s"%(passFailCheck(passed)))
#~ 
  #~ for i in range(runs):
    #~ log.info("CONFERENCE CALL T1/PRI VERIFICATION#################################")
    #~ passed = conferenceCall(SIP_300,PRI2FXO_A,SIP_310)
    #~ RESULTS.append("CONFERENCE CALL T1/PRI VERIFICATION----------------------------%s"%(passFailCheck(passed)))
#~ 
  #~ for i in range(runs):
    #~ log.info("CONFERENCE CALL FXO VERIFICATION#################################")
    #~ for j in ATLAS_ANALOG_NUM:
      #~ passed += int(not(conferenceCall(SIP_400,j,SIP_410)))
    #~ RESULTS.append("CONFERENCE CALL FXO VERIFICATION----------------------------%s"%(passFailCheck(passed)))
atexit.register(finalizeTest)

if __name__=="__main__":
  test()

