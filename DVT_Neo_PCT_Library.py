#!/usr/bin/env python
#########################################################################################################################
# This software belongs to Adtran, Inc.
# Author Jeffrey McAnarney from U.S. 7/26/2013
#        Julian Sy  10/11/2013
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
username, password, enable = 'adtran\n', 'adtran\n', 'adtran\n' #Login credentials telnet to Neo and Bulk Callers
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
pType="pType"
BC="BC"
name="name"
IP="IP"
TrunkID="TrunkID"
number="number"
altnum="altnum"
port="port"
alias="alias"
Virtual="Virtual"
log_filename = 'Results_DVT_Neo_PCT.log'
aaKey="aaKey"
vm="vm"
mailboxTone="mailboxTone"
passwordTone="passwordTone"
person_at_extTone="person_at_extTone"
unavailableTone="unavailableTone"
pTones="pTones"

#vm dictionary
mailboxMenu='mailboxMenu'
passwordMenu='passwordMenu'
unavailableMenu='unavailableMenu'
leaveMenu='leaveMenu'

#aa dictionary
loginMenu='loginMenu'
localMenu='localMenu'
externalMenu='externalMenu'
voicemailMenu='voicemailMenu'
transferMainMenu='transferMainMenu'
transferSalesMenu='transferSalesMenu'
transferAccountingMenu='transferAccountingMenu'
transferMarketingMenu='transferMarketingMenu'

DEBUG=logging.DEBUG
INFO=logging.INFO

#Telnet Globals
con=telnetlib.Telnet()
con2=telnetlib.Telnet()
neo_con=telnetlib.Telnet()

#Bulk Call Globals
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
phone="phone"
phone1="phone1"
phone2="phone2"
phone3="phone3"

#Blank Phone Global
BLANK_PHONE={pType:False, name:False, IP:False, number:False, port:False, alias:False, aaKey:False, pTones:False}

#Different callTypes for Voicemail, Auto Attendant, and Ring Groups
AA_DIAL="Auto Attendant Dial by Extension Call"
AA_TRANSFER="Auto Attendant Call Tranfer"
AA_VM="Auto Attendant Voicemail Call"
AA_TRANSFER_MENU_CALL="Auto Attendant Transfer Menu Call Phone"
AA_TRANSFER_MENU_PROMPT="Auto Attendant Transfer Menu Play Prompt"

VMAIL_MSG_BUTTON="Voicemail Message Button Call"
VMAIL_STAR98="Voicemail *98 Call"
VMAIL_DIR_EXT="Voicemail Direct Phone Extension Call"
VMAIL_LOGIN_EXT="Voicemail 8500 Login Extension Call"

RG_ALL_RING="Ring Group All Ring Call"
RG_LINEAR_HUNT="Ring Group Linear Hunt Call"
RG_UCD="Ring Group UCD Call"
RG_EXEC_RING="Ring Group Executive Ring Call"

CQ_ALL_RING="Call Queuing All Ring Call"
CQ_LINEAR_HUNT="Call Queuing Linear Hunt Call"
CQ_MOST_IDLE="Call Queuing Most Idle Phone Call"

log=logging.getLogger('AutoVerify')

def getFunctionName(): #For debugging
  return inspect.stack()[1][3]

def getCallingModuleName(): #For debugging
  return inspect.stack()[3][3]

def getArguments(frame):
  args, _, _, values = inspect.getargvalues(frame)
  return [(i, values[i]) for i in args]

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
  elif A[pType]==Virtual:
    return True

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
    #Whether current state is ringing or connected, the BC will return "<STATE> to Connected" or "<STATE> to Connecting"
    #Any other response means it is not connected
    connected=goOffHook(A)
    return connected

def call(A, B, inHeadsetMode):
  """
  A calls B and if A is not in headeset mode, goes to headset mode
  """
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  callNum(A, B[number])
  if not inHeadsetMode and A[pType]==IP:
    pressKey(A,"Headset")

def callNum(A, num):
  """
  sends a call to num if SIP phone
  OR
  sends a command to BC to dial num
  OR
  exits program if invalid phone type
  """
  if A[pType]==IP:
    URL=constructPushURL(A)
    PAYLOAD=(PAYLOAD_A+"tel:\\"+num+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
  elif A[pType]==BC:
    #Determine correct Bulk Caller
    BC2found=bool(A[port].find("BC2")+1)
    if BC2found:
      telnetCon=con2 # Log in to Bulk Caller 2
    else:
      telnetCon=con # Log in to Bulk Caller 1
    baseCommand="script-manager fxo %s " % (A[port],)
    telnetCon.write(baseCommand + seize)
    time.sleep(1)
    telnetCon.write(baseCommand + dial + num + '\n')
    time.sleep(1)
  else:
    log.error("%s has an invalid phone type %s"%(A[name],A[pType]))
    exit()
  
def connect(A):
  """
  sends a push to press the headset button if SIP phone
  OR
  sends a command to BC to go off-hook
  """
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if A[pType]==IP:
    pressKey(A,"Headset")
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
        pressKey(A,"Softkey2") #Softkey to end call
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
    pressKey(A,"Transfer")
    call(A,C, True)
    while not isRinging(C):
      time.sleep(1)
    connect(C)
    verifyCallPath(A, C, 'attended transfer call AC')
    time.sleep(3)
    pressKey(A,"Transfer")
    disconnect(A)

def unattendedTransfer(A, C):
  """
  TODO:  Add functionality to initiate from BC
  From connected call (A-B), performs unattended transfer resulting in (B-C)
  """
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if isConnected(A):
    pressKey(A,"Transfer")
    call(A, C, True)
    pressKey(A,"Transfer")
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
    pressKey(A,"Transfer")
    pressKey(A,"Softkey3") #Key to transfer blind
    initializeCall(A, C, 'blind transfer call leg BC', log, True)

def constructPushURL(A):
  """
  Given IP address returns properly constructed push URL
  """ 
  result=URL_A + A[IP] + URL_B
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  #log.debug('%s returned from %s'% (result, (getFunctionName())))  
  return result

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
  """
  sends a push to press button 'number'
  used for dial pad keys
  """
  for i in number:
    if i=='#':
      i="Pound"
    elif i=='*':
      i="Star"
    payload=PAYLOAD_A+"Key:Dialpad"+i+PAYLOAD_B
    url=constructPushURL(A)
    sendCurl(payload, url)
 
def sendTones(A, number):
  """
  sends a command to BC to send tones 'number'
  """
  #Determine correct Bulk Caller
  BC2found=bool(A[port].find("BC2")+1)
  if BC2found:
    telnetCon=con2 # Log in to Bulk Caller 2
  else:
    telnetCon=con # Log in to Bulk Caller 1
  cmd="script-manager fxo %s send-tones %s\n" % (A[port][0:3], number)
  telnetCon.write(cmd)

def maxVolume(A):
  """
  send Push to increase volume 10 times
  """
  for i in range(10):
    pressKey(A,"VolUp")

def pressConference(A):
  """
  IFF connected: conference with number
  From active call, presses conference softkey
  """
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  state=sendPoll(A)
  callState=state["CallState"]
  if callState=="Connected":
    pressKey(A,"Conference")

def pressKey(A, key):
  """
  sends a push to press 'key'
  """
  URL=constructPushURL(A)
  PAYLOAD=(PAYLOAD_A+"Key:"+key+PAYLOAD_B)
  sendCurl(PAYLOAD, URL)

def goOffHook(A):
  """
  sends a command to BC to go off-hook
  returns True if phone state is connected
  returns False otherwise
  """
  success="to Connect"
  temp=con.read_eager()
  con.write("script-manager fxo %s off-hook\n" % (A[port],))
  result=con.expect([BC_RESPONSE, "to Connect",],5)
  #THIS IS UGLY
  try:
    if success in result[1].group(2):
      return True
  except Exception:
    pass
  if result[0]==1:
    return True
  else:
    print result
    return False
  #con.read_until(PROMPT)

def goOnHook(A):
  """
  sends a command to BC to go on-hook
  """
  con.write("script-manager fxo %s on-hook\n" % (A[port],))
  con.expect([BC_RESPONSE,],5)
  #con.read_until(PROMPT)

def telnet(address):
  """
  Creates telnet connection to address
  returns telnet object
  returns -1 if connection unsuccessful
  """
  try:
    con = telnetlib.Telnet(address,23,10)
    return con
  except:
    log.error( "Error connecting to %s:" %(address))
    log.error(sys.exc_info()[0])
    return -1

def login(telnetCon=con):
  """
  sends a command through telnet to log in to unit
  if no argument, default telnet object is for BC1 
  """
  global username
  global password
  global enable

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

def resetPort(port):
  """
  enters CLI commands "Shutdown" and "No Shutdown"
  on the port interface
  """
  #Determine correct Bulk Caller
  BC2found = bool(port.find("BC2")+1)
  if BC2found:
    telnetCon=con2 # Log in to Bulk Caller 2
  else:
    telnetCon=con # Log in to Bulk Caller 1

  telnetCon.write("configure terminal\n")
  time.sleep(1)
  telnetCon.write("interface fxo %s\n"%(port[0:3],))
  telnetCon.write("shutdown\n")
  time.sleep(1)
  telnetCon.write("no shutdown\n")
  time.sleep(1)
  telnetCon.write("exit\n")
  telnetCon.write("exit\n")

def initializePort(port):
  """
  Takes connection and FXO port number (string)
  as arguments and sets the given port into Idle state
  """
  #Determine correct Bulk Caller
  BC2found = bool(port.find("BC2")+1)#Checks if Bulk Caller port is in BC1 or BC2
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
  #Determine correct Bulk Caller
  BC2found=bool(port.find("BC2")+1)
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
  #Determine correct Bulk Caller
  BC2found = bool(port.find("BC2")+1)
  if BC2found:
    telnetCon=con2 # Log in to Bulk Caller 2
  else:
    telnetCon=con # Log in to Bulk Caller 1
  cmd="script-manager fxo %s listen %s %s\n" % (port[0:3], time, tones)
  telnetCon.write(cmd)

def verifyVirtualPhoneCallPath(A,B,tone=""):
  """
  verifies prompt being played
  returns True if correct prompt is played (i.e. tones in prompt are heard) 
  """
  success=False
  if tone=="":
    tone=B[pTones]
  if A[pType]==IP:
    initializeSIP(A[port])
  log.info("Listening for %s on Bulk Caller fxo %s:"%(tone,A[port]))
  listenForTones(A[port],time='15000',tones=(3*len(tone))) #listen to the tones
  #Determine correct Bulk Caller
  BC2foundA = bool(A[port].find("BC2")+1)
  if BC2foundA:
    telnetCon=con2 # Log in to Bulk Caller 2
  else:
    telnetCon=con # Log in to Bulk Caller 1
  result=telnetCon.expect([BC_RESPONSE,], 10)
  try:
    while result[1].group(2) not in ['5000', '5001']:
      result=telnetCon.expect([BC_RESPONSE,], 15)
    log.info("Received (%s) on fxo %s" %(result[1].group(4), A[port]))
    if result[1].group(2) in ['5000', '5001']:
      #Check if the dtmf tones in tone are found in prompt
      foundTones=True
      toneIndex = (result[1].group(4)).find(tone)+(3*len(tone))-(len(result[1].group(4)))
      patternNotFound = bool((result[1].group(4)).find(tone)==-1)
      if patternNotFound:
        log.error("Error: %s: (%s)" %result[1].group(3). result[1].group(4))
      else:
        log.info("%s found after %s tones"%(tone, toneIndex))
        success=True
    else:
      log.error("Error: %s: (%s)" %result[1].group(3). result[1].group(4))
  except:
    log.error("Error: unknown return value")
  return success

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
    BC2foundA=False
    BC2foundB=False
    tonesA='333'
    tonesB='444'
    toneLen='3'
    if B[pType]==BC:
      listenForTones(A[port], time=12000,tones=toneLen)
    else:
      listenForTones(A[port],tones=toneLen)
    time.sleep(2)#pause for BC
    log.info("Listening for a %s on Bulk Caller fxo %s: %s -> %s"%(tonesA[0], A[port], B[name], A[name]))
    sendTones(B, tonesA)
    #Determine correct Bulk Caller
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
      listenForTones(B[port], time=12000,tones=toneLen)
    else:
      listenForTones(B[port],tones=toneLen)
    time.sleep(2)#pause for BC
    log.info("Listening for a %s on Bulk Caller fxo %s: %s -> %s"%(tonesB[0], B[port], A[name], B[name]))
    sendTones(A, tonesB)
    #Determine listening Bulk Caller
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
  if B[pType]==Virtual:
    return verifyVirtualPhoneCallPath(A,B)

  agood=False
  bgood=False
  attempts=0
  while not (agood and bgood):
    attempts+=1
    agood=isConnected(A)
    bgood=isConnected(B)
    time.sleep(1)
    if attempts==20:
     log.error("Unable to determine connection between %s and %s" %(A[name], B[name]))    
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
  log.info('%s talk path test initiated between %s and %s' %(callType, A[name], B[name]))
  #seize associated ports and get them into Connected state
  log.info('initializing talk path verification between %s and %s during %s'% (A[name], B[name], callType))
  (successRateAB, successRateBA)=verifyTalkPath(A, B, callType)
  log.info('%s success rate from %s to %s in %s'%(successRateBA,B[name], A[name], callType))
  log.info('%s success rate from %s to %s in %s'%(successRateAB,A[name], B[name], callType))  
  #RESULTS.append('%s success rate from %s to %s in %s'%(successRateBA,B[name], A[name], callType))
  #RESULTS.append('%s success rate from %s to %s in %s'%(successRateAB,A[name], B[name], callType))
  log.info('%s test complete'%(callType, ))
  return (int(successRateAB[:-1]) and int(successRateBA[:-1]))

def initializeCall(A, B, callType, log, inHeadsetMode):
  """
  initializes a call of callType between A and B
  waits for B to start ringing and then connects
  skips wait for ringing if B is virtual phone or
  has same number as A
  """
  if B[pType]!=Virtual:
    if B[port]:
      initializePort(B[port])      
  if A[port]:
    initializePort(A[port])   

  time.sleep(6)
  call(A,B, inHeadsetMode)
  log.info('initializing %s from %s to %s' %(callType, A[name], B[name]))
  if B[pType]!=Virtual and A[number]!=B[number]: #Skip ring check if calling virtual phone or own number
    attempts = 0
    time.sleep(1)
    while not isRinging(B):
      time.sleep(1)
      attempts += 1
      if attempts==20:
        log.error('Call failed from %s to %s' %(A[name], B[name]))
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
  success=True
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if (initializeCall(A, B, 'normal call', log, False)):
    if callID==True:
      success=callerIDtest(A, B)
    else:
      success=verifyCallPath(A, B, 'normal call')
  else:
    success = False
  time.sleep(1)
  disconnect(A)
  disconnect(B)
  log.info("TEST %s"%(passFailCheck(success)))
  log.info(" \n")
  return success
  
def conferenceCall(A, B, C):
  """
  creates conference call between A,B, and C
  does NOT validate A-B talkpath before conferencing
  verifies talk path in between all three participants
  #logs results and hangs up
  """
  success = True
  ##log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if (initializeCall(A,B,'conference call AB', log, False)):
    if verifyCallPath(A, B, 'conference call leg AB'):
      pressConference(A)
      if(initializeCall(A,C,'conference call AC', log, True)):
        if verifyCallPath(A, C, 'conference call leg AC'):
          pressConference(A)
          time.sleep(2)
          log.info("connecting conference call legs AB->AC")
          if verifyCallPath(A, B, 'conference call ABC'):
            if verifyCallPath(A, C, 'conference call ABC'):
              success=verifyCallPath(B, C, 'conference call ABC')
    else:
      success = False
  else:
    passed = False
  time.sleep(1)
  disconnect(C)
  disconnect(B)
  disconnect(A)
  log.info("TEST %s"%(passFailCheck(passed)))
  log.info(" \n")
  return passed
  
def attendedTransferCall(A, B, C):
  """
  places call between A and B,
  verifies talk path in both directions,
  attended transfer from A->C
  verifies talk path in both directions,
  #logs results and hangs up
  """
  success = True
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if(initializeCall(A, B, 'attended transfer call leg AB', log, False)):
    #time.sleep(5)
    if verifyCallPath(A, B, 'attended transfer call leg AB'):
      attendedTransfer(A, C)
      #time.sleep(5)
      success = verifyCallPath(C, B, 'attended transfer call leg BC')
  else :
    success = False
  time.sleep(1)
  disconnect(C)
  disconnect(B)
  disconnect(A)
  log.info("TEST %s"%(passFailCheck(success)))
  log.info(" \n")
  return success
  
def unattendedTransferCall(A, B, C):
  """
  places call between A and B,
  verifies talk path in both directions,
  unattended transfer from A->C
  verifies talk path in both directions,
  #logs results and hangs up
  """
  success = True
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if(initializeCall(A, B, 'unattended transfer call leg AB', log, False)):
    if verifyCallPath(A, B, 'unattended transfer call leg AB'):
      time.sleep(10)
      unattendedTransfer(A, C)
      success = verifyCallPath(C, B, 'unattended transfer call leg BC')
  else :
    success = False
  time.sleep(1)
  disconnect(C)
  disconnect(B)
  disconnect(A)
  log.info("TEST %s"%(passFailCheck(success)))
  log.info(" \n")
  return success
  
def blindTransferCall(A, B, C):
  """
  places call between A and B,
  verifies talk path in both directions,
  blind transfer from A->C
  verifies talk path in both directions,
  #logs results and hangs up
  """
  success = True
  #log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  if(initializeCall(A, B, 'blind transfer call leg AB', log, False)):
    if verifyCallPath(A, B, 'blind transfer call leg AB'):
      blindTransfer(A, C)
      success = verifyCallPath(C, B, 'blind transfer call leg BC')
  else :
    success = False
  time.sleep(1)
  disconnect(C)
  disconnect(B)
  disconnect(A)
  log.info("TEST %s"%(passFailCheck(success)))
  log.info(" \n")
  return success

def pressKeyVirtualPhone(A,key):
  """
  sends a push to press key if SIP phone
  OR
  sends a command to BC to send tone 'key'
  """
  if A[pType]==IP:
    sendKeyPress(A,key)
    return True
  elif A[pType]==BC:
    sendTones(A,key)
    time.sleep(1) #Prevent busy port
    return True
  else:
    log.error("Unknown phone type %s"%(A[pType]))
    return False

def virtualPhoneTransferMenu(A,B,callType,menuKey="0",transfer=False):
  """
  Verifies if in correct menu through correct tones heard
  Retries at most 3 times
  If set to True, transfer from menu by pressing menuKey
  """
#Verify if on correct menu
  log.info("Verifying connection to %s menu..."%(B[name]))
  for i in range(3): #Three attempts to listen for tones
    time.sleep(1)
    if verifyCallPath(A,B,callType):
      break
    else:
      log.info("Tone %s not found"%(B[pTones]))
      if i==2:
        return False
#Transfer to next menu
  if transfer:
    log.info("Pressing key(s) %s"%(menuKey))
    return pressKeyVirtualPhone(A,menuKey)
  else:
    return True
  
#Testing for voicemail
def voicemailCall(vm,A, callType, B=BLANK_PHONE):
  """
  Checks which call type
  Calls voicemail via call type.
  Verifies tones and navigates through
  until password prompt is reached
  """
  if A[pType]==IP:
    pressKey(A,"Headset")
  success=False
#Message button vm test
  if callType==VMAIL_MSG_BUTTON:
    log.info("Pressing Messages button",)
    pressKey(A,"Messages")
    time.sleep(1)
    success=virtualPhoneTransferMenu(A,vm[passwordMenu],callType)
#*98 vm test
  elif callType==VMAIL_STAR98:
    initializeCall(A,vm[passwordMenu],"Password Prompt",log,True)
    time.sleep(1)
    success=virtualPhoneTransferMenu(A,vm[passwordMenu],callType)
#Dialing vm login extension vm test
  elif callType==VMAIL_LOGIN_EXT:
    initializeCall(A,vm[mailboxMenu],"VM Login Call",log,True)
    time.sleep(1)
    if virtualPhoneTransferMenu(A,vm[mailboxMenu],callType,'##',True):
      success=virtualPhoneTransferMenu(A,vm[passwordMenu],callType)
#Dialing direct extension vm test
  elif callType==VMAIL_DIR_EXT:
    initializeCall(A,B,"Normal Call",log,True)
    time.sleep(1)
    if virtualPhoneTransferMenu(A,vm[unavailableMenu],callType,'*',True):	
      if virtualPhoneTransferMenu(A,vm[mailboxMenu],callType,'##',True):
        success=virtualPhoneTransferMenu(A,vm[passwordMenu],callType)
#Unknown call type
  else:
    log.error("Unknown Voicemail Call Type")
  disconnect(A)
  log.info("TEST %s"%(passFailCheck(success)))
  log.info(" \n")
  return success

def autoAttendantCall(aa,A,B,callType,C=BLANK_PHONE, fxoCall=False):
  """
  Checks which call type and sets number to call AA and
  sets num to AA key or phone number to enter in AA menu
  For FXO Calls, calls are made to C which is Neo FXO port
  with a trunk number set to AA
  Makes calls and dials by extensiont OR presses key to transfer using num.
  Verifies talk path
  For Voicemail, once navigated to voicemail person-unavailable prompt,
  navigates to voicemail password prompt
  For Transfer Menu Call Type, Calls autoAttendantTransferMenu
  and returns its return values
  """
  success=True
#Set to dial an extension in AA
  if callType==AA_DIAL:
    if fxoCall: #FXO DIAL
      virtual_phone=B
      num=C[number]
    else :
      virtual_phone=aa[loginMenu] #NON FXO DIAL
      num=B[number]
    menu="Default"
#Set to transfer call in AA
  elif callType==AA_TRANSFER:
    if B[name].find("LOCAL")!=-1: #LOCAL TRANSFER
      virtual_phone=aa[localMenu]
      num=B[aaKey]
      menu="Local"
    else:
      if fxoCall: #FXO EXTERNAL TRANSFER
        virtual_phone=B
        num=C[aaKey]
      else :
        virtual_phone=aa[externalMenu] #NON FXO EXTERNAL TRANSFER
        num=B[aaKey]
      menu="External"
#Set to transfer to voicemail in AA
  elif callType==AA_VM:
    if fxoCall: #FXO VM
      virtual_phone=B
      num=C[aaKey]
    else :
      virtual_phone=aa[voicemailMenu] #NON FXO VM
      num=B[aaKey]
    menu="Voicemail"
#Set to transfer call in company menu
  elif callType==AA_TRANSFER_MENU_CALL or callType==AA_TRANSFER_MENU_PROMPT:
    return autoAttendantTransferMenu(aa,A,B,callType,C,fxoCall)
#Unknown callType
  else:
    log.error("Unknown call type")
    log.info("TEST %s"%(passFailCheck(False)))
    log.info(" \n")
    return False
#Call AutoAttendant
  initializeCall(A,virtual_phone,'%s Auto Attendant call'%(menu), log, False)
  if callType==AA_VM: 
    virtual_phone=aa[voicemailMenu]
  if virtualPhoneTransferMenu(A,virtual_phone,callType,num,True):
  #If checking voicemail/leaving message
    if callType==AA_VM:
      if virtualPhoneTransferMenu(A,aa[voicemailMenu][vm][unavailableMenu],callType,'*',True):	
        if virtualPhoneTransferMenu(A,aa[voicemailMenu][vm][mailboxMenu],callType,'##',True):
          success=virtualPhoneTransferMenu(A,aa[voicemailMenu][vm][passwordMenu],callType)
      else:
        success=False
  #If calling phone
    else:
      attempts=0
      while not isRinging(B):
        time.sleep(1)
        attempts+=1
        if attempts==5:
          log.error('Call failed from %s to %s' %(A[name], B[name]))
          success=False
          break
      if success:
        connect(B)
        success=verifyCallPath(A,B,'%s Auto Attendant call'%(menu))
  disconnect(A)
  disconnect(B)
  log.info("TEST %s"%(passFailCheck(success)))
  log.info(" \n")
  return success

def autoAttendantTransferMenu(aa,A,B,callType,C, fxoCall):
  """
  Checks which call type
  Calls autoatendant and navigates through menus
  Makes calls via call type and aaKey.
  Verifies talk path or selected audio prompt
  """
  success=True
  if fxoCall:
    menu=B
  else:
    menu=aa[transferMainMenu]
  initializeCall(A,menu, "Auto Attendant Transfer Menu call",log,False)
  if fxoCall:
    B=C #use person/prompt in C
  if B[name].find("SALES")!=-1:
    subMenu=aa[transferSalesMenu]
  elif B[name].find("ACCOUNTING")!=-1:
    subMenu=aa[transferAccountingMenu]
  elif B[name].find("MARKETING")!=-1:
    subMenu=aa[transferMarketingMenu]
  else:
    log.error("Unknown Phone/Prompt Menu %s"%(B[name]))
    log.info("TEST %s"%(passFailCheck(False)))
    log.info(" \n")
    return False
  if virtualPhoneTransferMenu(A,aa[transferMainMenu],callType,subMenu[aaKey],True):
    if virtualPhoneTransferMenu(A,subMenu,callType,B[aaKey],True):
      if callType==AA_TRANSFER_MENU_CALL:
        attempts=0
        while not isRinging(B[phone]):
          time.sleep(1)
          attempts+=1
          if attempts==5:
            log.error('Call failed from %s to %s' %(A[name], B[phone][name]))
            success=False
            break
        if success:
          connect(B[phone])
          success=verifyCallPath(A,B[phone],'%s Auto Attendant call'%(subMenu[name]))
      elif callType==AA_TRANSFER_MENU_PROMPT:
        success=virtualPhoneTransferMenu(A,B,callType)
    else:
      success=False
  else:
    success=False
  disconnect(A)
  if callType==AA_TRANSFER_MENU_CALL:
    disconnect(B[phone])
  log.info("TEST %s"%(passFailCheck(success)))
  log.info(" \n")
  return success

def ringGroupCall(A,B,callType):
  """
  Creates Call Queuing Call and verifies talk path
  for each of the 3 phones in Ring Group
  """
  if A[port]:
    initializePort(A[port])
  if B[phone1]:
    initializePort(B[phone1][port])
  if B[phone2]:
    initializePort(B[phone2][port])
  if B[phone3]:
    initializePort(B[phone3][port])   

  success=True
  if callType==RG_ALL_RING or RG_LINEAR_HUNT or RG_UCD or RG_EXEC_RING:
    for i in (B[phone1],B[phone2],B[phone3]):
      if i:
        initializeCall(A,B,callType,log,False)
        time.sleep(1)
        attempts=0
        while not isRinging(i):
          attempts+=1
          time.sleep(2)
          if attempts==30:
            log.error('Call failed from %s to %s' %(A[name], B[name]))
            success=False
        if success:    
          connect(i)
          time.sleep(1)
          if not verifyCallPath(A, i,callType):
            success=False
          disconnect(i)
      disconnect(A)
  else:
    log.error("Unknown call type %s"%(callType))
    success=False
  log.info("TEST %s"%(passFailCheck(success)))
  log.info(" \n")
  return success

def callQueuingCall(A,B,callType):
  """
  Creates Call Queuing Call and verifies call queue and pick up prompts
  and talk path for each of the 3 phones in Group
  """
  if A[port]:
    initializePort(A[port])
  if B[phone1][port]:
    initializePort(B[phone1][port])
  if B[phone2][port]:
    initializePort(B[phone2][port])
  if B[phone3][port]:
    initializePort(B[phone3][port])   

  success=True
  if callType==CQ_ALL_RING or CQ_LINEAR_HUNT or CQ_MOST_IDLE:
    for i in (B[phone1],B[phone2],B[phone3]):
      if i:
        initializeCall(A,B,callType,log,False)
        time.sleep(1)
        log.info("Verifying Greeting Prompt...")
        if verifyCallPath(A,B,callType):
          attempts=0
          while not isRinging(i):
            attempts+=1
            time.sleep(2)
            if attempts==30:
              log.error('Call failed from %s to %s' %(A[name], B[name]))
              success=False
          if success:
            connect(i)
            time.sleep(1	)
            log.info("Verifying Call Pickup Prompt...")
            if verifyCallPath(i,B,callType):
              if not verifyCallPath(A, i,callType):
                success=False
            disconnect(i)
          disconnect(A)
  else:
    log.error("Unknown call type %s"%(callType))
    success=False
  log.info("TEST %s"%(passFailCheck(success)))
  log.info(" \n")
  return success

def pickupGroupCall(A,pickUpGroup):
  success=True
  B=pickUpGroup[phone1]
  C=pickUpGroup[phone2]

  if A[port]:
    initializePort(A[port])
  if B[port]:
    initializePort(B[port])
  if C[port]:
    initializePort(C[port])

  call(A,B, False)
  log.info('initializing %s from %s to %s' %("Normal Call", A[name], B[name]))
  attempts = 0
  while not isRinging(B):
    time.sleep(1)
    attempts += 1
    if attempts==20:
      log.error('Call failed from %s to %s' %(A[name], B[name]))
      log.info("TEST %s"%(passFailCheck(False)))
      log.info(" \n")
      return False
  log.info('initializing %s from %s to %s' %("PickUp Group Call", C[name], pickUpGroup[name]))
  call(C,pickUpGroup,False)
  time.sleep(1)
  if not verifyCallPath(A,C,"PickUp Group Call"):
    success=False
  disconnect(A)
  disconnect(C)

  time.sleep(2)
  if A[port]:
    initializePort(A[port])
  if B[port]:
    initializePort(B[port])
  if C[port]:
    initializePort(C[port])

  call(A,C, False)
  log.info('initializing %s from %s to %s' %("Normal Call", A[name], C[name]))
  attempts = 0
  while not isRinging(C):
    time.sleep(1)
    attempts += 1
    if attempts==20:
      log.error('Call failed from %s to %s' %(A[name], B[name]))
      log.info("TEST %s"%(passFailCheck(False)))
      log.info(" \n")
      return False
  log.info('initializing %s from %s to %s' %("PickUp Group Call", B[name], pickUpGroup[name]))
  call(B,pickUpGroup,False)
  time.sleep(1)
  if not verifyCallPath(A,B,"PickUp Group Call"):
    success=False
  disconnect(A)
  disconnect(B)
  log.info("TEST %s"%(passFailCheck(success)))
  log.info(" \n")
  return success


def setTrunkNumber(trunkID, trunkNum):
  """  
  sets trunk number of trunk ID
  """
  neo_con.write("configure terminal \n")
  temp=neo_con.expect(['\(config\)#'], 5)
  if temp[0] == -1:
      print temp
      exit()
  neo_con.write("voice trunk %s\n"%(trunkID,))
  temp=neo_con.expect(['\(config-%s\)#'%(trunkID,)], 5)
  if temp[0] == -1:
      print temp
      exit()
  log.info("Setting %s trunk-number to %s"%(trunkID,trunkNum))
  neo_con.write("trunk-number %s\n"%(trunkNum,))
  time.sleep(1)
  neo_con.write("exit\n")
  temp=neo_con.expect(['\(config\)#'], 5)
  if temp[0] == -1:
      print temp
      exit()
  neo_con.write("exit\n")
  temp=neo_con.expect(['#'], 5)
  if temp[0] == -1:
      print temp
      exit()
  neo_con.write(" \n")


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

def callerIDtest(A,B):
  """
  Verifies if Caller ID has correct phone number
  """
  try:
    state = sendPoll(B)
    passed=True
    caller=(state["CallingPartyName"])
    callerNum=(state["CallingPartyDirNum"])
    log.info("Calling Party: %s - %s"%(caller, callerNum))
    if not(callerNum.find(A[number])+1):
      log.error("Incorrect phone number in Caller ID")
      passed=False
    else:
      log.info("Correct phone number in Caller ID")
  except:
    log.warn('No headers returned from poll')
  return passed
   
def initializeTest(bc1Ip, bc2Ip, neoIp, level):
  """
  creates connection to bulk caller
  initializes ports in bulk callers
  returns telnet connection
  """
  global PROMPT
  global con
  global con2
  global neo_con

  log.info('Creating Telnet Connection to %s...'%(bc1Ip))
  con=telnet(bc1Ip)
  #~ setupLogging(level)
  if con==-1:
    log.error("No connection to device")
    exit()
  PROMPT=login(con)

  log.info('Creating Telnet Connection to %s...'%(bc2Ip))
  con2=telnet(bc2Ip)
  if con2==-1:
    log.error("No connection to device")
    exit()
  PROMPT=login(con2)

  log.info('Creating Telnet Connection to %s...'%(neoIp))
  neo_con=telnet(neoIp) 
  if neo_con==-1:
    log.error("No connection to device")
    exit()
  PROMPT=login(neo_con)  

  #~ log.info("Initializing Bulk Caller Ports...")
  #~ for i in BC_PORTS:
    #~ initializePort(i)
  
def finalizeTest():
  """
  Prints results in RESULTS and log AutoCallPathVerify.log
  into new Test Results log
  """
  log.info('\n\n#### TEST RESULTS #####\n\n')
  #~ for result in RESULTS:
    #~ log.info(result)
  log_file = open(log_filename)
  log_output = log_file.read()
  result_file = open("Final_Test_Results_DVT_Neo_PCT.log", 'w')
  result_file.write('#### TEST RESULTS #####\n\n')
  for result in RESULTS: #Write summary of tests
    result_file.write(result + '\n')
  print(log_output)
  result_file.write(log_output) #Write log file
  log_file.close()
  result_file.close()

def passFailCheck(passed):
  """
  Returns string PASS or FAIL*** if True or False
  """
  if passed:
     return "PASS"
  else:
     return "FAIL***"

def test():
  """
  Unit testing of automation script
  """
  pass
  
atexit.register(finalizeTest)

if __name__=="__main__":
  test()
