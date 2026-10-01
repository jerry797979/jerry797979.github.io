' Runs a .bat that sits in this folder without showing a console window.
' Task Scheduler calls this:  wscript.exe run_hidden.vbs run_alert.bat 557108
' (added 2026-10-01 - the black window kept popping up every time a task fired)
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
If WScript.Arguments.Count = 0 Then WScript.Quit 1
target = """" & fso.GetParentFolderName(WScript.ScriptFullName) & "\" & WScript.Arguments(0) & """"
For i = 1 To WScript.Arguments.Count - 1
  target = target & " " & WScript.Arguments(i)
Next
' 0 = hidden window, True = wait so the task's result is the .bat's exit code
WScript.Quit sh.Run("cmd /c """ & target & """", 0, True)
