Set objShell = CreateObject("WScript.Shell")
objShell.CurrentDirectory = "D:\First-cc\first_cc\dictation-app"
objShell.Run "powershell -ExecutionPolicy Bypass -File launcher.ps1", 1, False
WScript.Sleep 3000
objShell.Run "http://localhost:5173"
