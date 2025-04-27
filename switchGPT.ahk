CoordMode, Mouse, Screen
Loop
{
	IfWinExist, ChatGPT
	{
		WinActivate
		Break
	}
	else
	{
		MsgBox, No window with "ChatGPT" found. Please ensure the tab is open.
	}
}

; MsgBox, % A_Args[1] " , " A_Args[2] " , " A_Args[3] " , " A_Args[4] " , " A_Args[5] " , " A_Args[6] " "
formattedText := "Question : " . A_Args[5] . "`n`n`nAnswer : " . A_Args[6] . "`n`nList the parts in the answer thats written after 'Answer : ' that are correct, incorrect, incomplete or misleading in seperate areas. Then provide some improvements as keypoints.`n`nFinally, provide a more accurate answer to the question."

Clipboard := formattedText
Click, % A_Args[3] ", " A_Args[4]
sleep 10

Click, % A_Args[1] ", " A_Args[2]
Send, ^v
Send, {Enter}
ExitApp

RShift::ExitApp
