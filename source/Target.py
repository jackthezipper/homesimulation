import CommonEnum
import Common
import Global

class Target:
	s_unNamedCount = 0
	def __init__(self,fIndex, type, envEffect, tp = None, id = None, powerCons = 0, active = False, autoTrigger = "-"):
		if id == None:
			self.m_id = "UNNAMED"+str(Target.s_unNamedCount)
			Target.s_unNamedCount += 1
		else:
			self.m_id = id
		# self.m_id = id
		self.m_targetPoint = tp
		self.m_floorIndex = fIndex
		self.m_available = True
		self.activities = []
		self.m_specificAgent = []
		self.m_type = type
		self.m_powerCons = powerCons
		self.m_usageStartTime = 0
		self.m_activatedByAct = "Auto"
		self.m_activatorAgent = "Auto"
		if active:
			self.StartUsage("Auto")
		listEnvEffect = [] if envEffect == "-" else envEffect.split(";")
		# numericEnvEffect = [float(effect) for effect in listEnvEffect]
		self.m_envEffect = [float(effect) for effect in listEnvEffect]
		self.m_autoTrigger = autoTrigger.split(";")
		if len(self.m_autoTrigger) > 1:
			self.m_autoTrigger[1] = float(self.m_autoTrigger[1]) #min value to trigger
			self.m_autoTrigger[2] = float(self.m_autoTrigger[2]) #max valur to stop
			self.m_autoTrigger[3] = float(self.m_autoTrigger[3]) #rate
		self.m_inTimer = False
		self.m_isRun = False
		
	def setTargetPoint(self,point):
		self.m_targetPoint = point
		
	def setActivity(self,activity):
		self.activities.append(activity)
	
	def hasActivity(self,activity):
		for act in self.activities:
			if act == activity:
				return True
		return False
		
	def setSpecificAgent(self,agent):
		self.m_specificAgent.append(agent)
	
	def isSpecificToAgent(self,agent):
		for spec in self.m_specificAgent:
			if spec == agent:
				return True
		return False
		
	def notHaveSpecific(self):
		return (len(self.m_specificAgent) == 0)
	
	def CreateCopyForId(self, id):
		return Target(self.m_floorIndex,self.m_type,self.m_targetPoint,id)
	
	def StartUsage(self, activityId, timer = 0, offset = 0, agent = "Auto", useTimer = False, putLog = True):
		Global.Logger.LogDebug("Wanton start "+str(self.m_usageStartTime)+" "+str(Global.g_timer.m_time))
		if self.m_usageStartTime == 0:
			self.m_usageStartTime = Global.g_timer.m_time - offset
		self.m_usageTimer = timer
		
		if putLog:
			Global.HouseLog("Starting device "+self.m_id+" by "+agent+" Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
		
		self.m_activatedByAct = activityId
		self.m_activatorAgent = agent
		self.m_inTimer = useTimer
		self.m_isRun = True
		Global.Logger.LogDebug("Start the usage "+self.m_id+" by "+agent+" "+activityId+" at "+str(self.m_usageStartTime)+" off "+str(offset)+" timer "+str(timer)+"\n")
	
	def StopUsage(self, agent="Auto", putLog = True):
		if not self.m_isRun:
			Global.Logger.LogDebug("Setoping without startig. What the matter?\n")
		Global.Logger.LogDebug("RegisterUsage by stop "+self.m_id+" start "+str(self.m_usageStartTime)+" end "+str(Global.g_timer.m_time)+"\n")
		self.m_isRun = False
		usage = [Common.ENERGY_TYPE_ELECTRICITY, self.m_id, self.m_activatorAgent, self.m_activatedByAct, self.m_usageStartTime, Global.g_timer.m_time, self.m_powerCons]
		Global.g_myHouse.RegisterEnergyUsage(usage)
		self.m_usageTimer = 0
		self.m_usageStartTime = 0
		self.m_inTimer = False
		
		if putLog:
			Global.HouseLog("Stopping device "+self.m_id+" by "+agent+" Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
	
	def UpdateUsage(self):
		if self.m_inTimer:
			if Global.g_timer.m_time - self.m_usageStartTime >= self.m_usageTimer:
				self.StopUsage()
		self.UpdateAutoTrigger()
	
	def SetAvailable(self, available, by = "Auto"):
		Global.Logger.LogDebug("Set devuce "+self.m_id+" to "+str(available)+" by "+by+"\n")
		self.m_available = available
	
	def UpdateAutoTrigger(self):
		if len(self.m_autoTrigger) > 1:
			generalRoom = Global.g_myHouse.FindGeneralRoomForResource(self.m_autoTrigger[0])
			if generalRoom != None and generalRoom.m_resource[self.m_autoTrigger[0]][0] < self.m_autoTrigger[1]:
				onTime = (self.m_autoTrigger[2] - generalRoom.m_resource[self.m_autoTrigger[0]][0]) / self.m_autoTrigger[3]
				self.StartUsage("Auto", onTime, useTimer = True)
			
			if generalRoom != None and self.m_inTimer:
				generalRoom.m_resource[self.m_autoTrigger[0]][0] += self.m_autoTrigger[3]
		
		
		