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
# Author Jeffrey McAnarney from U.S. 7/31/2013
###############################################################################

import logging
#!!!!!IF I WANT TO DO THIS I SHOULD JUST COMBINE ALL LIBRARIES!!!!!!!!!#
from polycom_library import *  #allows me to reference library functions without namespace
from bulk_call_library import *  #allows me to reference library functions without namespace
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

def normal_call(A, B):
  result=call(A[IP], B[number])
  while not isRinging(B[IP]): 
    sleep(1)
  connect(B[IP])
#  connected=isConnected(A[IP]) and isConnected(B[IP])
  sleep(10)
  disconnect(A[IP])
  disconnect(B[IP])
  
def conference_call(A,B,C):
  call(A[IP], B[number])
  while not isRinging(B[IP]):
    sleep(1)
  connect(B[IP])
  sleep(2)
  conference(A[IP], C[number], C[IP])
  sleep(5)
  disconnect(A[IP])
  disconnect(B[IP])
  disconnect(C[IP])
  
def attended_transfer_call(A,B,C):
  call(A[IP], B[number])
  while not isRinging(B[IP]):
    sleep(1)
  connect(B[IP])
  transfer(A[IP], C[number], C[IP])
  sleep(5)
  disconnect(B[IP])
  disconnect(C[IP])
 
def unattended_transfer_call(A,B,C):
  call(A[IP], B[number])
  while not isRinging(B[IP]):
    sleep(1)
  connect(B[IP])
  unattendedTransfer(A[IP], C[number], C[IP])
  sleep(5)
  disconnect(B[IP])
  disconnect(C[IP])

def blind_transfer_call(A,B,C):
  call(A[IP], B[number])
  while not isRinging(B[IP]):
    sleep(1)
  connect(B[IP])
  blindTransfer(A[IP], C[number], C[IP])
  sleep(5)
  disconnect(B[IP])
  disconnect(C[IP])

def setupLogging():
  #setup basic logging configuration
  logging.basicConfig(level=logging.INFO,
                      format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                      datefmt='%m-%d %H:%M',
                      filename='POC.log',
                      filemode='w')
  


def main():
  lg=setupLogging()
  #normal_call(A,C)
  #sleep(5)
  #attended_transfer_call(A,B,C)
  #sleep(5)
  #unattended_transfer_call(A,B,C)  #still have some issues with this
  #sleep(5)
  #blind_transfer_call(A,B,C)
  #sleep(5)
  #conference_call(A,B,C)
  con=connect("10.17.220.7")
  prompt=login(con)
  initializeSIP(con, '0/1')
  initializeSIP(con, '0/3')
  listenForTones(con, '0/3', '60000', '2')
  time.sleep(1)
  tones='12'
  sendKeyPress('10.17.220.217', tones)
  result=con.expect(['0x5000', '0x5001'], 20)
  if str(result[0])==1:
    print 'Success!'
  else:
    print result[2]
  
  

if __name__=="__main__":
  main()