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
# Author Jeffrey McAnarney from U.S. 7/26/2013
# 
#
#  Beautiful is better than ugly
#  Explicit is better than implicit
#  Simple is better than complex
#  Complex is better than complicated
#  Readability counts
#
###############################################################################
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
################################################################################

###Requires requests : sudo apt-get install python-requests

import requests
import inspect
import sys
import json
from requests.auth import HTTPDigestAuth as digest
from time import sleep
from subprocess import call as syscall
import re
import logging

#Set globals
USER='Push'
PWD='Push'
AUTH=digest(USER, PWD)
URL_A=r"http://"
URL_B=r"/push"
HEADERA="Content-Type: application/x-com-polycom-spipx"
HEADERB="User-Agent: DVT User Agent"
PAYLOAD_A="<PolycomIPPhone><Data priority=\"Critical\">"
PAYLOAD_B="</Data></PolycomIPPhone>"

#Define state machine transistions
"""
Outgoing call states: Dialtone, Setup, Ringback
Incoming call states: Offering
Outgoing/incoming call states: Connected, CallConference,
CallHold, CallHeld, CallConfHold, CallConfHeld
Line state: Active, Inactive
Shared line states: CallRemoteActive
Call type: Incoming, Outgoing

!!!!!!TODO!!!!!!  If I return a callstate poll and the line is inactive
!!!!!!TODO!!!!!!     then make sure I am testing any call state checks
!!!!!!TODO!!!!!!     to handle 'None'; positive tests should serve
"""

def getFunctionName():
  return inspect.stack()[1][3]

def getCallingModuleName():
  return inspect.stack()[3][3]

def getArguments(frame):
  args, _, _, values = inspect.getargvalues(frame)
  return [(i, values[i]) for i in args]


#!!!!!!!!!!!!!!TODO!!!!!!!!!!! need to be able to set the log level dynamically!!!!!!!!!!!!!!!!!!!!
def setLogging(name):
  log=logging.getLogger(name)
  #requests_log=logging.getLogger("requests").setLevel(logging.level)
  return log

def isHome(ip):
  """
  returns true if phone is on default page (not settings)
  ***STILL NOT REALLY SURE HOW TO DO THIS****

  
  """
  pass

def goHome(ip):
  """
  Sets phone at IP back to home screen
  ***STILL NOT REALLY SURE HOW TO DO THIS****
  
  !!!if I send an http message and then hit the home button it sends us to home......
  """
  pass

def isActive(ip):
  """
  Returns True if line state is Active, else False
  """
  log=setLogging(__name__)
  state=sendPoll(ip)
  result=(state["LineState"]=="Active")
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  log.debug('%s returned from %s'% (result, (getFunctionName())))
  return result

def isRingback(ip):
  """
  Returns True if call state is RingBack, else False
  """
  state=sendPoll(ip)
  result=(state["CallState"]=="Ringback")
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  log.debug('%s returned from %s'% (result, (getFunctionName())))
  return result

def isRinging(ip):
  """
  Returns True if phone has incoming call, else False
  """
  state=sendPoll(ip)
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  try:
    result=(state["CallState"]=="Offering")
    log.debug('%s returned from %s'% (result, (getFunctionName())))
    return result
  except:
    log.warn('No headers returned from poll')
    return False

def isConnected(ip):
  """
  Returns True if line state is Active, else False
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  state=sendPoll(ip)
  try:
    result=state["CallState"]=="Connected"
    log.debug('%s returned from %s'% (result, (getFunctionName())))
    return result
  except Exception:
    log.error(Exception)
    return False

def call(ip, number):
  """
  IFF LineState?INACTIVE==>DIALTONE->SETUP->RINGBACK
  Given the ip address of the phone from which to call and a number to call
  calls number, and goes to headset mode
  TODO:  Returns -1 if no registered line is inactive or if push message rejected 
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  URL=constructPushURL(ip)
  #command="Key:Softkey1\n"+constructDialPadString(number)+"Key:Softkey2"
  PAYLOAD=(PAYLOAD_A + "tel:\\"+number+ PAYLOAD_B)
  if not isActive(ip):
    #result=sendRequest(PAYLOAD, URL)
    result=sendCurl(PAYLOAD, URL)
  PAYLOAD=(PAYLOAD_A+"Key:Headset"+PAYLOAD_B)
  sendCurl(PAYLOAD, URL)
  sleep(2)

  
def connect(ip):
  """
  IFF isRinging(ip)?TRUE==>isActive(ip)
  STATE==OFFERING=>ACTIVE
  """
  callstate=""
  PAYLOAD=(PAYLOAD_A+"Key:Headset"+PAYLOAD_B)
  URL=constructPushURL(ip)
  print "connecting to %s"%ip
  sendCurl(PAYLOAD, URL)
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))

def disconnect(ip):
  """
  IFF isConnected(ip)?TRUE==>isActive(ip)?FALSE
  STATE==CONNECTED=>INACTIVE
  ???Can we reliably use the HandsFree key if we use it to answer the phone initially???
  """
  state=sendPoll(ip)
  #Lets not test for connected call, rather test the line
  #Active line state covers all call states 

  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  state=sendPoll(ip)
  lineState=state["LineState"]
  log.debug("Linestate at %s is %s" %(ip, lineState))
  try:
    if lineState=="Active":
      PAYLOAD=(PAYLOAD_A+"Key:Softkey2"+PAYLOAD_B)
      URL=constructPushURL(ip)
      sendCurl(PAYLOAD, URL)
  except Exception:
    
    PAYLOAD=(PAYLOAD_A+"Key:Softkey2"+PAYLOAD_B)
    URL=constructPushURL(ip)
    sendCurl(PAYLOAD, URL)
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))

def transfer(ipA, number, ipC):
  """
  IFF isActive(ipA)?TRUE==>transfer
  From active call, performs attended transfer to number
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  state=sendPoll(ipA)
  lineState=state["LineState"]
  log.debug("Linestate at %s is %s" %(ipA, lineState))
  if lineState=="Active":
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    URL=constructPushURL(ipA)
    sendCurl(PAYLOAD, URL)
    call(ipA, number)
    while not isRinging(ipC):
      sleep(1)
    connect(ipC)
    sleep(3)
    #while not isConnected(ipB):
    #  sleep(1)
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    URL=constructPushURL(ipA)
    sendCurl(PAYLOAD, URL)    
    disconnect(ipA)
    
def unattendedTransfer(ipA, number, ipC):
  """
  IFF isActive(ipA)?TRUE==>transfer
  From active call, performs unattended transfer to number
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  state=sendPoll(ipA)
  lineState=state["LineState"]
  log.debug("Linestate at %s is %s" %(ipA, lineState))
  if lineState=="Active":
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    URL=constructPushURL(ipA)
    sendCurl(PAYLOAD, URL)
    call(ipA, number)
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    URL=constructPushURL(ipA)
    sendCurl(PAYLOAD, URL)
    disconnect(ipA)
    while not isRinging(ipC):
      sleep(1)
    connect(ipC)
    #while not isConnected(ipC):
    #  sleep(1)
    PAYLOAD=(PAYLOAD_A+"Key:Softkey3"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))

def blindTransfer(ipA, number, ipC):
  """
  IFF isActive(ipA)?TRUE==>transfer
  From active call, performs blind transfer to number
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  state=sendPoll(ipA)
  lineState=state["LineState"]
  log.debug("Linestate at %s is %s" %(ipA, lineState))
  if lineState=="Active":
    URL=constructPushURL(ipA)
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
    sleep(3)
    PAYLOAD=(PAYLOAD_A+"Key:Softkey4"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
    PAYLOAD=(PAYLOAD_A+"Key:Softkey1"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
    call(ipA, number)
    sleep(1)
    disconnect(ipA)
    sleep(1)
    #while not isRinging(ipC):
    #  sleep(1)
    connect(ipC)
    #while not isConnected(ipC):
    #  sleep(1)
    URL=constructPushURL(ipA)
    PAYLOAD=(PAYLOAD_A+"Key:Softkey3"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
  
###????TODO????###  I think this should stay separate from the initial call; 
#                   The only downside is I can't check all three phones for conf state
#                   unless I send in the extra ip, but I can get confirmation from two
#                   of the three IP, and they won't give conf without the third
def conference(ipA, number, ipB):
  """
  IFF connected: conference with number
  From active call, conferences with number
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  state=sendPoll(ipA)
  callState=state["CallState"]
  log.debug("Callstate between %s and %s is %s" %(ipA, number, callState))
  if callState=="Connected":
    PAYLOAD=(PAYLOAD_A+"Key:Conference"+PAYLOAD_B)
    URL=constructPushURL(ipA)
    sendCurl(PAYLOAD, URL)
    call(ipA, number)
    sleep(3)
    while not isRinging(ipB):
      sleep(1)
    connect(ipB)
    #while not isConnected(ipB):
    #  sleep(1)
    sleep(3)
    PAYLOAD=(PAYLOAD_A+"Key:Conference"+PAYLOAD_B)
    URL=constructPushURL(ipA)
    sendCurl(PAYLOAD, URL)

 
def constructPushURL(ip):
  """
  Given IP address returns properly constructed push URL
  """ 
  result=URL_A + ip + URL_B
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
 
def sendCurl(PAYLOAD, URL):
  global HEADERS
  global USER
  global PWD
  AUTH=USER+":"+PWD
  curl=['curl', '--digest', '-u', AUTH, '-d', PAYLOAD, '--header', HEADERA , '--header', HEADERB , URL]
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
   
def sendPoll(IP, pollType="callstate"):
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
  payload="http://" + IP + "/polling/"+pollType+"Handler"
  result=requests.get(payload, auth=AUTH)
  while result.status_code!=200:
    if count>5:
      sys.exit()
    log.warn('%s returned from sendPoll; regenerating Authorization'%(result.status_code,))
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

def sendKeyPress(ip, number):
  payload=PAYLOAD_A+constructDialPadString(number)+PAYLOAD_B
  url=constructPushURL(ip)
  sendCurl(payload, url)
  



def test():
  #call('10.17.220.217','5552112')
  #state=sendPoll("10.17.220.219")
  #for  key, value in state.iteritems():
    #print '%s : %s' %(key, value)
  connect('10.17.220.218')
  sleep(1)
  print isConnected('10.17.220.218')
 
  
  


  


if __name__=="__main__":
  test()

