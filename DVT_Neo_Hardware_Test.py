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

NV7100_SIP_400={pType:IP, name:"NV7100 POLYCOM VVX500 THROUGH SIP TRUNK", IP:"10.17.235.71:111", number:"5552221", port:"0/5"}

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
NEO_06={pType:IP, name:"VVX500 THROUGH FXO 0/6 T06", IP:"10.10.10.105", number:"5566011", port:"0/5"} 

DoorRelayPort="0/24"

ROUTER="10.17.235.254"
BULK_CALLER="10.10.10.16"
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
  elif A[pType]==BC:
    baseCommand="script-manager fxo %s " % (A[port],)
    cmd=baseCommand + db
    con.write(cmd)
    time.sleep(1)
    cmd=baseCommand + on
    con.write(cmd)
    time.sleep(1)
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
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    URL=constructPushURL(A)
    sendCurl(PAYLOAD, URL)
    call(A,C, True)
    while not isRinging(C):
      time.sleep(1)
    connect(C)
    verifyCallPath(A, C, 'attended transfer call AC')
    time.sleep(3)
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
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    URL=constructPushURL(A)
    sendCurl(PAYLOAD, URL)
    call(A, C, True)
    while not isRinging(C):
      time.sleep(1)
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
  cmd="script-manager fxo %s send-tones %s\n" % (A[port], number)
  con.write(cmd)

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

def login():
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

def initializePort(port):
  """
  Takes connection and FXO port number (string)
  as arguments and sets the given port into Idle state
  """
  baseCommand="script-manager fxo %s " % (port,)
  # results in Offline state
  cmd=baseCommand + on
  con.write(cmd)
  con.expect([''], 2)
  con.read_until(PROMPT, 5)  
  # results in Idle state
  cmd=baseCommand + db
  con.write(cmd)
  con.expect(['to Idle'], 2)
  con.read_until(PROMPT, 5)  

def initializeSIP(port):
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
  #con.read_until(PROMPT)
  time.sleep(1)
  #results in Dialtone state
  cmd=baseCommand + seize
  con.write(cmd)
  con.expect(['Dialtone'], 2)
  #con.read_until(PROMPT)
  time.sleep(1)
  #results in Connected state
  cmd=baseCommand + flash
  con.write(cmd)
  con.expect(['Connected'], 2)
  #con.read_until(PROMPT)

def listenForTones(port, time='10000', tones='1'):
  """
  Takes a port in Connected State and
  listens for $time MS for $tones tones
  """
  cmd="script-manager fxo %s listen %s %s\n" % (port, time, tones)
  con.write(cmd)

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
    if B[pType]==IP:
      sendTones(B, tonesA)
      #sendKeyPress(B, tonesA)
    else:
      sendTones(B, tonesA)
    result=con.expect([BC_RESPONSE,], 10)
    try:
      while result[1].group(2) not in ['5000', '5001']:
        result=con.expect([BC_RESPONSE,], 15)
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
    if A[pType]==IP:
      sendTones(A, tonesB)
      #sendKeyPress(A, tonesB)
    else:
      sendTones(A, tonesB)
    result=con.expect([BC_RESPONSE,], 10)
    try:
      while result[1].group(2) not in ['5000', '5001']:
        result=con.expect([BC_RESPONSE,], 15)
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

def normalCall(A, B):
  """
  places call between A and B,
  verifies talk path in both directions,
  #logs results and hangs up
  """
  passed = True
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if (initializeCall(A, B, 'normal call', log, False)):
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
  
  
def initializeTest(ip, level, testType):
  """
  creates connection to bulk caller
  returns telnet connection
  """
  global PROMPT
  global con
  con=telnet(ip)
  #~ setupLogging(level)
  log.info('\n\nCreating %s...\n' %(testType))
  if con==-1:
    log.error("No connection to device")
    exit()
  PROMPT=login()
  if(ip == BULK_CALLER):
    for i in ('1','2','3','4','5','6','7','8'):
      port="0/"+i
      initializePort(port)
 
  
def finalizeTest():
  log.info('\n\n#### TEST RESULTS #####\n\n')
  #~ for result in RESULTS:
    #~ log.info(result)
  log_file = open(log_filename)
  log_output = log_file.read()
  result_file = open("Test_Results.log", 'w')
  result_file.write('#### TEST RESULTS #####\n\n')
  for result in RESULTS:
    result_file.write(result + '\n')
  print(log_output)
  result_file.write(log_output)
  log_file.close()
  result_file.close()


def testPinging(device):
  log.info("Pinging device with IP address %s..."%(device))
  cmd = "ping " + device + '\n'
  con.write(cmd)
  time.sleep(5)
  log.info("Checking for response...")
  temp=con.expect(['Success rate is 100 percent'], 5)
  if temp==-1:
    log.error("Pinging was unsuccessful.\n")
    return False
  else :
    log.info("Pinging successful.\n")
  return True

def setDoorRelay(setType, method, A):
	if method == "CLI":
		cmd_telneo = "telnet "+ NEO + '\n'
		con.write(cmd_telneo)
		login()
		log.info("Setting relay to %s via CLI..."%(setType))
		cmd = "set relay %s \n"%(setType);
		con.write(cmd)
		cmd = "exit\n"
		con.write(cmd) #Exit telnet from Neo
		con.write("enable\n")
		con.write(enable)
	elif method == "Dial-in":
		log.info("Setting relay to %s via %s..."%(setType, A[name]))		
		URL=constructPushURL(A)
		PAYLOAD=(PAYLOAD_A+"tel:\\*38"+PAYLOAD_B)
		sendCurl(PAYLOAD, URL)
	else:
		log.error("Method for setting door relay not specified")
		return
	
    
def testDoorRelay(method,A=0):
	"""
	Unit testing of Door Relay
	"""
	error = 0
	cmd_spi = spi + DoorRelayPort + '\n'
	log.info('Checking Power Inline for Ethernet %s' %(DoorRelayPort))
	con.write(cmd_spi)
	temp=con.expect(['Searching','to SEARCHING','down'], 5)
	if temp[0] == -1:
		log.info("Status already 'Delivering'")
	else:
		log.info("Status is 'Searching'")
	setDoorRelay("close", method, A)
	log.info('Checking Power Inline for Ethernet %s' %(DoorRelayPort))
	time.sleep(5)
	con.write(cmd_spi)
	temp=con.expect(['Delivering','to DELIVERING','up'], 5)
	if temp[0] == -1:
		log.error("Status still 'Searching'")
		error += 1
	else:
		log.info("Status is 'Delivering'")
	setDoorRelay("open", method, A)
	log.info('Checking Power Inline for Ethernet %s' %(DoorRelayPort))
	time.sleep(5)
	con.write(cmd_spi)
	temp=con.expect(['Searching','to SEARCHING','down'], 5)
	if temp[0] == -1:
			log.error("Status still 'Delivering'")
			error += 1
	else:
			log.info("Status is 'Searching'")
	log.info("Test completed")
	if error == 0:
		log.info("%s Door Relay Test Passed\n\n" %(method))
		return True
	else:
		log.info("%s Door Relay Test Failed\n\n" %(method, ))
		return False

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
  log.info("Neo Hardware Verification Test")
  RESULTS.append("Neo Hardware Verification Test")
  runs = 1

#Door Relay Testing
  initializeTest(NV6355, INFO, "NV6355 Telnet Connection")
  log.info("DOOR RELAY VERIFICATION############################\n")
  for i in range(runs):
    passed_doorRelA = testDoorRelay("CLI")
    passed_doorRelB = testDoorRelay("Dial-in",SIP_300)
    passed = passed_doorRelA and passed_doorRelB
    RESULTS.append("DOOR RELAY VERIFICATION---------------------%s"%(passFailCheck(passed)))

#Phone Calls Testing
  initializeTest(BULK_CALLER, INFO, "Neo Telnet Connection")  
  for i in range(runs):
		#SIP to SIP local
    log.info("LAN VERIFICATION#################################")
    passed_lanA = testPinging(BULK_CALLER)
    passed_lanB = normalCall(SIP_300,SIP_400)
    passed = passed_lanA and passed_lanB
    RESULTS.append("LAN VERIFICATION----------------------------%s"%(passFailCheck(passed)))

  for i in range(runs):
		#~ #SIP to SIP through SIP trunks
    log.info("WAN VERIFICATION#################################")
    passed_wanA = testPinging(ROUTER)
    #passed_wanB = normalCall(SIP_300,NV7100_SIP_400)
    passed = passed_wanA #and passed_wanB
    RESULTS.append("WAN VERIFICATION----------------------------%s"%(passFailCheck(passed)))

  for i in range(runs):
		#~ #SIP to analog local FXS 0/1
    log.info("FXS 0/1 VERIFICATION#############################")
    passed_fxs01A = normalCall(SIP_300,BC_A)
    passed_fxs01B = normalCall(BC_A,SIP_300)
    passed = passed_fxs01A and passed_fxs01B
    RESULTS.append("FXS 0/1 VERIFICATION------------------------%s"%(passFailCheck(passed)))

  for i in range(runs):
		#~ #SIP to analog local FXS 0/2
    log.info("FXS 0/2 VERIFICATION#############################")
    passed_fxs02A = normalCall(SIP_300,BC_B)
    passed_fxs02B = normalCall(BC_B,SIP_300)
    passed = passed_fxs02A and passed_fxs02B
    RESULTS.append("FXS 0/2 VERIFICATION------------------------%s"%(passFailCheck(passed)))

  #time.sleep(10)
  for i in range(runs):
		#~ #SIP to analog through T1/PRI 
    log.info("T1/PRI VERIFICATION##############################\n")
    passed_t1priA = normalCall(SIP_300,PRI2FXO_A)
    passed_t1priB = normalCall(PRI2FXO_A,SIP_300)
    passed = passed_t1priA and passed_t1priB
    RESULTS.append("T1/PRI VERIFICATION-------------------------%s"%(passFailCheck(passed)))

  #time.sleep(10)
  for i in range(runs):
		#~ #SIP to analog through FX0 0/1
    log.info("FXO 0/1 VERIFICATION#############################\n")
    passed_fxo01A = normalCall(SIP_300,NEO2FXO_A)
    passed_fxo01B = normalCall(PRI2FXO_A,NEO_01)
    passed = passed_fxo01A and passed_fxo01B
    RESULTS.append("FXO 0/1 VERIFICATION------------------------%s"%(passFailCheck(passed)))

  #time.sleep(10)
  for i in range(runs):
		#~ #SIP to analog through FX0 0/2
    log.info("FXO 0/2 VERIFICATION#############################\n")
    passed_fxo02A = normalCall(SIP_300,NEO2FXO_B)
    passed_fxo02B = normalCall(PRI2FXO_A,NEO_02)
    passed = passed_fxo02A and passed_fxo02B
    RESULTS.append("FXO 0/2 VERIFICATION------------------------%s"%(passFailCheck(passed)))

  #time.sleep(10)
  for i in range(runs):
		#~ #SIP to analog through FX0 0/3
    log.info("FXO 0/3 VERIFICATION#############################\n")
    passed_fxo03A = normalCall(SIP_300,NEO2FXO_C)
    passed_fxo03B = normalCall(PRI2FXO_A,NEO_03)
    passed = passed_fxo03A and passed_fxo03B
    RESULTS.append("FXO 0/3 VERIFICATION------------------------%s"%(passFailCheck(passed)))

  #time.sleep(10)
  for i in range(runs):
		#~ #SIP to analog through FX0 0/4
    log.info("FXO 0/4 VERIFICATION#############################\n")
    passed_fxo04A = normalCall(SIP_300,NEO2FXO_D)
    passed_fxo04B = normalCall(PRI2FXO_A,NEO_04)
    passed = passed_fxo04A and passed_fxo04B
    RESULTS.append("FXO 0/4 VERIFICATION------------------------%s"%(passFailCheck(passed)))

  #time.sleep(10)
  for i in range(runs):
		#~ #SIP to analog through FX0 0/5
    log.info("FXO 0/5 VERIFICATION#############################\n")
    passed_fxo05A = normalCall(SIP_300,NEO2FXO_E)
    passed_fxo05B = normalCall(PRI2FXO_A,NEO_05)
    passed = passed_fxo05A and passed_fxo05B
    RESULTS.append("FXO 0/5 VERIFICATION------------------------%s"%(passFailCheck(passed)))

  #time.sleep(10)
  for i in range(runs):
		#~ #SIP to analog through FX0 0/7
    log.info("FXO 0/6 VERIFICATION#############################\n")
    passed_fxo06A = normalCall(SIP_300,NEO2FXO_F)
    passed_fxo06B = normalCall(PRI2FXO_A,NEO_06)
    passed = passed_fxo06A and passed_fxo06B
    RESULTS.append("FXO 0/6 VERIFICATION------------------------%s"%(passFailCheck(passed)))

  log.info("MUSIC ON HOLD VERIFICATION NOT YET AVAILABLE\n\n")
  RESULTS.append("MUSIC ON HOLD VERIFICATION------------------N\A")

  log.info("PAGE VERIFICATION NOT YET AVAILABLE\n\n")  
  RESULTS.append("PAGE VERIFICATION---------------------------N\A")

atexit.register(finalizeTest)


if __name__=="__main__":
  test()
