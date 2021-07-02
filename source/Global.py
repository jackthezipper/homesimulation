import sys
import os

import rhinoscriptsyntax as rs
import scriptcontext as sc

import House
import Timer


sourceFilePath	= os.path.dirname(os.path.abspath(__file__))
sourceDirPath	= sourceFilePath[0:sourceFilePath.rfind('\\')+1]
resPath			= sourceDirPath+"res\\"+sc.sticky["MapName"]+"\\"

class Logger:
	s_debugStr = ""
	s_debugActive = True

	@staticmethod
	def LogDebug(debugLog):
		if Logger.s_debugActive:
			Logger.s_debugStr += debugLog

	@staticmethod
	def ResetDebug():
		Logger.s_debugStr = ""

	@staticmethod
	def DumpDebug():
		if not Logger.s_debugActive:
			return
		dFile = open(resPath+"dmp.txt","a+")
		dFile.write(Logger.s_debugStr)
		dFile.close()
		Logger.s_debugStr = ""

House = reload(House)
g_myHouse = House.House()
g_timer = Timer.GetInstance()