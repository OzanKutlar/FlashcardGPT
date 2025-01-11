CoordMode, Mouse, Screen
IfWinExist, ChatGPT
{
	WinActivate
}
else
{
	MsgBox, No window with "ChatGPT" found. Please ensure the tab is open.
}


; MsgBox, % A_Args[1] " , " A_Args[2] " , " A_Args[3] " , " A_Args[4] " , " A_Args[5] " , " A_Args[6] " "
formattedText := "Q : " . A_Args[5] . "`n`nA  " . A_Args[6] . "`n`nList the parts in the answer above that are correct, incorrect and mislea:ding. Then provide some improvements as keypoints."

Clipboard := formattedText
Click, % A_Args[3] ", " A_Args[4]
sleep 10

Click, % A_Args[1] ", " A_Args[2]
Send, ^v
Send, {Enter}
ExitApp

RShift::ExitApp
