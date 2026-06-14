Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' 获取脚本所在目录
strPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' 切换到项目目录
objShell.CurrentDirectory = strPath

' 检查 node_modules 是否存在
If Not objFSO.FolderExists("node_modules") Then
    WScript.Echo "首次运行，正在安装依赖，请稍候..."
    objShell.Run "cmd /c npm install", 1, True
End If

' 后台启动开发服务器
objShell.Run "cmd /c npm run dev", 0, False

' 等待服务器启动
WScript.Sleep 3000

' 打开浏览器
objShell.Run "http://localhost:5173"

WScript.Echo "听写练习已启动！" & vbCrLf & vbCrLf & _
             "浏览器已打开，如需关闭请在任务管理器中结束 node.exe 进程。"
