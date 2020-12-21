#import Agent

#DISTANCE_TOLERANCE

class Door:
	def __init__(self, panel, frameBB, status):
		self.m_panel = panel
		self.m_frameBB = frameBB #doorframe bounding box
		self.m_status = status
		self.m_lock = False
		self.m_rectTest = None
		
		print(self.m_frameBB)
	
	#this basic function 
	def ShouldOpen(self, rect):
		if self.m_lock:
			return False
		
	
	# def Update(self):
		# for agent in Agent.agentList:
			