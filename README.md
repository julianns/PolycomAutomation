PolycomAutomation
=================
For hardware testing, run DVT_Neo_Hardware_Test.py

For software(phone calls) testing, run DVT_Neo_Phone_Calls_Test.py


Project to automate polycom phone wall and test beds

Notes:
   1.   Every call should start from the home menu
   2.   Use a map for the softkeys so that new phones / firmware changes can be added later
   3.   Automate the phone to accept push and log to file
   4.   Need a state machine for soft keys

Found that I need to construct the authorization header each time or else it did not respond to the 401
Tried using session, but it did not work, still need to construct the AUTH each time
I can push curl commands using supprocess; very kludgy but works which is better than elegant and broken
The methods I use to construct the strings can be used with requests if I ever get it working


!!!!!There is XML data that does not show up in the online format embedded in this document.  Click raw to see!!!

Polycom call state:  (The <CallInfo> block is included if and only if <LineState> is ‘Active’. Otherwise it is not included.)

CallLineInfo>
<LineKeyNum> </LineKeyNum>
<LineDirNum> </LineDirNum>
<LineState>Active</LineState>
<CallInfo>
<CallState> </CallState>
<CallType> </CallType>
<UIAppearanceIndex> </UIAppearanceIndex>
<CalledPartyName> </CalledPartyName>
<CalledPartyDirNum> </CalledPartyDirNum>
<CallingPartyName> </CallingPartyName>
<CallingPartyDirNum> </CallingPartyDirNum>
<CallReference> </CallReference>
<CallDuration> </CallDuration>
</CallInfo>
</CallLineInfo>


Polycom device info:

<DeviceInformation>
<MACAddress> </MACAddress>
<PhoneDN> </PhoneDN>
<AppLoadID> </AppLoadID>
<BootROMID> </BootROMID>
<ModelNumber> </ModelNumber>
<TimeStamp> </TimeStamp>
</DeviceInformation>


Polycom network info:

<NetworkConfiguration>
<DHCPServer> </DHCPServer>
<MACAddress> </MACAddress>
<DNSSuffix> </DNSSuffix>
<IPAddress> </IPAddress>
<SubnetMask> </SubnetMask>
<ProvServer> </ProvServer>
<DefaultRouter> </DefaultRouter>
<DNSServer1> </DNSServer1>
<DNSServer2> </DNSServer2>
<VLANID> </VLANID>
<DHCPEnabled> </DHCPEnabled>
</NetworkConfiguration>

