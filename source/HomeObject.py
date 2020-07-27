import Target
import EntryPoint

ENERGY_TYPE_NONE	= 0
ENERGY_TYPE_POWER	= ENERGY_TYPE_NONE + 1
ENERGY_TYPE_WATER	= ENERGY_TYPE_POWER + 1
ENERGY_TYPE_GAS		= ENERGY_TYPE_WATER + 1

class HomeObject:
	HomeObjectList = []
	
	def __init__(self):
		self.objectParts = []
		self.targets = []
		self.entryPoints = []
		
		self.m_name = ""
		self.m_code = ""
		self.m_initialDate = ""
		self.m_lifeSpan = 0
		self.m_size = (0,0,0)
		self.m_function = ""
		
		m_objectCondition = 0
		m_maintenanceStatus = 0
		m_cleanliness = 0
		m_temperature = 0
		m_appearance = (0,0)
		
		m_useEnergyType = ENERGY_TYPE_NONE
	
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