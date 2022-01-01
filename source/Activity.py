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

def GenerateActivity(dbFile, matrixFile):
	# sourceFilePath	= os.path.dirname(os.path.abspath(__file__))
	# inputFilePath	= sourceFilePath[0:sourceFilePath.rfind('\\')+1]+"input_file\\"+dbFile
	activityList = {}
	
	with open(dbFile) as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			if row[Common.TABLE_ACTIVITY_ID] == "ID":
				continue
			activityID = row[Common.TABLE_ACTIVITY_ID]
			# # Global.Logger.LogDebug("loading activity "+activityID+"\n");
			# bioEffectRun = []
			# # bioEffectSuspend = []
			# bioStandard = []
			# for i in range(Common.TABLE_ACTIVITY_BIO_EFFECT_START, Common.TABLE_ACTIVITY_EMO_EFFECT):
				# effStr = row[i].split(";")
				# bioEffectRun.append(float(effStr[Common.ACT_EFFECT_RUN]))
				# # bioEffectSuspend.append(float(effStr[Common.ACT_EFFECT_SUSPEND]))
				# bioStandard.append(float(effStr[Common.ACT_EFFECT_STD]))
			
			# emoEffect = row[Common.TABLE_ACTIVITY_EMO_EFFECT].split(";")
			# # Global.Logger.LogDebug("loading activity bio eff "+str(bioEffectRun)+"\n")
			# # Global.Logger.LogDebug("loading activity emo eff "+emoEffect[Common.ACT_EFFECT_RUN]+"\n")
			
			# duration = -1
			# if(row[Common.TABLE_ACTIVITY_DURATION]) != "-":
				# match = re.match(r'(\d+):(\d+)',row[Common.TABLE_ACTIVITY_DURATION])
				# duration = int(match.group(1))*Timer.MINUTE_IN_HOUR + int(match.group(2))
			# # Global.Logger.LogDebug("loading activity dur "+row[Common.TABLE_ACTIVITY_DURATION]+"\n")
			
			# startTime = -1
			# match = re.match(r'(\d+):(\d+)', row[Common.TABLE_ACTIVITY_START])
			# if match != None:
				# startTime = int(match.group(1))*Timer.MINUTE_IN_HOUR + int(match.group(2))
			
			# # Global.Logger.LogDebug("loading activity biostd "+str(bioStandard)+"\n");
			
			# if (row[Common.TABLE_ACTIVITY_ROOM] == "-"):
				# rooms = []
			# else:
				# rooms = row[Common.TABLE_ACTIVITY_ROOM].split("|")
			
			# planProperty = []
			# for i in range(Common.TABLE_ACTIVITY_PLAN_START, Common.TABLE_ACTIVITY_ROUTINE):
				# planProperty.append(0.0 if row[i] == "" else float(row[i]))
			
			# routine = []
			# match = re.match(r'(\d+)\|(.+)',row[Common.TABLE_ACTIVITY_ROUTINE])
			# if match != None:
				# # print(row[Common.TABLE_ACTIVITY_ROUTINE])
				# routine.append(int(match.group(1)))
				# # print(match.group(1))
				# rTimeStr = match.group(2).split(";")
				# rTime = []
				# for tstr in rTimeStr:
					# rTime.append(int(tstr))
				# routine.append(rTime)
			
			# prequisite = []
			# if row[Common.TABLE_ACTIVITY_PREQUISITE] != "-":
				# prequisite = row[Common.TABLE_ACTIVITY_PREQUISITE].split(";")
			
			# if (row[Common.TABLE_ACTIVITY_ELIMINATE_ACTIVITY] == "-"):
				# eliminate = []
			# else:
				# eliminate = row[Common.TABLE_ACTIVITY_ELIMINATE_ACTIVITY].split(";")
			
			# status = row[Common.TABLE_ACTIVITY_STATUS].split("|")
			# light = row[Common.TABLE_ACTIVITY_LIGHTTHRESHOLD].split("|")
			# temperature = row[Common.TABLE_ACTIVITY_TEMPERATURE].split("|")
			
			# terms = [light, status, temperature]
			
			# tRes = row[Common.TABLE_ACTIVITY_RESOURCE].split("|")
			
			# resource = []
			# for res in tRes:
				# resource.append(res.split(";"))
			
			# # print(row[Common.TABLE_ACTIVITY_AUTO] +"-"+row[Common.TABLE_ACTIVITY_REPEAT]+"-"+row[Common.TABLE_ACTIVITY_PRIORITY])
			# effectList = row[Common.TABLE_ACTIVITY_EFFECT].split("|")
			# effect = []
			# for efL in effectList:
				# if efL == "-":
					# effectPerRoomList = []
				# else:
					# effectPerRoomList = efL.split(";")
				# roomEf = []
				# for ef in effectPerRoomList:
					# efSingle = ef.split(":")
					# roomEf.append(efSingle)
				# effect.append(roomEf)
			
			# activity = Activity(row[Common.TABLE_ACTIVITY_ID], row[Common.TABLE_ACTIVITY_DESC], int(row[Common.TABLE_ACTIVITY_AUTO]), duration, int(row[Common.TABLE_ACTIVITY_REPEAT]), (row[Common.TABLE_ACTIVITY_BIOACTIVITY] == "1"), [bioEffectRun, bioEffectSuspend], [float(emoEffect[Common.ACT_EFFECT_RUN]), float(emoEffect[Common.EMO_EFFECT_SUSPEND])], startTime, int(row[Common.TABLE_ACTIVITY_PRIORITY]), bioStandard, float(emoEffect[Common.ACT_EFFECT_STD]), float(row[Common.TABLE_ACTIVITY_PHY_STD]), planProperty, rooms, routine, prequisite, row[Common.TABLE_ACTIVITY_INTERACT_AGENT], (int(row[Common.TABLE_ACTIVITY_OUTDOOR]) == 1), terms, row[Common.TABLE_ACTIVITY_DEVICE].split("|"), row[Common.TABLE_ACTIVITY_NEXT_ACTIVITY], eliminate, row[Common.TABLE_ACTIVITY_SET], resource, effect)
			# activity = Activity(row[Common.TABLE_ACTIVITY_ID], row[Common.TABLE_ACTIVITY_DESC], int(row[Common.TABLE_ACTIVITY_AUTO]), duration, int(row[Common.TABLE_ACTIVITY_REPEAT]), (row[Common.TABLE_ACTIVITY_BIOACTIVITY] == "1"), [bioEffectRun], [float(emoEffect[Common.ACT_EFFECT_RUN]), float(emoEffect[Common.EMO_EFFECT_SUSPEND])], startTime, int(row[Common.TABLE_ACTIVITY_PRIORITY]), bioStandard, float(emoEffect[Common.ACT_EFFECT_STD]), float(row[Common.TABLE_ACTIVITY_PHY_STD]), planProperty, rooms, routine, prequisite, row[Common.TABLE_ACTIVITY_INTERACT_AGENT], (int(row[Common.TABLE_ACTIVITY_OUTDOOR]) == 1), terms, row[Common.TABLE_ACTIVITY_DEVICE].split("|"), row[Common.TABLE_ACTIVITY_NEXT_ACTIVITY], eliminate, row[Common.TABLE_ACTIVITY_SET], resource, effect)
			activity = Activity(row)#[Common.TABLE_ACTIVITY_ID], row[Common.TABLE_ACTIVITY_DESC], int(row[Common.TABLE_ACTIVITY_AUTO]), duration, int(row[Common.TABLE_ACTIVITY_REPEAT]), (row[Common.TABLE_ACTIVITY_BIOACTIVITY] == "1"), [bioEffectRun], [float(emoEffect[Common.ACT_EFFECT_RUN]), float(emoEffect[Common.EMO_EFFECT_SUSPEND])], startTime, int(row[Common.TABLE_ACTIVITY_PRIORITY]), bioStandard, float(emoEffect[Common.ACT_EFFECT_STD]), float(row[Common.TABLE_ACTIVITY_PHY_STD]), planProperty, rooms, routine, prequisite, row[Common.TABLE_ACTIVITY_INTERACT_AGENT], (int(row[Common.TABLE_ACTIVITY_OUTDOOR]) == 1), terms, row[Common.TABLE_ACTIVITY_DEVICE].split("|"), row[Common.TABLE_ACTIVITY_NEXT_ACTIVITY], eliminate, row[Common.TABLE_ACTIVITY_SET], resource, effect)
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
				act = activityList[row[0]]
				idx = 1
				for id in idList:
					act.m_matrix[id] = int(row[idx])
					idx += 1
				# print("kakaro "+act.m_ID)
				# print(act.m_matrix)
	
	return activityList


EFFECT_RUN		= 0
EFFECT_SUSPEND	= EFFECT_RUN + 1

SUSPEND_TIME = [1, 6, 12, 24, 168]
class Activity:
	s_pendingEffect = []
	# def __init__(self, ID, description, auto, duration, maxRepeat, isBioActivity, bioEffect, emotionalEffect, startTime, priority, bioStandard, emotionalStandard, phyStandard, planProperty, rooms, routine, prequisite, interactAgent, outdoor, terms, device, next, eliminate, activitySet, resource, effect):
	def __init__(self, params):
		self.m_ID = params[Common.TABLE_ACTIVITY_ID]
		self.m_auto = int(params[Common.TABLE_ACTIVITY_AUTO]) == 1
		
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

		self.m_targetRoom = 0
		self.m_interactAgent = params[Common.TABLE_ACTIVITY_INTERACT_AGENT]
		self.m_next = params[Common.TABLE_ACTIVITY_NEXT_ACTIVITY]
		
		if (params[Common.TABLE_ACTIVITY_ELIMINATE_ACTIVITY] == "-"):
			self.m_eliminate = []
		else:
			self.m_eliminate = params[Common.TABLE_ACTIVITY_ELIMINATE_ACTIVITY].split(";")

		self.m_activitySet = params[Common.TABLE_ACTIVITY_SET]
		
		self.m_requiredResource = []
		tRes = params[Common.TABLE_ACTIVITY_RESOURCE].split("|")
		for res in tRes:
			self.m_requiredResource.append(res.split(";"))

		self.m_effect = []
		effectList = params[Common.TABLE_ACTIVITY_EFFECT].split("|")
		for efL in effectList:
			if efL == "-":
				effectPerRoomList = []
			else:
				effectPerRoomList = efL.split(";")
			roomEf = []
			for ef in effectPerRoomList:
				efSingle = ef.split(":")
				print efSingle
				efSingle[1] = int(efSingle[1])
				efSingle[2] = float(efSingle[2])
				roomEf.append(efSingle)
			self.m_effect.append(roomEf)
		
		self.m_postActivity = []
		postActivity = params[Common.TABLE_POST_ACTIVITY].split("|")
		for activities in postActivity:
			singleRoomPA = []
			if activities != "-":
				singleRoomPA = activities.split(";")
			self.m_postActivity.append(singleRoomPA)
	
	def GetBioEffect(self, property):
		# return self.m_bioEffect[EFFECT_RUN if self.m_status == Common.ACT_STATUS_RUN else EFFECT_SUSPEND][BioProperty3.BIOPROPERTY[property]] if self.m_status != Common.ACT_STATUS_NONE else 0
		return self.m_bioEffect[EFFECT_RUN][BioProperty3.BIOPROPERTY[property]] if self.m_status != Common.ACT_STATUS_NONE else 0
	
	def GetEmotionalEffect(self):
		return self.m_emotionalEffect[EFFECT_RUN if self.m_status == Common.ACT_STATUS_RUN else EFFECT_SUSPEND]
	
	def Update(self):
		if self.IsRunning():
			# print(self.m_ID+" udd me")
			self.m_runningTime += 1
		if self.m_isIncidental:
			if self.m_remainingIncidentalTime > 0:
				self.m_remainingIncidentalTime -= 1
			# if self.m_rangeDuration > 0:
				# self.m_rangeDuration -= 1
			else:
				self.m_isIncidental = False
				self.m_status == Common.ACT_STATUS_NONE
				
		if Global.g_timer.GetHour() == 0 and Global.g_timer.GetMinute() == 0:
			if Global.g_timer.GetDay() % self.m_routine[0] == 0:
				self.m_quota = 0
				if self.m_ID == "A74" or self.m_ID == "A72":
					print(self.m_ID+" do "+str(self.m_alreadyDoItYesterday))
				if not self.IsRunning():
					Global.Logger.LogDebug("stop9\n")
					self.Stop()
				self.m_alreadyDoItYesterday = self.m_alreadyDoIt
				self.m_alreadyDoIt = False
		# if ((Timer.GetInstance().GetHour() - self.m_startTime) % Timer.HOUR_IN_DAY) > 3:
			# self.m_repeatCount = 0
	
	def Start(self, runTime = 0):
		print("Starting activity "+self.m_ID+" - "+self.m_description)
		self.m_status = Common.ACT_STATUS_RUN
	
	def IsDone(self):
		# print("check done "+self.m_ID+" "+str(self.m_duration)+" "+str(self.m_forceStop))
		return (self.m_duration != -1 and (self.m_runningTime >= self.m_duration)) or self.m_forceStop
	
	def ForceStop(self):
		self.m_forceStop = True
		if not self.m_isBioActivity:
			self.m_repeatCount +=1
		self.m_alreadyDoIt = True
		self.m_targetRoom = 0
	
	def Stop(self):
		self.m_status = Common.ACT_STATUS_NONE
		self.m_runningTime = 0
		self.m_forceStop = False
		if not self.m_isBioActivity:
			self.m_repeatCount +=1
		self.m_alreadyDoIt = True
		self.m_targetRoom = 0
		# pass

	def GetDescription(self):
		return self.m_description
	
	def GoTo(self):
		self.m_status = Common.ACT_STATUS_GOTO
	
	def Suspend(self):
		self.m_status = Common.ACT_STATUS_SUSPEND
		self.m_targetRoom = 0
	
	def Pause(self):
		self.m_status = Common.ACT_STATUS_PAUSED
	
	def Resume(self):
		self.m_status = Common.ACT_STATUS_RUN
	
	def CanStart(self, agent):
		#if self.m_isIncidental:
			#print(self.m_ID + " is incidental remaining "+str(self.m_remainingIncidentalTime)+" range "+str(self.m_rangeDuration))
		# Global.Logger.LogDebug("time "+str(Global.g_timer.GetHour())+" sti "+str(self.m_startTime)+" do "+str(self.m_alreadyDoIt)+" ins "+str(((Global.g_timer.GetHour() - self.m_startTime) % Timer.HOUR_IN_DAY))+"\n")
		if self.m_alreadyDoIt and not self.m_isBioActivity:
			return False
		
		if self.m_ID in agent.m_eliminatedActivity:
			return False
		
		if ((self.m_activitySet != "-") and self.m_activitySet.endswith("C")):
			return False
		
		if (self.m_interactAgent != "-"):
			interactAgent = next((agent for agent in Agent.Agent.agentList if (agent.m_role == self.m_interactAgent)), None)
			if interactAgent == None:
				return False
		
		prequisiteDone = len(self.m_prequisite) == 0
		for prequisite in self.m_prequisite:
			# print("prekoka "+prequisite)
			prequisiteDone |= agent.GetActivityById(prequisite).m_alreadyDoIt
			if self.m_ID == "A03":# or self.m_ID == "A73":
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
				# print("cek routine "+str(routine)+" "+str(self.m_quota)+" "+str(routineTime))
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
		if not self.m_isBioActivity:
			self.m_isIncidental = True
			self.m_remainingIncidentalTime = SUSPEND_TIME[self.m_priority] * Timer.MINUTE_IN_HOUR
			#self.m_rangeDuration = ((3 + SUSPEND_TIME[self.m_priority]) * Timer.MINUTE_IN_HOUR) - self.m_duration
	
	def GetTargetRoom(self):
		if len(self.m_rooms) == 0:
			return "Agent"
		if (self.m_targetRoom == -1) or (self.m_rooms[self.m_targetRoom] == "NONE"):
			return "None"
		return self.m_rooms[self.m_targetRoom]
	
	def NextTargetRoom(self):
		if self.m_targetRoom == 0:
			self.m_targetRoom = 1
		else:
			self.m_targetRoom = -1
	
	def CheckTerms(self, agent):
		stopPlaces = []
		cancel = False
		
		for i in range(0, Common.TERM_COUNT):
			if (self.m_terms[i][self.m_targetRoom] != "-"):
				if i == Common.TERM_LIGHT:
					lightTerm = self.m_terms[i][self.m_targetRoom].split(";")
					if agent.m_targetRoom.m_light < int(lightTerm[0]):
						if (lightTerm[1] == "CC"):
							cancel |= True
							break;
						else:
							stopPlaces.extend(agent.m_targetRoom.GetLampToTurn())
				elif i == Common.TERM_STATUS:
					cancel |= ((self.m_terms[i][self.m_targetRoom] != "-") and (self.m_will > float(self.m_terms[i][self.m_targetRoom])))
				elif i == Common.TERM_TEMPERATURE:
					if agent.m_targetRoom.m_temperature > float(self.m_terms[i][self.m_targetRoom]):
						hasFan, active, fanObj = agent.m_targetRoom.HasAndActive("Fan")
						if hasFan and (not active):
							stopPlaces.append(fanObj)
						cancel |= hasFan
		
		return cancel, stopPlaces
	
	def CalculateEnvUrgency(self, agent):
		if self.m_urgency == 0:
			# simple number
			return int(self.m_urgencyValue)
		elif self.m_urgency == 1:
			# agent own property
			return (10.0 - ((agent.GetProperty(self.m_urgencyValue)/10.0) * 10.0))
		elif self.m_urgency == 2:
			# negative resource amount
			return (10.0 - (Global.g_myHouse.GetResourceAmount(self.m_urgencyValue)))
		elif self.m_urgency == 3:
			# other agent property
			toCheck = self.m_urgencyValue.split(";")
			amount = 0
			for agt in Agent.Agent.agentList:
				if (agent.m_role != agent.m_role):
					amount += agent.GetProperty(toCheck[0]).GetScore()
			return float(toCheck[1]) * amount
		elif self.m_urgency == 4:
			# property interact agent
			toCheck = self.m_urgencyValue.split(";")
			interactAgent = next((agent for agent in Agent.Agent.agentList if (agent.m_role == self.m_interactAgent)), None)
			return float(toCheck[1]) * interactAgent.GetProperty(toCheck[0])
		elif self.m_urgency == 5:
			# resource amount
			return Global.g_myHouse.GetResourceAmount(self.m_urgencyValue)
		elif self.m_urgency == 6:
			# emotional interact agent
			interactAgent = next((agent for agent in Agent.Agent.agentList if (agent.m_role == self.m_interactAgent)), None)
			return 10 - interactAgent.GetEmotionalFactor()/interactAgent.m_emotionalNormal
		elif self.m_urgency == 7:
			# let there be light
			room = next((rom for rom in Global.g_myHouse.m_rooms if(rom.m_name == self.GetTargetRoom())), None)
			return 10 - room.m_light/10
		elif self.m_urgency == 8:
			# resource amount 2
			return (100 - Global.g_myHouse.GetResourceAmount(self.m_urgencyValue))/10
	
	def CalculateEffects(self, agent):
		for effect in self.m_effect[self.m_targetRoom]:
			Global.Logger.LogDebug("effect "+str(effect)+"\n")
			self.CalculateEffect(agent, effect)
	
	def CalculateEffect(self, agent, effect):
		if effect[0] == "Room":
			# room = next((rom for rom in Global.g_myHouse.m_rooms if rom.m_name == self.m_rooms[self.m_targetRoom]), None)
			if agent.m_currentRoom != None:
				if effect[1] == 0:
					agent.m_currentRoom.m_value += effect[2]
				elif effect[1] == 3:
					agent.m_currentRoom.m_value += (effect[2] * agent.m_currentRoom.m_value)
				elif effect[1] == 5:
					agent.m_currentRoom.m_value = effect[2]
		else:
			effectValue = 0
			if effect[1] == 0:
				self.ApplyEffect(agent.m_currentRoom, effect[0], effect[2])
			elif effect[1] == 1:
				#should find object and calculate usage
				usage = effect[2] * self.m_duration
				if agent.m_currentRoom.CheckResource(effect[0], usage):
					self.ApplyEffect(agent.m_currentRoom, effect[0], -usage)
				else:
					object = next(obj for obj in Agent.Agent.s_possibleTarget if obj.m_id == effect[0])
					if self.m_auto:
						object.StartUsage((self.m_realDuration - self.m_duration), self.m_duration)
			elif effect[1] == 2:
				self.ApplyEffect(agent.m_currentRoom, effect[0], (10.0 - (Global.g_myHouse.GetResourceAmount(effect[0]))))
			elif effect[1] == 3:
				self.ApplyEffect(agent.m_currentRoom, effect[0], (effect[2] * agent.m_currentRoom.m_resource[effect[0]]))
			elif effect[1] == 4:
				s_pendingEffect.append([agent.m_currentRoom, effect[0], effect[2], (self.m_realDuration - self.m_duration)])
			elif effect[1] == 5:
				self.ApplyEffect(agent.m_currentRoom, effect[0], effect[2], True)
			elif effect[1] == 6:
				if agent.m_currentRoom.m_resource[effect[0]] <= 0:
					usage = effect[2] * self.m_duration * 60
					self.ApplyEffect(agent.m_currentRoom, effect[0], -usage, autoRoom = False)
					generalRoom = Global.g_myHouse.FindGeneralRoomForResource(effect[0])
					if generalRoom != None:
						self.ApplyEffect(generalRoom, effect[0], usage, autoRoom = False)
			elif effect[1] == 7:
				if effect[2] == 0:
					self.ApplyEffect(agent.m_currentRoom, effect[0], self.m_prevResValue)
				else:
					s_pendingEffect.append([agent.m_currentRoom, effect[0], self.m_prevResValue, (effect[2] - self.m_duration)])
			elif effect[1] == 8:
				s_savedEffect = agent.m_currentRoom.m_resource[effect[0]][0]
				self.ApplyEffect(agent.m_currentRoom, effect[0], effect[2], True)
			elif effect[1] == 9:
				self.ApplyEffect(agent.m_currentRoom, effect[0], s_savedEffect, True)
			elif effect[1] == 10:
				self.ApplyEffect(agent.m_currentRoom, effect[0], (-agent.GetProperty("Thirst").m_currentEffectScore * self.m_duration))
			
			if effect[1] != 1:
				room = agent.m_currentRoom if effect in agent.m_currentRoom.m_resource.keys() else Global.g_myHouse.FindGeneralRoomForResource(effect[0])
				self.m_prevResValue = 0 if room == None else room.m_resource[effect[0]][0]
	
	def CheckResource(self, room):
		ok = room.CheckResource(self.m_requiredResource[self.m_targetRoom][0],int(self.m_requiredResource[self.m_targetRoom][1]))
		if not ok:
			generalRoom = Global.g_myHouse.FindGeneralRoomForResource(self.m_requiredResource[self.m_targetRoom][0])#,int(self.m_requiredResource[self.m_targetRoom][1]))
			if generalRoom != None:
				ok = generalRoom.CheckResource(self.m_requiredResource[self.m_targetRoom][0],int(self.m_requiredResource[self.m_targetRoom][1]))
		
		return ok
	
	def ApplyEffect(self, room, effectType, amount, set = False, autoRoom = True):
		affectedRoom = room
		if autoRoom and not room.CheckResource(effectType, amount):
			Global.Logger.LogDebug("Search general room\n")
			generalRoom = Global.g_myHouse.FindGeneralRoomForResource(effectType)
			if generalRoom != None:
				Global.Logger.LogDebug("General room found "+generalRoom.m_name+"\n")
				affectedRoom = generalRoom
		
		Global.Logger.LogDebug("Applyeffect room "+affectedRoom.m_name+" "+str(effectType)+" "+str(amount)+"\n")
		Global.Logger.LogDebug("Before "+str(affectedRoom.m_resource[effectType][0])+"\n")
		
		if set:
			affectedRoom.m_resource[effectType][0] = amount
		else:
			affectedRoom.m_resource[effectType][0] += amount
		
		Global.Logger.LogDebug("After "+str(affectedRoom.m_resource[effectType][0])+"\n")
		
		if (effectType == "Water" or effectType == "Gas") and autoRoom:
			if effectType == "Water":
				usage = [Common.ENERGY_TYPE_WATER, self.m_ID, room.m_name, Global.g_timer.m_time, amount]
			else:
				usage = [Common.ENERGY_TYPE_GAS, self.m_ID, Global.g_timer.m_time, amount]
			Global.g_myHouse.RegisterEnergyUsage(usage)
	