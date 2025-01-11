#Persistent

MsgBox, Please move the mouse to the 'Reset Button' and press Enter.

CoordMode, Mouse, Screen

While (!GetAsyncKeyState("Enter", "P"))
{
	MouseGetPos, resetX, resetY
    ToolTip, %resetX%, %resetY%
	sleep 10
}
MsgBox, Reset Button coordinates recorded: %resetX%, %resetY%

; Ask for the location of the 'ChatBox'
MsgBox, Please move the mouse to the 'ChatBox' and press Enter.

; Wait for Enter key to be pressed and record the coordinates
While (!GetAsyncKeyState("Enter", "P"))
{
    MouseGetPos, chatX, chatY
    ToolTip, %chatX%, %resetY%
	sleep 10
}
MsgBox, ChatBox coordinates recorded: %chatX%, %chatY%

; Run the Python script with the coordinates for Reset Button
RunWait, python save.py %resetX% %resetY%

; Exit script
ExitApp
