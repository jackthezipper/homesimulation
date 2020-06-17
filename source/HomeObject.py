import Target
import EntryPoint

class HomeObject:
	HomeObjectList = []
	
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
		
	def IsPartFromThis(self, object):
		for parts in self.objectParts:
			if object.Id == parts.Id:
				return True
		return False
	
	def HasTarget(self):
		return (len(self.targets) > 0 and self.targets[0] != None)
	
	def Occupied(self):
		if not self.HasTarget():
			return 0,0
		occupied = 0
		for target in self.targets:
			if not target.available:
				occupied += 1
		return occupied,len(self.targets)