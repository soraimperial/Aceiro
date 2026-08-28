' Abre o Aceiro sem mostrar nenhuma janela preta — só a aplicação.
' Precisa que "IniciarAceiro.bat" já tenha sido executado pelo menos uma
' vez antes (para preparar a pasta "venv").
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = scriptDir & "\venv\Scripts\pythonw.exe"
appPath = scriptDir & "\app.py"

If Not fso.FileExists(pythonw) Then
    MsgBox "Ainda não encontrei a preparação do Aceiro nesta pasta." & vbCrLf & vbCrLf & _
           "Corra primeiro ""IniciarAceiro.bat"" (duplo clique) — só precisa de o fazer uma vez.", _
           vbExclamation, "Aceiro"
    WScript.Quit 1
End If

shell.CurrentDirectory = scriptDir
shell.Run """" & pythonw & """ """ & appPath & """", 0, False
