import Activity
import Agent
import Envi

#------------------------------------------------------------------------------------------------------------
#------------------Terms for activity------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

ACTIVITY_TURN_ONLIGHT	= "S1"
ACTIVITY_TURN_ONTEMP	= "S2"

ACTIVITY_OBJECT_NONE	= "-"

class ActivityTerm()
	def __init__(self, id, environmentFactor, resourceFactor, roomFactor, roomPrio)
		self.m_activityID = id
		self.m_environmentFactor = environmentFactor #contain light and temperature factor;each factor contain affect/not, and object afected by terms
		self.m_resourceFactor = resourceFactor
		self.m_roomFactor = roomFactor
		self.m_roomPrio = roomPrio
	
	def CheckEnvironmentSatisfied(self, agentEnvironmentFactor, agentEnvironmentThreshold, room):
		satisfied = False
		
		#check light factor
		if self.m_environmentFactor[Agent.TERM_ENVI_LIGHT][Agent.TERM_ENVI_AFFECT] != 0:
			satisfied = room.m_light >= agentEnvironmentThreshold[Agent.TERM_ENVI_LIGHT]
			if not satisfied:
				return ACTIVITY_TURN_ONLIGHT,self.m_environmentFactor[Agent.TERM_ENVI_LIGHT][Agent.TERM_ENVI_OBJECT]

		#check temperature factor
		if self.m_environmentFactor[Agent.TERM_ENVI_TEMPERATURE][Agent.TERM_ENVI_AFFECT] != 0:
			satisfied = room.m_temperature < agentEnvironmentThreshold[Agent.TERM_ENVI_TEMPERATURE]
			if not satisfied:
				return ACTIVITY_TURN_ONTEMP,self.m_environmentFactor[Agent.TERM_ENVI_TEMPERATURE][Agent.TERM_ENVI_OBJECT]
		
		#all condition satisfied
		return None,None