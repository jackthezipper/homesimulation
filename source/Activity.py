import csv
import os
import re

import Common
import Timer
import BioProperty3
import Config

def GenerateActivity(dbFile):
	# sourceFilePath	= os.path.dirname(os.path.abspath(__file__))
	# inputFilePath	= sourceFilePath[0:sourceFilePath.rfind('\\')+1]+"input_file\\"+dbFile
	activityList = {}
	
	with open(dbFile) as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			if row[Common.TABLE_ACTIVITY_ID] == "ID":
				continue
			activityID = row[Common.TABLE_ACTIVITY_ID]
			activityData = []
			activityData.append(row[Common.TABLE_ACTIVITY_DESC])
			bioEffectRun = []
			for i in range(Common.TABLE_ACTIVITY_BIO_EFFECT_RUN_START, Common.TABLE_ACTIVITY_EMO_EFFECT_RUN):
				bioEffectRun.append(1.0 if row[i] == "" else float(row[i]))
			activityData.append(bioEffectRun)
			activityData.append(float(row[Common.TABLE_ACTIVITY_EMO_EFFECT_RUN]))
			
			bioEffectSuspend = []
			for i in range(Common.TABLE_ACTIVITY_BIO_EFFECT_SUSPEND_START, Common.TABLE_ACTIVITY_EMO_EFFECT_SUSPEND):
				bioEffectSuspend.append(1.0 if row[i] == "" else float(row[i]))
			activityData.append(bioEffectSuspend)
			activityData.append(float(row[Common.TABLE_ACTIVITY_EMO_EFFECT_SUSPEND]))
			
			duration = -1
			if(row[Common.TABLE_ACTIVITY_DURATION]) != "-":
				duration = int(row[Common.TABLE_ACTIVITY_DURATION])
			
			startTime = -1
			match = re.match(r'(\d+):00', row[Common.TABLE_ACTIVITY_START])
			if match != None:
				startTime = int(match.group(1))
			
			bioStandard = []
			for i in range(Common.TABLE_ACTIVITY_BIO_STD_START, Common.TABLE_ACTIVITY_EMO_STD):
				bioStandard.append(0.0 if row[i] == "" else float(row[i]))
			
			planProperty = []
			for i in range(Common.TABLE_ACTIVITY_PLAN_START, Common.TABLE_ACTIVITY_ROOMS):
				planProperty.append(0.0 if row[i] == "" else float(row[i]))
			
			rooms = [row[Common.TABLE_ACTIVITY_ROOMS], row[Common.TABLE_ACTIVITY_ROOMS + 1]]
			
			activity = Activity(row[Common.TABLE_ACTIVITY_ID], row[Common.TABLE_ACTIVITY_DESC], duration, (row[Common.TABLE_ACTIVITY_BIOACTIVITY] == "1"), [bioEffectRun, bioEffectSuspend], [float(row[Common.TABLE_ACTIVITY_EMO_EFFECT_RUN]), float(row[Common.TABLE_ACTIVITY_EMO_EFFECT_SUSPEND])], startTime, int(row[Common.TABLE_ACTIVITY_PRIORITY]), bioStandard, float(row[Common.TABLE_ACTIVITY_EMO_STD]), float(row[Common.TABLE_ACTIVITY_PHY_STD]), planProperty, rooms)
			activityList[activityID] = activity
	
	return activityList


EFFECT_RUN		= 0
EFFECT_SUSPEND	= EFFECT_RUN + 1

SUSPEND_TIME = [0, 6, 12, 24, 168]
class Activity:
	def __init__(self, ID, description, duration, isBioActivity, bioEffect, emotionalEffect, startTime, priority, bioStandard, emotionalStandard, phyStandard, planProperty, rooms):
		self.m_ID = ID
		self.m_duration = duration
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
		self.m_rooms = rooms
		self.m_targetRoom = 0
	
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
		if self.m_alreadyDoIt:
			if ((self.m_startTime - Timer.GetInstance().GetHour()) % Timer.HOUR_IN_DAY) > 3:
				print("reset dodol "+self.m_ID)
				self.m_alreadyDoIt = False
	
	def Start(self, runTime = 0):
		print("Starting activity "+self.m_ID)
		self.m_status = Common.ACT_STATUS_RUN
	
	def IsDone(self):
		# print("check done "+self.m_ID+" "+str(self.m_duration)+" "+str(self.m_forceStop))
		return (self.m_duration != -1 and (self.m_runningTime >= self.m_duration)) or self.m_forceStop
	
	def ForceStop(self):
		self.m_forceStop = True
		if not self.m_isBioActivity:
			self.m_alreadyDoIt = True
	
	def Stop(self):
		self.m_status = Common.ACT_STATUS_NONE
		self.m_runningTime = 0
		self.m_forceStop = False
		if not self.m_isBioActivity:
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
	
	def CanStart(self):
		if self.m_isIncidental:
			print(self.m_ID + " is incidental remaining "+str(self.m_remainingIncidentalTime)+" range "+str(self.m_rangeDuration))
		return self.m_startTime == -1 or ((not self.m_alreadyDoIt) and (not self.m_isIncidental) and ((self.m_startTime - Timer.GetInstance().GetHour()) % Timer.HOUR_IN_DAY) <= 3) or (self.m_isIncidental and self.m_remainingIncidentalTime <= 0 and self.m_rangeDuration > 0)
	
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