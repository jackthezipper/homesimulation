class Target:
	def __init__(self,tp = None):
		self.targetPoint = tp
		self.available = True
		self.activities = []
		self.specificAgent = []
		
	def setTargetPoint(self,point):
		self.targetPoint = point
		
	def setActivity(self,activity):
		self.activities.append(activity)
	
	def hasActivity(self,activity):
		for act in self.activities:
			if act == activity:
				return True
		return False
		
	def setSpecificAgent(self,agent):
		self.specificAgent.append(agent)
	
	def isSpecificToAgent(self,agent):
		for spec in self.specificAgent:
			if spec == agent:
				return True
		return False
		
	def notHaveSpecific(self):
		return (len(self.specificAgent) == 0)
	