# $language = "PerlScript"
# $interface = "1.0"

# Enable error warnings
use Win32::OLE;
Win32::OLE->Option(Warn => 3);


$crt->Screen->Send("terminal length 0\n");
$crt->Screen->WaitForString("#");

#Get ports in correct IDLE state
$crt->Screen->Send("script-manager fxo 0/7 on-hook\n");
$crt->Screen->WaitForString("#");
$crt->Screen->Send("script-manager fxo 0/2 on-hook\n");
$crt->Screen->WaitForString("#");
$crt->Screen->Send("script-manager fxo 0/7 detect-battery\n");
$crt->Screen->WaitForString("to Idle");
$crt->Screen->Send("script-manager fxo 0/2 detect-battery\n");
$crt->Screen->WaitForString("to Idle");

#Start the call between the ports
$crt->Screen->Send("script-manager fxo 0/7 supervision loop-start\n");
$crt->Screen->WaitForString("#");
$crt->Screen->Send("script-manager fxo 0/2 supervision loop-start\n");
$crt->Screen->WaitForString("#");

$crt->Screen->Send("script-manager fxo 0/7 detect-battery\n");
$crt->Screen->WaitForString("#");
$crt->Screen->Send("script-manager fxo 0/2 detect-battery\n");
$crt->Screen->WaitForString("#");
sleep 1;
$crt->Screen->Send("script-manager fxo 0/7 seize\n");
$crt->Screen->WaitForString("Dialtone");
sleep 8;
$crt->Screen->Send("\nscript-manager fxo 0/7 send-digits 5551111#\n");
$crt->Screen->WaitForString("#");
sleep 5;
$crt->Screen->Send("script-manager fxo 0/2 seize\n");
$crt->Screen->WaitForString("Dialtone");
sleep 1;
$crt->Screen->Send("script-manager fxo 0/2 flash 10\n");
$crt->Screen->WaitForString("Connected");
sleep 1;
$crt->Screen->Send("script-manager fxo 0/2 listen 5000 6\n");
$crt->Screen->WaitForString("#");
sleep 1;
$crt->Screen->Send("script-manager fxo 0/7 send-tones 123456\n");
$crt->Screen->WaitForString("(123456)");
$crt->Screen->Send("\n\n!                  WE PASSED THE TEST AND RECEIVED THE DIGITS\n\n");