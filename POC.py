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

from polycom_library import *  #allows me to reference library functions without "name"space


#All parameters modified with A, B, or C reference the three possible actors in calling scenarios

A={"name":"Maynard Keenan", "IP":"10.17.220.217", "number":"5551111"}
B={"name":"Roger Daltry", "IP":"10.17.220.218", "number":"5551112"}
C={"name":"Getty Lee", "IP":"10.17.220.24", "number":"5552112"}

def normal_call(A, B):
  result=call(A["IP"], B["number"])
  while not isRinging(B["IP"]):
    sleep(1)
  connect(B["IP"])
  if isConnected(A["IP"]) and isConnected(B["IP"]):
    print "%s is talking to %s" % (A["name"], B["name"])
  
def conference_call(A,B,C):
  call(ipA, numberB)
  pass
  
def transfer_call(ipA, ipB, numberB, ipC, numberC):
  pass



def main():
  normal_call(A,B)

if __name__=="__main__":
  main()