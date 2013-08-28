#!/usr/bin/env python

from DVT_phone_library import *

SIP_A={pType:'IP', name:"Buddy Holly", IP:"10.10.10.101", number:"5551111", port:"0/1"}
SIP_B={pType:'IP', name:"Big Bopper", IP:"10.10.10.102", number:"5551112", port:"0/2"}


initializeTest('10.10.10.16', INFO)
normalCall(SIP_A, SIP_B)

