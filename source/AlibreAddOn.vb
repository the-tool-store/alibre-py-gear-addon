Imports System.IO
Imports System.Reflection
Imports AlibreAddOn
Imports AlibreX
Imports IronPython.Hosting
Imports Microsoft.Scripting.Hosting

Namespace AlibreAddOnAssembly
    Public Module AlibreAddOn
        Private Property AlibreRoot As IADRoot
        Private _parentWinHandle As IntPtr
        Private _addOnHandle As AddOnRibbon
        Public Sub AddOnLoad(ByVal hwnd As IntPtr, ByVal pAutomationHook As IAutomationHook, ByVal unused As IntPtr)
            AlibreRoot = CType(pAutomationHook.Root, IADRoot)
            _parentWinHandle = hwnd
            _addOnHandle = New AddOnRibbon(AlibreRoot, _parentWinHandle)
        End Sub
        Public Sub AddOnUnload(ByVal hwnd As IntPtr, ByVal forceUnload As Boolean, ByRef cancel As Boolean, ByVal reserved1 As Integer, ByVal reserved2 As Integer)
            _addOnHandle = Nothing
            AlibreRoot = Nothing
        End Sub
        Public Function GetRoot() As IADRoot
            Return AlibreRoot
        End Function
        Public Sub AddOnInvoke(ByVal hwnd As IntPtr, ByVal pAutomationHook As IntPtr, ByVal sessionName As String, ByVal isLicensed As Boolean, ByVal reserved1 As Integer, ByVal reserved2 As Integer)
        End Sub
        Public Function GetAddOnInterface() As IAlibreAddOn
            Return CType(_addOnHandle, IAlibreAddOn)
        End Function
    End Module
    Public Class AddOnRibbon
        Implements IAlibreAddOn
        Private Const ROOT_ID As Integer = 901
        Private Const CMD As Integer = 1001
        Private ReadOnly _AlibreRoot As IADRoot
        Private ReadOnly _parentWinHandle As IntPtr
        Public Sub New(alibreRoot As IADRoot, parentWinHandle As IntPtr)
            _AlibreRoot = alibreRoot
            _parentWinHandle = parentWinHandle
        End Sub
        Public ReadOnly Property RootMenuItem As Integer Implements IAlibreAddOn.RootMenuItem
            Get
                Return ROOT_ID
            End Get
        End Property
        <STAThread>
        Public Function InvokeCommand(menuId As Integer, sessionIdentifier As String) As IAlibreAddOnCommand Implements IAlibreAddOn.InvokeCommand
            Try
                Dim session As IADSession = Nothing
                If _AlibreRoot IsNot Nothing Then
                    Try
                        If Not String.IsNullOrEmpty(sessionIdentifier) Then
                            For Each s As IADSession In _AlibreRoot.Sessions
                                If String.Equals(s.Identifier, sessionIdentifier, StringComparison.OrdinalIgnoreCase) Then
                                    session = s
                                    Exit For
                                End If
                            Next
                        End If
                        If session Is Nothing Then
                            For Each s As IADSession In _AlibreRoot.Sessions
                                session = s
                                Exit For
                            Next
                        End If
                    Catch
                    End Try
                End If
                Dim runner As New ScriptRunner1(_AlibreRoot)
                Dim addOnDirectory As String = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location)
                Dim scriptsPath = Path.Combine(addOnDirectory, "scripts")
                Select Case menuId
                    Case CMD
                        runner.ExecuteScript(session,Path.Combine(scriptsPath ,"Template.py"))
                End Select
            Catch ex As Exception
                System.Windows.MessageBox.Show("An error occurred while invoking the command:" & vbLf & ex.ToString(),"alibre-py-gear-addon")
            End Try
            Return Nothing
        End Function
        Public Class ScriptRunner1
            Private ReadOnly _engine As ScriptEngine
            Private ReadOnly _alibreRoot As IADRoot
            Public Sub New(alibreRoot As IADRoot)
                _alibreRoot = alibreRoot
                _engine = Python.CreateEngine()
                Dim alibreInstallPath As String = System.Reflection.Assembly.GetAssembly(GetType(IADRoot)).Location.Replace("\Program\AlibreX.dll", "")
                Dim searchPaths = _engine.GetSearchPaths()
                searchPaths.Add(Path.Combine(alibreInstallPath, "Program", "Addons", "AlibreScript", "PythonLib"))
                searchPaths.Add(Path.Combine(alibreInstallPath, "Program", "Addons", "AlibreScript", "PythonLib","site-packages"))
                searchPaths.Add(Path.Combine(alibreInstallPath, "Program", "Addons", "AlibreScript"))
                _engine.SetSearchPaths(searchPaths)
            End Sub
            Public Sub ExecuteScript(session As IADSession, mainScriptFileName As String)
                Try
                    Dim addOnDirectory As String = Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location)
                    Dim ScriptsPath As String = Path.Combine(addOnDirectory, "scripts")
                    Dim setupScriptPath As String = Path.Combine(ScriptsPath, "alibre_setup.py")
                    Dim mainScriptPath As String = Path.Combine(ScriptsPath, mainScriptFileName)
                    If (Not File.Exists(setupScriptPath)) OrElse (Not File.Exists(mainScriptPath)) Then
                        System.Windows.MessageBox.Show("Error: Script not found." & vbLf & "Setup: " & setupScriptPath & vbLf & "Main: " & mainScriptPath, "Script Error")
                        Return
                    End If
                    Dim scope As ScriptScope = _engine.CreateScope()
                    scope.SetVariable("ScriptFileName", mainScriptFileName)
                    scope.SetVariable("ScriptFolder", ScriptsPath)
                    scope.SetVariable("SessionIdentifier", session.Identifier)
                    scope.SetVariable("Arguments", New List(Of String)())
                    scope.SetVariable("AlibreRoot", _alibreRoot)
                    scope.SetVariable("CurrentSession", session)
                    _engine.ExecuteFile(setupScriptPath, scope)
                    _engine.ExecuteFile(mainScriptPath, scope)
                Catch ex As Exception
                    System.Windows.MessageBox.Show("An error occurred while running the script:" & vbLf & ex.ToString(), "Python Execution Error")
                End Try
            End Sub
        End Class
        Public Function HasSubMenus(menuId As Integer) As Boolean Implements IAlibreAddOn.HasSubMenus
            If menuId = ROOT_ID Then Return True
            Return False
        End Function
        Public Function SubMenuItems(menuId As Integer) As Array Implements IAlibreAddOn.SubMenuItems
            If menuId = ROOT_ID Then
                Return New Integer() {CMD}
            End If
            Return Nothing
        End Function
        Public Function MenuItemText(menuId As Integer) As String Implements IAlibreAddOn.MenuItemText
            Select Case menuId
                Case ROOT_ID : Return "py-gear"
                Case CMD : Return "py-gear Tool"
                Case Else : Return String.Empty
            End Select
        End Function
        Public Function MenuItemState(menuId As Integer, sessionIdentifier As String) As ADDONMenuStates Implements IAlibreAddOn.MenuItemState
            Return ADDONMenuStates.ADDON_MENU_ENABLED
        End Function
        Public Function MenuItemToolTip(menuId As Integer) As String Implements IAlibreAddOn.MenuItemToolTip
            Select Case menuId
                Case ROOT_ID : Return "py-gear"
                Case CMD : Return "py-gear Tool"
                Case Else : Return String.Empty
            End Select
        End Function
        Public Function MenuIcon(menuID As Integer) As String Implements IAlibreAddOn.MenuIcon
            Select Case menuID
                Case ROOT_ID : Return ""                  
                Case CMD : Return "logo.ico"
                Case Else : Return ""
            End Select
        End Function
        Public Function PopupMenu(menuId As Integer) As Boolean Implements IAlibreAddOn.PopupMenu
            Return False
        End Function
        Public Function HasPersistentDataToSave(sessionIdentifier As String) As Boolean Implements IAlibreAddOn.HasPersistentDataToSave
            Return False
        End Function
        Public Sub SaveData(pCustomData As IStream, sessionIdentifier As String) Implements IAlibreAddOn.SaveData
        End Sub
        Public Sub LoadData(pCustomData As IStream, sessionIdentifier As String) Implements IAlibreAddOn.LoadData
        End Sub
        Public Function UseDedicatedRibbonTab() As Boolean Implements IAlibreAddOn.UseDedicatedRibbonTab
            Return False
        End Function
        Private Sub IAlibreAddOn_setIsAddOnLicensed(isLicensed As Boolean) Implements IAlibreAddOn.setIsAddOnLicensed
        End Sub
    End Class
End Namespace