#import from python lib
import random
import math
import sys
import os
import re

#import custom file
import Target
import PathFinding
import Schedule
Schedule = reload(Schedule)
import csv
import Activity
Activity = reload(Activity)
import CommonEnum
import Term
Term = reload(Term)
import Global
Global = reload(Global)
import EntryPoint
import Config
import Common
import Timer
import BioProperty3
BioProperty3 = reload(BioProperty3)

from Rhino.Geometry import Point3d, Vector3f,Vector3d,Line,Polyline
import rhinoscriptsyntax as rs

import scriptcontext as sc
import Rhino.Geometry

import time

PathFinding = reload(PathFinding)

#agent state
STATE_IDLE			= 0
STATE_PRE_MOVE		= STATE_IDLE + 1
STATE_MOVE			= STATE_PRE_MOVE + 1
STATE_WAIT			= STATE_MOVE + 1
STATE_CHECK_PA		= STATE_WAIT + 1
STATE_PREMOVE_PA	= STATE_CHECK_PA + 1
STATE_MOVE_PA		= STATE_PREMOVE_PA + 1

#target type
TARGET_NONE		= -1
TARGET_ROOM		= 0
TARGET_POINT	= TARGET_ROOM + 1

TERM_ENVI		= 0
TERM_ROOM		= TERM_ENVI + 1
TERM_COUNT		= TERM_ROOM + 1

AGENT_PREACT_ID		= 0
AGENT_PREACT_OBJ	= AGENT_PREACT_ID + 1
AGENT_PREACT_LOC	= AGENT_PREACT_OBJ + 1

errPause = False

#30 min -> 15 sec
TIMECONVERSION = 2 #to multiply dt
TIMEFACTOR = 1000 #to multiply waitTime

#find resources path
# sourceFilePath	= ghenv.Component.OnPingDocument().FilePath
sourceFilePath	= os.path.dirname(os.path.abspath(__file__))
sourceDirPath	= sourceFilePath[0:sourceFilePath.rfind('\\')+1]
resPath			= sourceDirPath+"res\\"+sc.sticky["MapName"]+"\\"

def Fmt(val):
	return "{:.3f}".format(float(val))

PROPERTY_CODE = ["Hu","Di","Th","En","Ex","Sl","De","Ur"]

#---------------------------------------------------------------------------------------
class Agent:
	s_possibleTarget = []
	s_entryPointList = []
	hasErr = False
	agentList = []
	s_scaleSpeed = 8.0
	# s_debugStr = ""
	# s_debugActive = True
	
	# @staticmethod
	# def LogDebug(debugLog):
		# if Agent.s_debugActive:
			# Agent.s_debugStr += debugLog
	
	# @staticmethod
	# def ResetDebug():
		# Agent.s_debugStr = ""
	
	# @staticmethod
	# def DumpDebug():
		# if not Agent.s_debugActive:
			# return
		# dFile = open(resPath+"dmp.txt","a+")
		# dFile.write(Agent.s_debugStr)
		# dFile.close()
		# Agent.s_debugStr = ""
	
	def __init__(self,position,m_targetPoint,index,role = "ayah",state = STATE_IDLE):
		self.pos = position
		self.m_targetPoint = m_targetPoint
		self.entryPoint = None
		self.oldEntryPoint = None
		self.m_state = state
		self.initialPos = position
		self.hasNewTarget = False
		self.waitTime = (Schedule.SCHEDULE[index][0][1] * TIMEFACTOR)
		self.myPath = None
		self.m_pathIndex = 0
		self.m_target = None
		self.moveDir = Vector3f(0,1,0)
		self.pathCalculated = False
		self.m_myIndex = index
		self.m_blockedBy = -1
		self.blockCounter = 0
		self.m_hasWait = False
		self.targetIndex = 0
		self.initialized = False
		self.m_canGetNewTarget = True
		self.boundArea = None
		self.curveBoundArea = None
		self.diagonalBound = 0
		
		self.objectList = []
		
		self.m_speedFactor = 0.15
		self.m_myFloorIndex = 0
		self.needStair = False
		
		self.m_active = False
		self.m_role = role
		
		
		self.m_bioProperty = []
		self.m_switchBioLoader = {
			"Energy" : self.LoadEnergyProperty,
			"Hunger" : self.LoadHungerProperty,
			"Dirty" : self.LoadDirtyProperty,
			"Thirst" : self.LoadThirstProperty,
			"Exhausted" : self.LoadTiredProperty,
			"Sleepy" : self.LoadSleepyProperty,
			"Defecate" : self.LoadDefecateProperty,
			"Urinate" : self.LoadUrinateProperty,
		}
		self.m_emotionalFactor = 0.417
		self.m_emotionalNormal = 0.417
		self.m_emotionalTotal = 1 + (self.m_emotionalFactor / (self.m_emotionalNormal * 100))
		self.m_emotionalTimeEffect = self.m_emotionalNormal
		self.m_badMoodRate = 0.002
		self.m_goodMoodRate = 0.003
		self.m_currentAbility = 0
		dbFile = resPath+self.m_role+"\\"+Config.ACTIVITY_DB_FILE
		matrixFile = resPath+self.m_role+"\\"+Config.ACTIVITY_MATRIX_FILE
		self.m_activityList = Activity.GenerateActivity(dbFile, matrixFile	)
		self.m_currentActivity = None
		self.m_currentRoom = None
		self.LoadBioProperty(Config.IC_FILE_NAME)
		self.m_bioActivityToTrigger = "" if self.m_currentActivity == None else self.m_currentActivity.m_ID
		self.m_wasAsleep = True
		self.m_pendingActivity = None
		self.m_lastActivity = None
		self.m_timeAdjuster = Timer.TIMEFACTOR / Timer.TIMECONVERSION
		self.m_elapsedAdjustTimer = self.m_timeAdjuster
		
		self.m_targetRoom = None
		self.m_targetType = TARGET_NONE
		self.m_eliminatedActivity = []
		self.m_postActivityStops = []
		self.m_prevActivity = None
		self.m_following = False
		self.m_followedAgent = None
		self.m_roomCoordIndex = -1
		self.ConvertStandardToPoint()
		
	def ConvertStandardToPoint(self):
		hungerBase = self.GetProperty("Hunger").m_rate[Common.RATE_BASE]
		energyBase = self.GetProperty("Energy").m_rate[Common.RATE_BASE]
		for act in self.m_activityList:
			self.m_activityList[act].m_bioStandard[0] /= (hungerBase / 10)
			self.m_activityList[act].m_bioStandard[3] /= (energyBase / 10)
	
	def LoadBioProperty(self, filename):
		for room in Global.g_myHouse.m_rooms:
			if room.IsInRoom(self.pos):
				self.m_currentRoom = room
				break
		sourceFilePath	= os.path.dirname(os.path.abspath(__file__))
		inputFilePath = resPath+self.m_role+"\\"+filename
		# inputFilePath	= sourceFilePath[0:sourceFilePath.rfind('\\')+1]+"input_file\\"+filename
		with open(inputFilePath) as csvfile:
			reader = csv.reader(csvfile)
			for row in reader:
				if row[Common.IC_PROPERTY] == "Current Activity":
					self.m_currentActivity = self.GetActivityById(row[Common.IC_VALUE])
					self.m_currentActivity.Start()
					self.m_currentRoom.m_countAgent += 1
					continue
				if row[Common.IC_PROPERTY] == "Ability":
					self.m_currentAbility = float(row[Common.IC_VALUE])
					continue
				if row[Common.IC_PROPERTY] == "Weight":
					self.m_weight = float(row[Common.IC_VALUE])
					continue
				if row[Common.IC_PROPERTY] == "EmotionNorm":
					self.m_emotionalNormal = float(row[Common.IC_VALUE])
					continue
				if row[Common.IC_PROPERTY] == "EmotionCurrent":
					self.m_emotionalFactor = float(row[Common.IC_VALUE])
					continue
				if row[Common.IC_PROPERTY] == "RateGood":
					self.m_goodMoodRate = float(row[Common.IC_VALUE])
					continue
				if row[Common.IC_PROPERTY] == "RateBad":
					self.m_badMoodRate = float(row[Common.IC_VALUE])
					continue
				if row[Common.IC_PROPERTY] == "Property":
					continue
				loader = self.m_switchBioLoader.get(row[Common.IC_PROPERTY],self.UnknownLoad)
				self.m_bioProperty.append(loader(row))
		if self.m_currentActivity != None:
			for property in self.m_bioProperty:
				if (self.m_currentActivity.m_ID == property.m_relatedActivityId):
					property.m_relatedActivity = self.m_currentActivity
					break
	
	#------Converter--------------------------------------------------------------------------------------------------------------
	def ConvertToRate(self, line):
		match = re.match(r'(\d+\.?\d*)\|(\d+)\|(-?\d+\.?\d*):(-?\d+\.?\d*)(:(-?\d+\.?\d*))?',line)
		divider = float(match.group(2))
		baseRate = float(match.group(1))
		minuteBaseRate = baseRate / ( divider * Timer.MINUTE_IN_HOUR )
		rate = []
		if len(match.groups()) >= 6 and match.group(6) != None:
			rate = [(minuteBaseRate * float(match.group(3))), (minuteBaseRate * float(match.group(4))), (minuteBaseRate * float(match.group(6))), baseRate, divider]
		else:
			rate = [(minuteBaseRate * float(match.group(3))), (minuteBaseRate * float(match.group(4))), 0, baseRate, divider]
		return rate
	
	def ConvertToEffect(self, line):
		effects = []
		effectList = line.split(";")
		for effectStr in effectList:
			effect = []
			match = re.match(r'(-?\d+\.?\d*):(-?\d+\.?\d*)', effectStr)
			
			effect.append(float(match.group(1)))
			effect.append(float(match.group(2)))
			
			effects.append(effect)
		
		return effects
	
	def ConvertToEffectSingle(self, line):
		effect = []
		match = re.match(r'(-?\d+\.?\d*):(-?\d+\.?\d*)', line)
		
		effect.append(float(match.group(1)))
		effect.append(float(match.group(2)))
		return effect
	
	def ConvertToEffectTimeBased(self, line):
		effects = []
		effectList = line.split(";")
		for effectStr in effectList:
			effect = []
			match = re.match(r'(\d+)(-(\d+))?:(\d+)(-(\d+))?:(.*)', effectStr)
			
			effect.append(int(match.group(1)))
			if match.group(3) != None:
				effect.append(int(match.group(3)))
			else:
				effect.append(int(match.group(1)))
			
			effect.append(float(match.group(4)))
			if match.group(6) != None:
				effect.append(int(match.group(6)))
			else:
				effect.append(int(match.group(4)))
			
			effect.append(float(match.group(7)))
			
			effects.append(effect)
		
		return effects
	
	def ConvertToHabit(self, line):
		habit = [False for i in range(24)]
		if line != "-":
			habitList = line.split(";")
			for habitStr in habitList:
				match = re.match(r'(\d+)(-(\d+))?',habitStr)
				start = int(match.group(1))
				end = start
				if match.group(3) != None:
					end = int(match.group(3))
				habit[start:end + 1] = [True] * (end - start + 1)
		return habit
	
	def ConvertToHabitMulti(self, line):
		habitList = line.split("|")
		habits = []
		for habitStr in habitList:
			habit = self.ConvertToHabit(habitStr)
			habits.append(habit)
		return habits
		
	def ConvertToRule(self, line):
		rule = []
		ruleList = line.split(";")
		
		for ruleStr in ruleList:
			rule.append(float(ruleStr))
		
		return rule
	
	def ConvertToListFloat(self, line):
		customList = line.split(";")
		
		custom = [float(lineStr) for lineStr in customList]
		
		return custom
	#-----------------------------------------------------------------------------------------------------------------------------
	
	#------Bio property Loader----------------------------------------------------------------------------------------------------
	def UnknownLoad(self, row):
		print("Unknown type")
		return None
	
	def LoadHungerProperty(self, row):
		rate = self.ConvertToRate(row[Common.IC_RATE])
		habit = self.ConvertToHabit(row[Common.IC_HABIT])
		threshold = self.ConvertToListFloat(row[Common.IC_EFFECT])
		
		property = BioProperty3.Hunger(self, row[Common.IC_PROPERTY], rate, float(row[Common.IC_CURRENT]), habit, threshold)
		return property
		
	def LoadDirtyProperty(self, row):
		rate = self.ConvertToRate(row[Common.IC_RATE])
		effect = float(row[Common.IC_EFFECT])
		habit = self.ConvertToHabit(row[Common.IC_HABIT])
		
		property = BioProperty3.Dirty(self, row[Common.IC_PROPERTY], rate, float(row[Common.IC_CURRENT]), habit, effect)
		return property
	
	def LoadThirstProperty(self, row):
		rate = self.ConvertToRate(row[Common.IC_RATE])
		effect = self.ConvertToEffect(row[Common.IC_EFFECT])
		habit = self.ConvertToHabit(row[Common.IC_HABIT])
		
		property = BioProperty3.Thirst(self, row[Common.IC_PROPERTY], rate, float(row[Common.IC_CURRENT]), habit, effect)
		return property
	
	def LoadDefecateProperty(self, row):
		habit = self.ConvertToHabit(row[Common.IC_HABIT])
		# rule = self.ConvertToRule(row[Common.IC_EFFECT])
		custom = self.ConvertToListFloat(row[Common.IC_CUSTOM])
		
		property = BioProperty3.Defecate(self, row[Common.IC_PROPERTY], habit, custom[0], custom[1], custom[2], custom[3])
		return property
	
	def LoadUrinateProperty(self, row):
		rate = float(row[Common.IC_RATE])
		effect = self.ConvertToEffect(row[Common.IC_EFFECT])
		custom = self.ConvertToListFloat(row[Common.IC_CUSTOM])
		property = BioProperty3.Urinate(self, row[Common.IC_PROPERTY], rate, effect, custom[0], custom[1], custom[2])
		return property
		
	def LoadEnergyProperty(self, row):
		rate = self.ConvertToRate(row[Common.IC_RATE])
		current = float(row[Common.IC_CURRENT])
		
		property = BioProperty3.Energy(self, row[Common.IC_PROPERTY], rate, current)
		return property
	
	def LoadTiredProperty(self, row):
		rate = self.ConvertToRate(row[Common.IC_RATE])
		current = float(row[Common.IC_CURRENT])
		
		property = BioProperty3.Exhausted(self, row[Common.IC_PROPERTY], rate, current)
		return property
	
	def LoadSleepyProperty(self, row):
		Global.Logger.LogDebug("Load sleepy "+row[Common.IC_RATE]+"\n")
		rate = self.ConvertToRate(row[Common.IC_RATE])
		Global.Logger.LogDebug("Rate sleep "+str(rate))
		current = float(row[Common.IC_CURRENT])
		habit = self.ConvertToHabitMulti(row[Common.IC_HABIT])
		
		property = BioProperty3.Sleepy(self, row[Common.IC_PROPERTY], rate, current, habit)
		return property
	#-----------------------------------------------------------------------------------------------------------------------------
	
	def GetActivityById(self, id):
		onit = id in self.m_activityList
		if id in self.m_activityList:
			return self.m_activityList[id]
		return None
	
	def TryTrigger(self, activityId):
		for property in self.m_bioProperty:
			if (self.m_currentActivity != None and self.m_currentActivity.m_ID == property.m_relatedActivityId and (not (self.m_currentActivity.IsDone() or self.m_currentActivity.m_status == Common.ACT_STATUS_SUSPEND))):
				return None
		
		self.m_bioActivityToTrigger = activityId
		return self.GetActivityById(activityId)
	
	def UpdateAbility(self):
		energyEffect = self.GetProperty("Energy").GetScore() / ((6 if self.IsAsleep() else 24) * Timer.MINUTE_IN_HOUR)
		exhaustEffect = self.GetProperty("Exhausted").GetScore() / ((12 if self.IsAsleep() else 6) * Timer.MINUTE_IN_HOUR)
		# print("abi "+Fmt(self.m_currentAbility)+" "+Fmt(energyEffect)+" "+Fmt(exhaustEffect))
		self.m_currentAbility += (energyEffect - exhaustEffect) #/ (24 * Timer.MINUTE_IN_HOUR))
		self.m_currentAbility = min(self.m_currentAbility,8.875)
	
	def IsAsleep(self):
		return (self.m_currentActivity != None) and (self.m_currentActivity.m_ID == "B04" or self.m_currentActivity.m_ID == "TD")
	
	def GetProperty(self, propertyName):
		return next(property for property in self.m_bioProperty if property.m_type == propertyName)
	
	def setTarget(self,newTarget):
		self.m_target = newTarget
		self.hasNewTarget = True
		if newTarget != None:
			self.m_target.m_available = False
	
	def Update(self,dt):
		if not self.initialized:
			self.AssignToClosestTarget()
			self.initialized = True
		
		if not self.m_active:
			return self.pos
		
		timeA = int(time.time()*1000)
		
		self.m_elapsedAdjustTimer += dt
		if self.m_elapsedAdjustTimer >= self.m_timeAdjuster:
			self.m_elapsedAdjustTimer = 0
			self.m_wasAsleep = self.IsAsleep() 
			if Global.g_timer.GetHour() == 0 and Global.g_timer.GetMinute() == 0:
				del self.m_eliminatedActivity[:]
			for property in self.m_bioProperty:
				if property == None:
					continue
				if self.m_currentActivity == None or not self.m_currentActivity.m_outdoor:
					property.CalculateScore()
			Global.Logger.DumpDebug()
			self.UpdateAbility()
			self.UpdateActivity()
			self.UpdateEmotionalFactor()
		
			for property in self.m_bioProperty:
				if property == None:
					continue
				if self.m_currentActivity != None and not self.m_currentActivity.m_outdoor:
					property.PostUpdateActivityCalculation()
		
		timeB = int(time.time()*1000)
		# self.UpdateBioStatus(dt)
		# self.UpdateESStatus(dt)
		# self.UpdateActivityOrder()
		# self.UpdateAgentActivity(dt)
		self.UpdateAgentMovement(dt)
		timeC = int(time.time()*1000)
		
		Global.Logger.LogDebug("Time act "+(str(timeB-timeA))+" move "+str(timeC-timeB)+"\n")
		
		Global.Logger.LogDebug("\n agent pos "+self.m_role+" "+str(self.pos)+"\n")
		Global.Logger.DumpDebug()
		return self.pos
	
	def IsLastActivityRunning(self):
		return self.m_currentActivity != None and self.m_currentActivity.IsRunning()
	
	def GetActivityEffect(self, type):
		if self.m_currentActivity == None:
			return 0
		Global.Logger.LogDebug("Get Effect "+self.m_currentActivity.m_ID+" "+type+" "+str(self.m_currentActivity.GetBioEffect(type))+"\n")
		return self.m_currentActivity.GetBioEffect(type) / 60#((60 if (self.m_currentActivity.m_duration == -1 or type == "Hunger" or type == "Energy") else self.m_currentActivity.m_duration) if Config.USE_MINUTE_FORMAT else 1)
		
	def GetActivityEmotionalEffect(self):
		if self.m_currentActivity == None or (not self.m_currentActivity.IsDone()):
			return 0
		return self.m_currentActivity.GetEmotionalEffect()
	
	def GetEmotionalFactor(self):
		return self.m_emotionalTotal
	
	def UpdateEmotionalFactor(self):
		if self.IsLastActivityRunning():
			if self.m_emotionalFactor >= self.m_emotionalNormal:
				if self.m_emotionalFactor - self.m_goodMoodRate < self.m_emotionalNormal:
					self.m_emotionalTimeEffect = self.m_emotionalNormal
				else:
					self.m_emotionalTimeEffect = -self.m_goodMoodRate
			else:
				if self.m_emotionalFactor <= self.m_emotionalNormal:
					if self.m_emotionalFactor + self.m_badMoodRate < self.m_emotionalNormal:
						self.m_emotionalTimeEffect = self.m_badMoodRate
					else:
						self.m_emotionalTimeEffect = self.m_emotionalNormal
		else:
			if self.m_emotionalFactor > 0:
				self.m_emotionalTimeEffect = self.m_badMoodRate
			else:
				self.m_emotionalTimeEffect = -self.m_badMoodRate
		
		moodByTime = self.m_emotionalNormal if (self.m_emotionalTimeEffect == self.m_emotionalNormal) else (self.m_emotionalFactor + self.m_emotionalTimeEffect)
		self.m_emotionalFactor = moodByTime + self.GetActivityEmotionalEffect()
		#print("Emotion ActivityJalan:"+str(self.IsLastActivityRunning())+" Normal:"+Fmt(self.m_emotionalNormal)+" TimeEffect:"+Fmt(self.m_emotionalTimeEffect)+" Mood:"+Fmt(moodByTime)+" ActivityEffect:"+Fmt(self.GetActivityEmotionalEffect())+" Total:"+Fmt(self.m_emotionalFactor)+" CCE:"+Fmt(self.m_emotionalTotal) )
		self.m_emotionalTotal = 1 + (self.m_emotionalFactor / (self.m_emotionalNormal * 100))
	
	def UpdateActivity(self):
		# print("update act "+self.m_bioActivityToTrigger+" cur "+("None" if self.m_currentActivity == None else self.m_currentActivity.m_ID))
		Global.Logger.LogDebug("Current Activity "+self.m_role+" "+("None" if self.m_currentActivity == None else self.m_currentActivity.m_ID)+" lon "+str(len(self.m_activityList))+" viona "+self.m_bioActivityToTrigger+"\n")
		# Global.Logger.LogDebug("Condition "+str(self.m_currentActivity == None)+" "+str(not self.m_currentActivity.m_isBioActivity)+" "+str((self.m_currentActivity.IsDone() and self.m_currentActivity.m_ID != self.m_bioActivityToTrigger))+"\n")
		if self.m_following:
			return
		if self.m_bioActivityToTrigger != "" and (self.m_currentActivity == None or (not self.m_currentActivity.m_isBioActivity) or (self.m_currentActivity.IsDone() and self.m_currentActivity.m_ID != self.m_bioActivityToTrigger)):
			isActivityDone = False
			if self.m_currentActivity != None and self.m_currentActivity.IsDone():
				# Global.Logger.LogDebug("stop6\n")
				self.m_currentActivity.Stop()
				self.m_currentRoom.m_countAgent -= 1
				self.m_currentRoom.SetUseCoord(self.m_roomCoordIndex, False)
				if self.m_currentActivity.m_currentInteractAgent != None and self.m_currentActvity.m_followerActivity != "-":
					self.m_currentActivity.m_currentInteractAgent.SetFollowing(self, False)
				self.m_prevActivity = self.m_currentActivity
				if self.m_target != None:
					self.m_target.SetAvailable(True)
					self.m_target = None
				self.m_currentActivity.CalculateEffects(self)
				self.ClearSuspendForNextActivity()
				if (self.m_currentActivity.m_next != "-"):
					self.m_currentActivity = self.GetActivityById(self.m_currentActivity.m_next)
				self.m_lastActivity = self.m_currentActivity.m_ID
				isActivityDone = True
				#self.m_currentActivity = None
				for property in self.m_bioProperty:
					if property == None:
						continue
					# Global.Logger.LogDebug("property "+property.m_type+" "+str(property.m_relatedActivity != None)+"\n")
					# if property.m_relatedActivity != None:
						# Global.Logger.LogDebug("relateID "+property.m_relatedActivity.m_ID+"\n")
					if property.m_relatedActivity != None and property.m_relatedActivity.m_ID != self.m_bioActivityToTrigger:
						# Global.Logger.LogDebug("Emptying "+property.m_type+"\n")
						property.m_relatedActivity = None
			if not isActivityDone:
				self.m_pendingActivity = self.m_currentActivity
				self.m_pendingActivity.Pause()
				self.m_currentRoom.m_countAgent -= 1
				self.m_currentRoom.SetUseCoord(self.m_roomCoordIndex, False)
				self.m_state = STATE_CHECK_PA
			
			self.m_currentActivity = self.GetActivityById(self.m_bioActivityToTrigger)
			# Global.Logger.LogDebug("goto 5\n")
			self.m_currentActivity.GoTo()
		incidentalAct = []
		if self.m_currentActivity != None:
			isActivityDone = False
			if self.m_currentActivity.IsDone() or self.m_currentActivity.m_status == Common.ACT_STATUS_SUSPEND:
				# Global.Logger.LogDebug("stop2\n")
				isActivityDone = True
				self.m_currentActivity.Stop()
				self.m_currentRoom.m_countAgent -= 1
				self.m_currentRoom.SetUseCoord(self.m_roomCoordIndex, False)
				if self.m_currentActivity.m_currentInteractAgent != None and self.m_currentActvity.m_followerActivity != "-":
					self.m_currentActivity.m_currentInteractAgent.SetFollowing(self, False)
				self.m_prevActivity = self.m_currentActivity
				if self.m_target != None:
					self.m_target.SetAvailable(True)
					self.m_target = None
				self.m_currentActivity.CalculateEffects(self)
				self.ClearSuspendForNextActivity()
				if self.m_currentActivity.m_ID == self.m_bioActivityToTrigger:
					self.m_bioActivityToTrigger = ""
				self.m_lastActivity = self.m_currentActivity.m_ID
				if (self.m_currentActivity.m_next != "-"):
					self.m_currentActivity = self.GetActivityById(self.m_currentActivity.m_next)
				else:
					self.m_currentActivity = None
					if self.m_pendingActivity != None:
						if self.m_pendingActivity.m_status == Common.ACT_STATUS_PAUSED:
							self.m_currentActivity = self.m_pendingActivity
							self.m_currentActivity.Resume()
						self.m_pendingActivity = None
				for property in self.m_bioProperty:
					if property == None:
						continue
					property.m_relatedActivity = None
		
		if self.m_bioActivityToTrigger == "" and (self.m_currentActivity == None or self.m_currentActivity.IsDone() or self.m_currentActivity.m_status == Common.ACT_STATUS_SUSPEND or self.m_currentActivity.m_interrupt[Common.INT_CAN_BE_INTERRUPTED]):
			interruptChecking = self.m_bioActivityToTrigger == "" and self.m_currentActivity != None and (not self.m_currentActivity.IsDone()) and self.m_currentActivity.m_interrupt[Common.INT_CAN_BE_INTERRUPTED]
			actList = []
			for act in self.m_activityList:
				custard = self.m_activityList[act].CanStart(self)
				# Global.Logger.LogDebug("acut "+act+" "+str(custard)+"\n")
				if custard and not self.m_activityList[act].m_isBioActivity:# and (not interruptChecking or self.m_activityList[act].m_interrupt[Common.INT_CAN_INTERRUPT]):
					actList.append(self.m_activityList[act])
			
			Global.Logger.LogDebug("Activity Calculation: Timed:"+Global.g_timer.GetFormattedHour()+"\n")
			actToRemove = []
			todayTime = Global.g_timer.GetTodayTime()
			for act in actList:
				act.m_timeScore = 5
				timeDiff = -1
				if act.m_startTime != -1:
					timeDiff = abs(todayTime - act.m_startTime)
					act.m_timeScore = 10 - (timeDiff/60)
				actDebugStr = "Activity:"+act.m_ID
				actDebugStr += (" Time Diff: "+Fmt(timeDiff)+" Urgency: "+Fmt(act.m_timeScore))
				
				act.m_score = 0
				bioDelta = ""
				for i in range(0,Common.BIOLOGICAL_PROPERTY_COUNT):
					delta = act.m_bioStandard[i] - self.m_bioProperty[i].GetScore()
					Global.Logger.LogDebug("calcio "+PROPERTY_CODE[i]+" "+Fmt(act.m_bioStandard[i])+" "+Fmt(self.m_bioProperty[i].GetScore())+" "+Fmt(delta)+" ")
					act.m_score += delta
					
					bioDelta += (PROPERTY_CODE[i]+"-" +self.m_bioProperty[i].m_type+":"+Fmt(delta) +" - ")
				
				act.m_score /= 8
				
				act.m_emotionalScore = 0
				actDebugStr += (" BioDelta:"+bioDelta+" BioScore:"+Fmt(act.m_score)+"\n")#+" EmoFactor:"+Fmt(self.m_emotionalTotal)+" EmoStd:"+Fmt(act.m_emotionalStandard)
				act.m_emotionalScore = max(0,self.m_emotionalTotal - act.m_emotionalStandard)
				# if self.m_emotionalTotal > act.m_emotionalStandard:
					# act.m_emotionalScore = self.m_emotionalTotal - act.m_emotionalStandard
					# actDebugStr += " TotalEmoEffect:"+Fmt(act.m_emotionalScore)
				# else:
					# actToRemove.append(act)
					# actDebugStr += " REMOVED"
					# print(actDebugStr)
					# continue
				
				# act.m_planScore = act.m_planProperty[Common.PLAN_PROPERTY_ADVANTAGE] + (act.m_planProperty[Common.PLAN_PROPERTY_AUTHORITY] * act.m_planProperty[Common.PLAN_PROPERTY_OBEDIENCE]) + act.m_planProperty[Common.PLAN_PROPERTY_HABIT] + act.m_planProperty[Common.PLAN_PROPERTY_URGENCY]
				# actDebugStr += " PlanScore:"+Fmt(act.m_planScore)
				Global.Logger.LogDebug(actDebugStr)
			
			for act in actToRemove:
				actList.remove(act)
			
			actList.sort(key = lambda x: x.m_emotionalScore, reverse = True)
			
			Global.Logger.LogDebug("Activity Emotional Multiplication:\n")
			lastEmoScore = 0
			curMultiplier = 1
			for act in actList:
				# act.m_score += (act.m_emotionalScore + act.m_planScore)
				if lastEmoScore != 0:
					if act.m_emotionalScore < lastEmoScore:
						curMultiplier -= 0.1
						curMultiplier = max(curMultiplier,0)
				wish = act.m_planProperty[Common.PLAN_PROPERTY_WISH] * curMultiplier
				act.m_planScore = act.m_planProperty[Common.PLAN_PROPERTY_WISH] * curMultiplier
				# print("lasto "+self.m_lastActivity)
				# print(self.GetActivityById(self.m_lastActivity).m_matrix)
				actDebugStr = "Activity: "+act.m_ID
				actDebugStr += " EmoScore:"+Fmt(act.m_emotionalScore)+" Multiplier:"+Fmt(curMultiplier)
				advantage = act.m_planProperty[Common.PLAN_PROPERTY_ADVANTAGE] + (0 if self.m_lastActivity == None else self.GetActivityById(self.m_lastActivity).m_matrix[act.m_ID])
				act.m_planScore += act.m_planProperty[Common.PLAN_PROPERTY_ADVANTAGE] + (0 if self.m_lastActivity == None else self.GetActivityById(self.m_lastActivity).m_matrix[act.m_ID])
				rule = (act.m_planProperty[Common.PLAN_PROPERTY_AUTHORITY] * act.m_planProperty[Common.PLAN_PROPERTY_OBEDIENCE] * 0) #dummy value 0; fill it with agent existance at home
				act.m_planScore += (act.m_planProperty[Common.PLAN_PROPERTY_AUTHORITY] * act.m_planProperty[Common.PLAN_PROPERTY_OBEDIENCE] * 0) #dummy value 0; fill it with agent existance at home
				need = act.m_planProperty[Common.PLAN_PROPERTY_URGENCY]
				act.m_planScore += (act.m_planProperty[Common.PLAN_PROPERTY_URGENCY] + act.CalculateEnvUrgency(self))
				act.m_planScore /= 4
				
				actDebugStr += " Wish: "+Fmt(wish)+" Advantage: "+Fmt(advantage)+" Rule: "+Fmt(rule)+" Need: "+Fmt(need)+" PlanScore: "+Fmt(act.m_planScore)
				
				act.m_score += act.m_timeScore + act.m_planScore
				
				actDebugStr += " TotalScore:"+Fmt(act.m_score)+"\n"
				# act.m_score *= curMultiplier
				actDebugStr += " TotalScore:"+Fmt(act.m_score)
				lastEmoScore = act.m_emotionalScore
				Global.Logger.LogDebug(actDebugStr)
			
			actList.sort(key = lambda x: x.m_score,reverse = True)
			
			Global.Logger.LogDebug("Activity sorted by score:\n")
			for act in actList:
				Global.Logger.LogDebug(act.m_ID+" score "+str(act.m_score)+"\n")
			
			while(len(actList) > 0):
				debugStr = "Check ability:"+actList[0].m_ID+" Standard:"+Fmt(actList[0].m_physicalStandard)+" Current:"+Fmt(self.m_currentAbility)
				if self.m_currentAbility < actList[0].m_physicalStandard:
					actList[0].SetToIncidental()
					debugStr += " Move to incidental\n"
					Global.Logger.LogDebug(debugStr)
					incidentalAct.append(actList.pop(0))
				else:
					Global.Logger.LogDebug(debugStr+" OK\n")
					break
			
			if len(actList) > 0:
				if (actList[0].m_activitySet == "-"):
					self.m_currentActivity = actList[0]
				else:
					traceAct = actList[0]
					if len(traceAct.m_prequisite) > 0:
						parentAct = self.GetActivityById(traceAct.m_prequisite[0])
						actSet = actList[0].m_activitySet[:3]
						while (parentAct != None):
							traceAct = parentAct
							parentAct = None
							for pAct in traceAct.m_prequisite:
								testAct = self.GetActivityById(pAct)
								if testAct.m_activitySet.startswith(actSet):
									parentAct = testAct
									break
					self.m_currentActivity = traceAct
		Global.Logger.LogDebug("act statt "+self.m_currentActivity.m_ID+" "+str(self.m_currentActivity.m_status)+" "+str(self.m_currentActivity.IsDone())+"\n")
		if self.m_currentActivity != None  and (not self.m_currentActivity.IsDone()) and (not self.m_currentActivity.IsRunning()) and self.m_state != STATE_MOVE and self.m_state != STATE_MOVE_PA:
			# Global.Logger.LogDebug("goto 4 "+self.m_currentActivity.m_ID+" "+str(self.m_currentActivity.m_status)+"\n")
			self.m_currentActivity.GoTo()
			self.CheckFollowingAgent()
			if self.m_state != STATE_CHECK_PA and self.m_state != STATE_PREMOVE_PA and self.m_state != STATE_MOVE_PA:
				self.m_state = STATE_CHECK_PA
			for act in incidentalAct:
				if act.m_priority == 1:
					act.m_remainingIncidentalTime = self.m_currentActivity.m_duration
		
		for activity in self.m_activityList:
			self.m_activityList[activity].Update()
		Global.Logger.DumpDebug()

	def recalculateMoveDir(self):
		destination  = self.myPath[self.m_pathIndex]
		self.moveDir = Vector3f.Subtract(Vector3f(destination.X,destination.Y,destination.Z),Vector3f(self.pos.X,self.pos.Y,self.pos.Z))
		self.moveDir.Unitize()
		
	def AssignToClosestTarget(self):
		distanceMin = float(sys.maxint)
		targetIndex = 0
		for (i,target) in enumerate(Agent.s_possibleTarget):
			curDistance = self.pos.DistanceTo(target.m_targetPoint)
			if curDistance < distanceMin:
				distanceMin = curDistance
				targetIndex = i
#		print Agent.s_possibleTarget[targetIndex]
#		print Agent.s_possibleTarget[targetIndex].m_targetPoint
		epList = []
		for (i,ep) in enumerate(Agent.s_entryPointList):
			if ep.target == Agent.s_possibleTarget[targetIndex]:
				epList.append(ep)
		self.setTarget(Agent.s_possibleTarget[targetIndex])
		self.entryPoint = epList[0]
		self.m_myFloorIndex = self.m_target.m_floorIndex
		self.oldEntryPoint = self.entryPoint
		
	def setBoundArea(self,area):
		if area != self.boundArea:
			self.boundArea = area
			self.curveBoundArea = rs.coercecurve(area)
			self.diagonalBound = Vector3d.Subtract(Vector3d(self.curveBoundArea.Points[0].Location),Vector3d(self.curveBoundArea.Points[2].Location)).Length
			
	def getBoundArea(self):
		return self.curveBoundArea,self.diagonalBound
		
	def updateView(self):
		#print "vrtijo"
		#print self.boundArea
		curveBound = rs.coercecurve(self.boundArea)
		rc,pl = curveBound.TryGetPolyline()
		
		diagL = Vector3d.Subtract(Vector3d(curveBound.Points[0].Location),Vector3d(curveBound.Points[2].Location)).Length
		
		vec1 = rs.VectorRotate(self.moveDir,-60,(0,0,1))
		endl1 = Point3d.Add(self.pos,(vec1*diagL))
		mLine1 = Line(self.pos,endl1)
		
		vec2 = rs.VectorRotate(self.moveDir,60,(0,0,1))
		endl2 = Point3d.Add(self.pos,(vec2*diagL))
		mLine2 = Line(self.pos,endl2)
		#Line.to
		iSect1 = Rhino.Geometry.Intersect.Intersection.CurveCurve(curveBound,mLine1.ToNurbsCurve(),0,0)
		iSect2 = Rhino.Geometry.Intersect.Intersection.CurveCurve(curveBound,mLine2.ToNurbsCurve(),0,0)
		
		for inte in iSect1:
			point1 = inte.PointA
			
		for inte in iSect2:
			point2 = inte.PointA
			
		vpointList = []
		for poin in curveBound.Points:
			vect = Vector3d.Subtract(Vector3d(poin.Location),Vector3d(self.pos))
			vect.Unitize()
			angle = math.degrees(math.atan2(vect.Y,vect.X)-math.atan2(vec1.Y,vec1.X))
			if angle >= 0 and angle <= 120:
				vpointList.append((vect,poin.Location))
		
		vpointList.sort(key = lambda x: math.degrees(math.atan2(x[0].Y,x[0].X)-math.atan2(vec1.Y,vec1.X)),reverse = True)
		
		#print vpointList
		pointList = []
		pointList.append(self.pos)
		pointList.append(point2)
		for vpoint in vpointList:
			pointList.append(vpoint[1])
		pointList.append(point1)
		pointList.append(self.pos)
		
		view = sc.doc.Views.ActiveView.ActiveViewport      
		self.objectList = Rhino.RhinoDoc.ActiveDoc.Objects.FindByCrossingWindowRegion(view,pointList,True,Rhino.DocObjects.InstanceObject)
		#print olist
		#print self.objectList
	
	def GeneratePath(self, start, end, stair = None):
		if stair != None:
			end = stair.pos
			Global.Logger.LogDebug("have stair "+str(stair.pos)+"\n")
		else:
			Global.Logger.LogDebug("no stair\n")
		pStart = TranslateToGridPos(start,self.m_myFloorIndex)
		pEnd = TranslateToGridPos(end,self.m_myFloorIndex)
		Global.Logger.LogDebug(self.m_role+" pos start "+str(pStart)+" "+str(start))
		Global.Logger.LogDebug(self.m_role+" pos end "+str(pEnd)+" "+str(end))
		Global.Logger.DumpDebug()
		path = PathFinding.astarv3(pStart,pEnd,self.m_myIndex,self.m_myFloorIndex)
		
		#No path found. Wait a moment
		if path == None:
			#print "nopopak"
			Global.Logger.LogDebug("no Path"+"\n")
			Global.Logger.DumpDebug()
			return
		
		#path found
		if self.oldEntryPoint != None and path[0] != self.pos:
			path.insert(0,self.pos)
		
		if self.needStair:
			path.append(stair.target.m_targetPoint)
		elif (self.m_targetRoom == None or self.m_targetRoom.IsInRoom(self.pos)) and self.entryPoint.pos != self.entryPoint.target.m_targetPoint:
			path.append(self.entryPoint.target.m_targetPoint)
		# self.m_pathIndex = 1
		#print path
		Global.Logger.LogDebug(self.m_role+" Path "+str(path)+"\n")
		Global.Logger.DumpDebug()
		return path
	
	def CheckStartMovement(self):
		# Global.Logger.LogDebug("StartCheckMove\n")
		if self.m_currentActivity.m_status == Common.ACT_STATUS_GOTO and self.m_state != STATE_MOVE and self.m_state != STATE_MOVE_PA:
			if self.m_following:
				self.m_targetRoom = self.m_followedAgent.m_targetRoom
			else:
				roomName = self.m_currentActivity.GetTargetRoom()
				Global.Logger.LogDebug("Check startmove "+self.m_currentActivity.m_ID+" "+roomName+"\n")
				if (roomName == "Agent"):
					interactAgent = next((agent for agent in Agent.agentList if (agent.m_role == self.m_currentActivity.m_interactAgent)), None)
					if interactAgent != None:
						self.m_targetRoom = interactAgent.m_currentRoom
				else:
					# Global.Logger.LogDebug("Rukiane = "+self.m_currentActivity.m_ID+"|"+str(roomName)+"|"+str(self.m_currentActivity.m_rooms)+" "+"\n")
					# Global.Logger.DumpDebug()
					#print "rumina "+roomName
					self.m_targetRoom = next((room for room in Global.g_myHouse.m_rooms if room.m_name == roomName),None)
			self.m_targetType = TARGET_ROOM
			if not self.m_targetRoom.IsInRoom(self.pos):
				if self.m_state == STATE_CHECK_PA:
					self.m_postActivityStops = self.CheckPostActivity()
					if len(self.m_postActivityStops) > 0:
						self.myPath = []
						start = self.pos
						for stop in self.m_postActivityStops:
							path = self.GeneratePath(start,stop)
							start = stop
							self.myPath.append(path)
						self.m_pathIndex = 1
						self.recalculateMoveDir()
						self.m_state = STATE_PREMOVE_PA
					else:
						self.m_state = STATE_WAIT
				if self.m_state != STATE_CHECK_PA and self.m_state != STATE_PREMOVE_PA and self.m_state != STATE_MOVE_PA:
					Global.Logger.LogDebug(self.m_role+" state fintar "+str(self.m_state)+"\n")
					self.FindTargetAndEntryPointForObject(CommonEnum.CP_ROOM)
					start = self.pos
					if self.oldEntryPoint != None:
						start = self.oldEntryPoint.pos
					
					self.needStair = (self.m_targetRoom.m_floorIndex != self.m_myFloorIndex)
					Global.Logger.LogDebug("RoomName "+self.m_targetRoom.m_name+" Coord "+str(self.m_targetRoom.GetTargetCoord(self.m_roomCoordIndex))+"\n")
					Global.Logger.LogDebug("Floor "+str(self.m_targetRoom.m_floorIndex)+" "+str(self.m_myFloorIndex)+"\n")
					Global.Logger.LogDebug("NeedStair "+str(self.needStair)+"\n")
					
					# self.m_roomCoordIndex = self.m_targetRoom.GetAvailableCoord()
					targetCoord = self.m_targetRoom.GetTargetCoord(self.m_roomCoordIndex)
					self.m_targetRoom.SetUseCoord(self.m_roomCoordIndex, True)
					if self.needStair:
						stairIndex = "STAIR_"+str(self.m_myFloorIndex)
						stairEntry = next(entry for entry in Agent.s_entryPointList if entry.target.m_id == stairIndex)
						self.myPath = self.GeneratePath(start,targetCoord, stairEntry)
					else:
						self.myPath = self.GeneratePath(start,targetCoord)
					
					self.m_pathIndex = 1
					self.recalculateMoveDir()
					self.m_state = STATE_PRE_MOVE
			else:
				self.m_targetType = TARGET_NONE
				self.m_currentActivity.Start()
				self.m_currentRoom.m_countAgent += 1
		# Global.Logger.LogDebug("EndCheckMove\n")
	
	#update pergerakan dan posisi agent
	def UpdateAgentMovement(self, dt):
		print(self.pos)
		for room in Global.g_myHouse.m_rooms:
			if room.IsInRoom(self.pos):
				self.m_currentRoom = room
				break
		self.CheckStartMovement()
		Global.Logger.LogDebug(self.m_role+" Update movement dt = "+str(dt)+" state "+str(self.m_state)+"\n")
		Global.Logger.DumpDebug()
		if self.m_state != STATE_MOVE and self.m_state != STATE_MOVE_PA:
			if self.m_state == STATE_PRE_MOVE:
				self.m_state = STATE_MOVE
			if self.m_state == STATE_PREMOVE_PA:
				self.m_state = STATE_MOVE_PA
			return
		
		Global.Logger.LogDebug(self.m_role+" Path : ")
		for path in self.myPath:
			Global.Logger.LogDebug("["+str(path.X)+","+str(path.Y)+"],")
		Global.Logger.LogDebug("\ncurrent index "+str(self.m_pathIndex)+"\n")
		
		destination  = self.myPath[self.m_pathIndex]
		distance = self.pos.DistanceTo(destination)
		distanceCovered = float(dt) * Agent.s_scaleSpeed / 1000.0
		Global.Logger.LogDebug("Scale distance "+str(dt)+" "+str(Agent.s_scaleSpeed)+"\n")
		Global.Logger.LogDebug("Distance "+str(distance)+" covered "+str(distanceCovered)+"\n")
		Global.Logger.DumpDebug()
		if distance > distanceCovered:
#		and (self.m_targetRoom == None or (not self.m_targetRoom.IsInRoom(self.pos))):
			#masih ada jarak yang perlu ditempuh
			myGrid = TranslateToGridPos(self.pos,self.m_myFloorIndex)
			self.m_blockedBy,blocked = PathFinding.IsBlocked(myGrid,self.m_myFloorIndex)
			
			if blocked:
				#jalur kemungkinan terhalang
				blockPos = PathFinding.TranslateToRealPos(PathFinding.Map.liveBlock[self.m_blockedBy][0],self.m_myFloorIndex)
				blockDir = Vector3f.Subtract(Vector3f(blockPos[0],blockPos[1],0),Vector3f(self.pos.X,self.pos.Y,0))
				blockDir = Vector3f.Divide(blockDir,blockDir.Length)
				dotP = (blockDir.X*self.moveDir.X) + (blockDir.Y*self.moveDir.Y)
				angle = math.acos(dotP)
				angle = math.degrees(angle)
				if angle > 60 and (abs(myGrid[0]-PathFinding.Map.liveBlock[self.m_blockedBy][0][0]) > PathFinding.OVERLAP_LIMIT or abs(myGrid[1]-PathFinding.Map.liveBlock[self.m_blockedBy][0][1]) > PathFinding.OVERLAP_LIMIT):
					blocked = False
				if self.entryPoint.pos != self.entryPoint.target.m_targetPoint and self.m_pathIndex == (len(self.myPath) - 1):
					blocked = False
			
			if blocked:
				#jalur terhalang
				if self.blockCounter < 10 and self.m_myIndex > self.m_blockedBy:
					if not self.m_hasWait:
						self.blockCounter += 1
						return
					else:
						self.m_hasWait = True
				
				if self.needStair:
					stairIndex = "STAIR_"+str(self.m_myFloorIndex)
					stairEntry = next(entry for entry in Agent.s_entryPointList if entry.target.m_id == stairIndex)
					# stairEntry = next(trgt for trgt in Agent.s_possibleTarget if trgt.m_id == stairIndex)
					myNextDest = stairEntry.pos
				elif self.m_targetRoom.IsInRoom(self.pos):
					myNextDest = self.entryPoint.pos
				else:
					# self.m_roomCoordIndex = self.m_targetRoom.GetAvailableCoord()
					myNextDest = self.m_targetRoom.GetTargetCoord(self.m_roomCoordIndex)
					self.m_targetRoom.SetUseCoord(self.m_roomCoordIndex, True)
				midPath = self.GeneratePath(self.pos,myNextDest)
				
				#No path found. Wait a moment
				if midPath == None:
					self.blockCounter += 1
					if self.blockCounter > 10 and self.m_myIndex > self.m_blockedBy and self.m_pathIndex > 2:
						self.pos = rs.PointAdd(self.pos,(Vector3d.Multiply(self.moveDir,self.m_speedFactor) * (-1)))
					return
				
				del self.myPath[self.m_pathIndex-1:]
				self.myPath.extend(midPath)
				self.m_hasWait = False
				self.recalculateMoveDir()
			else:
				#not blocked, continue to move
				self.blockCounter = 0
				self.m_blockedBy = -1
			
			#update agent position
			self.pos = rs.PointAdd(self.pos,Vector3d.Multiply(self.moveDir,distanceCovered))
			
			
		else:
			#already close with destination
			remainingDistance = distanceCovered - distance
			while (remainingDistance > 0):
				self.pos = destination
				self.m_pathIndex+=1
				if self.m_pathIndex < len(self.myPath):
					self.recalculateMoveDir()
					destination  = self.myPath[self.m_pathIndex]
					distance = self.pos.DistanceTo(destination)
					if remainingDistance < distance:
						self.pos = rs.PointAdd(self.pos,Vector3d.Multiply(self.moveDir,remainingDistance))
					remainingDistance = remainingDistance - distance
				elif self.needStair:
					nextStairIndex = "STAIR_"+str(self.m_targetRoom.m_floorIndex)
					nextStairTarget = next(trgt for trgt in Agent.s_possibleTarget if trgt.m_id == nextStairIndex)
					nextStairEntry = next(entry for entry in Agent.s_entryPointList if entry.target == nextStairTarget)
					self.m_myFloorIndex = self.m_targetRoom.m_floorIndex
					start = TranslateToGridPos(nextStairEntry.pos,self.m_myFloorIndex)
					end = TranslateToGridPos(self.entryPoint.pos,self.m_myFloorIndex)
					
					self.myPath = PathFinding.astarv3(start,end,self.m_myIndex,self.m_myFloorIndex)
					self.pos = nextStairTarget.m_targetPoint
					self.myPath.insert(0,self.pos)
					if self.entryPoint.pos != self.entryPoint.target.m_targetPoint:
						self.myPath.append(self.entryPoint.target.m_targetPoint)
					self.m_pathIndex = 1
					self.recalculateMoveDir()
					self.needStair = False
					distance = self.pos.DistanceTo(destination)
					if remainingDistance < distance:
						self.pos = rs.PointAdd(self.pos,Vector3d.Multiply(self.moveDir,remainingDistance))
					remainingDistance = remainingDistance - distance
				else:
					self.m_state = STATE_WAIT
					if self.m_state == STATE_MOVE:
						
						#tiba di tempat, mulai menjalankan aktivitas (pendukung ataupun utama)
						remainingDistance = 0
						self.m_targetType == TARGET_NONE
						Global.Logger.LogDebug("Try starting activity...\n")
						
						## no support activity yet
						
						# if self.m_currentSupportActivity != None:
							# self.m_currentSupportActivity.Start()
						# else:
							# self.m_currentActivity.Start()
							
						self.m_currentActivity.Start()
						self.m_currentRoom.m_countAgent += 1
						
						Global.Logger.LogDebug("Try starting activity DONE\n")
					else:
						return
		Global.Logger.LogDebug(self.m_role+" Target type "+str(self.m_targetType))
		if(self.m_targetType == TARGET_ROOM):
			Global.Logger.LogDebug(" target room "+self.m_targetRoom.m_name)
		Global.Logger.LogDebug("\n")
		
		if self.IsArriveInRoom():
			recalculatePath = False
			cancel, stopPlaces = self.m_currentActivity.CheckTerms(self)
			if cancel:
				self.m_currentActivity.NextTargetRoom()
				if (self.m_currentActivity.GetTargetRoom() == "None"):
					self.m_currentActivity.Suspend()
					self.m_currentActivity.SetToIncidental()
					self.ClearSuspendForNextActivity(self.m_currentActivity.m_ID)
				else:
					Global.Logger.LogDebug("goto 3\n")
					self.m_currentActivity.GoTo()
					self.CheckFollowingAgent()
					self.m_state = STATE_WAIT
				return
			
			start = self.pos
			newPath = []
			if len(stopPlaces) > 0:
				for stops in stopPlaces:
					for ep in Agent.s_entryPointList:
						if ep.target.m_id == stops:
							if ep.target.m_type == "Lamp":
								self.m_targetRoom.SetLampTurn(self, stops, True)
							path = self.GeneratePath(start,ep.pos)
							newPath.extend(path)
							start = ep.pos
							recalculatePath = True
							break
				
			
			Global.Logger.LogDebug("act device "+str(self.m_currentActivity.m_device)+"\n")
			hasDevice, device = self.m_targetRoom.HasAndAvailable(self.m_currentActivity.m_device[self.m_currentActivity.m_targetRoom])
			Global.Logger.LogDebug("device "+str(hasDevice)+" "+str(device)+"\n")
			Global.Logger.DumpDebug()
			if hasDevice:
				for ep in Agent.s_entryPointList:
					if ep.target.m_id == device:
						self.FindTargetAndEntryPointForObject(ep.target.m_id)
						self.m_targetRoom.SetUseCoord(self.m_roomCoordIndex, False)
						path = self.GeneratePath(start,ep.pos)
						newPath.extend(path)
						start = ep.pos
						recalculatePath = True
						self.m_target = ep.target
						self.m_target.SetAvailable(False)
						break
			elif (self.m_currentActivity.m_device[self.m_currentActivity.m_targetRoom] != "-"):
				self.m_currentActivity.NextTargetRoom()
				if (self.m_currentActivity.GetTargetRoom() == "None"):
					self.m_currentActivity.Suspend()
					self.m_currentActivity.SetToIncidental()
					self.ClearSuspendForNextActivity(self.m_currentActivity.m_ID)
				else:
					Global.Logger.LogDebug("goto 2\n")
					self.m_currentActivity.GoTo()
					self.CheckFollowingAgent()
					self.m_state = STATE_WAIT
				return
				# path = self.GeneratePath(start,self.m_targetRoom.m_targetCoord)
			# else:
				# newPath = self.GeneratePath(start,self.m_targetRoom.m_targetCoord)
			Global.Logger.LogDebug("newpath "+str(newPath)+" reek "+str(recalculatePath)+"\n")
			
			Global.Logger.LogDebug("req resource "+str(self.m_currentActivity.m_requiredResource)+"\n")
			if len(self.m_currentActivity.m_requiredResource[self.m_currentActivity.m_targetRoom]) > 0:
				if not self.m_currentActivity.CheckResource(self.m_targetRoom):
					self.m_currentActivity.NextTargetRoom()
					if (self.m_currentActivity.GetTargetRoom() == "None"):
						self.m_currentActivity.Suspend()
						self.m_currentActivity.SetToIncidental()
						self.ClearSuspendForNextActivity(self.m_currentActivity.m_ID)
						Global.Logger.LogDebug("suspend\n")
					else:
						Global.Logger.LogDebug("goto 1\n")
						self.m_currentActivity.GoTo()
						self.CheckFollowingAgent()
						self.m_state = STATE_WAIT
					return
			
			if recalculatePath:
				self.myPath = newPath
				self.m_pathIndex = 1
				self.recalculateMoveDir()
				Global.Logger.LogDebug("recalc")
				self.m_targetType = TARGET_POINT
		# if self.m_targetType == TARGET_ROOM and self.IsArriveInRoom():
			# self.GenerateAndCheckPreActivityList()
		
	def FindTargetAndEntryPointForObject(self, ID):
		self.oldEntryPoint = self.entryPoint
		if ID == CommonEnum.CP_ROOM:
			self.m_roomCoordIndex = self.m_targetRoom.GetAvailableCoord()
			targetCoord = self.m_targetRoom.GetTargetCoord(self.m_roomCoordIndex)
			self.m_targetRoom.SetUseCoord(self.m_roomCoordIndex, True)
			self.entryPoint = EntryPoint.EntryPoint(targetCoord,self.m_targetRoom.m_floorIndex)
			self.entryPoint.target = Target.Target(self.m_targetRoom.m_floorIndex,CommonEnum.RF_NONE, "-", targetCoord,"TMP_CENTER")
		else:
			self.entryPoint = next(entry for entry in Agent.s_entryPointList if entry.target.m_id == ID)
		Global.Logger.LogDebug(self.m_role+" find entry for "+ID+" "+str(self.entryPoint)+"\n")
		Global.Logger.DumpDebug()
		
	#memeriksa jika agent telah tiba di ruang untuk melakukan aktivitas
	def IsArriveInRoom(self):
		return self.m_targetType == TARGET_ROOM and self.m_targetRoom.IsInRoom(self.pos)
	
	def EliminateActivity(self):
		for act in self.m_currentActivity.m_eliminate:
			alreadyEliminated = next((elmAct for elmAct in self.m_eliminatedActivity if elmAct.equals(act)),None)
			if alreadyEliminated == None:
				self.m_eliminatedActivity.append(act)
	
	def ClearSuspendForNextActivity(self, excepts = ""):
		for act in self.m_activityList:
			if self.m_activityList[act].m_ID != excepts and self.m_activityList[act].m_priority == 0 and self.m_activityList[act].m_status ==  Common.ACT_STATUS_SUSPEND:
				self.m_activityList[act].m_status = Common.ACT_STATUS_NONE
	
	def UpdatePendingEffect(self):
		for effect in Activity.Activity.s_pendingEffect:
			effect[3] -= 1
			if effect[3] <= 0:
				effect[0].m_resource[effect[1]][0] += effect[2]
			
			Activity.Activity.s_pendingEffect.remove(effect)
	
	def CheckPostActivity(self):
		postActivity = self.m_prevActivity.GetPostActivity()
		stops = []
		for postAct in postActivity:
			if postAct == "L2":
				if self.m_currentRoom.CountAgentInRoom() == 1:
					lamps = self.m_currentRoom.GetLampToTurn(False)
					for lampId in lamps:
						objLamp = next((entry for entry in s_entryPointList if entry.m_id == lampId), None)
						if objLamp != None:
							stops.append(objLamp.pos)
			elif postAct == "D2" or postAct == "E2":
				hasDevice, active, device = self.m_targetRoom.HasAndActive(self.m_prevActivity.m_device[self.m_prevActivity.m_targetRoom])
				if hasDevice and active:
					deviceObj = next((trgt for trgt in Agent.s_possibleTarget if trgt.m_id == device), None)
					if deviceObj != None:
						deviceObj.StopUsage()
		
		hasFan, active, fanDevice = self.m_targetRoom.HasAndActive("Fan")
		if hasFan and active:
			stops.append(fanDevice.pos)
		
		return stops
	
	def SetFollowing(self, agent, following):
		self.m_following = following
		self.m_followedAgent = agent if following else None
	
	def ForceStartActivity(self, activity):
		self.m_currentRoom.SetUseCoord(self.m_roomCoordIndex, False)
		self.m_currentActivity.ForceStop()
		self.m_currentActivity = self.self.GetActivityById[activity]
		self.m_currentActivity.GoTo()
		self.m_state = STATE_WAIT
		
	def CheckFollowingAgent(self):
		if self.m_currentActivity.m_currentInteractAgent != None and self.m_currentActvity.m_followerActivity != "-":
			self.m_currentActivity.m_currentInteractAgent.SetFollowing(self, True)
			self.m_currentActivity.m_currentInteractAgent.ForceStartActivity(self.m_currentActvity.m_followerActivity)
#-----------------------------------------------------------------------------------------------------------------------------------------

def TranslateToGridPos(pos,mazeIndex):
	try:
		gridX = int(math.floor((pos.X - PathFinding.Map.topPos[mazeIndex].X)/0.08))
		gridY = int(math.floor((PathFinding.Map.topPos[mazeIndex].Y - pos.Y)/0.08))
		posGrid = (gridX,gridY)
	except Exception as e:
#		print e
		#print pos
		Agent.hasErr = True
		posGrid = (0,0)
	return posGrid