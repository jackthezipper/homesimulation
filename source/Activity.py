import csv
import os
import re

import Common
import Timer
import BioProperty3
import Config
import Global

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
			Global.Logger.LogDebug("loading activity "+activityID+"\n");
			activityData = []
			activityData.append(row[Common.TABLE_ACTIVITY_DESC])
			bioEffectRun = []
			for i in range(Common.TABLE_ACTIVITY_BIO_EFFECT_RUN_START, Common.TABLE_ACTIVITY_EMO_EFFECT_RUN):
				bioEffectRun.append(1.0 if row[i] == "" else float(row[i]))
			activityData.append(bioEffectRun)
			Global.Logger.LogDebug("loading activity bio eff "+str(bioEffectRun)+"\n");
			activityData.append(float(row[Common.TABLE_ACTIVITY_EMO_EFFECT_RUN]))
			Global.Logger.LogDebug("loading activity emo eff "+row[Common.TABLE_ACTIVITY_EMO_EFFECT_RUN]+"\n");
			
			bioEffectSuspend = []
			for i in range(Common.TABLE_ACTIVITY_BIO_EFFECT_SUSPEND_START, Common.TABLE_ACTIVITY_EMO_EFFECT_SUSPEND):
				bioEffectSuspend.append(1.0 if row[i] == "" else float(row[i]))
			activityData.append(bioEffectSuspend)
			activityData.append(float(row[Common.TABLE_ACTIVITY_EMO_EFFECT_SUSPEND]))
			
			duration = -1
			if(row[Common.TABLE_ACTIVITY_DURATION]) != "-":
				match = re.match(r'(\d+):(\d+)',row[Common.TABLE_ACTIVITY_DURATION])
				duration = int(match.group(1))*Timer.MINUTE_IN_HOUR + int(match.group(2))
			Global.Logger.LogDebug("loading activity dur "+row[Common.TABLE_ACTIVITY_DURATION]+"\n");
			
			startTime = -1
			match = re.match(r'(\d+):(\d+)', row[Common.TABLE_ACTIVITY_START])
			if match != None:
				startTime = int(match.group(1))*Timer.MINUTE_IN_HOUR + int(match.group(2))
			
			bioStandard = []
			for i in range(Common.TABLE_ACTIVITY_BIO_STD_START, Common.TABLE_ACTIVITY_EMO_STD):
				bioStandard.append(0.0 if row[i] == "" else float(row[i]))
			Global.Logger.LogDebug("loading activity biostd "+str(bioStandard)+"\n");
			
			planProperty = []
			for i in range(Common.TABLE_ACTIVITY_PLAN_START, Common.TABLE_ACTIVITY_ROUTINE):
				planProperty.append(0.0 if row[i] == "" else float(row[i]))
			
			routine = []
			match = re.match(r'(\d+)\|(.+)',row[Common.TABLE_ACTIVITY_ROUTINE])
			if match != None:
				# print(row[Common.TABLE_ACTIVITY_ROUTINE])
				routine.append(int(match.group(1)))
				# print(match.group(1))
				rTimeStr = match.group(2).split(";")
				rTime = []
				for str in rTimeStr:
					rTime.append(int(str))
				routine.append(rTime)
			
			prequisite = []
			if row[Common.TABLE_ACTIVITY_PREQUISITE] != "-":
				prequisite = row[Common.TABLE_ACTIVITY_PREQUISITE].split(";")
			
			# print(row[Common.TABLE_ACTIVITY_AUTO] +"-"+row[Common.TABLE_ACTIVITY_REPEAT]+"-"+row[Common.TABLE_ACTIVITY_PRIORITY])
			activity = Activity(row[Common.TABLE_ACTIVITY_ID], row[Common.TABLE_ACTIVITY_DESC], int(row[Common.TABLE_ACTIVITY_AUTO]), duration, int(row[Common.TABLE_ACTIVITY_REPEAT]), (row[Common.TABLE_ACTIVITY_BIOACTIVITY] == "1"), [bioEffectRun, bioEffectSuspend], [float(row[Common.TABLE_ACTIVITY_EMO_EFFECT_RUN]), float(row[Common.TABLE_ACTIVITY_EMO_EFFECT_SUSPEND])], startTime, int(row[Common.TABLE_ACTIVITY_PRIORITY]), bioStandard, float(row[Common.TABLE_ACTIVITY_EMO_STD]), float(row[Common.TABLE_ACTIVITY_PHY_STD]), planProperty, routine, prequisite, (int(row[Common.TABLE_ACTIVITY_OUTDOOR]) == 1))
			activityList[activityID] = activity
	
	with open(matrixFile) as csvfile:
		reader = csv.reader(csvfile)
		idList = None
		for row in reader:
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

SUSPEND_TIME = [0, 6, 12, 24, 168]
class Activity:
	def __init__(self, ID, description, auto, duration, maxRepeat, isBioActivity, bioEffect, emotionalEffect, startTime, priority, bioStandard, emotionalStandard, phyStandard, planProperty, routine, prequisite, outdoor):
		self.m_ID = ID
		self.m_duration = 5 if auto else duration
		self.m_runningTime = 0
		self.m_isBioActivity = isBioActivity
		self.m_bioEffect = bioEffect
		self.m_emotionalEffect = emotionalEffect
		self.m_startTime = startTime
		self.m_description = description
		self.m_status = Common.ACT_STATUS_NONE
		self.m_forceStop = False
		self.m_priority = priority
		self.m_bioStandard = bioStandard
		self.m_emotionalStandard = emotionalStandard
		self.m_physicalStandard = phyStandard
		self.m_planProperty = planProperty
		self.m_score = 0
		self.m_emotionalScore = 0
		self.m_planScore = 0
		self.m_isIncidental = False
		self.m_remainingIncidentalTime = 0
		self.m_rangeDuration = 0
		self.m_alreadyDoIt = False
		self.m_alreadyDoItYesterday = False
		self.m_maxRepeat = maxRepeat
		self.m_repeatCount = 0
		self.m_routine = routine
		self.m_auto = auto
		self.m_prequisite = prequisite
		self.m_quota = 0
		self.m_matrix = {}
		self.m_timeScore = 5
		self.m_outdoor = outdoor
	
	def GetBioEffect(self, property):
		return self.m_bioEffect[EFFECT_RUN if self.m_status == Common.ACT_STATUS_RUN else EFFECT_SUSPEND][BioProperty3.BIOPROPERTY[property]] if self.m_status != Common.ACT_STATUS_NONE else 0
	
	def GetEmotionalEffect(self):
		return self.m_emotionalEffect[EFFECT_RUN if self.m_status == Common.ACT_STATUS_RUN else EFFECT_SUSPEND]
	
	def Update(self):
		if self.IsRunning():
			# print(self.m_ID+" udd me")
			self.m_runningTime += 1
		if self.m_isIncidental:
			if self.m_remainingIncidentalTime > 0:
				self.m_remainingIncidentalTime -= 1
			if self.m_rangeDuration > 0:
				self.m_rangeDuration -= 1
			else:
				self.m_isIncidental = False
				
		if Global.g_timer.GetHour() == 0 and Global.g_timer.GetMinute() == 0:
			if Global.g_timer.GetDay() % self.m_routine[0] == 0:
				self.m_quota = 0
				if self.m_ID == "A74" or self.m_ID == "A72":
					print(self.m_ID+" do "+str(self.m_alreadyDoItYesterday))
				if not self.IsRunning():
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
	
	def Stop(self):
		self.m_status = Common.ACT_STATUS_NONE
		self.m_runningTime = 0
		self.m_forceStop = False
		if not self.m_isBioActivity:
			self.m_repeatCount +=1
		self.m_alreadyDoIt = True
		# pass

	def GetDescription(self):
		return self.m_description
	
	def GoTo(self):
		self.m_status = Common.ACT_STATUS_GOTO
	
	def Suspend(self):
		self.m_status = Common.ACT_STATUS_SUSPEND
	
	def Pause(self):
		self.m_status = Common.ACT_STATUS_PAUSED
	
	def Resume(self):
		self.m_status = Common.ACT_STATUS_RUN
	
	def CanStart(self, agent):
		if self.m_isIncidental:
			print(self.m_ID + " is incidental remaining "+str(self.m_remainingIncidentalTime)+" range "+str(self.m_rangeDuration))
		Global.Logger.LogDebug("time "+str(Global.g_timer.GetHour())+" sti "+str(self.m_startTime)+" do "+str(self.m_alreadyDoIt)+" ins "+str(((Global.g_timer.GetHour() - self.m_startTime) % Timer.HOUR_IN_DAY))+"\n")
		if self.m_alreadyDoIt and not self.m_isBioActivity:
			return False
		
		prequisiteDone = len(self.m_prequisite) == 0
		for prequisite in self.m_prequisite:
			# print("prekoka "+prequisite)
			prequisiteDone |= agent.GetActivityById(prequisite).m_alreadyDoIt
			if self.m_ID == "A75" or self.m_ID == "A73":
				prequisiteDone |= agent.GetActivityById(prequisite).m_alreadyDoItYesterday
			
		if not prequisiteDone:
			# print("canstart fail prequisite")
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
			# print("canstart fail routine")
			return False
		
		if self.m_isIncidental:
			# print("canstart fail incidental")
			return False
		
		return True
	
	def IsRunning(self):
		return self.m_status == Common.ACT_STATUS_RUN
	
	def SetToIncidental(self):
		self.m_isIncidental = True
		self.m_remainingIncidentalTime = SUSPEND_TIME[self.m_priority - 1] * Timer.MINUTE_IN_HOUR
		self.m_rangeDuration = ((3 + SUSPEND_TIME[self.m_priority - 1]) * Timer.MINUTE_IN_HOUR) - self.m_duration
	
	def GetTargetRoom(self):
		if self.m_targetRoom == -1:
			return "None"
		return self.m_rooms[self.m_targetRoom]
	
	def NextTargetRoom(self):
		if self.m_targetRoom == 0:
			self.m_targetRoom = 1
		else:
			self.m_targetRoom = -1