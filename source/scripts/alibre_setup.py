# Version 3
import clr
clr.AddReference('AlibreX')
clr.AddReference('AlibreScriptAddOn')
import AlibreX
from AlibreScript.API import *
CurrentPart = None
CurrentAssembly = None
if CurrentSession and isinstance(CurrentSession, AlibreX.IADPartSession):
    CurrentPart = Part(CurrentSession)
elif CurrentSession and isinstance(CurrentSession, AlibreX.IADAssemblySession):
    CurrentAssembly = Assembly(CurrentSession)