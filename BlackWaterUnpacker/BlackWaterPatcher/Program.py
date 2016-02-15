# -*- coding: utf-8 -*-
import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')
clr.AddReference("IronPython")
clr.AddReference("IronPython.Modules")
import sys 
sys.path.append("C:\Program Files (x86)\IronPython 2.7\Lib")
from System.Windows.Forms import Application
import MainForm

Application.EnableVisualStyles()
form = MainForm.MainForm()
Application.Run(form)
