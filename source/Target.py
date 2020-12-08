class Target:
	s_unNamedCount = 0
	def __init__(self,fIndex,tp = None, id = "UNNAMED"):
		if id == "UNNAMED":
			m_id = id+str(Target.s_unNamedCount)
			Target.s_unNamedCount += 1
		else:
			m_id = id
		self.m_id = id
		self.m_targetPoint = tp
		self.m_floorIndex = fIndex
		self.m_available = True
		self.activities = []
		self.m_specificAgent = []
		
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
	