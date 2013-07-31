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

import requests
import json
from requests.auth import HTTPDigestAuth as digest
from time import sleep
from subprocess import call
import re

#Set globals
USER='Push'
PWD='Push'
AUTH=digest(USER, PWD)
URL_A=r"http://"
URL_B=r"/push"
HEADERS={"Content-Type":"application/x-com-polycom-spipx", "User-Agent":"Voice DVT Automation"}
PAYLOAD_A=r"<PolycomIPPhone><Data priority=\"Critical\">"
PAYLOAD_B=r"</Data></PolycomIPPhone>"

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
  """
  pass

def isActive(ip):
  """
  Returns True if line state is Active, else False
  """
  state=sendPoll(ip)
  return["LineState"]=="Active"

def isRingback(ip):
  """
  Returns True if call state is RingBack, else False
  """
  state=sendPoll(ip)
  return["CallState"]=="RingBack"

def isRinging(ip):
  """
  Returns True if phone has incoming call, else False
  """
  state=sendPoll(ip)
  return["CallState"]=="Offering"

def isConnected(ip):
  """
  Returns True if line state is Active, else False
  """
  state=sendPoll(ip)
  return["CallState"]=="Connected"

def call(ip, number):
  """
  IFF LineState?INACTIVE==>DIALTONE->SETUP->RINGBACK
  Given the ip address of the phone from which to call and a number to call
  calls number
  TODO:  Returns -1 if no registered line is inactive or if push message rejected 
  """
  URL=constructURL(ip)
  PAYLOAD=(PAYLOAD_A + "tel:\\" + number + PAYLOAD_B)
  if not isActive(ip):
    result=sendRequest(PAYLOAD, URL)
  else:
    return -1
  
def connect(ip):
  """
  IFF isRinging(ip)?TRUE==>isActive(ip)
  STATE==OFFERING=>ACTIVE
  """
  state=sendPoll(ip)
  if state["CallState"]=="Offering":
    PAYLOAD=(PAYLOAD_A+"Key:Handsfree"+PAYLOAD_B)
    URL=constructURL(ip)
    sendCurl(PAYLOAD, URL)

def disconnect(ip):
  """
  IFF isConnected(ip)?TRUE==>isActive(ip)?FALSE
  STATE==CONNECTED=>INACTIVE
  ???Can we reliably use the HandsFree key if we use it to answer the phone initially???
  """
  state=sendPoll(ip)
  #Lets not test for connected call, rather test the line
  #Active line state covers all call states 
  if state["LineState"]=="Active":
    PAYLOAD=(PAYLOAD_A+"Key:Softkey2"+PAYLOAD_B)
    URL=constructURL(ip)
    sendCurl(PAYLOAD, URL)

def transfer(ipA, number, ipB):
  """
  IFF isActive(ip)?TRUE==>transfer
  From active call, performs attended transfer to number
  """
  state=sendPoll(ip)
  if state["CallState"]=="Active":
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    URL=constructURL(ipA)
    sendCurl(PAYLOAD, URL)
    call(ipA, number)
    while not isRinging(ipB):
      sleep(1)
    connect(ipB)
    while not isConnected(ipB):
      sleep(1)
    disconnect(ipA)
    
def unattendedTransfer(ipA, number, ipB):
  """
  IFF isActive(ip)?TRUE==>transfer
  From active call, performs unattended transfer to number
  """
  state=sendPoll(ip)
  if state["CallState"]=="Active":
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    URL=constructURL(ipA)
    sendCurl(PAYLOAD, URL)
    call(ipA, number)
    while not isRingBack(ip):
      sleep(1)
    disconnect(ipA)
    while not isRinging(ipB):
      sleep(1)
    connect(ipB)
    while not isConnected(ipB):
      sleep(1)

def blindTransfer(ipA, number, ipB):
  """
  IFF isActive(ip)?TRUE==>transfer
  From active call, performs blind transfer to number
  """
  state=sendPoll(ip)
  if state["CallState"]=="Active":
    URL=constructURL(ipA)
    PAYLOAD=(PAYLOAD_A+"Key:Transfer"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
    PAYLOAD=(PAYLOAD_A+"Key:Softkey4"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
    PAYLOAD=(PAYLOAD_A+"Key:Softkey1"+PAYLOAD_B)
    sendCurl(PAYLOAD, URL)
    call(ipA, number)
    disconnect(ipA)
    while not isRinging(ipB):
      sleep(1)
    connect(ipB)
    while not isConnected(ipB):
      sleep(1)


###????TODO????###  I think this should stay separate from the initial call; 
#                   The only downside is I can't check all three phones for conf state
#                   unless I send in the extra ip, but I can get confirmation from two
#                   of the three IP, and they won't give conf without the third
def conference(ipA, number, ipB):
  """
  IFF isActive(ip): conference with number
  From active call, conferences with number
  """
  state=sendPoll(ip)
  if state["CallState"]=="Active":
    PAYLOAD=(PAYLOAD_A+"Key:Conference"+PAYLOAD_B)
    URL=constructURL(ipA)
    sendCurl(PAYLOAD, URL)
    call(ipA, number)
    while not isRinging(ipB):
      sleep(1)
    connect(ipB)
    while not isConnected(ipB):
      sleep(1)
    PAYLOAD=(PAYLOAD_A+"Key:Conference"+PAYLOAD_B)
    URL=constructURL(ipA)
    sendCurl(PAYLOAD, URL)
    

def constructPushURL(ip):
  """
  Given IP address returns properly constructed push URL
  """ 
  return (URL_A + ip + URL_B)

def constructDialPadString(number):
  dialPadString=""
  for n in str(number):
    dialPadString+="Key:Dialpad"+n+"\n"
  return dialPadString
 
def sendCurl(PAYLOAD, URL):
  global HEADERS
  global USER
  global PWD
  AUTH=USER+":"+PWD
  curl=['curl', '--digest', '-u', AUTH, '-d', PAYLOAD, '-H', HEADERS[0], '-H', HEADERS[1], URL]
  return call(curl)

def sendRequest(payload, URL):
  global HEADERS
  global AUTH
  DATA=json.dumps(payload)
  return requests.post(URL, auth=AUTH, verify=False, data=DATA, headers=HEADERS)
   
def sendPoll(IP, pollType="callstate"):
  """
  The handlers Polycom offers are:
  polling/callStateHandler
  polling/deviceHandler
  polling/networkHandler
  """
  global AUTH
  payload="http://" + IP + "/polling/"+pollType+"Handler"
  XMLstring= requests.get(payload, auth=AUTH).text.splitlines()
  pattern=re.compile(r".*<(.*)>(.*)<.*")
  state={}
  for line in XMLstring:
    m=pattern.match(line)
    if m:
      state.append({m.group(1):m.group(2)})
  return state    

def main():
  #from 
  state=sendPoll("10.17.220.218")

  

  
  
  


  


if __name__=="__main__":
  main()

