import Activity
import Agent
import Global
Global = reload(Global)
import CommonEnum

#------------------------------------------------------------------------------------------------------------
#------------------Terms for activity------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

ACTIVITY_TURN_ONLIGHT	= "S1"
ACTIVITY_TURN_ONTEMP	= "S2"

ACTIVITY_OBJECT_NONE	= "-"

#room factor
ROOM_DEVICE			= 0
ROOM_FAILACTIVITY	= ROOM_DEVICE + 1

class ActivityTerm():
	def __init__(self, id, ability, environmentFactor, resourceFactor, roomFactor, roomPrio):
		self.m_activityID = id
		self.m_ability = ability
		self.m_environmentFactor = environmentFactor #contain light and temperature factor;each factor contain affect/not, and object afected by terms
		self.m_resourceFactor = resourceFactor #contain resource type, activity if failed the condition, and object to interact
		self.m_roomFactor = roomFactor #contain object need to be available in the room, and corresponding activity for each object
		self.m_roomPrio = roomPrio
	
	#memeriksa faktor lingkungan
	def CheckEnvironmentSatisfied(self, agentEnvironmentThreshold, room):
		satisfied = True
		
		#memeriksa pencahayaan
		if self.m_environmentFactor[CommonEnum.TERM_ENVI_LIGHT][CommonEnum.TERM_ENVI_AFFECT] != 0:
			satisfied = room.m_light >= agentEnvironmentThreshold[CommonEnum.TERM_ENVI_LIGHT]
			if not satisfied:
				return satisfied,ACTIVITY_TURN_ONLIGHT,self.m_environmentFactor[CommonEnum.TERM_ENVI_LIGHT][CommonEnum.TERM_ENVI_OBJECT]

		#memeriksa suhu
		if self.m_environmentFactor[CommonEnum.TERM_ENVI_TEMPERATURE][CommonEnum.TERM_ENVI_AFFECT] != 0:
			satisfied = room.m_temperature < agentEnvironmentThreshold[CommonEnum.TERM_ENVI_TEMPERATURE]
			if not satisfied:
				return satisfied, ACTIVITY_TURN_ONTEMP, self.m_environmentFactor[CommonEnum.TERM_ENVI_TEMPERATURE][CommonEnum.TERM_ENVI_OBJECT]
		
		#kondisi terpenuhi
		return satisfied, None, None
	
	#memeriksa faktor ruang
	def CheckRoomSatisfied(self, room):
		print room.m_name
		print self.m_roomFactor
		for roomFactor in self.m_roomFactor:
			for (device,activity) in zip(roomFactor[ROOM_DEVICE],roomFactor[ROOM_FAILACTIVITY]):
				print "check "+str(device)+" "+str(activity)
				available, objectID = room.HasAndAvailable(device)
				if available:
					return True, activity, objectID
		return (len(self.m_roomFactor) == 0), None, None
	
	def CheckResourcesSatisfied(self):
		for res in self.m_resourceFactor:
			if Global.g_myHouse.m_resources[res[CommonEnum.RES_TYPE]] <= 0:
				return res[CommonEnum.RES_FAILACTIVITY],res[CommonEnum.RES_OBJECT]
		return None,None