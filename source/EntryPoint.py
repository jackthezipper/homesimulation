class EntryPoint:
	def __init__(self,position,fIndex):
		self.pos = position
		self.target = None
		self.m_floorIndex = fIndex
	
	def CreateCopyForTarget(self, newTarget):
		entry = EntryPoint(self.pos,self.m_floorIndex)
		entry.target = newTarget
		return entry