import CommonEnum

class Target:
	s_unNamedCount = 0
	def __init__(self,fIndex, type, tp = None, id = None, powerCons = 0):
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
	
	def StartUsage(self, timer = 0, offset = 0):
		if self.m_usageStartTime == 0:
			self.m_usageStartTime = Global.g_timer.m_time - offset
	
	def StopUsage(self):
		usage = [Common.ENERGY_TYPE_ELECTRICITY, self.m_usageStartTime, Global.g_timer.m_time, self.m_powerCons]
		Global.g_myHouse.RegisterEnergyUsage(usage)
		self.m_usageTimer = 0
		self.m_usageStartTime = 0
	
	def UpdateUsage(self):
		if self.m_usageTimer != 0:
			if Global.g_timer.m_time - self.m_usageStartTime > self.m_usageTimer:
				self.StopUsage()
	