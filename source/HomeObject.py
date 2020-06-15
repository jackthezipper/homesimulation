import Target
import EntryPoint

class HomeObject:
	def __init__(self):
		self.objectParts = []
		self.targets = []
		self.entryPoints = []
	
	def AddParts(self, part):
		self.objectParts.append(part)
	
	def AddTargetPoint(self, target):
		self.targets.append(target)
	
	def AddEntryPoint(self, entry):
		self.entryPoints.append(entry)