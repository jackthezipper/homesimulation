import Activity
import Agent
import Global
Global = reload(Global)
import CommonEnum
CommonEnum = reload(CommonEnum)

#------------------------------------------------------------------------------------------------------------
#------------------Terms for activity------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

ACTIVITY_TURN_ONLIGHT	= "S1"
ACTIVITY_TURN_ONTEMP	= "S2"
ACTIVITY_WALK_TOROOM	= "J1"

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
	
	def CheckEnvironmentTerm(self, agentEnvironmentThreshold, room):
		enviTerm = []
		if self.m_environmentFactor[CommonEnum.TERM_ENVI_LIGHT][CommonEnum.TERM_ENVI_AFFECT] != 0 and room.m_light >= agentEnvironmentThreshold[CommonEnum.TERM_ENVI_LIGHT]:
			index = CommonEnum.TERM_ENVI_OBJECT if room.m_name == self.m_roomPrio[0] else CommonEnum.TERM_ENVI_OBJECT2
			for obj in self.m_environmentFactor[CommonEnum.TERM_ENVI_LIGHT][index]:
				if obj != "-":
					enviTerm.append([ACTIVITY_TURN_ONLIGHT,obj])
		if self.m_environmentFactor[CommonEnum.TERM_ENVI_TEMPERATURE][CommonEnum.TERM_ENVI_AFFECT] != 0 and room.m_temperature > agentEnvironmentThreshold[CommonEnum.TERM_ENVI_TEMPERATURE]:
			index = CommonEnum.TERM_ENVI_OBJECT if room.m_name == self.m_roomPrio[0] else CommonEnum.TERM_ENVI_OBJECT2
			for obj in self.m_environmentFactor[CommonEnum.TERM_ENVI_TEMPERATURE][index]:
				if obj != "-":
					enviTerm.append([ACTIVITY_TURN_ONTEMP,obj])
		return enviTerm

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
	
	def CheckRoomTerm(self, room):
		roomTerm = []
		Global.Logger.LogDebug("Check room term "+room.m_name+"\n")
		roomIdx = -1
		for idx,roomFactor in enumerate(self.m_roomFactor):
			if room.m_name != self.m_roomPrio[idx]:
				Global.Logger.LogDebug("Room prio #"+room.m_name+"# !"+self.m_roomPrio[idx]+"!\n")
				Global.Logger.DumpDebug()
				continue
			roomIdx = idx
			Global.Logger.LogDebug("room factor "+str(roomFactor)+"\n")
			if len(roomFactor[ROOM_DEVICE]) == 0:
				roomTerm.append([ACTIVITY_WALK_TOROOM,CommonEnum.CP_ROOM])
			for (device,activity) in zip(roomFactor[ROOM_DEVICE],roomFactor[ROOM_FAILACTIVITY]):
				Global.Logger.LogDebug("device act "+str(device)+" "+str(activity)+"\n" )
				if device == CommonEnum.RF_NONE:
					continue
				available, objectID = room.HasAndAvailable(device)
				if available:
					Global.Logger.LogDebug("obj id "+str(objectID)+"\n")
					roomTerm.append([activity, objectID])
		Global.Logger.LogDebug("terms "+str(roomTerm))
		Global.Logger.DumpDebug()
		return (roomIdx == -1 or (len(self.m_roomFactor[roomIdx][ROOM_DEVICE]) == 0) or (len(roomTerm) > 0)),roomTerm
		
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