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

#Include the private libraries implicitly; there are no namespace conflicts
from polycom_library import *
from bulk_call_library import *
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#

#just so I can avoid quotes in all my keys
name="name"
IP="IP"
number="number"
port="port"

#All parameters modified with A, B, or C reference the three possible actors in calling scenarios
A={name:"Maynard Keenan", IP:"10.17.220.217", number:"5551111", port:"0/1"}
B={name:"Roger Daltry", IP:"10.17.220.218", number:"5551112", port:"0/2"}
C={name:"Getty Lee", IP:"10.17.220.219", number:"5552112", port:"0/3"}
D={name:"Freedie Mercury", IP:"10.17.220.220", number:"5552113", port:False}
BULK_CALLER="10.17.220.7"

def verifyTalkPath(A, B, con):
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
    sendKeyPress(A[IP], tones)
    result=con.expect(["0x5000", "0x5001"], 15)
    log.debug("count %f result is %s"%(count,result))
    if result[0]!=0:
      success+=1
    else:
      log.error("Error verifying talk path from %s to %s" %(A[name], B[name])) 
  return "{0:.0%}".format(success/count)


def normal_call(A, B, con):
  """
  places call between A and B,
  verifies talk path in both directions,
  logs results and hangs up
  """
  log=setLogging(__name__)
  log.debug('%s called from %s with %s' %(getFunctionName(), getCallingModuleName(),  getArguments(inspect.currentframe())))
  call(A[IP], B[number])
  log.info('Normal call test initiated between %s and %s' %(A[name], B[name]))
  while not isRinging(B[IP]):
    sleep(1)
  connect(B[IP])
  sleep(2)
  agood=isConnected(A[IP])
  bgood=isConnected(B[IP])
  log.debug("It is %s that A is connected"%agood)
  log.debug("It is %s that B is connected"%bgood)
  if agood and bgood:
    #crank up the headset volumes
    maxVolume(A[IP])
    maxVolume(B[IP])
    log.info('%s connected to %s'% (A[name], B[name]))
  else:
    log.error('error connecting %s to %s'% (A[name], B[name]))
  #seize associated ports and get them into Connected state
  log.info('initiating talk path verification from %s to %s'% (A[name], B[name]))
  successAB=verifyTalkPath(A,B,con)
  log.info('%s success rate from %s to %s in normal call'%(successAB,A[name], B[name]))  
  log.info('initiating talk path verification from %s to %s'% (B[name], A[name]))
  successBA=verifyTalkPath(B,A,con)
  log.info('%s success rate from %s to %s in normal call'%(successBA,B[name], A[name]))
  log.info('Normal call test complete')  
  disconnect(A[IP])
  
def conference_call(A,B,C):
  call(A[IP], B[number])
  while not isRinging(B[IP]):
    sleep(1)
  connect(B[IP])
  sleep(2)
  conference(A[IP], C[number], C[IP])
  sleep(5)
  disconnect(A[IP])
  
def attended_transfer_call(A,B,C):
  call(A[IP], B[number])
  while not isRinging(B[IP]):
    sleep(1)
  connect(B[IP])
  transfer(A[IP], C[number], C[IP])
  sleep(5)
  disconnect(B[IP])
  
 
def unattended_transfer_call(A,B,C):
  call(A[IP], B[number])
  while not isRinging(B[IP]):
    sleep(1)
  connect(B[IP])
  unattendedTransfer(A[IP], C[number], C[IP])
  sleep(5)
  disconnect(B[IP])
  

def blind_transfer_call(A,B,C):
  call(A[IP], B[number])
  while not isRinging(B[IP]):
    sleep(1)
  connect(B[IP])
  blindTransfer(A[IP], C[number], C[IP])
  sleep(5)
  disconnect(B[IP])
  

def setupLogging():
  #setup basic logging configuration for INFO
  logging.basicConfig(level=logging.INFO,
                      format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                      datefmt='%m-%d %H:%M',
                      filename='AutoCallPathVerify.log',
                      filemode='w')
  #set requests logging to WARNING
  requests_log = logging.getLogger("requests")
  requests_log.setLevel(logging.WARNING)
  
  
def initiallize(ip):
  """
  sets up logging and creates connection to bulk caller
  returns telnet connection
  """
  setupLogging()
  con=telnet(ip)
  prompt=login(con)
  return (con)


def test():
  """
  Unit testing of automation script
  """
  con=initiallize(BULK_CALLER)
  #disconnect(A[IP])
  normal_call(A,B,con)
  normal_call(A,C,con)
  normal_call(B,C,con)
  


  
  
  """
  Old unit tests down here
  """
 
  
  

if __name__=="__main__":
  test()