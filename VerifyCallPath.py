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
# Author Jeffrey McAnarney from U.S. 8/15/2013
###############################################################################
#Let's get the time travelling out of the way...
from __future__ import division #to avoid the necessity of float conversion

import logging
import timing

#Include the private library implicitly; there are no namespace conflicts
from DVT_phone_library import *
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#

#just so I can avoid quotes in all my keys
name="name"
IP="IP"
number="number"
port="port"
DEBUG=logging.DEBUG
INFO=logging.INFO

#All parameters modified with A, B, or C reference the three possible actors in calling scenarios
A={name:"Maynard Keenan", IP:"10.17.220.217", number:"5551111", port:"0/1"}
B={name:"Roger Daltry", IP:"10.17.220.218", number:"5551112", port:"0/2"}
C={name:"Getty Lee", IP:"10.17.220.219", number:"5552112", port:"0/3"}
D={name:"Freedie Mercury", IP:"10.17.220.220", number:"5552113", port:False}
BULK_CALLER="10.17.220.7"

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
  call(A,B)
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
  #verifyCallPath(A, B, con, 'attended transfer call')
  attendedTransfer(A, C)
  #verifyCallPath(C, B, con, 'attended transfer call')
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