import csv
import os
import os.path
import Common
import Config

version = "0.0.2"
class Utility:
	s_log = ""
	s_columnName = []
	s_fileDirectories = []
	s_actList = {}
	s_room1Valid = {}
	s_room2Valid = {}
	s_room1 = {}
	s_room2 = {}

def LogWarning(actID, columnID, message):
	Utility.s_log += (actID+" Column: "+columnID+" => "+message+"\n")

def GetFileDirectories():
	sourceFilePath	= os.path.dirname(os.path.abspath(__file__))
	for agent in Config.AgentList:
		agentPath = sourceFilePath+"\\"+agent+"\\"+Config.FileName
		Utility.s_fileDirectories.append(agentPath)

def LoadActivityTable():
	success = True
	for (agentName, files) in zip(Config.AgentList, Utility.s_fileDirectories):
		actList = {}
		if os.path.exists(files):
			with open(files) as csvfile:
				reader = csv.reader(csvfile)
				for row in reader:
					if row[Common.TABLE_ACTIVITY_ID] == "ID":
						Utility.s_columnName = row
						continue
					actList[row[Common.TABLE_ACTIVITY_ID]] = row
			Utility.s_actList[agentName] = actList
		else:
			print("File "+files+" not exist. Please recheck!")
			success = False
	return success

def CheckEmpty(row, index):
	if len(row) <= index:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], "ColumnError", "Column count is "+str(len(row))+" less than required index "+str(index)+" (index start from 0)")
		return True
	if row[index] == None or row[index] == "":
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Cell is empty!")
		return True
	return False

def IsInt(value):
	try:
		result = int(value)
		return True, result
	except ValueError:
		return False, 0

def IsFloat(value):
	try:
		result = float(value)
		return True, result
	except ValueError:
		return False, 0

def IsBinary(value):
	return (value == "0" or value == "1")

def IsRoomValid(value):
	return (value in Config.RoomList)

def CheckRepeat(row):
	indexColumn = Common.TABLE_ACTIVITY_REPEAT
	if(CheckEmpty(row, indexColumn)):
		return
	isInt, value = IsInt(row[indexColumn])
	if not isInt:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[indexColumn], "Invalid value. Not a number!")
		return
	
	if ( value < -1 or value == 0):
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[indexColumn], "Invalid value. Not within valid range!")

def CheckBinary(row, index):
	if(CheckEmpty(row, index)):
		return
	
	if not IsBinary(row[index]):
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value!")

def CheckInterrupt(row):
	index = Common.TABLE_ACTIVITY_INTERRUPT
	if(CheckEmpty(row, index)):
		return
	
	content = row[index].split(";")
	if len(content) != 2:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format!")
		return
	
	for val in content:
		if not IsBinary(val):
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value: "+val)

def CheckFisioItem(row, index):
	if(CheckEmpty(row, index)):
		return
	
	content = row[index].split(";")
	if len(content) != 2:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format!")
		return
	
	for val in content:
		isFloat, value = IsFloat(val)
		if not isFloat:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value: "+val)

def CheckEmotion(row, index):
	if(CheckEmpty(row, index)):
		return
	
	content = row[index].split(";")
	if len(content) != 3:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format!")
		return
	
	for val in content:
		isFloat, value = IsFloat(val)
		if not isFloat:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value: "+val)

def CheckFormatTime(row, index, use24Format):
	if(CheckEmpty(row, index)):
		return
	
	if(row[index] == "-"):
		return
	
	content = row[index].split(":")
	if len(content) != 2:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format!")
		return
	
	isInt, value = IsInt(content[0])
	if not isInt:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value: "+content[0])
	elif (use24Format and (value < 0 or value >=24)):
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value, should be between 0-23! Current: "+content[0])
	elif (not use24Format and value < 0):
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value, should be positive value! Current: "+content[0])
	
	isInt, value = IsInt(content[1])
	if not isInt:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value: "+content[1])
	elif (value < 0 or value >=60):
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value, should be between 0-59! Current:"+content[1])

def CheckPriority(row):
	index = Common.TABLE_ACTIVITY_PRIORITY
	if(CheckEmpty(row, index)):
		return
	
	isInt, value = IsInt(row[index])
	if not isInt:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value!")
		return
	
	if not (value in range(0, 5)):
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value. Outside range!")

def CheckFloat(row, index):
	if(CheckEmpty(row, index)):
		return
	
	isFloat, value = IsFloat(row[index])
	if not isFloat:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value!")
		return
	
	if value < 0 or value > 10:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value. Outside range!")

def CheckRoutine(row):
	index = Common.TABLE_ACTIVITY_ROUTINE
	if(CheckEmpty(row, index)):
		return
	
	content = row[index].split("|")
	if len(content) != 2:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format!")
		return
	
	isInt, routinePeriod = IsInt(content[0])
	if not isInt or routinePeriod < 1:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid routine period format: "+content[0])
		return
	
	routineTime = content[1].split(";")
	
	if len(routineTime) == 1:
		isInt, routine = IsInt(routineTime[0])
		if not isInt:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid routine time: "+routineTime[0])
		elif routine == 0:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid routine time cannot zero!")
		elif routine > routinePeriod:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid routine cannot more than routine period! Routine period: "+content[0]+" - Routine Time: "+routineTime[0])
		elif abs(routine) > routinePeriod:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid routine cannot less than negative routine period! Routine period: "+content[0]+" - Routine Time: "+routineTime[0])
	else:
		for rTime in routineTime:
			isInt, routine = IsInt(rTime)
			if not isInt:
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid routine time: "+rTime)
			elif routine < 1:
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid routine time less than one! Current: "+rTime)
			elif routine > routinePeriod:
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid routine cannot more than routine period! Routine period: "+content[0]+" - Routine Time: "+rTime)

def CheckActivityExist(row, index, agentName, single = True):
	if(CheckEmpty(row, index)):
		return
	
	if row[index] != "-":
		if single:
			if not(row[index] in Utility.s_actList[agentName].keys()):
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Cannot find activity "+row[index]+" in "+agentName+" activity list!")
		else:
			actList = row[index].split(";")
			for act in actList:
				if not(act in Utility.s_actList[agentName].keys()):
					LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Cannot find activity "+act+" in "+agentName+" activity list!")

def CheckInteractAgent(row, agentName):
	empty = CheckEmpty(row, Common.TABLE_ACTIVITY_INTERACT_AGENT)
	empty |= CheckEmpty(row, Common.TABLE_ACTIVITY_FOLLOWER_ACTIVITY)
	empty |= CheckEmpty(row, Common.TABLE_ACTIVITY_FOLLOW_MOVEMENT)
	if empty:
		return
	
	interactAgents = row[Common.TABLE_ACTIVITY_INTERACT_AGENT]
	if interactAgents == "-":
		if row[Common.TABLE_ACTIVITY_FOLLOWER_ACTIVITY] != "-":
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[Common.TABLE_ACTIVITY_FOLLOWER_ACTIVITY], "No interact agent but have activity!")
		if row[Common.TABLE_ACTIVITY_FOLLOW_MOVEMENT] != "0":
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[Common.TABLE_ACTIVITY_FOLLOW_MOVEMENT], "No interact agent but follow movement not zero!")
	else:
		interactAgentList = interactAgents.split(";")
		interactListOK = False
		for agent in interactAgentList:
			if agent == agentName:
				continue
			interactListOK |= (agent in Config.AgentList)
		if not interactListOK:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[Common.TABLE_ACTIVITY_INTERACT_AGENT], "Invalid interact agent. No valid agent within the list!")
			return
		
		interactActivity = row[Common.TABLE_ACTIVITY_FOLLOWER_ACTIVITY]
		if interactActivity != "-":
			for agent in interactAgentList:
				if agent in Config.AgentList:
					if not interactActivity in Utility.s_actList[agent].keys():
						LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[Common.TABLE_ACTIVITY_FOLLOWER_ACTIVITY], "Invalid activity! Agent "+agent+" doesn't have activity "+interactActivity)
						if (row[Common.TABLE_ACTIVITY_FOLLOW_MOVEMENT] != "0"):
							LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[Common.TABLE_ACTIVITY_FOLLOW_MOVEMENT], "Follow movement has value but interact activity is invalid!")
					else:
						if not IsBinary(row[Common.TABLE_ACTIVITY_FOLLOW_MOVEMENT]):
							LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[Common.TABLE_ACTIVITY_FOLLOW_MOVEMENT], "Follow movement has should be 0 or 1!")
		else:
			if (row[Common.TABLE_ACTIVITY_FOLLOW_MOVEMENT] != "0"):
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[Common.TABLE_ACTIVITY_FOLLOW_MOVEMENT], "Follow movement is not 0 but doesn't have interact activity!")

def CheckRooms(row):
	index = Common.TABLE_ACTIVITY_ROOM
	if(CheckEmpty(row, index)):
		return
	
	if row[index] == "-":
		Utility.s_room1Valid[row[Common.TABLE_ACTIVITY_ID]] = Common.ROOM_VALID
		Utility.s_room2Valid[row[Common.TABLE_ACTIVITY_ID]] = Common.ROOM_NONE
		Utility.s_room1[row[Common.TABLE_ACTIVITY_ID]] = "Agent"
		Utility.s_room2[row[Common.TABLE_ACTIVITY_ID]] = "None"
	else:
		rooms = row[index].split("|")
		if len(rooms) != 2:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format!")
			Utility.s_room1Valid[row[Common.TABLE_ACTIVITY_ID]] = Common.ROOM_INVALID
			Utility.s_room2Valid[row[Common.TABLE_ACTIVITY_ID]] = Common.ROOM_INVALID
			return
		
		if rooms[0] == "NONE":
			Utility.s_room1Valid[row[Common.TABLE_ACTIVITY_ID]] = Common.ROOM_NONE
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Room 1 shouldn't be empty. Activity should at least have 1 room or follow interact agent room. Please check again!")
		elif IsRoomValid(rooms[0]):
			Utility.s_room1Valid[row[Common.TABLE_ACTIVITY_ID]] = Common.ROOM_VALID
			Utility.s_room1[row[Common.TABLE_ACTIVITY_ID]] = rooms[0]
		else:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Cannot find room "+rooms[0]+" in room list!")
			Utility.s_room1Valid[row[Common.TABLE_ACTIVITY_ID]] = Common.ROOM_INVALID
		
		if rooms[1] == "NONE":
			Utility.s_room2Valid[row[Common.TABLE_ACTIVITY_ID]] = Common.ROOM_NONE
		elif IsRoomValid(rooms[1]):
			Utility.s_room2Valid[row[Common.TABLE_ACTIVITY_ID]] = Common.ROOM_VALID
			Utility.s_room2[row[Common.TABLE_ACTIVITY_ID]] = rooms[1]
		else:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Cannot find room "+rooms[1]+" in room list!")
			Utility.s_room2Valid[row[Common.TABLE_ACTIVITY_ID]] = Common.ROOM_INVALID

def CheckDoor(row):
	index = Common.TABLE_ACTIVITY_DOOR
	if(CheckEmpty(row, index)):
		return
	
	doorAct = row[index].split("|")
	if len(doorAct) == 2:
		if doorAct[0]!= "-":
			if Utility.s_room1Valid[row[Common.TABLE_ACTIVITY_ID]] == Common.ROOM_INVALID:
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Room 1 is invalid. Activity should at least have 1 room or follow interact agent room. Please check again!")
			elif Utility.s_room1Valid[row[Common.TABLE_ACTIVITY_ID]] == Common.ROOM_NONE:
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Room 1 is empty. Activity should at least have 1 room or follow interact agent room. Please check again!")
			elif Utility.s_room1Valid[row[Common.TABLE_ACTIVITY_ID]] == Common.ROOM_VALID and doorAct[0] != "R1" and doorAct[0] != "CC":
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Wrong door activity for Room 1. Should be \"R1\", \"CC\", or \"-\"!")
		
		if doorAct[1]!= "-":
			if Utility.s_room2Valid[row[Common.TABLE_ACTIVITY_ID]] == Common.ROOM_INVALID:
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Room 2 is invalid. Please check again!")
			elif Utility.s_room2Valid[row[Common.TABLE_ACTIVITY_ID]] == Common.ROOM_NONE and doorAct[1] != "-":
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "(Opt) No room 2. This should be filled with \"-\"!")
			elif Utility.s_room2Valid[row[Common.TABLE_ACTIVITY_ID]] == Common.ROOM_VALID and doorAct[1] != "R1" and doorAct[1] != "CC":
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Wrong door activity for Room 2. Should be \"R1\", \"CC\", or \"-\"!")
	else:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format!")

def CheckLightThreshold(row):
	index = Common.TABLE_ACTIVITY_LIGHTTHRESHOLD
	if(CheckEmpty(row, index)):
		return
	
	threshold = row[index].split("|")
	if len(threshold) == 2:
		if threshold[0] != "-":
			if Utility.s_room1Valid[row[Common.TABLE_ACTIVITY_ID]] == Common.ROOM_INVALID:
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Room 1 is invalid. Activity should at least have 1 room or follow interact agent room. Please check again!")
			elif Utility.s_room1Valid[row[Common.TABLE_ACTIVITY_ID]] == Common.ROOM_NONE:
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Room 1 is empty. Activity should at least have 1 room or follow interact agent room. Please check again!")
			elif Utility.s_room1Valid[row[Common.TABLE_ACTIVITY_ID]] == Common.ROOM_VALID:
				threshold1Room = threshold[0].split(";")
				if len(threshold1Room) != 2:
					LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid light threshold format for Room 1!")
				else:
					isInt, value = IsInt(threshold1Room[0])
					if not isInt:
						LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid light threshold format for Room 1. Threshold value shoukd be a number!")
					if threshold1Room[1] != "L1" and threshold1Room[1] != "CC":
						LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Wrong pre activity for light Room 1. Should be \"L1\" or \"CC\"!")
		if threshold[1] != "-":
			if Utility.s_room2Valid[row[Common.TABLE_ACTIVITY_ID]] == Common.ROOM_INVALID:
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Room 2 is invalid. Please check again!")
			elif Utility.s_room2Valid[row[Common.TABLE_ACTIVITY_ID]] == Common.ROOM_NONE:
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "(Opt) No room 2. This should be filled with \"-\"!")
			elif Utility.s_room2Valid[row[Common.TABLE_ACTIVITY_ID]] == Common.ROOM_VALID:
				threshold1Room = threshold[1].split(";")
				if len(threshold1Room) != 2:
					LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid light threshold format for Room 1!")
				else:
					isInt, value = IsInt(threshold1Room[0])
					if not isInt:
						LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid light threshold format for Room 2. Threshold value shoukd be a number!")
					if threshold1Room[1] != "L1" and threshold1Room[1] != "CC":
						LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Wrong pre activity for light Room 2. Should be \"L1\" or \"CC\"!")
	else:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format!")

def CheckStatus(row):
	index = Common.TABLE_ACTIVITY_STATUS
	if(CheckEmpty(row, index)):
		return
	
	status = row[index].split("|")
	if len(status) == 2:
		if status[0] != "-":
			isFloat, value = IsFloat(status[0])	
			if not isFloat or value < 0:
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Status for Room 1 should be a positive number!")
		if status[1] != "-":
			isFloat, value = IsFloat(status[1])
			if not isFloat or value < 0:
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Status for Room 2 should be a positive number!")
	else:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format!")

def CheckTemperature(row):
	index = Common.TABLE_ACTIVITY_TEMPERATURE
	if(CheckEmpty(row, index)):
		return
	
	temperature = row[index].split("|")
	if len(temperature) == 2:
		if temperature[0] != "-":
			isInt, value = IsInt(temperature[0])
			if not isInt or value < 0:
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Temperature for Room 1 should be a positive number!")
		if temperature[1] != "-":
			isInt, value = IsInt(temperature[1])
			if not isInt or value < 0:
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Temperature for Room 2 should be a positive number!")
	else:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format!")

def CheckDevice(row):
	index = Common.TABLE_ACTIVITY_DEVICE
	if(CheckEmpty(row, index)):
		return
	
	devices = row[index].split("|")
	if len(devices) == 2:
		if devices[0] != "-":
			if Utility.s_room1Valid[row[Common.TABLE_ACTIVITY_ID]] == Common.ROOM_VALID and Utility.s_room1[row[Common.TABLE_ACTIVITY_ID]] != "Agent":
				deviceTypeInRoom = [x[2] for x in Config.DeviceIDList if x[1] == Utility.s_room1[row[Common.TABLE_ACTIVITY_ID]]]
				deviceList = devices[0].split(";")
				for device in deviceList:
					if not device in deviceTypeInRoom:
						LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Cannot find device "+device+" in Room 1 ("+Utility.s_room1[row[Common.TABLE_ACTIVITY_ID]]+")!")
		if devices[1] != "-":
			if Utility.s_room2Valid[row[Common.TABLE_ACTIVITY_ID]] == Common.ROOM_VALID:
				deviceTypeInRoom = [x[2] for x in Config.DeviceIDList if x[1] == Utility.s_room2[row[Common.TABLE_ACTIVITY_ID]]]
				deviceList = devices[1].split(";")
				for device in deviceList:
					if not device in deviceTypeInRoom:
						LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Cannot find device "+device+" in Room 2("+Utility.s_room2[row[Common.TABLE_ACTIVITY_ID]]+")!")
	else:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format!")

def CheckPostActivity(row):
	index = Common.TABLE_ACTIVITY_POST_ACTIVITY
	if(CheckEmpty(row, index)):
		return
	
	postActivities = row[index].split("|")
	if len(postActivities) == 2:
		if postActivities[0] != "-":
			postActivityInRoom = postActivities[0].split(";")
			for postActivity in postActivityInRoom:
				if not postActivity in Config.PostActivityList:
					LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Cannot find postActivity "+postActivity+" for Room 1!")
		if postActivities[1] != "-":
			postActivityInRoom = postActivities[1].split(";")
			for postActivity in postActivityInRoom:
				if not postActivity in Config.PostActivityList:
					LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Cannot find postActivity "+postActivity+" for Room 2!")
	else:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format!")

def CheckResource(row):
	index = Common.TABLE_ACTIVITY_RESOURCE
	if(CheckEmpty(row, index)):
		return
	
	allResourceList = row[index].split("|")
	if len(allResourceList) == 2:
		if allResourceList[0] != "-":
			roomResList = allResourceList[0].split(";")
			for resource in roomResList:
				resItem = resource.split(":")
				if len(resItem) != 2:
					LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid resource format for Room 1 : "+resource)
				else:
					if not resItem[0] in Config.ResourceList:
						LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Cannot find resource for Room 1 "+resItem[0]+" in resource list!")
					isFloat, value = IsFloat(resItem[1])	
					if not isFloat:
						LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Resource amount in Room 1 should be a number! Current: "+resource)
		if allResourceList[1] != "-":
			roomResList = allResourceList[1].split(";")
			for resource in roomResList:
				resItem = resource.split(":")
				if len(resItem) != 2:
					LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid resource format for Room 2 : "+resource)
				else:
					if not resItem[0] in Config.ResourceList:
						LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Cannot find resource for Room 2 "+resItem[0]+" in resource list!")
					isFloat, value = IsFloat(resItem[1])	
					if not isFloat:
						LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Resource amount in Room 2 should be a number! Current: "+resource)
	else:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format!")

def CheckInteractAgentStatus(row):
	index = Common.TABLE_ACTIVITY_INTERACTAGENTSTATUS
	if(CheckEmpty(row, index)):
		return
	
	if row[index] != "-":
		iAgentStatus = row[index].split(";")
		if len(iAgentStatus) == 2:
			if not iAgentStatus[0] in Config.FisioProperty:
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid fisiology property. Cannot find property "+iAgentStatus[0]+" in fisiology property list!")
			isFloat, value = IsFloat(iAgentStatus[1])	
			if not isFloat:
				LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Fisiology property value should be a number!")
		else:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format!")

def CheckUrgency(row):
	index = Common.TABLE_ACTIVITY_URGENCY_TYPE
	if(CheckEmpty(row, index)):
		return
	
	isInt, type = IsInt(row[index])
	if not isInt or not (type in range(0,10)):
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Urgency type should be a number between 0 - 9!")
	
	index = Common.TABLE_ACTIVITY_URGENCY_VALUE
	if(CheckEmpty(row, index)):
		return
	
	if type == 0:
		isFloat, const = IsFloat(row[index])
		if not isFloat:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Formula 0 for urgency type should have a number for value!")
	elif type == 1:
		if not row[index] in Config.FisioProperty:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Formula 1 for urgency type should have a fisiology property for value!")
	elif type in [2, 5, 9]:
		if not row[index] in Config.ResourceList:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Formula "+str(type)+" for urgency type should have a single resource for value!")
	elif type in [3, 4]:
		value = row[index].split(";")
		if len(value) != 2:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Wrong value format for urgency type formula "+str(type)+"!")
		if not value[0] in Config.FisioProperty:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Cannot find fisiology property "+value[0]+" for urgency type formula "+str(type)+"!")
		isFloat, const = IsFloat(value[1])
		if not isFloat:
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Formula "+str(type)+" for urgency type should have a number for second value!")
	elif type in range(6, 10):
		if row[index] != "-":
			LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Formula "+str(type)+" for urgency type should have a \"-\" for value!")

def CheckEffect(row):
	index = Common.TABLE_ACTIVITY_EFFECT
	if(CheckEmpty(row, index)):
		return
	
	allEffectList = row[index].split("|")
	if len(allEffectList) == 2:
		if allEffectList[0] != "-":
			allEffectRoom1 = allEffectList[0].split(";")
			prevEffectValid = False
			prevEffectFirstValue = ""
			for (idx, effectSet) in enumerate(allEffectRoom1):
				effectValid = True
				effect = effectSet.split(":")
				if len(effect) == 3:
					isInt, formulaType = IsInt(effect[1])
					if not isInt or not formulaType in range(0, 12):
						effectValid = False
						LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid formula type for effect "+effectSet +" at Room 1!")
					else:
						if formulaType in [0, 5]:
							if effect[0] != "Room" and not effect[0] in Config.ResourceList:
								effectValid = False
								LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value for effect "+effectSet +" at Room 1. Formula "+str(formulaType)+" should have \"Room\" or a resource type as first value!")
						elif formulaType in [2, 4, 6, 7, 8, 9, 10, 11]:
							if effect[0] not in Config.ResourceList:
								effectValid = False
								LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value for effect "+effectSet +" at Room 1. Formula "+str(formulaType)+" should have a resource type as first value!")
							
							if formulaType == 6:
								for i in range(idx + 1, len(allEffectRoom1)):
									if allEffectRoom1[i].startswith(effect[0] +":"):
										effectValid = False
										LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Error Room 1 effect. Next effect with same resource type detected. To be able use formula 6, this effect must be the at the last position for the similar resource type!")
										break
							elif formulaType == 7:
								if not prevEffectValid:
									effectValid = False
									LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Error Room 1 effect. Previous effect not valid. To be able use formula 7, previous effect must be a valid one! Previous: "+allEffectRoom1[idx - 1]+" Current: "+effectSet)
								elif not prevEffectFirstValue in Config.ResourceList:
									effectValid = False
									LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Error Room 1 effect. Previous effect not a resource. To be able use formula 7, previous effect must be a resource type! Previous: "+allEffectRoom1[idx - 1]+" Current: "+effectSet)
						elif formulaType == 3:
							if effect[0] != "Room":
								effectValid = False
								LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Error Room 1 effect. Formula 3 should have \"Room\" as first value!")
						elif formulaType == 1:
							idDevice = [x[0] for x in Config.DeviceIDList if x[3]]
							if not effect[0] in idDevice:
								effectValid = False
								LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Device id "+effect[0]+" not found in Device Id list for Formula 1 in Room 1!")
					
					isConstantFloat, formulaConstant = IsFloat(effect[2])
					if not isConstantFloat:
						effectValid = False
						LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value for effect "+effectSet +" at Room 1. Third value should be a number. In case it's not actually used in the formula, please put 0 as value!")
					prevEffectFirstValue = effect[0]
				else:
					effectValid = False
					LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format for effect "+effectSet +" at Room 1!")
				prevEffectValid = effectValid
		
		if allEffectList[1] != "-":
			allEffectRoom2 = allEffectList[1].split(";")
			prevEffectValid = False
			prevEffectFirstValue = ""
			for (idx, effectSet) in enumerate(allEffectRoom2):
				effectValid = True
				effect = effectSet.split(":")
				if len(effect) == 3:
					isInt, formulaType = IsInt(effect[1])
					if not isInt or not formulaType in range(0, 12):
						effectValid = False
						LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid formula type for effect "+effectSet +" at Room 2!")
					else:
						if formulaType in [0, 5]:
							if effect[0] != "Room" and not effect[0] in Config.ResourceList:
								effectValid = False
								LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value for effect "+effectSet +" at Room 2. Formula "+str(formulaType)+" should have \"Room\" or a resource type as first value!")
						elif formulaType in [2, 4, 6, 7, 8, 9, 10, 11]:
							if effect[0] not in Config.ResourceList:
								effectValid = False
								LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value for effect "+effectSet +" at Room 2. Formula "+str(formulaType)+" should have a resource type as first value!")
							
							if formulaType == 6:
								for i in range(idx + 1, len(allEffectRoom2)):
									if allEffectRoom2[i].startswith(effect[0] +":"):
										effectValid = False
										LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Error Room 2 effect. Next effect with same resource type detected. To be able use formula 6, this effect must be the at the last position for the similar resource type!")
										break
							elif formulaType == 7:
								if not prevEffectValid:
									effectValid = False
									LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Error Room 2 effect. Previous effect not valid. To be able use formula 7, previous effect must be a valid one! Previous: "+allEffectRoom2[idx - 1]+" Current: "+effectSet)
								elif not prevEffectFirstValue in Config.ResourceList:
									effectValid = False
									LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Error Room 2 effect. Previous effect not a resource. To be able use formula 7, previous effect must be a resource type! Previous: "+allEffectRoom2[idx - 1]+" Current: "+effectSet)
						elif formulaType == 3:
							if effect[0] != "Room":
								effectValid = False
								LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Error Room 2 effect. Formula 3 should have \"Room\" as first value!")
						elif formulaType == 1:
							idDevice = [x[0] for x in Config.DeviceIDList if x[3]]
							if not effect[0] in idDevice:
								effectValid = False
								LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Device id "+effect[0]+" not found in Device Id list for Formula 1 in Room 2!")
					
					isConstantFloat, formulaConstant = IsFloat(effect[2])
					if not isConstantFloat:
						effectValid = False
						LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid value for effect "+effectSet +" at Room 2. Third value should be a number. In case it's not actually used in the formula, please put 0 as value!")
					prevEffectFirstValue = effect[0]
				else:
					effectValid = False
					LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format for effect "+effectSet +" at Room 2!")
				prevEffectValid = effectValid
	else:
		LogWarning(row[Common.TABLE_ACTIVITY_ID], Utility.s_columnName[index], "Invalid format!")

def ExportWarning():
	with open("warning.txt", mode = 'w+', newline='') as outputFile:
		outputFile.write(Utility.s_log)

def ValidateActivityTable(actList, agentName):
	for act in actList:
		CheckRepeat(actList[act])
		CheckBinary(actList[act], Common.TABLE_ACTIVITY_AUTO) # column Auto
		CheckBinary(actList[act], Common.TABLE_ACTIVITY_OUTDOOR) # column Outdoor
		CheckBinary(actList[act], Common.TABLE_ACTIVITY_BIOACTIVITY) # column BioActivity
		CheckInterrupt(actList[act]) # column Interrupt
		for i in range(Common.TABLE_ACTIVITY_BIO_EFFECT_START, Common.TABLE_ACTIVITY_EMO_EFFECT):
			CheckFisioItem(actList[act], i) # column Hunger - Urinate
		CheckFormatTime(actList[act], Common.TABLE_ACTIVITY_DURATION, False) # column Duration
		CheckFormatTime(actList[act], Common.TABLE_ACTIVITY_START, True) # column Start
		CheckPriority(actList[act]) # column Priority
		CheckFloat(actList[act], Common.TABLE_ACTIVITY_PHY_STD) # column Physical_Std
		for i in range(Common.TABLE_ACTIVITY_PLAN_START, Common.TABLE_ACTIVITY_ROUTINE):
			CheckFloat(actList[act], i) # column Wish - Urgency
		CheckRoutine(actList[act]) # column Routine
		CheckActivityExist(actList[act], Common.TABLE_ACTIVITY_PREQUISITE, agentName, False) # column Prerequisite
		CheckInteractAgent(actList[act], agentName) # column InteractAgent - FollowMovement
		CheckActivityExist(actList[act], Common.TABLE_ACTIVITY_NEXT_ACTIVITY, agentName) # column Next
		CheckActivityExist(actList[act], Common.TABLE_ACTIVITY_ELIMINATE_ACTIVITY, agentName, False) # column Eliminate
		CheckRooms(actList[act]) # column Rooms
		CheckDoor(actList[act]) # column Door
		CheckLightThreshold(actList[act]) # column LightThreshold
		CheckStatus(actList[act]) # column Status
		CheckTemperature(actList[act]) # column Temperature
		CheckDevice(actList[act]) # column Device
		CheckPostActivity(actList[act]) # column PostActivity
		CheckResource(actList[act]) # column Resource
		CheckInteractAgentStatus(actList[act]) # column InteractAgentStatus
		CheckUrgency(actList[act]) # column UrengencyType & UrgencyValue
		CheckEffect(actList[act]) # column Effect

def ValidateDeviceIDList():
	success = True
	for device in Config.DeviceIDList:
		if not device[1] in Config.RoomList:
			success = False
			print("Invalid room "+device[1]+" for device "+device[0])
		if not device[2] in Config.DeviceList:
			success = False
			print("Invalid device type "+device[2]+" for device "+device[0])
	
	if success:
		print("Checking device ID OK")
	else:
		print("Problem with device ID. Please fix Config.DeviceIDList first!!")
	return success

def main():
	print("Running validator version "+version)
	deviceOK = ValidateDeviceIDList()
	GetFileDirectories()
	loadSuccess = LoadActivityTable()
	if loadSuccess and deviceOK:
		for act in Utility.s_actList:
			Utility.s_log += ("Check Table for "+act+"\n")
			ValidateActivityTable(Utility.s_actList[act], act)
			Utility.s_log += ("---------------------------------------------------------------------------------------\n")
		ExportWarning()
		print("Finished running validator")

# ValidateDeviceIDList()
main()