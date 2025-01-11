#Persistent

MsgBox, Please move the mouse to the 'Reset Button' and press Enter.

CoordMode, Mouse, Screen

While (!GetKeyState("Enter", "P"))
{
	MouseGetPos, resetX, resetY
    ToolTip, % resetX "," resetY
	sleep 10
}
; MsgBox, Reset Button coordinates recorded: %resetX%, %resetY%

RunWait, py save.py "reset" 1 %resetX% %resetY%

MsgBox, Please move the mouse to the 'ChatBox' and press Enter.

; Wait for Enter key to be pressed and record the coordinates
While (!GetKeyState("Enter", "P"))
{
    MouseGetPos, chatX, chatY
    ToolTip, % chatX "," chatY
	sleep 10
}
; MsgBox, ChatBox coordinates recorded: %chatX%, %chatY%

RunWait, py save.py "chat" 1 %chatX% %chatY%

; Exit script
ExitApp
