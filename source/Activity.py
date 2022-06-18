import csv
import os
import re

import Common
Common = reload(Common)
import Timer
import BioProperty3
BioProperty3 = reload(BioProperty3)
import Config
import Global
import Agent
Agent = reload(Agent)

def GenerateActivity(dbFile, matrixFile, agent):
	# sourceFilePath	= os.path.dirname(os.path.abspath(__file__))
	# inputFilePath	= sourceFilePath[0:sourceFilePath.rfind('\\')+1]+"input_file\\"+dbFile
	activityList = {}
	Global.Logger.LogDebug("Load matrix "+matrixFile+"\n")
	with open(dbFile) as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			if row[Common.TABLE_ACTIVITY_ID] == "ID":
				continue
			activityID = row[Common.TABLE_ACTIVITY_ID]
			activity = Activity(row, agent)
			activityList[activityID] = activity
	
	with open(matrixFile) as csvfile:
		reader = csv.reader(csvfile)
		idList = None
		for row in reader:
			# print(row[0])
			if row[0] == "":
				# print(row)
				row.pop(0)
				idList = row
				# print("aidul")
				# print(idList)
			else:
				if row[0] in activityList:
					act = activityList[row[0]]
					idx = 1
					for id in idList:
						act.m_matrix[id] = int(row[idx])
						idx += 1
					Global.Logger.LogDebug("kakaro "+act.m_ID+"\n")
					Global.Logger.LogDebug(str(act.m_matrix)+"\n")
				else:
					Global.Logger.LogDebug("id not fond "+row[0]+"\n")
	
	return activityList


EFFECT_RUN		= 0
EFFECT_SUSPEND	= EFFECT_RUN + 1

SUSPEND_TIME = [1, 6, 12, 24, 168]
class Activity:
	s_multiAgent = {}
	s_pendingEffect = []
	# def __init__(self, ID, description, auto, duration, maxRepeat, isBioActivity, bioEffect, emotionalEffect, startTime, priority, bioStandard, emotionalStandard, phyStandard, planProperty, rooms, routine, prequisite, interactAgent, outdoor, terms, device, next, eliminate, activitySet, resource, effect):
	def __init__(self, params, agent):
		self.m_ID = params[Common.TABLE_ACTIVITY_ID]
		self.m_auto = int(params[Common.TABLE_ACTIVITY_AUTO]) == 1
		# Global.Logger.LogDebug("init activity "+self.m_ID)
		# Global.Logger.DumpDebug()
		
		duration = -1
		if(params[Common.TABLE_ACTIVITY_DURATION]) != "-":
			match = re.match(r'(\d+):(\d+)',params[Common.TABLE_ACTIVITY_DURATION])
			duration = int(match.group(1))*Timer.MINUTE_IN_HOUR + int(match.group(2))
		
		self.m_duration = 5 if self.m_auto else duration
		self.m_realDuration = duration
		self.m_runningTime = 0
		self.m_isBioActivity = (params[Common.TABLE_ACTIVITY_BIOACTIVITY] == "1")
		
		bioEffectRun = []
		bioStandard = []
		for i in range(Common.TABLE_ACTIVITY_BIO_EFFECT_START, Common.TABLE_ACTIVITY_EMO_EFFECT):
			effStr = params[i].split(";")
			bioEffectRun.append(float(effStr[Common.ACT_EFFECT_RUN]))
			bioStandard.append(float(effStr[Common.ACT_EFFECT_STD]))
		self.m_bioEffect = [bioEffectRun]
		self.m_bioStandard = bioStandard
		
		self.m_emotionalEffect = [float(emo) for emo in params[Common.TABLE_ACTIVITY_EMO_EFFECT].split(";")]
		self.m_emotionalStandard = self.m_emotionalEffect[Common.EMO_EFFECT_STD]
		
		startTime = -1
		match = re.match(r'(\d+):(\d+)', params[Common.TABLE_ACTIVITY_START])
		if match != None:
			startTime = int(match.group(1))*Timer.MINUTE_IN_HOUR + int(match.group(2))
		self.m_startTime = startTime
		
		self.m_description = params[Common.TABLE_ACTIVITY_DESC]
		self.m_status = Common.ACT_STATUS_NONE
		self.m_forceStop = False
		self.m_priority = int(params[Common.TABLE_ACTIVITY_PRIORITY])
		self.m_physicalStandard = float(params[Common.TABLE_ACTIVITY_PHY_STD])
		
		self.m_planProperty = []
		for i in range(Common.TABLE_ACTIVITY_PLAN_START, Common.TABLE_ACTIVITY_ROUTINE):
			self.m_planProperty.append(0.0 if params[i] == "" else float(params[i]))
		
		self.m_score = 0
		self.m_emotionalScore = 0
		self.m_planScore = 0
		self.m_isIncidental = False
		self.m_remainingIncidentalTime = 0
		self.m_rangeDuration = 0
		self.m_alreadyDoIt = False
		self.m_alreadyDoItYesterday = False
		self.m_maxRepeat = int(params[Common.TABLE_ACTIVITY_REPEAT])
		self.m_repeatCount = 0
		self.m_lastUsedRoom = -1
		
		self.m_routine = []
		match = re.match(r'(\d+)\|(.+)',params[Common.TABLE_ACTIVITY_ROUTINE])
		if match != None:
			self.m_routine.append(int(match.group(1)))
			rTimeStr = match.group(2).split(";")
			rTime = []
			for tstr in rTimeStr:
				rTime.append(int(tstr))
			self.m_routine.append(rTime)

		self.m_prequisite = []
		if params[Common.TABLE_ACTIVITY_PREQUISITE] != "-":
			self.m_prequisite = params[Common.TABLE_ACTIVITY_PREQUISITE].split(";")
		
		self.m_quota = 0
		self.m_matrix = {}
		self.m_timeScore = 5
		self.m_outdoor = (int(params[Common.TABLE_ACTIVITY_OUTDOOR]) == 1)

		self.m_terms = [params[Common.TABLE_ACTIVITY_LIGHTTHRESHOLD].split("|"), params[Common.TABLE_ACTIVITY_STATUS].split("|"), params[Common.TABLE_ACTIVITY_TEMPERATURE].split("|")]

		self.m_device = params[Common.TABLE_ACTIVITY_DEVICE].split("|")
		self.m_will = 0.1
		self.m_stopPlaces = []
		
		if (params[Common.TABLE_ACTIVITY_ROOM] == "-"):
			self.m_rooms = []
		else:
			self.m_rooms = params[Common.TABLE_ACTIVITY_ROOM].split("|")
		
		self.m_doorAct = params[Common.TABLE_ACTIVITY_DOOR].split("|")

		self.m_targetRoom = 0
		self.m_interactAgent = [] if params[Common.TABLE_ACTIVITY_INTERACT_AGENT] == "-" else params[Common.TABLE_ACTIVITY_INTERACT_AGENT].split(";")
		self.m_currentInteractAgent = None
		self.m_next = params[Common.TABLE_ACTIVITY_NEXT_ACTIVITY]
		
		if (params[Common.TABLE_ACTIVITY_ELIMINATE_ACTIVITY] == "-"):
			self.m_eliminate = []
		else:
			self.m_eliminate = params[Common.TABLE_ACTIVITY_ELIMINATE_ACTIVITY].split(";")

		self.m_activitySet = params[Common.TABLE_ACTIVITY_SET]
		
		self.m_requiredResource = []
		roomRes = params[Common.TABLE_ACTIVITY_RESOURCE].split("|")
		for singleRoomRes in roomRes:
			roomResList = []
			if singleRoomRes != "-":
				singleResList = singleRoomRes.split(";")
				for res in singleResList:
					singleRes = res.split(":")
					roomResList.append(singleRes)
			self.m_requiredResource.append(roomResList)

		self.m_effect = []
		# Global.Logger.LogDebug("parsu "+str(len(params))+"\n")
		# Global.Logger.LogDebug("porapi "+str(params)+"\n")
		# Global.Logger.DumpDebug(10)
		effectList = params[Common.TABLE_ACTIVITY_EFFECT].split("|")
		# Global.Logger.LogDebug("elis "+str(effectList)+"\n")
		# Global.Logger.DumpDebug()
		for efL in effectList:
			if efL == "-":
				effectPerRoomList = []
			else:
				effectPerRoomList = efL.split(";")
			roomEf = []
			for ef in effectPerRoomList:
				efSingle = ef.split(":")
				efSingle[1] = int(efSingle[1])
				efSingle[2] = float(efSingle[2])
				roomEf.append(efSingle)
			self.m_effect.append(roomEf)
		
		self.m_postActivity = []
		postActivity = params[Common.TABLE_ACTIVITY_POST_ACTIVITY].split("|")
		for activities in postActivity:
			singleRoomPA = []
			if activities != "-":
				singleRoomPA = activities.split(";")
			self.m_postActivity.append(singleRoomPA)
		
		interuptStr = params[Common.TABLE_ACTIVITY_INTERRUPT].split(";")
		self.m_interrupt = [(value == "1") for value in interuptStr]
		self.m_followerActivity = params[Common.TABLE_ACTIVITY_FOLLOWER_ACTIVITY]
		self.m_followMovement = params[Common.TABLE_ACTIVITY_FOLLOW_MOVEMENT] == "1"
		self.m_urgency = int(params[Common.TABLE_ACTIVITY_URGENCY_TYPE])
		self.m_urgencyValue = params[Common.TABLE_ACTIVITY_URGENCY_VALUE]
		self.m_lastRunningTime = 0
		self.m_lastUpdateTime = Global.g_timer.m_time
		
		self.m_activityKey = ""
		self.m_agent = agent
		self.m_waterLog = []
		self.m_elecLog = []
	
	def GetPostActivity(self):
		Global.Logger.LogDebug("Gapoktan "+str(self.m_postActivity)+" "+str(self.m_targetRoom)+"\n")
		return self.m_postActivity[self.m_targetRoom]
	
	def GetBioEffect(self, property):
		# return self.m_bioEffect[EFFECT_RUN if self.m_status == Common.ACT_STATUS_RUN else EFFECT_SUSPEND][BioProperty3.BIOPROPERTY[property]] if self.m_status != Common.ACT_STATUS_NONE else 0
		return self.m_bioEffect[EFFECT_RUN][BioProperty3.BIOPROPERTY[property]] if self.m_status != Common.ACT_STATUS_NONE else 0
	
	def GetEmotionalEffect(self):
		return self.m_emotionalEffect[EFFECT_RUN if self.m_status == Common.ACT_STATUS_RUN else EFFECT_SUSPEND]
	
	def Update(self):
		deltaUpdate = Global.g_timer.m_time - self.m_lastUpdateTime
		if self.IsRunning():
			# print(self.m_ID+" udd me")
			self.m_runningTime += deltaUpdate
		if self.m_isIncidental:
			if self.m_remainingIncidentalTime > 0:
				self.m_remainingIncidentalTime -= deltaUpdate
			# if self.m_rangeDuration > 0:
				# self.m_rangeDuration -= 1
			else:
				self.m_isIncidental = False
				self.m_status == Common.ACT_STATUS_NONE
				
		if not self.m_isBioActivity and Global.g_timer.GetHour() == 0 and Global.g_timer.GetMinute() == 0:
			if Global.g_timer.GetDay() % self.m_routine[0] == 0:
				self.m_quota = 0
				if self.m_ID == "A74" or self.m_ID == "A72":
					print(self.m_ID+" do "+str(self.m_alreadyDoItYesterday))
			if self.m_status == Common.ACT_STATUS_SUSPEND:
				Global.Logger.LogDebug(self.m_ID+" stop9\n")
				self.Stop()
			self.m_alreadyDoItYesterday = self.m_alreadyDoIt
			self.m_alreadyDoIt = False
			Global.Logger.LogDebug("dodit yesterde "+self.m_ID+" "+str(self.m_alreadyDoItYesterday)+"\n")
		self.m_lastUpdateTime = Global.g_timer.m_time
		# if ((Timer.GetInstance().GetHour() - self.m_startTime) % Timer.HOUR_IN_DAY) > 3:
			# self.m_repeatCount = 0
	
	def Start(self, agent="Auto", runTime = 0):
		if self.m_status == Common.ACT_STATUS_RUN:
			Global.Logger.LogDebug("Call start again---\n")
		self.m_currentInteractAgent = None
		print("Starting activity "+self.m_ID+" - "+self.m_description)
		Global.Logger.LogDebug("Starting activity "+agent+" "+self.m_ID+" - "+self.m_description+" at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
		# self.m_targetRoom = 0
		self.m_status = Common.ACT_STATUS_RUN
		actAgent = None
		if agent != "Auto":
			actAgent = next((agt for agt in Agent.Agent.agentList if agt.m_role == agent), None)
			if actAgent != None:
				if actAgent.m_following:
					self.m_currentInteractAgent = actAgent.m_followedAgent
		if self.m_currentInteractAgent == None:
			self.m_currentInteractAgent = self.GetInteractAgent()
		
		if actAgent != None and not actAgent.m_following and self.m_currentInteractAgent != None and self.m_followerActivity != "-" and self.m_currentInteractAgent.m_currentActivity != None and self.m_currentInteractAgent.m_currentActivity.m_status != Common.ACT_STATUS_RUN and self.m_currentInteractAgent.m_state != Agent.STATE_MOVE:
			self.m_currentInteractAgent.m_currentActivity.m_status = Common.ACT_STATUS_RUN
			self.m_currentInteractAgent.ActivityLog("Starting "+self.m_currentInteractAgent.m_currentActivity.m_ID+" at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
		
		# deviceIds = [device.m_id for device in Agent.Agent.s_possibleTarget]
		for effect in self.m_effect[self.m_targetRoom]:
			# hasEffectDevice = False
			# actualDevice = None
			# if effect[0] in deviceIds:
				# hasEffectDevice = True
			actualDevice = next((device for device in Agent.Agent.s_possibleTarget if device.m_id == effect[0]), None)
			if actualDevice != None and actualDevice.m_powerCons > 0 and not actualDevice.m_isRun:
				Global.HouseLog("Starting device "+effect[0]+" by "+agent+" Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
		Global.Logger.DumpDebug()
		
		agentObj = next((agt for agt in Agent.Agent.agentList if agt.m_role == agent), None)
		if agentObj != None and agentObj.m_passingDoor != None:
			if "R2" in self.GetPostActivity():
				agentObj.m_passingDoor.Close()
			agentObj.m_passingDoor = None
	
	def IsDone(self):
		# Global.Logger.LogDebug("check done "+self.m_ID+" "+str(self.m_duration)+" "+str(self.m_runningTime)+" "+str(self.m_forceStop)+"\n")
		return (self.m_duration != -1 and (self.m_runningTime >= self.m_duration)) or self.m_forceStop
	
	def ForceStop(self):
		self.m_forceStop = True
		if not self.m_isBioActivity:
			self.m_repeatCount +=1
		if self.m_status == Common.ACT_STATUS_RUN:
			self.m_alreadyDoIt = True
	
	def Stop(self):
		self.m_forceStop = False
		if self.m_status == Common.ACT_STATUS_RUN:
			if not self.m_isBioActivity:
				self.m_repeatCount +=1
			self.m_alreadyDoIt = True
			self.m_lastUsedRoom = self.m_targetRoom
			self.m_lastRunningTime = self.m_runningTime
		self.m_targetRoom = 0
		self.m_currentInteractAgent = None
		self.m_runningTime = 0
		Global.Logger.LogDebug("sutop meee "+self.m_ID+" "+str(self.m_status)+" "+str(self.m_lastRunningTime)+" "+str(self.m_runningTime)+"\n")
		self.m_status = Common.ACT_STATUS_NONE
		# pass

	def GetDescription(self):
		return self.m_description
	
	def GoTo(self, agent = None):
		self.m_activityKey = self.m_ID+"-"+str(Global.g_timer.m_time)
		self.m_waterLog = []
		self.m_elecLog = []
		self.m_status = Common.ACT_STATUS_GOTO
		self.m_currentInteractAgent = self.GetInteractAgent()
		if agent != None and self.m_targetRoom == 0:
			agent.AddActivityTableEntry(self.m_activityKey)
			agent.PutActTableLogValue(self.m_ID, Common.ACT_TABLE_LOG_SWITCH_TO)
			agent.PutActTableLogValue(Global.g_timer.GetFullFormattedTime(), Common.ACT_TABLE_LOG_TIME)
	
	def Suspend(self):
		self.m_status = Common.ACT_STATUS_SUSPEND
		# self.m_targetRoom = 0
	
	def Pause(self):
		self.m_status = Common.ACT_STATUS_PAUSED
	
	def Resume(self):
		self.m_status = Common.ACT_STATUS_RUN
	
	def CanStart(self, agent):
		#if self.m_isIncidental:
			#print(self.m_ID + " is incidental remaining "+str(self.m_remainingIncidentalTime)+" range "+str(self.m_rangeDuration))
		# Global.Logger.LogDebug("time "+str(Global.g_timer.GetHour())+" sti "+str(self.m_startTime)+" do "+str(self.m_alreadyDoIt)+" ins "+str(((Global.g_timer.GetHour() - self.m_startTime) % Timer.HOUR_IN_DAY))+"\n")
		Global.Logger.LogDebug(agent.m_role+" CheckStart "+self.m_ID+"\n")
		if self.m_alreadyDoIt and not self.m_isBioActivity and self.m_maxRepeat != -1:
			Global.Logger.LogDebug("canstart fail already done\n")
			return False
		
		if self.m_ID in agent.m_eliminatedActivity:
			Global.Logger.LogDebug("canstart fail eliminated\n")
			return False
		
		# if ((self.m_activitySet != "-") and self.m_activitySet.endswith("C")):
			# Global.Logger.LogDebug("canstart fail set\n")
			# return False
		
		if (len(self.m_interactAgent) > 0):
			# if not agent.IsIndependentAgent():
				# Global.Logger.LogDebug("canstart fail non independent agent but have to interact")
				# return False
			for iAgent in self.m_interactAgent:
				interactAgent = next((agt for agt in Agent.Agent.agentList if (agt.m_role == iAgent)), None)
				if interactAgent != None:
					break
			if interactAgent == None or (interactAgent.m_currentActivity != None and interactAgent.m_currentActivity.m_isBioActivity and self.m_ID != "P01" and self.m_ID != "A25"):
				Global.Logger.LogDebug("canstart fail interact\n")
				return False
		
			if self.m_ID == "P01" or self.m_ID == "A25":
				if not interactAgent.IsAsleep():
					Global.Logger.LogDebug("canstart agent awake\n")
					return False
			
			if interactAgent.m_followedAgent != None and interactAgent.m_followedAgent.m_role != agent.m_role:
				Global.Logger.LogDebug("canstart fail, following other agent\n")
				return False
			
			if interactAgent.m_currentRoom.m_name == "RTG01" or interactAgent.m_currentRoom.m_name == "RTG02":
				Global.Logger.LogDebug("canstart fail, interact agent at stair\n")
				return False
		
		if self.m_ID in agent.m_nonIndependentAct:
			Global.Logger.LogDebug("canstart fail is a nonindependent act, should be trigerred by other agent")
			return False
		
		prequisiteDone = len(self.m_prequisite) == 0
		for prequisite in self.m_prequisite:
			# print("prekoka "+prequisite)
			prequisiteDone |= agent.GetActivityById(prequisite).m_alreadyDoIt
			if self.m_ID == "A03" or self.m_ID == "A61":
				prequisiteDone |= agent.GetActivityById(prequisite).m_alreadyDoItYesterday
			
		if not prequisiteDone:
			Global.Logger.LogDebug("canstart fail prequisite\n")
			return False
		
		routineTime = (Global.g_timer.GetDay() % self.m_routine[0]) + 1
		routineOK = self.m_isBioActivity
		# print(self.m_ID)
		# print(self.m_routine)
		if not routineOK:
			for routine in self.m_routine[1]:
				Global.Logger.LogDebug("cek routine "+str(routine)+" "+str(self.m_quota)+" "+str(routineTime)+"\n")
				if routine < 0 and self.m_quota < abs(routine):
					routineOK = True
					break
				if routine == routineTime:
					routineOK = True
					break
		
		if not routineOK:
			Global.Logger.LogDebug("canstart fail routine\n")
			return False
		
		if self.m_isIncidental:
			Global.Logger.LogDebug("canstart fail incidental\n")
			return False
		
		return True
	
	def IsRunning(self):
		return self.m_status == Common.ACT_STATUS_RUN
	
	def SetToIncidental(self):
		Global.Logger.LogDebug("Set act "+self.m_ID+" to incindetsu\n")
		self.m_targetRoom = 0
		# if not self.m_isBioActivity:
		self.m_isIncidental = True
		self.m_remainingIncidentalTime = SUSPEND_TIME[self.m_priority] * Timer.MINUTE_IN_HOUR
			#self.m_rangeDuration = ((3 + SUSPEND_TIME[self.m_priority]) * Timer.MINUTE_IN_HOUR) - self.m_duration
		self.m_agent.PutActTableLogValue(Global.g_timer.GetFullFormattedTime(), Common.ACT_TABLE_LOG_INCIDENTAL, force = True)
		self.m_agent.PutActTableLogValue(Global.g_timer.GetFullFormattedTime(Global.g_timer.m_time + self.m_remainingIncidentalTime), Common.ACT_TABLE_LOG_INCIDENTALTIME, force = True)
	
	def GetTargetRoom(self):
		Global.Logger.LogDebug("grataro gato da rum "+self.m_ID+" "+str(self.m_targetRoom)+" "+str(self.m_rooms)+"\n")
		if len(self.m_rooms) == 0:
			Global.Logger.LogDebug("grataro zero room\n")
			return "Agent"
		if (self.m_targetRoom == -1) or (self.m_rooms[self.m_targetRoom] == "NONE"):
			Global.Logger.LogDebug("grataro none room "+str(self.m_targetRoom)+" "+self.m_rooms[self.m_targetRoom]+"\n")
			return "None"
		Global.Logger.LogDebug("grataro get room "+self.m_rooms[self.m_targetRoom]+"\n")
		return self.m_rooms[self.m_targetRoom]
	
	def NextTargetRoom(self):
		if self.m_targetRoom == 0:
			self.m_targetRoom = 1
		else:
			self.m_targetRoom = -1
	
	def CheckTerms(self, agent):
		stopPlaces = []
		cancel = False
		
		Global.Logger.LogDebug("Ceka termia "+self.m_ID+"\n");
		agent.Log("Check terms:\n")
		for i in range(0, Common.TERM_COUNT):
			Global.Logger.LogDebug("Hamburterm "+str(self.m_terms)+"\n")
			Global.Logger.LogDebug("In da chucked "+str(i)+" "+str(self.m_targetRoom)+" "+self.m_terms[i][self.m_targetRoom]+" "+str(self.m_terms[i][self.m_targetRoom] != "-")+"\n")
			if (self.m_terms[i][self.m_targetRoom] != "-"):
				Global.Logger.LogDebug("apipah\n "+str(i)+" "+str(Common.TERM_LIGHT)+"\n")
				if i == Common.TERM_LIGHT:
					lightTerm = self.m_terms[i][self.m_targetRoom].split(";")
					Global.Logger.LogDebug("Terma da laito "+str(lightTerm[0]) + " "+str(agent.m_targetRoom.m_light)+"\n")
					agent.Log("Check light: Require = "+lightTerm[0]+" Current = "+str(agent.m_targetRoom.m_light))
					termOfLight = int(lightTerm[0])
					if termOfLight > 0 and agent.m_targetRoom.m_light < termOfLight:
						if (lightTerm[1] == "CC"):
							cancel |= True
							agent.Log(" CANCEL\n")
							break
						else:
							stopPlaces.extend(agent.m_targetRoom.GetLampToTurn())
							agent.Log(" TURN ON\n")
					elif termOfLight < 0 and agent.m_targetRoom.m_light > -termOfLight:
						if (lightTerm[1] == "CC"):
							cancel |= True
							agent.Log(" CANCEL\n")
							break
						else:
							stopPlaces.extend(agent.m_targetRoom.GetLampToTurn(False))
							agent.Log(" TURN OFF\n")
					else:
						agent.Log(" OK\n")
				elif i == Common.TERM_STATUS:
					Global.Logger.LogDebug("StatStur "+str(agent.GetCurrentRoomSocial()) +"\n")
					cancel |= ((self.m_terms[i][self.m_targetRoom] != "-") and (agent.GetCurrentRoomSocial() > float(self.m_terms[i][self.m_targetRoom])))
					agent.Log("Check status: Max = "+self.m_terms[i][self.m_targetRoom]+" Current "+str(agent.GetCurrentRoomSocial())+(" CANCEL\n" if cancel else " OK\n"))
					if cancel:
						break
				elif i == Common.TERM_TEMPERATURE:
					Global.Logger.LogDebug("Tempertotor "+self.m_terms[i][self.m_targetRoom] + " "+str(agent.m_targetRoom.m_temperature)+"\n")
					agent.Log("Check temperature: Require = "+self.m_terms[i][self.m_targetRoom]+" Current = "+str(agent.m_targetRoom.m_temperature))
					if agent.m_targetRoom.m_temperature > float(self.m_terms[i][self.m_targetRoom]):
						hasFan, active, fanObj = agent.m_targetRoom.HasAndActive("Fan")
						if hasFan:
							if (not active):
								stopPlaces.append(fanObj)
								agent.Log(" TURN ON\n")
							else:
								agent.Log(" OK\n")
						cancel |= (not hasFan)
						if cancel:
							agent.Log(" CANCEL\n")
					else:
						agent.Log(" OK\n")
				Global.Logger.LogDebug("Cancera "+str(cancel)+"\n")
		
		return cancel, stopPlaces
	
	def CalculateEnvUrgency(self, agent):
		if self.m_urgency == 0:
			# simple number
			return int(self.m_urgencyValue)
		elif self.m_urgency == 1:
			# agent own property
			return (10.0 - ((agent.GetProperty(self.m_urgencyValue).GetScore()/10.0) * 10.0))
		elif self.m_urgency == 2:
			# negative resource amount
			return (10.0 - (Global.g_myHouse.GetResourceAmount(self.m_urgencyValue)))
		elif self.m_urgency == 3:
			# other agent property
			toCheck = self.m_urgencyValue.split(";")
			amount = 0
			for agt in Agent.Agent.agentList:
				if (agt.m_role != agent.m_role):
					amount += agent.GetProperty(toCheck[0]).GetScore()
			return float(toCheck[1]) * amount
		elif self.m_urgency == 4:
			# property interact agent
			toCheck = self.m_urgencyValue.split(";")
			interactAgent = self.GetInteractAgent()
			if interactAgent == None:
				return 0
			Global.Logger.LogDebug("urgenteract "+str(toCheck)+"\n")
			return float(toCheck[1]) * interactAgent.GetProperty(toCheck[0]).GetScore()
		elif self.m_urgency == 5:
			# resource amount
			return Global.g_myHouse.GetResourceAmount(self.m_urgencyValue)
		elif self.m_urgency == 6:
			# emotional interact agent
			interactAgent = self.GetInteractAgent()
			if interactAgent == None:
				return 0
			return 10 - interactAgent.GetEmotionalFactor()/interactAgent.m_emotionalNormal
		elif self.m_urgency == 7:
			# let there be light
			room = next((rom for rom in Global.g_myHouse.m_rooms if(rom.m_name == self.GetTargetRoom())), None)
			return 10 - room.m_light/10
		elif self.m_urgency == 8:
			# room
			room = next((room for room in Global.g_myHouse.m_rooms if room.m_name == self.m_urgencyValue),None)
			if room != None:
				return room.m_value
			return 0
		elif self.m_urgency == 9:
			# resource amount 2
			return (100 - Global.g_myHouse.GetResourceAmount(self.m_urgencyValue))/10
	
	def CalculateEffects(self, agent):
		for effect in self.m_effect[self.m_targetRoom]:
			Global.Logger.LogDebug("effect "+str(effect)+"\n")
			self.CalculateEffect(agent, effect)
	
	def CalculateEffect(self, agent, effect):
		resLog = [0] * 5
		resType = ["RawFood", "DrinkWater", "DirtyUtensils", "Food", "Trash"]
		for i in range(0,5):
			if resType[i] in agent.m_currentRoom.m_resource:
				resLog[i] = agent.m_currentRoom.m_resource[resType[i]][0]
		if effect[0] == "Room":
			# room = next((rom for rom in Global.g_myHouse.m_rooms if rom.m_name == self.m_rooms[self.m_targetRoom]), None)
			if agent.m_currentRoom != None:
				if effect[1] == 0:
					agent.m_currentRoom.m_value += effect[2]
					agent.PutActTableLogValue(str(effect[2]), Common.ACT_TABLE_LOG_HR_FLOORSTATUS, force = True)
				elif effect[1] == 3:
					agent.m_currentRoom.m_value += (effect[2] * agent.m_currentRoom.m_value)
					agent.PutActTableLogValue(str(effect[2] * agent.m_currentRoom.m_value), Common.ACT_TABLE_LOG_HR_FLOORSTATUS, force = True)
				elif effect[1] == 5:
					agent.PutActTableLogValue(str(effect[2] - agent.m_currentRoom.m_value), Common.ACT_TABLE_LOG_HR_FLOORSTATUS, force = True)
					agent.m_currentRoom.m_value = effect[2]
		else:
			effectValue = 0
			if effect[1] == 0:
				self.ApplyEffect(agent, agent.m_currentRoom, effect[0], effect[2])
			elif effect[1] == 1:
				#should find object and calculate usage
				object = next(obj for obj in Agent.Agent.s_possibleTarget if obj.m_id == effect[0])
				# usage = effect[2] * self.m_duration
				if self.m_auto:
					object.StartUsage(self.m_ID, self.m_realDuration, self.m_duration, agent.m_role, useTimer = True, putLog = False)
				else:
					powerUsage = effect[2]
					if powerUsage == 0:
						powerUsage = object.m_powerCons
					energyUsage = [Common.ENERGY_TYPE_ELECTRICITY, object.m_id, agent.m_role, self.m_ID, Global.g_timer.m_time - self.m_lastRunningTime, Global.g_timer.m_time, powerUsage]
					Global.g_myHouse.RegisterEnergyUsage(energyUsage)
					idx = len(self.m_elecLog)
					if len(self.m_elecLog) == 0 or not object.m_id in self.m_elecLog:
						self.m_elecLog.append(object.m_id)
					else:
						idx = 0 if self.m_elecLog[0] == object.m_id else 1
					agent.PutActTableLogValue(object.m_id, Common.ACT_TABLE_LOG_HR_ELECTRICITY_START + idx*3, force = True)
					agent.PutActTableLogValue(str(self.m_lastRunningTime), Common.ACT_TABLE_LOG_HR_ELECTRICITY_START + idx*3 + 1, force = True)
					agent.PutActTableLogValue(str(powerUsage * self.m_lastRunningTime), Common.ACT_TABLE_LOG_HR_ELECTRICITY_START + idx*3 + 2, force = True)
						
					Global.Logger.LogDebug("RegisterUsage by effect "+object.m_id+" larunta "+str(self.m_lastRunningTime)+" end "+str(Global.g_timer.m_time)+"\n")
					Global.HouseLog("Stopping device "+object.m_id+" by "+agent.m_role+" Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
				# if agent.m_currentRoom.CheckResource(effect[0], usage):
					# self.ApplyEffect(agent.m_currentRoom, effect[0], -usage)
				# else:
			elif effect[1] == 2:
				self.ApplyEffect(agent, agent.m_currentRoom, effect[0], (10.0 - (Global.g_myHouse.GetResourceAmount(effect[0]))))
			elif effect[1] == 3:
				self.ApplyEffect(agent, agent.m_currentRoom, effect[0], (effect[2] * agent.m_currentRoom.m_resource[effect[0]]))
			elif effect[1] == 4:
				Activity.s_pendingEffect.append([agent.m_currentRoom, effect[0], effect[2], (self.m_realDuration - self.m_duration)])
			elif effect[1] == 5:
				self.ApplyEffect(agent, agent.m_currentRoom, effect[0], effect[2], True)
			elif effect[1] == 6:
				Global.Logger.LogDebug("pesix "+agent.m_currentRoom.m_name+" "+str(agent.m_currentRoom.m_resource))
				if agent.m_currentRoom.m_resource[effect[0]][0] <= 0:
					usage = effect[2] * self.m_duration * 60
					self.ApplyEffect(agent, agent.m_currentRoom, effect[0], -usage, autoRoom = False)
					generalRoom = Global.g_myHouse.FindGeneralRoomForResource(effect[0])
					if generalRoom != None:
						self.ApplyEffect(agent, generalRoom, effect[0], usage, autoRoom = False)
			elif effect[1] == 7:
				if effect[2] == 0:
					self.ApplyEffect(agent, agent.m_currentRoom, effect[0], self.m_prevResValue)
				else:
					Activity.s_pendingEffect.append([agent.m_currentRoom, effect[0], self.m_prevResValue, (effect[2] - self.m_duration)])
			elif effect[1] == 8:
				s_savedEffect = Global.g_myHouse.GetResourceAmount(effect[0])
				self.ApplyEffect(agent, agent.m_currentRoom, effect[0], effect[2], True)
			elif effect[1] == 9:
				self.ApplyEffect(agent, agent.m_currentRoom, effect[0], s_savedEffect, True)
			elif effect[1] == 10:
				self.ApplyEffect(agent, agent.m_currentRoom, effect[0], (-agent.GetProperty("Thirst").m_currentEffectScore * self.m_duration * effect[2]))
			elif effect[1] == 11:
				self.ApplyEffect(agent, agent.m_currentRoom, effect[0], effect[2] * self.m_duration)
			
			if effect[1] != 1:
				room = agent.m_currentRoom if effect in agent.m_currentRoom.m_resource.keys() else Global.g_myHouse.FindGeneralRoomForResource(effect[0])
				self.m_prevResValue = 0 if room == None else room.m_resource[effect[0]][0]
		
		for i in range(0,5):
			if resType[i] in agent.m_currentRoom.m_resource:
				resLog[i] = agent.m_currentRoom.m_resource[resType[i]][0] - resLog[i]
				if resLog[i] != 0:
					agent.PutActTableLogValue(str(resLog[i]), Common.ACT_TABLE_LOG_HR_RESOURCES_START + i, force = True)
	
	def CheckResource(self, room, agent):
		ok = True
		for res in self.m_requiredResource[self.m_targetRoom]:
			if res == "Water":
				continue
			ok = ok and room.CheckResource(res[0],float(res[1]))
			enough, amount = room.GetResourceAmount(res[0])
			if not ok:
				generalRoom = Global.g_myHouse.FindGeneralRoomForResource(res[0], res[0] == "Food")#,int(self.m_requiredResource[self.m_targetRoom][1]))
				if generalRoom != None:
					ok = ok or generalRoom.CheckResource(res[0],int(res[1]))
					enough, amount = generalRoom.GetResourceAmount(res[0])
			
			if not ok:
				agent.Log("Not enough at room "+room.m_name+" Resource: "+res[0]+" Require: "+res[1]+" Available: "+str(amount)+"\n")
				break
		
		return ok
	
	def ApplyEffect(self, agent, room, effectType, amount, set = False, autoRoom = True):
		affectedRoom = room
		generalRoom = Global.g_myHouse.FindGeneralRoomForResource(effectType)
		if autoRoom and not room.CheckResource(effectType, amount):
			Global.Logger.LogDebug("Search general room\n")
			if generalRoom != None:
				Global.Logger.LogDebug("General room found "+generalRoom.m_name+"\n")
				affectedRoom = generalRoom
		
		Global.Logger.LogDebug("Applyeffect room "+affectedRoom.m_name+" "+str(effectType)+" "+str(amount)+"\n")
		# self.Log("Applyeffect room "+affectedRoom.m_name+" "+str(effectType)+" "+str(amount)+"\n")
		Global.Logger.LogDebug("Before "+str(affectedRoom.m_resource[effectType][0])+"\n")
		
		if set:
			affectedRoom.m_resource[effectType][0] = amount
			agent.Log("Apply effect "+effectType+" at "+affectedRoom.m_name+" set "+str(amount)+"\n")
		else:
			if amount < 0 and affectedRoom.m_resource[effectType][0] < abs(amount) and affectedRoom != generalRoom:
				generalRoom.m_resource[effectType][0] += amount
				agent.Log("Apply effect "+effectType+" at "+generalRoom.m_name+" change "+str(amount)+"\n")
			else:
				affectedRoom.m_resource[effectType][0] += amount
				agent.Log("Apply effect "+effectType+" at "+affectedRoom.m_name+" change "+str(amount)+"\n")
		
		Global.Logger.LogDebug("After "+str(affectedRoom.m_resource[effectType][0])+"\n")
		
		if (effectType == "Water" or effectType == "Gas") and autoRoom:
			if effectType == "Water":
				usage = [Common.ENERGY_TYPE_WATER, agent.m_role, self.m_ID, room.m_name, Global.g_timer.m_time, amount]
				agent.PutActTableLogValue(amount, Common.ACT_TABLE_LOG_HR_WATER_START + len(self.m_waterLog), force = True)
				self.m_waterLog.append(amount)
			else:
				usage = [Common.ENERGY_TYPE_GAS, agent.m_role, self.m_ID, Global.g_timer.m_time, amount]
				agent.PutActTableLogValue(self.m_duration, Common.ACT_TABLE_LOG_HR_GAS_START, force = True)
				agent.PutActTableLogValue(amount, Common.ACT_TABLE_LOG_HR_GAS_START + 1, force = True)
			Global.g_myHouse.RegisterEnergyUsage(usage)
	
	def GetInteractAgent(self):
		interactAgent = None
		Global.Logger.LogDebug("GetInteractAgent - Act "+self.m_ID+" "+str(self.m_interactAgent)+"\n")
		for iAgent in self.m_interactAgent:
			interactAgent = next((agent for agent in Agent.Agent.agentList if (agent.m_role == iAgent)), None)
			if interactAgent != None:
				break
		Global.Logger.LogDebug("Final interactAgent "+str(interactAgent)+"\n")
		return interactAgent
	
def LoadMultiAgent():
	multiAgentFile = Agent.resPath+"multi_agent.csv"
	with open(multiAgentFile) as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			if row[Common.TABLE_ACTIVITY_ID] == "ID":
				continue
			Activity.s_multiAgent[row[0]] = row[1] == "1"