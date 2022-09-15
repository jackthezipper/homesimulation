import sys
import os

import rhinoscriptsyntax as rs
import scriptcontext as sc

import House
House = reload(House)
import Timer
Timer = reload(Timer)

"""
Holder for generic thing that used across simulation component, such as house and timer instance
"""
sourceFilePath	= os.path.dirname(os.path.abspath(__file__))
sourceDirPath	= sourceFilePath[0:sourceFilePath.rfind('\\')+1]
resPath			= "-"#sourceDirPath+"res\\"+sc.sticky["MapName"]+"\\"

g_timer = Timer.GetInstance()
class Logger:
	s_debugStr = []
	s_debugActive = False
	
	s_agentLog = {}
	s_dumpRequest = 0
	s_resPath = "-"
	
	@staticmethod
	def RegisterAgentLog(agentList):
		for agent in agentList:
			s_agentLog[agent] = []
	
	@staticmethod
	def LogAgent(agent, logText):
		Logger.s_agentLog[agent].append(logText)
	
	# @staticmethod
	# def ExportAgentLog():
		# for log in Logger.s_agentLog:
			

	@staticmethod
	def LogDebug(debugLog):
		if Logger.s_debugActive:
			Logger.s_debugStr.append(debugLog)

	@staticmethod
	def ResetDebug():
		Logger.s_debugStr = []

	@staticmethod
	def DumpDebug(req = 1):
		Logger.s_dumpRequest += req
		if not Logger.s_debugActive or Logger.s_dumpRequest < 10:
			return
		if Logger.s_resPath == "-":
			Logger.s_resPath = sourceDirPath+"res\\"+sc.sticky["MapName"]+"\\"
		
		dFile = open(Logger.s_resPath+"dmp-"+str(g_timer.GetDay())+".txt","a+")
		for debugStr in Logger.s_debugStr:
			dFile.write(debugStr)
		dFile.close()
		Logger.s_debugStr = []
		Logger.s_dumpRequest = 0

House = reload(House)
g_myHouse = House.House()

def HouseLog(log):
	g_myHouse.Log(log)