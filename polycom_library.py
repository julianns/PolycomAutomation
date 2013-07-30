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
import requests
import json
from requests.auth import HTTPDigestAuth as digest
from time import sleep
from subprocess import call
import re

#REFERENCE:  PAYLOAD=r"<PolycomIPPhone><Data priority=\"Critical\">tel:\\5552112</Data></PolycomIPPhone>"
#REFERENCE:  URL=r"http://10.17.220.10/push"

#local libraries
#import PolycomStateMachine



#Set globals
USER='Push'
PWD='Push'
AUTH=digest(USER, PWD)
URL_A=r"http://"
URL_B=r"/push"
HEADERS={"Content-Type":"application/x-com-polycom-spipx", "User-Agent":"Voice DVT Automation"}
PAYLOAD_A=r"<PolycomIPPhone><Data priority=\"Critical\">"
PAYLOAD_B=r"</Data></PolycomIPPhone>"

CALL,ATTENDED_XFER,UNATTENDED_XFER,BLIND_XFER,CONF,CONNECT,DISCONNECT=[0,1,2,3,4,5,6]

"""
Keys for VVX400 and VVX500 series:

Line1	    Line21	Line41	        Softkey1	DoNotDisturb
Line2	    Line22	Line42	        Softkey2	Select
Line3	    Line23	Line43	        Softkey3	Conference
Line4	    Line24	Line44	        Softkey4	Transfer
Line5	    Line25	Line45	        Softkey5	Redial
Line6	    Line26	Line46	        VolDown	        Hold
Line7	    Line27	Line47	        VolUp	        Status
Line8	    Line28	Line48	        Headset	        Call List
Line9	    Line29	Dialpad0	Handsfree	 
Line10	    Line30	Dialpad1	MicMute	 
Line11	    Line31	Dialpad2	Menu	 
Line12	    Line32	Dialpad3	Messages	 
Line13	    Line33	Dialpad4	Applications	 
Line14	    Line34	Dialpad5	Directories	 
Line15	    Line35	Dialpad6	Setup	 
Line16	    Line36	Dialpad7	ArrowUp	 
Line17	    Line37	Dialpad8	ArrowDown	 
Line18	    Line38	Dialpad9	ArrowLeft	 
Line19	    Line39	DialPadStar	ArrowRight	 
Line20	    Line40	DialPadPound	Backspace
"""

#Define state machine transistions
"""
POLYCOM DEFINES THEM AS:  
Outgoing call states: Dialtone, Setup, Ringback
Incoming call states: Offering
Outgoing/incoming call states: Connected, CallConference,
CallHold, CallHeld, CallConfHold, CallConfHeld
Line state: Active, Inactive
Shared line states: CallRemoteActive
Call type: Incoming, Outgoing


HOME (DEFAULT)
RINGING
INCOMING
ACTIVE
HOLD
ATTENDEDTRANSFER
BLINDTRANSFER
UNATTENDEDTRANSFER
DISCONNECT
"""

def isHome(ip):
  """
  returns true if phone is on default page (not settings)
  ***STILL NOT REALLY SURE HOW TO DO THIS****
  """


def isRinging(ip):
  """
  Returns True if phone has incoming call, else False
  STATE==?=>INCOMING
  """
  pass

def isActive(ip):
  """
  Returns True if phone has active call, else False
  STATE==?=>ACTIVE
  """
  pass

def go_home(ip):
  """
  Sets phone at IP back to home screen
  STATE==?=>HOME
  """
  pass

#Assumes Softkey1 connects; maybe pass in IP address and request type from phone
def connect():
  """
  IFF isRinging(ip): answers phone
  STATE==INCOMING=>ACTIVE
  """
  return "Key:Handsfree"

def transfer(ip, number):
  """
  IFF isActive(ip): transfer call
  From active call, performs attended transfer to number
  """
  pass

def unattendedTransfer(ip, number):
  """
  IFF isActive(ip): transfer call
  From active call, performs unattended transfer to number
  """
  pass

def blindTransfer(ip, number):
  """
  IFF isActive(ip): transfer call
  From active call, performs blind transfer to number
  """
  pass

def conference(ip, number):
  """
  IFF isActive(ip): conference with number
  From active call, conferences with number
  """
  pass

def disconnect(ip):
  """
  IFF isActive(ip): disconnect
  From active call, disconnect
  """
  pass

def constructPushURL(ip):
  """
  Given an ip address, constructs a properly formatted URL
  """
  return (URL_A + ip + URL_B)

def constructDialPadString(number):
  dialPadString=""
  for n in str(number):
    dialPadString+="Key:Dialpad"+n+"\n"
  return dialPadString
 
#Assumes Softkey3 transfers; maybe pass in IP address and request type from phone
def transfer(method):
  if method=="softkey":
    return "Key:Softkey3"
  elif method=="hardkey":
    return "Key:Transfer"

def getCallState(ip):
  """
  polls phone at ip, returns call state
  """


def constructPAYLOAD(transaction, number=0):
  """
  Given a phone number, constructs the proper payload based on transaction type
  ATTENDED_XFER,UNATTENDED_XFER,BLIND_XFER,CONFERENCE,CONNECT,DISCONNECT
  TODO: VAlidation for when a number is required
  """
  if transaction==CALL:
    #Assumes STATE==HOME
    PAYLOAD= (PAYLOAD_A + "tel:\\" + number + PAYLOAD_B)
  elif transaction==CONNECT:
    #Assumes STATE==INCOMING
    PAYLOAD= (PAYLOAD_A + connect() + PAYLOAD_B)
 
  elif transaction==ATTENDED_XFER:
    #Assumes STATE==ACTIVE
    PAYLOAD= (PAYLOAD_A + transfer('Softkey') + PAYLOAD_B)

  elif transaction==UNATTENDED_XFER:
    #Assumes STATE==ACTIVE
    pass
  elif transaction==BLIND_XFER:
    #Assumes STATE==ACTIVE
    pass
  elif transaction==CONFERENCE:
    #Assumes STATE==ACTIVE
    pass
  elif transaction==DISCONNECT:
    #Assumes STATE==ACTIVE
    pass
    
  return PAYLOAD

def sendCurl(payload, URL):
  return 

def sendRequest(payload, URL):
  
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
  for line in XMLstring:
    m=pattern.match(line)
    if m:
      print m.group(1) + " : " +m.group(2)
      
  

  
 
  #print tree[0][2].text
  #state={}
  #if pollType=="callstate":
  #  state.update({"LineKeyNum": tree[0][0].text,
  #                "LineDirNum": tree[0][1].text,
  #                "LineState": tree[0][2].text})
  #  
  #  if state["LineState"]=="Active":
  #    pass
  #return tree
      
    
  




def main():
  state=sendPoll("10.17.220.218")
  #print state["LineState"]
  #print state["LineDirNum"]

  
    
  #print state["LineState"]
  
  
  


  


if __name__=="__main__":
  main()

