<h1>PolycomAutomation</h1>
=================

<h2>Project to automate polycom phone wall and test beds</h2>

Notes:<ol>
    <li>  Every call should start from the home menu
    <li>  Use a map for the softkeys so that new phones / firmware changes can be added later
    <li>  Automate the phone to accept push and log to file
    <li>  Need a state machine for soft keys
    <li>  Polling needs to go to the requester

<ul><li>Found that I need to construct the authorization header each time or else it did not respond to the 401
<li>Tried using session, but it did not work, still need to construct the AUTH each time
<li>I can push curl commands using supprocess; very kludgy but works which is better than elegant and broken
<li>The methods I use to construct the strings can be used with requests if I ever get it working