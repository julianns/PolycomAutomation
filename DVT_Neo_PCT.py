#!/usr/bin/env python
#########################################################################################################################
# This software belongs to Adtran, Inc.
# Author Julian Sy 12/05/2013
#        
#
#  Beautiful is better than ugly
#  Explicit is better than implicit
#  Simple is better than complex
#  Complex is better than complicated
#  Readability counts
#
#  To Run Test: Enter on command line "python DVT_Neo_PCT.py"
#  You adjust the number of times you want to run every test by changing the value of 'run'
#  OR you can replace ;run' in the for loops for each test directly 
#
##########################################################################################################################
from DVT_Neo_PCT_Library import *
#Set globals

#Neo SIP Phone Globals 
SIP_300={pType:IP, name:"LOCAL VVX300", IP:"10.10.10.101", number:"5551111", alias:"1111", port:"0/1", aaKey:"1", }
SIP_310={pType:IP, name:"LOCAL VVX310", IP:"10.10.10.102", number:"5551112", alias:"1112", port:"0/2", aaKey:"2", }
SIP_400={pType:IP, name:"LOCAL VVX400", IP:"10.10.10.103", number:"5551113", alias:"1113", port:"0/3", aaKey:"3", }
SIP_410={pType:IP, name:"LOCAL VVX410", IP:"10.10.10.104", number:"5551114", alias:"1114", port:"0/4", aaKey:"4", }
SIP_500={pType:IP, name:"LOCAL VVX500", IP:"10.10.10.105", number:"5551115", alias:"1115", port:"0/5", aaKey:"5", }
#NV7100 SIP Phone Globals
NV7100_SIP_400={pType:IP, name:"NV7100 VVX400 THROUGH SIP TRUNK", IP:"10.17.235.71:111", number:"5552221", port:"0/0 at BC2", aaKey:"7"}
#FXS Analog Globals
BC_A={pType:BC, name:"LOCAL FXS 0/1", IP:False, number:"5551011", alias:"1011", port:"0/7", aaKey:"7", }
BC_B={pType:BC, name:"LOCAL FXS 0/2", IP:False, number:"5551012", alias:"1012", port:"0/6", aaKey:"6", }
#PRI Analog Globals 
PRI2FXO_A={pType:BC, name:"ATLAS ANALOG THROUGH PRI", IP:False, number:"5581011", port:"0/8", aaKey:"8"}
#FXO Globals
#For calling through FXO to phone outside local network
NEO2FXO_01={pType:BC, name:"ATLAS ANALOG THROUGH NEO FXO 0/1 T10", IP:False, number:"5591011", port:"0/8", aaKey:"1"}
NEO2FXO_02={pType:BC, name:"ATLAS ANALOG THROUGH NEO FXO 0/2 T02", IP:False, number:"5592011", port:"0/8", aaKey:"2"}
NEO2FXO_03={pType:BC, name:"ATLAS ANALOG THROUGH NEO FXO 0/3 T03", IP:False, number:"5593011", port:"0/8", aaKey:"3"}
NEO2FXO_04={pType:BC, name:"ATLAS ANALOG THROUGH NEO FXO 0/4 T04", IP:False, number:"5594011", port:"0/8", aaKey:"4"}
NEO2FXO_05={pType:BC, name:"ATLAS ANALOG THROUGH NEO FXO 0/5 T05", IP:False, number:"5595011", port:"0/8", aaKey:"5"}
NEO2FXO_06={pType:BC, name:"ATLAS ANALOG THROUGH NEO FXO 0/6 T06", IP:False, number:"5596011", port:"0/8", aaKey:"6"}
#For calling through FXO to phone on local network
ATLAS2FXO_01={pType:IP, name:"TRUNK-NUMBER OF NEO FXO 0/1 T10", IP:"10.10.10.101", number:"5561011", port:"0/1", aaKey:"1"} 
ATLAS2FXO_02={pType:IP, name:"TRUNK-NUMBER OF NEO FXO 0/2 T02", IP:"10.10.10.102", number:"5562011", port:"0/2", aaKey:"2"} 
ATLAS2FXO_03={pType:IP, name:"TRUNK-NUMBER OF NEO FXO 0/3 T03", IP:"10.10.10.103", number:"5563011", port:"0/3", aaKey:"3"} 
ATLAS2FXO_04={pType:IP, name:"TRUNK-NUMBER OF NEO FXO 0/4 T04", IP:"10.10.10.104", number:"5564011", port:"0/4", aaKey:"4"} 
ATLAS2FXO_05={pType:IP, name:"TRUNK-NUMBER OF NEO FXO 0/5 T05", IP:"10.10.10.105", number:"5565011", port:"0/5", aaKey:"5"}
ATLAS2FXO_06={pType:BC, name:"NEO ANALOG FXS 0/1 THROUGH NEO FXO 0/6 T06", IP:False, number:"5566011", port:"0/7", aaKey:"6"}

#Auto Attendant Transfer Menu Dictionaries
B_COMPANY_MENU_0={pType:Virtual, name:"COMPANY AUTO-ATTENDANT MAIN MENU", number:"8300", alias:"5558300", pTones:"0#"}

B_COMPANY_SALES_MENU_1={pType:Virtual, name:"COMPANY AUTO-ATTENDANT SALES MENU", number:"8301", aaKey:"1",pTones:"10#"}
B_COMPANY_SALES_PERSON_1={name:"COMPANY AUTO-ATTENDANT SALES PERSON 1", aaKey:"1",phone:SIP_300}
B_COMPANY_SALES_PERSON_2={name:"COMPANY AUTO-ATTENDANT SALES PERSON 2", aaKey:"2",phone:SIP_310}
B_COMPANY_SALES_PERSON_3={name:"COMPANY AUTO-ATTENDANT SALES PERSON 3", aaKey:"3",phone:BC_A}
B_COMPANY_SALES_PROMPT={pType:Virtual, name:"COMPANY AUTO-ATTENDANT SALES PROMPT", aaKey:"4", pTones:"14#"}

B_COMPANY_ACCOUNTING_MENU_2={pType:Virtual, name:"COMPANY AUTO-ATTENDANT ACCOUNTING MENU", number:"8302", aaKey:"2",pTones:"20#"}
B_COMPANY_ACCOUNTING_PERSON_1={name:"COMPANY AUTO-ATTENDANT ACCOUNTING PERSON 1", aaKey:"1",phone:SIP_300}
B_COMPANY_ACCOUNTING_PERSON_2={name:"COMPANY AUTO-ATTENDANT ACCOUNTING PERSON 2", aaKey:"2",phone:SIP_310}
B_COMPANY_ACCOUNTING_PERSON_3={name:"COMPANY AUTO-ATTENDANT ACCOUNTING PERSON 3", aaKey:"3",phone:BC_A}
B_COMPANY_ACCOUNTING_PROMPT={pType:Virtual, name:"COMPANY AUTO-ATTENDANT ACCOUNTING PROMPT", aaKey:"4", pTones:"24#"}

B_COMPANY_MARKETING_MENU_3={pType:Virtual, name:"COMPANY AUTO-ATTENDANT MARKETING MENU", number:"8303",aaKey:"3", pTones:"30#"}
B_COMPANY_MARKETING_PERSON_1={name:"COMPANY AUTO-ATTENDANT MARKETING PERSON 1", aaKey:"1",phone:SIP_300}
B_COMPANY_MARKETING_PERSON_2={name:"COMPANY AUTO-ATTENDANT MARKETING PERSON 2", aaKey:"2",phone:SIP_310}
B_COMPANY_MARKETING_PERSON_3={name:"COMPANY AUTO-ATTENDANT MARKETING PERSON 3", aaKey:"3",phone:BC_A}
B_COMPANY_MARKETING_PROMPT={pType:Virtual, name:"COMPANY AUTO-ATTENDANT MARKETING PROMPT", aaKey:"4", pTones:"34#"}

#Neo Voice Mail Virtual Phone Dictionaries
NEO_VM_MAILBOX={pType:Virtual, name:"NEO VOICEMAIL MAILBOX MENU", number:"8500", pTones:"366#"}
NEO_VM_PASSWORD={pType:Virtual, name:"NEO VOICEMAIL PASSWORD MENU", number:"*98", pTones:"971#"}
NEO_VM_UNAVAILABLE={pType:Virtual, name:"NEO VOICEMAIL LEAVE MESSAGE PROMPT", pTones:"1006#"}
NEO_VM_LEAVE={pType:Virtual, name:"NEO LEAVE VOICEMAIL MENU", number:"8504"}
NEO_VM={mailboxMenu:NEO_VM_MAILBOX, passwordMenu:NEO_VM_PASSWORD, unavailableMenu:NEO_VM_UNAVAILABLE, leaveMenu:NEO_VM_LEAVE}

#Neo Auto Attendant Virtual Phone Dictionaries
NEO_AA_LOGIN={pType:Virtual, name:"NEO AUTO-ATTENDANT MAIN LOG-IN MENU", number:"8200", alias:"5558200",pTones:"00#"}
NEO_AA_LOCAL={pType:Virtual, name:"NEO AUTO-ATTENDANT LOCAL CALLS MENU", number:"8201", pTones:"01#"}
NEO_AA_EXTERNAL={pType:Virtual, name:"NEO AUTO-ATTENDANT EXTERNAL CALLS MENU", number:"8202", pTones:"02#"}
NEO_AA_VM={pType:Virtual, name:"NEO AUTO-ATTENDANT VOICEMAIL MENU", number:"8203", pTones:"03#", vm:NEO_VM}
NEO_AA={loginMenu:NEO_AA_LOGIN, localMenu:NEO_AA_LOCAL, externalMenu:NEO_AA_EXTERNAL, voicemailMenu:NEO_AA_VM,
        transferMainMenu:B_COMPANY_MENU_0, transferSalesMenu:B_COMPANY_SALES_MENU_1,
        transferAccountingMenu:B_COMPANY_ACCOUNTING_MENU_2, transferMarketingMenu:B_COMPANY_MARKETING_MENU_3}

#Neo Ring Group Virtual Phone Dictionaries
NEO_RG_ALL_RING={pType:Virtual, name:"NEO RING GROUP ALL RING", number:"8001",phone1:SIP_400,phone2:SIP_410,phone3:SIP_500}
NEO_RG_LINEAR_HUNT={pType:Virtual, name:"NEO RING GROUP LINEAR HUNT", number:"8002",phone1:SIP_400,phone2:SIP_410,phone3:SIP_500}
NEO_RG_UCD={pType:Virtual, name:"NEO RING GROUP UCD", number:"8003",phone1:SIP_400,phone2:SIP_410,phone3:SIP_500}
NEO_RG_EXEC_RING={pType:Virtual, name:"NEO EXECUTIVE RING", number:"8004",phone1:SIP_410,phone2:SIP_500,phone3:False}

#Neo Call Queue Virtual Phone Dictionaries
NEO_CQ_ALL_RING={pType:Virtual, name:"NEO CALL QUEUING ALL RING", number:"8011",pTones:"11#",phone1:SIP_400,phone2:SIP_410,phone3:SIP_500}
NEO_CQ_LINEAR_HUNT={pType:Virtual, name:"NEO CALL QUEUING LINEAR HUNT", number:"8012",pTones:"12#",phone1:SIP_400,phone2:SIP_410,phone3:SIP_500}
NEO_CQ_MOST_IDLE={pType:Virtual, name:"NEO CALL QUEUING MOST IDLE", number:"8013",pTones:"13#",phone1:SIP_400,phone2:SIP_410,phone3:SIP_500}

#Neo Pickup Group Virtual Phone Dictionaries
NEO_PUG={pType:Virtual, name:"NEO PICK UP GROUP", number:"8031",phone1:SIP_400,phone2:SIP_410}

#Tuples Phones
SIP_LOCAL=[SIP_300,SIP_310,SIP_400,SIP_410,SIP_500]
ANALOG_LOCAL=[BC_A, BC_B]
LOCAL_PHONES=SIP_LOCAL+ANALOG_LOCAL
ATLAS_ANALOG_NUM=[PRI2FXO_A, NEO2FXO_01, NEO2FXO_02, NEO2FXO_03, NEO2FXO_04, NEO2FXO_05, NEO2FXO_06]
NEO_TRUNK_NUM=[ATLAS2FXO_01, ATLAS2FXO_02, ATLAS2FXO_03, ATLAS2FXO_04, ATLAS2FXO_05, ATLAS2FXO_06]

#Ports and addresses
NEO_FXO_TRUNKS={'0/1':'T10','0/2':'T02','0/3':'T03','0/4':'T04','0/5':'T05','0/6':'T06'}
BC_PORTS=['0/0 at BC2','0/1','0/2','0/3','0/4','0/5','0/6','0/7','0/8'] #Tuple of Bulk Callers's ports
ROUTER="10.17.235.254"
BULK_CALLER_IP="10.10.10.16"
BULK_CALLER_2_IP="10.10.10.17"
NEO_IP="10.10.10.254"

#TEST#####################################################################################################################

#Number of runs per test type
runs=1
#Set up logger
setupLogging(INFO)
#Clearing old logfile
open(log_filename, 'w').close()
log.info('\n')
log.info('\n')
log.info("Neo Phone Calls Verification Test")
RESULTS.append("Neo Phone Calls Verification Test")

#Phone Calls Testing
initializeTest(BULK_CALLER_IP, BULK_CALLER_2_IP, NEO_IP, INFO)
passed=True
#~ #Set Trunk Number 
for i in range(6):
	tID='0/'+str(1+i)
	setTrunkNumber(NEO_FXO_TRUNKS[tID],LOCAL_PHONES[i][number])

"""
Tests for Caller Id
"""
RESULTS.append("\nCALLER ID")
for i in range(runs):
	log.info("CALLER ID VERIFICATION######################################################")
	passed = normalCall(SIP_500,SIP_300, True)
	RESULTS.append("  CALLER ID SIP LOCAL CALLER VERIFICATION-----------------------------%s"%(passFailCheck(passed)))
	passed = normalCall(NV7100_SIP_400,SIP_310, True)
	RESULTS.append("  CALLER ID SIP TRUNK CALLER VERIFICATION-----------------------------%s"%(passFailCheck(passed)))
	passed = normalCall(PRI2FXO_A,SIP_400, True)
	RESULTS.append("  CALLER ID T1/PRI CALLER VERIFICATION--------------------------------%s"%(passFailCheck(passed)))
	passed = normalCall(PRI2FXO_A,ATLAS2FXO_04, True)
	RESULTS.append("  CALLER ID FXO VERIFICATION------------------------------------------%s"%(passFailCheck(passed)))
	log.info("CALLER ID VERIFICATION COMPLETE\n")

"""
Tests for Basic Calls
"""
RESULTS.append("BASIC CALLS")
log.info("BASIC CALLS")
for i in range(runs):
	log.info("NORMAL CALL LOCAL SIP-SIP VERIFICATION######################################")
	passedA = normalCall(SIP_300,SIP_310)
	passedB = normalCall(SIP_410,SIP_400)
	passedC = normalCall(SIP_500,SIP_410)
	passed = passedA and passedB and passedC
	RESULTS.append("    NORMAL CALL LOCAL SIP-SIP VERIFICATION----------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("NORMAL CALL LOCAL SIP-ANALOG VERIFICATION###################################")
	passedA = normalCall(SIP_400,BC_A)
	passedB = normalCall(BC_B,SIP_410)
	passed = passedA and passedB
	RESULTS.append("    NORMAL CALL LOCAL SIP-ANALOG VERIFICATION-------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("NORMAL CALL THROUGH SIP TRUNK VERIFICATION##################################")
	passedA = normalCall(SIP_500,NV7100_SIP_400)
	passedB = normalCall(NV7100_SIP_400,SIP_300)
	passed = passedA and passedB
	RESULTS.append("    NORMAL CALL THROUGH SIP TRUNK VERIFICATION------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("NORMAL CALL THROUGH T1/PRI VERIFICATION#####################################")
	passedA = normalCall(SIP_500,PRI2FXO_A)
	passedB = normalCall(PRI2FXO_A,SIP_300)
	passed = passedA and passedB
	RESULTS.append("    NORMAL CALL LOCAL THROUGH T1/PRI VERIFICATION---------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("NORMAL CALL THROUGH FXO 0/1 CALL VERIFICATION###############################")
	passedA = normalCall(SIP_300,NEO2FXO_01)
	passedB = normalCall(PRI2FXO_A,ATLAS2FXO_01)
	passed = passedA and passedB
	RESULTS.append("    NORMAL CALL THROUGH FXO 0/1 CALL VERIFICATION---------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("NORMAL CALL THROUGH FXO 0/2 CALL VERIFICATION###############################")
	passedA = normalCall(SIP_310,NEO2FXO_02)
	passedB = normalCall(PRI2FXO_A,ATLAS2FXO_02)
	passed = passedA and passedB
	RESULTS.append("    NORMAL CALL THROUGH FXO 0/2 CALL VERIFICATION---------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("NORMAL CALL THROUGH FXO 0/3 CALL VERIFICATION###############################")
	passedA = normalCall(SIP_400,NEO2FXO_03)
	passedB = normalCall(PRI2FXO_A,ATLAS2FXO_03)
	passed = passedA and passedB
	RESULTS.append("    NORMAL CALL THROUGH FXO 0/3 CALL VERIFICATION---------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("NORMAL CALL THROUGH FXO 0/4 CALL VERIFICATION###############################")
	passedA = normalCall(SIP_410,NEO2FXO_04)
	passedB = normalCall(PRI2FXO_A,ATLAS2FXO_04)
	passed = passedA and passedB
	RESULTS.append("    NORMAL CALL THROUGH FXO 0/4 CALL VERIFICATION---------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("NORMAL CALL THROUGH FXO 0/5 CALL VERIFICATION###############################")
	passedA = normalCall(SIP_500,NEO2FXO_05)
	passedB = normalCall(PRI2FXO_A,ATLAS2FXO_05)
	passed = passedA and passedB
	RESULTS.append("    NORMAL CALL THROUGH FXO 0/5 CALL VERIFICATION---------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("NORMAL CALL THROUGH FXO 0/6 CALL VERIFICATION###############################")
	passedA = normalCall(BC_A,NEO2FXO_06)
	passedB = normalCall(PRI2FXO_A,ATLAS2FXO_06)
	passed = passedA and passedB
	RESULTS.append("    NORMAL CALL THROUGH FXO 0/6 CALL VERIFICATION---------------------%s"%(passFailCheck(passed)))

"""
Tests for Attended Transfer Calls
"""
RESULTS.append("\nCALL TRANSFERS")
log.info("CALL TRANSFERS")
RESULTS.append("  ATTENDED TRANSFERS")
log.info("  ATTENDED TRANSFERS")
for i in range(runs):
	log.info("ATTENDED CALL TRANSFER LOCAL VERIFICATION###################################")
	passed = attendedTransferCall(SIP_400,SIP_410,SIP_500)
	RESULTS.append("    ATTENDED CALL TRANSFER LOCAL VERIFICATION-------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("ATTENDED CALL TRANSFER SIP TRUNK VERIFICATION###############################")
	passed = attendedTransferCall(SIP_300,NV7100_SIP_400,SIP_400)
	RESULTS.append("    ATTENDED CALL TRANSFER SIP TRUNK VERIFICATION---------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("ATTENDED CALL TRANSFER T1/PRI VERIFICATION##################################")
	passed = attendedTransferCall(SIP_300,PRI2FXO_A,SIP_310)
	RESULTS.append("    ATTENDED CALL TRANSFER T1/PRI VERIFICATION------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("ATTENDED CALL TRANSFER FXO 0/1 VERIFICATION#################################")
	passed = attendedTransferCall(SIP_400,NEO2FXO_01,SIP_410)
	RESULTS.append("    ATTENDED CALL TRANSFER FXO 0/1 CALL VERIFICATION------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("ATTENDED CALL TRANSFER FXO 0/2 VERIFICATION#################################")
	passed = attendedTransferCall(SIP_400,NEO2FXO_02,SIP_410)
	RESULTS.append("    ATTENDED CALL TRANSFER FXO 0/2 CALL VERIFICATION------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("ATTENDED CALL TRANSFER FXO 0/3 VERIFICATION#################################")
	passed = attendedTransferCall(SIP_400,NEO2FXO_03,SIP_410)
	RESULTS.append("    ATTENDED CALL TRANSFER FXO 0/3 CALL VERIFICATION------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("ATTENDED CALL TRANSFER FXO 0/4 VERIFICATION#################################")
	passed = attendedTransferCall(SIP_400,NEO2FXO_04,SIP_410)
	RESULTS.append("    ATTENDED CALL TRANSFER FXO 0/4 CALL VERIFICATION------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("ATTENDED CALL TRANSFER FXO 0/5 VERIFICATION#################################")
	passed = attendedTransferCall(SIP_400,NEO2FXO_05,SIP_410)
	RESULTS.append("    ATTENDED CALL TRANSFER FXO 0/5 CALL VERIFICATION------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("ATTENDED CALL TRANSFER FXO 0/6 VERIFICATION#################################")
	passed = attendedTransferCall(SIP_400,NEO2FXO_06,SIP_410)
	RESULTS.append("    ATTENDED CALL TRANSFER FXO 0/6 CALL VERIFICATION------------------%s"%(passFailCheck(passed)))

"""
Tests for Unattended Transfer Calls
"""
RESULTS.append("  UNATTENDED TRANSFERS")
log.info("  UNATTENDED TRANSFERS")
for i in range(runs):
	log.info("UNATTENDED CALL TRANSFER LOCAL VERIFICATION#################################")
	passed = unattendedTransferCall(SIP_400,SIP_410,SIP_500)
	RESULTS.append("    UNATTENDED CALL TRANSFER LOCAL VERIFICATION-----------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("UNATTENDED CALL TRANSFER SIP TRUNK VERIFICATION#############################")
	passed = unattendedTransferCall(SIP_300,NV7100_SIP_400,SIP_310)
	RESULTS.append("    UNATTENDED CALL TRANSFER SIP TRUNK VERIFICATION-------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("UNATTENDED CALL TRANSFER T1/PRI VERIFICATION################################")
	passed = unattendedTransferCall(SIP_300,PRI2FXO_A,SIP_310)
	RESULTS.append("    UNATTENDED CALL TRANSFER T1/PRI VERIFICATION----------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("UNATTENDED CALL TRANSFER FXO 0/1 VERIFICATION###############################")
	log.info("SKIPPED(AOS-11557)\n")
	#~ passed = unattendedTransferCall(SIP_400,NEO2FXO_01,SIP_410)
	RESULTS.append("    UNATTENDED CALL TRANSFER FXO 0/1 CALL VERIFICATION----------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("UNATTENDED CALL TRANSFER FXO 0/2 VERIFICATION###############################")
	log.info("SKIPPED(AOS-11557)\n")
	#~ passed = unattendedTransferCall(SIP_400,NEO2FXO_02,SIP_410)
	RESULTS.append("    UNATTENDED CALL TRANSFER FXO 0/2 CALL VERIFICATION----------------%sAOS-11557"%(passFailCheck(False)))
for i in range(runs):
	log.info("UNATTENDED CALL TRANSFER FXO 0/3 VERIFICATION###############################")
	log.info("SKIPPED(AOS-11557)\n")
	#~ passed = unattendedTransferCall(SIP_400,NEO2FXO_03,SIP_410)
	RESULTS.append("    UNATTENDED CALL TRANSFER FXO 0/3 CALL VERIFICATION----------------%sAOS-11557"%(passFailCheck(False)))
for i in range(runs):
	log.info("UNATTENDED CALL TRANSFER FXO 0/4 VERIFICATION###############################")
	log.info("SKIPPED(AOS-11557)\n")
	#~ passed = unattendedTransferCall(SIP_400,NEO2FXO_04,SIP_410)
	RESULTS.append("    UNATTENDED CALL TRANSFER FXO 0/4 CALL VERIFICATION----------------%sAOS-11557"%(passFailCheck(False)))
for i in range(runs):
	log.info("UNATTENDED CALL TRANSFER FXO 0/5 VERIFICATION###############################")
	log.info("SKIPPED(AOS-11557)\n")
	#~ passed = unattendedTransferCall(SIP_400,NEO2FXO_05,SIP_410)
	RESULTS.append("    UNATTENDED CALL TRANSFER FXO 0/5 CALL VERIFICATION----------------%sAOS-11557"%(passFailCheck(False)))
for i in range(runs):
	log.info("UNATTENDED CALL TRANSFER FXO 0/6 VERIFICATION###############################")
	log.info("SKIPPED(AOS-11557)\n")
	#~ passed = unattendedTransferCall(SIP_400,NEO2FXO_06,SIP_410)
	RESULTS.append("    UNATTENDED CALL TRANSFER FXO 0/6 CALL VERIFICATION----------------%sAOS-11557"%(passFailCheck(False)))

"""
Tests for Blind Transfer Calls
"""
RESULTS.append("  BLIND TRANSFERS")
log.info("  BLIND TRANSFERS")
for i in range(runs):
	log.info("BLIND CALL TRANSFER LOCAL VERIFICATION######################################")
	passed = blindTransferCall(SIP_400,SIP_410,SIP_500)
	RESULTS.append("    BLIND CALL TRANSFER LOCAL VERIFICATION----------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("BLIND CALL TRANSFER SIP TRUNK VERIFICATION##################################")
	passed = blindTransferCall(SIP_300,NV7100_SIP_400,SIP_310)
	RESULTS.append("    BLIND CALL TRANSFER SIP TRUNK VERIFICATION------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("BLIND CALL TRANSFER T1/PRI VERIFICATION#####################################")
	passed = blindTransferCall(SIP_300,PRI2FXO_A,SIP_310)
	#~ RESULTS.append("    BLIND CALL TRANSFER T1/PRI VERIFICATION---------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("BLIND CALL TRANSFER FXO 0/1 VERIFICATION####################################")
	#~ passed = blindTransferCall(SIP_400,NEO2FXO_01,SIP_410)
	RESULTS.append("    BLIND CALL TRANSFER FXO 0/1 CALL VERIFICATION---------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("BLIND CALL TRANSFER FXO 0/2 VERIFICATION####################################")
	log.info("SKIPPED(AOS-11557)\n")
	#~ passed = blindTransferCall(SIP_400,NEO2FXO_02,SIP_410)
	RESULTS.append("    BLIND CALL TRANSFER FXO 0/2 CALL VERIFICATION---------------------%sAOS-11557"%(passFailCheck(False)))
for i in range(runs):
	log.info("BLIND CALL TRANSFER FXO 0/3 VERIFICATION####################################")
	log.info("SKIPPED(AOS-11557)\n")
	#~ passed = blindTransferCall(SIP_400,NEO2FXO_03,SIP_410)
	RESULTS.append("    BLIND CALL TRANSFER FXO 0/3 CALL VERIFICATION---------------------%sAOS-11557"%(passFailCheck(False)))
for i in range(runs):
	log.info("BLIND CALL TRANSFER FXO 0/4 VERIFICATION####################################")
	log.info("SKIPPED(AOS-11557)\n")
	#~ passed = blindTransferCall(SIP_400,NEO2FXO_04,SIP_410)
	RESULTS.append("    BLIND CALL TRANSFER FXO 0/4 CALL VERIFICATION---------------------%sAOS-11557"%(passFailCheck(False)))
for i in range(runs):
	log.info("BLIND CALL TRANSFER FXO 0/5 VERIFICATION####################################")
	log.info("SKIPPED(AOS-11557)\n")
	#~ passed = blindTransferCall(SIP_400,NEO2FXO_05,SIP_410)
	RESULTS.append("    BLIND CALL TRANSFER FXO 0/5 CALL VERIFICATION---------------------%sAOS-11557"%(passFailCheck(False)))
for i in range(runs):
	log.info("BLIND CALL TRANSFER FXO 0/6 VERIFICATION####################################")
	log.info("SKIPPED(AOS-11557)\n")
	#~ passed = blindTransferCall(SIP_400,NEO2FXO_06,SIP_410)
	RESULTS.append("    BLIND CALL TRANSFER FXO 0/6 CALL VERIFICATION---------------------%sAOS-11557"%(passFailCheck(False)))

"""
Tests for Conference Calls
"""
RESULTS.append("\nCONFERENCE CALLS")
log.info("CONFERENCE CALLS")
for i in range(runs):
	log.info("CONFERENCE CALL LOCAL VERIFICATION##########################################")
	log.info("SKIPPED\n")
	#~ passed = conferenceCall(SIP_300,SIP_310,SIP_500)
	RESULTS.append("    CONFERENCE CALL LOCAL VERIFICATION--------------------------------%s"%(passFailCheck(False)))
for i in range(runs):
	log.info("CONFERENCE CALL SIP TRUNK VERIFICATION######################################")
	log.info("SKIPPED\n")
	#~ passed = conferenceCall(SIP_400,NV7100_SIP_400,SIP_410)
	RESULTS.append("    CONFERENCE CALL SIP TRUNK VERIFICATION----------------------------%s"%(passFailCheck(False)))
for i in range(runs):
	log.info("CONFERENCE CALL T1/PRI VERIFICATION#########################################")
	log.info("SKIPPED\n")
	#~ passed = conferenceCall(SIP_500,PRI2FXO_A,SIP_300)
	RESULTS.append("    CONFERENCE CALL T1/PRI VERIFICATION-------------------------------%s"%(passFailCheck(False)))
for i in range(runs):
	log.info("CONFERENCE CALL FXO 0/1 VERIFICATION########################################")
	log.info("SKIPPED\n")
	#~ passed = conferenceCall(SIP_400,NEO2FXO_01,SIP_410)
	RESULTS.append("    CONFERENCE CALL FXO 0/1 VERIFICATION------------------------------%s"%(passFailCheck(False)))
for i in range(runs):
	log.info("CONFERENCE CALL FXO 0/2 VERIFICATION########################################")
	log.info("SKIPPED\n")
	#~ passed = conferenceCall(SIP_300,NEO2FXO_02,SIP_500)
	RESULTS.append("    CONFERENCE CALL FXO 0/2 VERIFICATION------------------------------%s"%(passFailCheck(False)))
for i in range(runs):
	log.info("CONFERENCE CALL FXO 0/3 VERIFICATION########################################")
	log.info("SKIPPED\n")
	#~ passed = conferenceCall(SIP_400,NEO2FXO_03,SIP_310)
	RESULTS.append("    CONFERENCE CALL FXO 0/3 VERIFICATION------------------------------%s"%(passFailCheck(False)))
for i in range(runs):
	log.info("CONFERENCE CALL FXO 0/4 VERIFICATION########################################")
	log.info("SKIPPED\n")
	#~ passed = conferenceCall(SIP_300,NEO2FXO_04,SIP_410)
	RESULTS.append("    CONFERENCE CALL FXO 0/4 VERIFICATION------------------------------%s"%(passFailCheck(False)))
for i in range(runs):
	log.info("CONFERENCE CALL FXO 0/5 VERIFICATION#######################################")
	log.info("SKIPPED\n")
	#~ passed = conferenceCall(SIP_500,NEO2FXO_05,SIP_310)
	RESULTS.append("    CONFERENCE CALL FXO 0/5 VERIFICATION------------------------------%s"%(passFailCheck(False)))
for i in range(runs):
	log.info("CONFERENCE CALL FXO 0/6 VERIFICATION########################################")
	#~ passed = conferenceCall(SIP_300,NEO2FXO_06,SIP_400)
	RESULTS.append("    CONFERENCE CALL FXO 0/6 VERIFICATION------------------------------%s"%(passFailCheck(False)))

for i in range(6):
	tID='0/'+str(1+i)
	setTrunkNumber(NEO_FXO_TRUNKS[tID],NEO_VM_MAILBOX[number])

"""
Tests for Voicemail Calls
"""
RESULTS.append("\nVOICEMAIL")
log.info("VOICEMAIL")
RESULTS.append("  LOCAL SIP VOICEMAIL")
log.info("  LOCAL SIP VOICEMAIL")
for i in range(runs):
	log.info("VOICEMAIL LOCAL SIP MESSAGES BUTTON VERIFICATION############################")
	passed = voicemailCall(NEO_VM,SIP_300,VMAIL_MSG_BUTTON)
	RESULTS.append("    VOICEMAIL LOCAL SIP MESSAGES BUTTON VERIFICATION------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("VOICEMAIL LOCAL SIP *98 VERIFICATION########################################")
	passed = voicemailCall(NEO_VM,SIP_300,VMAIL_STAR98)
	RESULTS.append("    VOICEMAIL LOCAL SIP *98 VERIFICATION------------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("VOICEMAIL LOCAL SIP DIRECT EXTENSION VERIFICATION###########################")
	passed = voicemailCall(NEO_VM,SIP_300,VMAIL_DIR_EXT,SIP_300)
	RESULTS.append("    VOICEMAIL LOCAL SIP DIRECT EXTENSION VERIFICATION-----------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("VOICEMAIL LOCAL SIP 8500 EXTENSION BUTTON VERIFICATION######################")
	passed = voicemailCall(NEO_VM,SIP_300,VMAIL_LOGIN_EXT)
	RESULTS.append("    VOICEMAIL LOCAL SIP 8500 EXTENSION VERIFICATION-------------------%s"%(passFailCheck(passed)))
RESULTS.append("  LOCAL FXS VOICEMAIL")
log.info("  LOCAL FXS VOICEMAIL")
for i in range(runs):
	log.info("VOICEMAIL LOCAL FXS DIRECT EXTENSION VERIFICATION###########################")
	passed = voicemailCall(NEO_VM,BC_A,VMAIL_DIR_EXT,BC_A)
	RESULTS.append("    VOICEMAIL LOCAL FXS DIRECT EXTENSION VERIFICATION-----------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("VOICEMAIL LOCAL FXS 8500 EXTENSION BUTTON VERIFICATION######################")
	passed = voicemailCall(NEO_VM,BC_A,VMAIL_LOGIN_EXT)
	RESULTS.append("    VOICEMAIL LOCAL FXS 8500 EXTENSION VERIFICATION-------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("VOICEMAIL LOCAL FXS *98 VERIFICATION########################################")
	passed = voicemailCall(NEO_VM,BC_A,VMAIL_STAR98)
	RESULTS.append("    VOICEMAIL LOCAL FXS *98 BUTTON VERIFICATION-----------------------%s"%(passFailCheck(passed)))
RESULTS.append("  FXO VOICEMAIL")
log.info("  FXO VOICEMAIL")
for i in range(runs):
	log.info("VOICEMAIL FXO DIRECT EXTENSION VERIFICATION#################################")
	passed = voicemailCall(NEO_VM,PRI2FXO_A,VMAIL_DIR_EXT,ATLAS2FXO_01)
	RESULTS.append("    VOICEMAIL FXO DIRECT EXTENSION VERIFICATION-----------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("VOICEMAIL SIP TRUNK 8500 EXTENSION VERIFICATION#############################")
	log.info("SKIPPED(AOS-13417)\n")
	RESULTS.append("    VOICEMAIL SIP TRUNK 8500 EXTENSION VERIFICATION-------------------%sAOS-13417"%(passFailCheck(False)))
RESULTS.append("  T1/PRI VOICEMAIL")
log.info("  T1/PRI VOICEMAIL")
for i in range(runs):
	log.info("VOICEMAIL LOCAL T1/PRI DIRECT EXTENSION VERIFICATION########################")
	passed = voicemailCall(NEO_VM,PRI2FXO_A,VMAIL_DIR_EXT,SIP_300)
	RESULTS.append("    VOICEMAIL T1/PRI DIRECT EXTENSION VERIFICATION--------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("VOICEMAIL T1/PRI TRUNK 8500 EXTENSION VERIFICATION##########################")
	passed = voicemailCall(NEO_VM,PRI2FXO_A,VMAIL_DIR_EXT,SIP_300)
	RESULTS.append("    VOICEMAIL T1/PRI 8500 EXTENSION VERIFICATION----------------------%sAOS-13417"%(passFailCheck(False)))
RESULTS.append("  SIP TRUNK VOICEMAIL")
log.info("  SIP TRUNK VOICEMAIL")
for i in range(runs):
	log.info("VOICEMAIL SIP TRUNK DIRECT EXTENSION VERIFICATION###########################")
	passed = voicemailCall(NEO_VM,NV7100_SIP_400,VMAIL_DIR_EXT,SIP_300)
	RESULTS.append("    VOICEMAIL SIP TRUNK DIRECT EXTENSION VERIFICATION-----------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("VOICEMAIL SIP TRUNK 8500 EXTENSION VERIFICATION#############################")
	log.info("SKIPPED(AOS-13417)\n")
	RESULTS.append("    VOICEMAIL SIP TRUNK 8500 EXTENSION VERIFICATION-------------------%sAOS-13417"%(passFailCheck(False)))

#Needed for FXO AA Tests 
for i in range(6):
	tID='0/'+str(1+i)
	setTrunkNumber(NEO_FXO_TRUNKS[tID],NEO_AA_LOGIN[number])

"""
Tests for Auto Attendant Calls
"""
RESULTS.append("\nAUTO ATTENDANT")
log.info("AUTO ATTENDANT")
RESULTS.append("  AA DIAL BY EXT CALL")
log.info("  AA DIAL BY EXT CALL")
for i in range(runs):
	log.info("AA DIAL BY EXT CALL LOCAL SIP VERIFICATION##################################")
	passed = autoAttendantCall(NEO_AA,SIP_300,SIP_310,AA_DIAL)
	RESULTS.append("    AA DIAL BY EXT CALL LOCAL SIP VERIFICATION------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA DIAL BY EXT CALL LOCAL FXS 0/1 VERIFICATION##############################")
	passedA=autoAttendantCall(NEO_AA,SIP_300,BC_A,AA_DIAL)
	passedB=autoAttendantCall(NEO_AA,BC_A,SIP_310,AA_DIAL)
	passed=passedA and passedB
	RESULTS.append("    AA DIAL BY EXT CALL LOCAL FXS 0/1 VERIFICATION--------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA DIAL BY EXT CALL LOCAL FXS 0/2 VERIFICATION##############################")
	passedA=autoAttendantCall(NEO_AA,SIP_300,BC_B,AA_DIAL)
	passedB=autoAttendantCall(NEO_AA,BC_B,SIP_310,AA_DIAL)
	passed=passedA and passedB
	RESULTS.append("    AA DIAL BY EXT CALL LOCAL FXS 0/2 VERIFICATION--------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA DIAL BY EXT CALL T1/PRI VERIFICATION#####################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,SIP_310,AA_DIAL)
	RESULTS.append("    AA DIAL BY EXT CALL T1/PRI VERIFICATION---------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA DIAL BY EXT CALL FXO 0/1 VERIFICATION####################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_01,AA_DIAL, SIP_300)
	RESULTS.append("    AA DIAL BY EXT CALL FXO 0/1 VERIFICATION--------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA DIAL BY EXT CALL FXO 0/2 VERIFICATION####################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_02,AA_DIAL, SIP_300)
	RESULTS.append("    AA DIAL BY EXT CALL FXO 0/2 VERIFICATION--------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA DIAL BY EXT CALL FXO 0/3 VERIFICATION####################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_03,AA_DIAL, SIP_300)
	RESULTS.append("    AA DIAL BY EXT CALL FXO 0/3 VERIFICATION--------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA DIAL BY EXT CALL FXO 0/4 VERIFICATION####################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_04,AA_DIAL, SIP_300)
	RESULTS.append("    AA DIAL BY EXT CALL FXO 0/4 VERIFICATION--------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA DIAL BY EXT CALL FXO 0/5 VERIFICATION####################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_05,AA_DIAL, SIP_300)
	RESULTS.append("    AA DIAL BY EXT CALL FXO 0/5 VERIFICATION--------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA DIAL BY EXT CALL FXO 0/6 VERIFICATION####################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_06,AA_DIAL, SIP_300)
	RESULTS.append("    AA DIAL BY EXT CALL FXO 0/6 VERIFICATION--------------------------%s"%(passFailCheck(passed)))

RESULTS.append("  AA TRANSFER CALL")
log.info("  AA TRANSFER CALL")
for i in range(runs):
	log.info("AA TRANSFER CALL LOCAL SIP VERIFICATION#####################################")
	passed = autoAttendantCall(NEO_AA,SIP_300,SIP_310,AA_TRANSFER)
	RESULTS.append("    AA TRANSFER CALL LOCAL SIP VERIFICATION---------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA TRANSFER CALL LOCAL FXS 0/1 VERIFICATION#################################")
	passed=autoAttendantCall(NEO_AA,BC_A,SIP_310,AA_TRANSFER)
	RESULTS.append("    AA TRANSFER CALL LOCAL FXS 0/1 VERIFICATION-----------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA TRANSFER CALL LOCAL FXS 0/2 VERIFICATION#################################")
	passed=autoAttendantCall(NEO_AA,BC_B,SIP_310,AA_TRANSFER)
	RESULTS.append("    AA TRANSFER CALL LOCAL FXS 0/2 VERIFICATION-----------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA TRANSFER CALL T1/PRI VERIFICATION########################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,SIP_310,AA_TRANSFER)
	RESULTS.append("    AA TRANSFER CALL T1/PRI VERIFICATION------------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA TRANSFER CALL FXO 0/1 VERIFICATION#######################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_01,AA_TRANSFER,SIP_300)
	RESULTS.append("    AA TRANSFER CALL FXO 0/1 VERIFICATION-----------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA TRANSFER CALL FXO 0/2 VERIFICATION#######################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_02,AA_TRANSFER,SIP_300)
	RESULTS.append("    AA TRANSFER CALL FXO 0/2 VERIFICATION-----------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA TRANSFER CALL FXO 0/3 VERIFICATION#######################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_03,AA_TRANSFER,SIP_300)
	RESULTS.append("    AA TRANSFER CALL FXO 0/3 VERIFICATION-----------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA TRANSFER CALL FXO 0/4 VERIFICATION#######################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_04,AA_TRANSFER,SIP_300)
	RESULTS.append("    AA TRANSFER CALL FXO 0/4 VERIFICATION-----------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA TRANSFER CALL FXO 0/5 VERIFICATION#######################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_05,AA_TRANSFER,SIP_300)
	RESULTS.append("    AA TRANSFER CALL FXO 0/5 VERIFICATION-----------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA TRANSFER CALL FXO 0/6 VERIFICATION#######################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_06,AA_TRANSFER,SIP_300)
	RESULTS.append("    AA TRANSFER CALL FXO 0/6 VERIFICATION-----------------------------%s"%(passFailCheck(passed)))

RESULTS.append("  AA VOICEMAIL CALL")
log.info("  AA VOICEMAIL CALL")
for i in range(runs):
	log.info("AA VOICEMAIL CALL LOCAL SIP VERIFICATION####################################")
	passed = autoAttendantCall(NEO_AA,SIP_300,SIP_310,AA_VM)
	RESULTS.append("    AA VOICEMAIL CALL LOCAL SIP VERIFICATION--------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA VOICEMAIL CALL LOCAL FXS 0/1 VERIFICATION################################")
	passed=autoAttendantCall(NEO_AA,BC_A,SIP_310,AA_VM)
	RESULTS.append("    AA VOICEMAIL CALL LOCAL FXS 0/1 VERIFICATION----------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA VOICEMAIL CALL LOCAL FXS 0/2 VERIFICATION################################")
	passed=autoAttendantCall(NEO_AA,BC_B,SIP_310,AA_VM)
	RESULTS.append("    AA VOICEMAIL CALL LOCAL FXS 0/2 VERIFICATION----------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA VOICEMAIL CALL T1/PRI VERIFICATION#######################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,SIP_310,AA_VM)
	RESULTS.append("    AA VOICEMAIL CALL T1/PRI VERIFICATION-----------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA VOICEMAIL CALL FXO 0/1 VERIFICATION######################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_01,AA_VM,SIP_300)
	RESULTS.append("    AA VOICEMAIL CALL FXO 0/1 VERIFICATION----------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA VOICEMAIL CALL FXO 0/2 VERIFICATION######################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_02,AA_VM,SIP_300)
	RESULTS.append("    AA VOICEMAIL CALL FXO 0/2 VERIFICATION----------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA VOICEMAIL CALL FXO 0/3 VERIFICATION######################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_03,AA_VM,SIP_300)
	RESULTS.append("    AA VOICEMAIL CALL FXO 0/3 VERIFICATION----------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA VOICEMAIL CALL FXO 0/4 VERIFICATION######################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_04,AA_VM,SIP_300)
	RESULTS.append("    AA VOICEMAIL CALL FXO 0/4 VERIFICATION----------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA VOICEMAIL CALL FXO 0/5 VERIFICATION######################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_05,AA_VM,SIP_300)
	RESULTS.append("    AA VOICEMAIL CALL FXO 0/5 VERIFICATION----------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA VOICEMAIL CALL FXO 0/6 VERIFICATION######################################")
	passed=autoAttendantCall(NEO_AA,PRI2FXO_A,ATLAS2FXO_06,AA_VM,SIP_300)
	RESULTS.append("    AA VOICEMAIL CALL FXO 0/6 VERIFICATION----------------------------%s"%(passFailCheck(passed)))

for i in range(6):
	tID='0/'+str(1+i)
	setTrunkNumber(NEO_FXO_TRUNKS[tID],B_COMPANY_MENU_0[number])

RESULTS.append("  AA MENU TRANSFER AUTO ATTENDANT")
log.info("  AA MENU TRANSFER AUTO ATTENDANT")
for i in range(runs):
	log.info("AA MENU TRANSFER AUTO ATTENDANT LOCAL SIP VERIFICATION######################")
	passedA=autoAttendantCall(NEO_AA,SIP_410,B_COMPANY_ACCOUNTING_PROMPT, AA_TRANSFER_MENU_PROMPT)
	passedB=autoAttendantCall(NEO_AA,SIP_410,B_COMPANY_ACCOUNTING_PERSON_1, AA_TRANSFER_MENU_CALL)
	passed=passedA and passedB
	RESULTS.append("    AA MENU TRANSFER AUTO ATTENDANT LOCAL SIP VERIFICATION------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA MENU TRANSFER AUTO ATTENDANT LOCAL FXS 0/1 VERIFICATION##################")
	passedA=autoAttendantCall(NEO_AA,BC_A,B_COMPANY_SALES_PROMPT, AA_TRANSFER_MENU_PROMPT)
	passedB=autoAttendantCall(NEO_AA,BC_A,B_COMPANY_SALES_PERSON_2, AA_TRANSFER_MENU_CALL)
	passed=passedA and passedB
	RESULTS.append("    AA MENU TRANSFER AUTO ATTENDANT LOCAL  FXS 0/1 VERIFICATION-------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA MENU TRANSFER AUTO ATTENDANT LOCAL FXS 0/2 VERIFICATION##################")
	passedA=autoAttendantCall(NEO_AA,BC_B,B_COMPANY_SALES_PROMPT, AA_TRANSFER_MENU_PROMPT)
	passedB=autoAttendantCall(NEO_AA,BC_B,B_COMPANY_SALES_PERSON_3, AA_TRANSFER_MENU_CALL)
	passed=passedA and passedB
	RESULTS.append("    AA MENU TRANSFER AUTO ATTENDANT LOCAL  FXS 0/2 VERIFICATION-------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA MENU TRANSFER AUTO ATTENDANT SIP TRUNK VERIFICATION######################")
	passedA=autoAttendantCall(NEO_AA,NV7100_SIP_400,B_COMPANY_ACCOUNTING_PROMPT, AA_TRANSFER_MENU_PROMPT)
	passedB=autoAttendantCall(NEO_AA,NV7100_SIP_400,B_COMPANY_ACCOUNTING_PERSON_1, AA_TRANSFER_MENU_CALL)
	passed=passedA and passedB
	RESULTS.append("    AA MENU TRANSFER AUTO ATTENDANT SIP TRUNK VERIFICATION------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA MENU TRANSFER AUTO ATTENDANT FXO 0/1 VERIFICATION########################")
	passedA=autoAttendantCall(NEO_AA,NEO2FXO_01,ATLAS2FXO_01, AA_TRANSFER_MENU_PROMPT,B_COMPANY_MARKETING_PROMPT, True)
	passedB=autoAttendantCall(NEO_AA,NEO2FXO_01,ATLAS2FXO_01, AA_TRANSFER_MENU_CALL,B_COMPANY_MARKETING_PERSON_2, True)
	passed=passedA and passedB
	RESULTS.append("    AA MENU TRANSFER AUTO ATTENDANT FXO 0/1 VERIFICATION--------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA MENU TRANSFER AUTO ATTENDANT FXO 0/2 VERIFICATION########################")
	passedA=autoAttendantCall(NEO_AA,NEO2FXO_02,ATLAS2FXO_02, AA_TRANSFER_MENU_PROMPT,B_COMPANY_MARKETING_PROMPT, True)
	passedB=autoAttendantCall(NEO_AA,NEO2FXO_02,ATLAS2FXO_02, AA_TRANSFER_MENU_CALL,B_COMPANY_MARKETING_PERSON_2, True)
	passed=passedA and passedB
	RESULTS.append("    AA MENU TRANSFER AUTO ATTENDANT FXO 0/2 VERIFICATION--------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA MENU TRANSFER AUTO ATTENDANT FXO 0/3 VERIFICATION########################")
	passedA=autoAttendantCall(NEO_AA,NEO2FXO_03,ATLAS2FXO_03, AA_TRANSFER_MENU_PROMPT,B_COMPANY_MARKETING_PROMPT, True)
	passedB=autoAttendantCall(NEO_AA,NEO2FXO_03,ATLAS2FXO_03, AA_TRANSFER_MENU_CALL,B_COMPANY_MARKETING_PERSON_2, True)
	passed=passedA and passedB
	RESULTS.append("    AA MENU TRANSFER AUTO ATTENDANT FXO 0/3 VERIFICATION--------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA MENU TRANSFER AUTO ATTENDANT FXO 0/4 VERIFICATION########################")
	passedA=autoAttendantCall(NEO_AA,NEO2FXO_04,ATLAS2FXO_04, AA_TRANSFER_MENU_PROMPT,B_COMPANY_MARKETING_PROMPT, True)
	passedB=autoAttendantCall(NEO_AA,NEO2FXO_04,ATLAS2FXO_04, AA_TRANSFER_MENU_CALL,B_COMPANY_MARKETING_PERSON_2, True)
	passed=passedA and passedB
	RESULTS.append("    AA MENU TRANSFER AUTO ATTENDANT FXO 0/4 VERIFICATION--------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA MENU TRANSFER AUTO ATTENDANT FXO 0/5 VERIFICATION########################")
	passedA=autoAttendantCall(NEO_AA,NEO2FXO_05,ATLAS2FXO_05, AA_TRANSFER_MENU_PROMPT,B_COMPANY_MARKETING_PROMPT, True)
	passedB=autoAttendantCall(NEO_AA,NEO2FXO_05,ATLAS2FXO_05, AA_TRANSFER_MENU_CALL,B_COMPANY_MARKETING_PERSON_2, True)
	passed=passedA and passedB
	RESULTS.append("    AA MENU TRANSFER AUTO ATTENDANT FXO 0/5 VERIFICATION--------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("AA MENU TRANSFER AUTO ATTENDANT FXO 0/6 VERIFICATION########################")
	passedA=autoAttendantCall(NEO_AA,NEO2FXO_06,ATLAS2FXO_06, AA_TRANSFER_MENU_PROMPT,B_COMPANY_MARKETING_PROMPT, True)
	passedB=autoAttendantCall(NEO_AA,NEO2FXO_06,ATLAS2FXO_06, AA_TRANSFER_MENU_CALL,B_COMPANY_MARKETING_PERSON_2, True)
	passed=passedA and passedB
	RESULTS.append("    AA MENU TRANSFER AUTO ATTENDANT FXO 0/6 VERIFICATION--------------%s"%(passFailCheck(passed)))

"""
Tests for Ring Group Calls
"""
RESULTS.append("\nRING GROUP")
log.info("RING GROUP")
RESULTS.append("  ALL RING")
log.info("  ALL RING")
for i in range(runs):
	log.info("RING GROUP ALL RING LOCAL SIP VERIFICATION##################################")
	passed=ringGroupCall(SIP_300,NEO_RG_ALL_RING,RG_ALL_RING)
	RESULTS.append("    RING GROUP ALL RING LOCAL SIP VERIFICATION------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("RING GROUP ALL RING LOCAL FXS 0/1 VERIFICATION##############################")
	passed=ringGroupCall(BC_A,NEO_RG_ALL_RING,RG_ALL_RING)
	RESULTS.append("    RING GROUP ALL RING LOCAL FXS 0/1 VERIFICATION--------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("RING GROUP ALL RING SIP TRUNK VERIFICATION##################################")
	passed=ringGroupCall(NV7100_SIP_400,NEO_RG_ALL_RING,RG_ALL_RING)
	RESULTS.append("    RING GROUP ALL RING SIP TRUNK VERIFICATION------------------------%s"%(passFailCheck(passed))) 
for i in range(runs):
	log.info("RING GROUP ALL RING T1/PRI VERIFICATION#####################################")
	passed=ringGroupCall(PRI2FXO_A,NEO_RG_ALL_RING,RG_ALL_RING)
	RESULTS.append("    RING GROUP ALL RING T1/PRI VERIFICATION---------------------------%s"%(passFailCheck(passed)))

RESULTS.append("  LINEAR HUNT")
log.info("  LINEAR HUNT")
for i in range(runs):
	log.info("RING GROUP LINEAR HUNT LOCAL SIP VERIFICATION###############################")
	passed=ringGroupCall(SIP_300,NEO_RG_LINEAR_HUNT,RG_LINEAR_HUNT)
	RESULTS.append("    RING GROUP LINEAR HUNT LOCAL SIP VERIFICATION---------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("RING GROUP LINEAR HUNT LOCAL FXS 0/1 VERIFICATION###########################")
	passed=ringGroupCall(BC_A,NEO_RG_LINEAR_HUNT,RG_LINEAR_HUNT)
	RESULTS.append("    RING GROUP LINEAR HUNT LOCAL FXS 0/1 VERIFICATION-----------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("RING GROUP LINEAR HUNT SIP TRUNK VERIFICATION###############################")
	passed=ringGroupCall(NV7100_SIP_400,NEO_RG_LINEAR_HUNT,RG_LINEAR_HUNT)
	RESULTS.append("    RING GROUP LINEAR HUNT SIP TRUNK VERIFICATION---------------------%s"%(passFailCheck(passed))) 
for i in range(runs):
	log.info("RING GROUP LINEAR HUNT T1/PRI VERIFICATION##################################")
	passed=ringGroupCall(PRI2FXO_A,NEO_RG_LINEAR_HUNT,RG_LINEAR_HUNT)
	RESULTS.append("    RING GROUP LINEAR HUNT T1/PRI VERIFICATION------------------------%s"%(passFailCheck(passed)))

RESULTS.append("  UCD")
log.info("  UCD")
for i in range(runs):
	log.info("RING GROUP UCD LOCAL SIP VERIFICATION#######################################")
	passed=ringGroupCall(SIP_300,NEO_RG_UCD,RG_UCD)
	RESULTS.append("    RING GROUP UCD LOCAL SIP VERIFICATION-----------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("RING GROUP UCD LOCAL FXS 0/1 VERIFICATION###################################")
	passed=ringGroupCall(BC_A,NEO_RG_UCD,RG_UCD)
	RESULTS.append("    RING GROUP UCD LOCAL FXS 0/1 VERIFICATION-------------------------%s"%(passFailCheck(passed)))
for i in range(runs):
	log.info("RING GROUP UCD SIP TRUNK VERIFICATION#######################################")
	passed=ringGroupCall(NV7100_SIP_400,NEO_RG_UCD,RG_UCD)
	RESULTS.append("    RING GROUP UCD SIP TRUNK VERIFICATION-----------------------------%s"%(passFailCheck(passed))) 
for i in range(runs):
	log.info("RING GROUP UCD T1/PRI VERIFICATION##########################################")
	passed=ringGroupCall(PRI2FXO_A,NEO_RG_UCD,RG_UCD)
	RESULTS.append("    RING GROUP UCD T1/PRI VERIFICATION--------------------------------%s"%(passFailCheck(passed)))

RESULTS.append("  EXECUTIVE RING")
log.info("  EXECUTIVE RING")
for i in range(1):
	log.info("RING GROUP EXECUTIVE RING LOCAL SIP VERIFICATION############################")
	passed=ringGroupCall(SIP_300,NEO_RG_EXEC_RING,RG_EXEC_RING)
	RESULTS.append("    RING GROUP EXECUTIVE RING LOCAL SIP VERIFICATION------------------%s"%(passFailCheck(passed)))
for i in range(1):
	log.info("RING GROUP EXECUTIVE RING LOCAL FXS 0/1 VERIFICATION########################")
	passed=ringGroupCall(BC_A,NEO_RG_EXEC_RING,RG_EXEC_RING)
	RESULTS.append("    RING GROUP EXECUTIVE RING LOCAL FXS 0/1 VERIFICATION--------------%s"%(passFailCheck(passed)))
for i in range(1):
	log.info("RING GROUP EXECUTIVE RING SIP TRUNK VERIFICATION############################")
	passed=ringGroupCall(NV7100_SIP_400,NEO_RG_EXEC_RING,RG_EXEC_RING)
	RESULTS.append("    RING GROUP EXECUTIVE RING SIP TRUNK VERIFICATION------------------%s"%(passFailCheck(passed)))
for i in range(1):
	log.info("RING GROUP EXECUTIVE RING T1/PRI VERIFICATION###############################")
	passed=ringGroupCall(PRI2FXO_A,NEO_RG_EXEC_RING,RG_EXEC_RING)
	RESULTS.append("    RING GROUP EXECUTIVE RING T1/PRI VERIFICATION---------------------%s"%(passFailCheck(passed)))


"""
Tests for Call Queuing Calls
"""
RESULTS.append("\nCALL QUEUING")
log.info("CALL QUEUING")
RESULTS.append("  ALL RING")
log.info("  ALL RING")
for i in range(1):
	log.info("CALL QUEUING ALL RING LOCAL SIP VERIFICATION################################")
	passed=callQueuingCall(SIP_300,NEO_CQ_ALL_RING,CQ_ALL_RING)
	RESULTS.append("    CALL QUEUING ALL RING LOCAL SIP VERIFICATION----------------------%s"%(passFailCheck(passed)))
for i in range(1):
	log.info("CALL QUEUING ALL RING LOCAL FXS 0/1 VERIFICATION############################")
	passed=callQueuingCall(BC_A,NEO_CQ_ALL_RING,CQ_ALL_RING)
	RESULTS.append("    CALL QUEUING ALL RING LOCAL FXS 0/1 VERIFICATION------------------%s"%(passFailCheck(passed)))
for i in range(1):
	log.info("CALL QUEUING ALL RING SIP TRUNK VERIFICATION################################")
	passed=callQueuingCall(NV7100_SIP_400,NEO_CQ_ALL_RING,CQ_ALL_RING)
	RESULTS.append("    CALL QUEUING ALL RING SIP TRUNK VERIFICATION----------------------%s"%(passFailCheck(passed)))
for i in range(1):
	log.info("CALL QUEUING ALL RING T1/PRI VERIFICATION###################################")
	passed=callQueuingCall(PRI2FXO_A,NEO_CQ_ALL_RING,CQ_ALL_RING)
	RESULTS.append("    CALL QUEUING ALL RING T1/PRI VERIFICATION-------------------------%s"%(passFailCheck(passed)))

RESULTS.append("  LINEAR HUNT")
log.info("  LINEAR HUNT")
for i in range(1):
	log.info("CALL QUEUING LINEAR HUNT LOCAL SIP VERIFICATION#############################")
	passed=callQueuingCall(SIP_300,NEO_CQ_LINEAR_HUNT,CQ_LINEAR_HUNT)
	RESULTS.append("    CALL QUEUING LINEAR HUNT LOCAL SIP VERIFICATION-------------------%s"%(passFailCheck(passed)))
for i in range(1):
	log.info("CALL QUEUING LINEAR HUNT LOCAL FXS 0/1 VERIFICATION#########################")
	passed=callQueuingCall(BC_A,NEO_CQ_LINEAR_HUNT,CQ_LINEAR_HUNT)
	RESULTS.append("    CALL QUEUING LINEAR HUNT LOCAL FXS 0/1 VERIFICATION---------------%s"%(passFailCheck(passed)))
for i in range(1):
	log.info("CALL QUEUING LINEAR HUNT SIP TRUNK VERIFICATION#############################")
	passed=callQueuingCall(NV7100_SIP_400,NEO_CQ_LINEAR_HUNT,CQ_LINEAR_HUNT)
	RESULTS.append("    CALL QUEUING LINEAR HUNT SIP TRUNK VERIFICATION-------------------%s"%(passFailCheck(passed)))
for i in range(1):
	log.info("CALL QUEUING LINEAR HUNT T1/PRI VERIFICATION################################")
	passed=callQueuingCall(PRI2FXO_A,NEO_CQ_LINEAR_HUNT,CQ_LINEAR_HUNT)
	RESULTS.append("    CALL QUEUING LINEAR HUNT T1/PRI VERIFICATION----------------------%s"%(passFailCheck(passed)))

RESULTS.append("  MOST IDLE")
log.info("  MOST IDLE")
for i in range(1):
	log.info("CALL QUEUING MOST IDLE LOCAL SIP VERIFICATION###############################")
	passed=callQueuingCall(SIP_300,NEO_CQ_MOST_IDLE,CQ_MOST_IDLE)
	RESULTS.append("    CALL QUEUING MOST IDLE LOCAL SIP VERIFICATION---------------------%s"%(passFailCheck(passed)))
for i in range(1):
	log.info("CALL QUEUING MOST IDLE LOCAL FXS 0/1 VERIFICATION###########################")
	passed=callQueuingCall(BC_A,NEO_CQ_MOST_IDLE,CQ_MOST_IDLE)
	RESULTS.append("    CALL QUEUING MOST IDLE LOCAL FXS 0/1 VERIFICATION-----------------%s"%(passFailCheck(passed)))
for i in range(1):
	log.info("CALL QUEUING MOST IDLE SIP TRUNK VERIFICATION###############################")
	passed=callQueuingCall(NV7100_SIP_400,NEO_CQ_MOST_IDLE,CQ_MOST_IDLE)
	RESULTS.append("    CALL QUEUING MOST IDLE SIP TRUNK VERIFICATION---------------------%s"%(passFailCheck(passed)))
for i in range(1):
	log.info("CALL QUEUING MOST IDLE T1/PRI VERIFICATION##################################")
	passed=callQueuingCall(PRI2FXO_A,NEO_CQ_MOST_IDLE,CQ_MOST_IDLE)
	RESULTS.append("    CALL QUEUING MOST IDLE T1/PRI VERIFICATION------------------------%s"%(passFailCheck(passed)))

"""
Tests for Pick Up Group Calls
"""
RESULTS.append("\nPICK UP GROUP")
log.info("PICK UP GROUP")
for i in range(1):
	log.info("PICK UP GROUP LOCAL SIP VERIFICATION########################################")
	passed=pickupGroupCall(SIP_300,NEO_PUG)
	RESULTS.append("    RING GROUP ALL RING LOCAL SIP VERIFICATION------------------------%s"%(passFailCheck(passed)))
for i in range(1):
	log.info("PICK UP GROUP LOCAL FXS 0/1 VERIFICATION####################################")
	passed=pickupGroupCall(BC_A,NEO_PUG)
	RESULTS.append("    RING GROUP ALL RING LOCAL FXS 0/1 VERIFICATION--------------------%s"%(passFailCheck(passed)))
for i in range(1):
	log.info("PICK UP GROUP SIP TRUNK VERIFICATION########################################")
	passed=pickupGroupCall(NV7100_SIP_400,NEO_PUG)
	RESULTS.append("    RING GROUP ALL RING SIP TRUNK VERIFICATION------------------------%s"%(passFailCheck(passed))) 
for i in range(1):
	log.info("PICK UP GROUP T1/PRI VERIFICATION###########################################")
	passed=pickupGroupCall(PRI2FXO_A,NEO_PUG)
	RESULTS.append("    RING GROUP ALL RING T1/PRI VERIFICATION---------------------------%s"%(passFailCheck(passed)))

atexit.register(finalizeTest)

