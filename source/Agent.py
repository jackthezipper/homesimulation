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
reportPath		= sourceDirPath+"report\\"+sc.sticky["MapName"]+"\\"

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
		self.m_preState = state
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
		self.m_nonIndependentAct = []
		
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
		self.m_activityLog = ""
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
		self.m_useCoordRoom = []
		self.ConvertStandardToPoint()
		self.m_bioRecord = []
		self.m_log = []
		self.m_shouldUpdate = False
		self.m_passingDoor = None
		self.m_socialValue = {}
	
	def SetState(self, state):
		self.m_preState = self.m_state
		self.m_state = state
		
	def ConvertStandardToPoint(self):
		hungerBase = self.GetProperty("Hunger").m_rate[Common.RATE_BASE]
		energyBase = self.GetProperty("Energy").m_rate[Common.RATE_BASE]
		urinateBase = self.GetProperty("Urinate").m_effect[Common.EFFECT_URINATE_NORMAL][Common.EFFECT_NEW_LIMIT]
		for act in self.m_activityList:
			self.m_activityList[act].m_bioStandard[0] /= (hungerBase / 10)
			self.m_activityList[act].m_bioStandard[3] /= (energyBase / 10)
			self.m_activityList[act].m_bioStandard[6] /= (28.747 / 10)
			self.m_activityList[act].m_bioStandard[7] /= (urinateBase / 10)
	
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
					self.m_currentActivity.Start(self.m_role)
					self.ActivityLog("Starting "+self.m_currentActivity.m_ID+" at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
					self.SetState(STATE_WAIT)
					# self.m_currentRoom.m_countAgent += 1
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
				if row[Common.IC_PROPERTY] == "NonIndependentAct":
					# Global.Logger.LogDebug(self.m_role+" "+row[Common.IC_VALUE] + "\n")
					if row[Common.IC_VALUE] != "-":
						self.m_nonIndependentAct = row[Common.IC_VALUE].split(";")
					# Global.Logger.LogDebug(str(self.m_nonIndependentAct)+"\n")
					continue
				if row[Common.IC_PROPERTY] == "Property":
					continue
				print(row[Common.IC_PROPERTY])
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
			rate = [(minuteBaseRate * float(match.group(3))), (minuteBaseRate * float(match.group(4))), (minuteBaseRate * float(match.group(6))), minuteBaseRate, baseRate, divider]
		else:
			rate = [(minuteBaseRate * float(match.group(3))), (minuteBaseRate * float(match.group(4))), 0, 0, baseRate, divider]
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
		if activityId in self.m_nonIndependentAct:
			return None
		if self.m_currentRoom != None and (self.m_currentRoom.m_name == "RTG01" or self.m_currentRoom.m_name == "RTG02"):
			return None
		for property in self.m_bioProperty:
			if (self.m_currentActivity != None and self.m_currentActivity.m_ID == property.m_relatedActivityId and (not (self.m_currentActivity.IsDone() or self.m_currentActivity.m_status == Common.ACT_STATUS_SUSPEND))):
				return None
		if self.m_currentActivity != None and self.m_currentActivity.m_currentInteractAgent != None and self.m_currentActivity.m_followerActivity != "-":
			return None
		
		self.m_bioActivityToTrigger = activityId
		activity = self.GetActivityById(activityId)
		if activity.m_status == Common.ACT_STATUS_SUSPEND or activity.m_isIncidental:
			return None
		return self.GetActivityById(activityId)
	
	def IsIndependentAgent(self):
		return len(self.m_nonIndependentAct) == 0
	
	def UpdateAbility(self):
		energyEffect = self.GetProperty("Energy").GetScore() / ((6 if self.IsAsleep() else 24) * Timer.MINUTE_IN_HOUR)
		exhaustEffect = self.GetProperty("Exhausted").GetScore() / ((12 if self.IsAsleep() else 6) * Timer.MINUTE_IN_HOUR)
		self.m_currentAbility += (energyEffect - exhaustEffect) #/ (24 * Timer.MINUTE_IN_HOUR))
		self.m_currentAbility = max(0,min(self.m_currentAbility,8.875))
		self.Log("Physical ability: Energy effect: "+Fmt(energyEffect)+" - Exhausted effect: "+Fmt(exhaustEffect)+" - Current Ability: "+Fmt(self.m_currentAbility)+"\n")
	
	def IsAsleep(self):
		return (self.m_currentActivity != None) and (self.m_currentActivity.m_ID == "B04" or self.m_currentActivity.m_ID == "TD") and self.m_currentActivity.IsRunning()
	
	def GetProperty(self, propertyName):
		return next(property for property in self.m_bioProperty if property.m_type == propertyName)
	
	def setTarget(self,newTarget):
		self.m_target = newTarget
		self.hasNewTarget = True
		if newTarget != None:
			self.m_target.m_available = False
	
	def Update(self,dt):
		if "SimulationSpeed" in sc.sticky:
			dt *= sc.sticky["SimulationSpeed"]
		if not self.initialized:
			self.AssignToClosestTarget()
			self.initialized = True
		
		if not self.m_active:
			return self.pos
		
		timeA = int(time.time()*1000)
		
		for room in Global.g_myHouse.m_rooms:
			if room.IsInRoom(self.pos):
				self.m_currentRoom = room
				Global.Logger.LogDebug("akoroom "+self.m_role+" "+str(self.pos)+" "+self.m_currentRoom.m_name+"\n")
				break
		
		self.m_elapsedAdjustTimer += dt
		if self.m_elapsedAdjustTimer >= self.m_timeAdjuster:
			self.m_shouldUpdate = True
			self.Log("Time: Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
			self.m_elapsedAdjustTimer = 0
			self.m_wasAsleep = self.IsAsleep() 
			if Global.g_timer.GetHour() == 0 and Global.g_timer.GetMinute() == 0:
				del self.m_eliminatedActivity[:]
				if self.m_pendingActivity != None:
					self.m_pendingActivity.Stop()
					self.m_pendingActivity = None
			for property in self.m_bioProperty:
				if property == None:
					continue
				# if self.m_currentActivity == None or not self.m_currentActivity.m_outdoor:
				property.CalculateScore()
			Global.Logger.DumpDebug()
			if self.m_currentActivity == None or not self.m_currentActivity.m_outdoor:
				self.UpdateAbility()
			self.UpdatePendingEffect()
			self.UpdateActivity()
			self.UpdateEmotionalFactor()
		
			propertyRecord = []
			for property in self.m_bioProperty:
				if property == None:
					continue
				if self.m_currentActivity == None or not self.m_currentActivity.m_outdoor:
					property.PostUpdateActivityCalculation()
				
				propertyRecord.extend(property.ProcessOutput())
			
			self.m_bioRecord.append(propertyRecord)
		
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
		self.m_shouldUpdate = False
		return self.pos
	
	def IsLastActivityRunning(self):
		return self.m_currentActivity != None and self.m_currentActivity.IsRunning()
	
	def GetActivityEffect(self, type):
		if self.m_currentActivity == None:
			return 0
		# Global.Logger.LogDebug("Get Effect "+self.m_currentActivity.m_ID+" "+type+" "+str(self.m_currentActivity.GetBioEffect(type))+"\n")
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
		self.Log("Emotion ActivityJalan:"+str(self.IsLastActivityRunning())+" Normal:"+Fmt(self.m_emotionalNormal)+" TimeEffect:"+Fmt(self.m_emotionalTimeEffect)+" Mood:"+Fmt(moodByTime)+" ActivityEffect:"+Fmt(self.GetActivityEmotionalEffect())+" Total:"+Fmt(self.m_emotionalFactor)+" CCE:"+Fmt(self.m_emotionalTotal)+"\n" )
		self.m_emotionalTotal = 1 + (self.m_emotionalFactor / (self.m_emotionalNormal * 100))
	
	def UpdateActivity(self):
		# print("update act "+self.m_bioActivityToTrigger+" cur "+("None" if self.m_currentActivity == None else self.m_currentActivity.m_ID))
		Global.Logger.LogDebug("Current Activity "+self.m_role+" "+("None" if self.m_currentActivity == None else self.m_currentActivity.m_ID)+" lon "+str(len(self.m_activityList))+" viona "+self.m_bioActivityToTrigger+"\n")
		self.Log("Current Activity "+("None" if self.m_currentActivity == None else self.m_currentActivity.m_ID)+"\n")
		if self.m_currentActivity == None:
			self.Log("No activity!!!\n")
		elif self.m_currentActivity.IsRunning():
			self.Log("Activity is running\n")
		else:
			self.Log("Agent move to activity location\n")
		# Global.Logger.LogDebug("Condition "+str(self.m_currentActivity == None)+" "+str(not self.m_currentActivity.m_isBioActivity)+" "+str((self.m_currentActivity.IsDone() and self.m_currentActivity.m_ID != self.m_bioActivityToTrigger))+"\n")
		if self.m_following:
			self.m_currentActivity.Update()
			self.m_bioActivityToTrigger = ""
			Global.Logger.LogDebug("runtime2 act = "+str(self.m_currentActivity.m_runningTime)+" duration = "+str(self.m_currentActivity.m_duration)+"\n")
			return
		
		inStair = False
		if self.m_currentRoom != None:
			inStair = self.m_currentRoom.m_name == "RTG01" or self.m_currentRoom.m_name == "RTG02"
		
		if self.m_bioActivityToTrigger != "" and not inStair and (self.m_currentActivity == None or (((not self.m_currentActivity.m_isBioActivity) or (self.m_currentActivity.IsDone() and self.m_currentActivity.m_ID != self.m_bioActivityToTrigger) or self.m_currentActivity.m_status == Common.ACT_STATUS_SUSPEND)) and (self.m_currentActivity.m_currentInteractAgent == None or not self.m_currentActivity.m_currentInteractAgent.m_following)):
			isActivityDone = False
			if self.m_currentActivity == None or self.m_currentActivity.IsRunning():
				self.m_prevActivity = self.m_currentActivity
			if self.m_currentActivity != None and (self.m_currentActivity.IsDone() or self.m_currentActivity.m_status == Common.ACT_STATUS_SUSPEND):
				Global.Logger.LogDebug("stop6\n")
				isActivityDone = self.m_currentActivity.IsDone()
				if self.m_currentActivity.m_currentInteractAgent != None and self.m_currentActivity.m_followerActivity != "-":
					self.m_currentActivity.m_currentInteractAgent.SetFollowing(self, False)
					self.m_currentActivity.m_currentInteractAgent.m_currentActivity.Stop()
				self.m_currentActivity.Stop()
				self.ActivityLog("Finish activity Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
				if not self.m_currentActivity.m_auto and self.m_target!= None and self.m_target.m_powerCons > 0:
					self.m_target.StopUsage(self.m_role)
				# self.m_currentRoom.m_countAgent -= 1
				self.SetUseCoordRoom(False)
				if self.m_target != None:
					self.m_target.SetAvailable(True)
					self.m_target = None
				if isActivityDone:
					self.m_currentActivity.CalculateEffects(self)
				self.ClearSuspendForNextActivity(self.m_currentActivity.m_ID)
				if (isActivityDone and self.m_currentActivity.m_next != "-"):
					Global.Logger.LogDebug("set activity "+self.m_role+" by 8\n")
					self.m_currentActivity = self.GetActivityById(self.m_currentActivity.m_next)
				self.m_lastActivity = self.m_currentActivity.m_ID
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
			if self.m_currentActivity != None and not isActivityDone:
				if self.m_currentActivity == None or self.m_currentActivity.m_status < Common.ACT_STATUS_RUN:
					self.SetState(STATE_IDLE)
					# self.ActivityLog("Idle 9\n")
				if not self.m_currentActivity.m_auto and self.m_target != None:
					self.m_target.SetAvailable(True)
					self.m_target = None
				if self.m_bioActivityToTrigger == "B04":
					self.m_currentActivity.Stop()
					self.ActivityLog("Finish activity Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
				else:
					self.m_pendingActivity = self.m_currentActivity
					self.m_pendingActivity.Pause()
				# self.m_currentRoom.m_countAgent -= 1
				self.SetUseCoordRoom(False)
			if isActivityDone:
				self.SetState(STATE_CHECK_PA)
			else:
				self.SetState(STATE_IDLE)
			
			Global.Logger.LogDebug("set activity "+self.m_role+" by 7\n")
			self.m_currentActivity = self.GetActivityById(self.m_bioActivityToTrigger)
			Global.Logger.LogDebug("goto 5\n")
			self.m_currentActivity.GoTo()
			self.ActivityLog("Switch activity to "+self.m_currentActivity.m_ID+" at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
		incidentalAct = []
		if self.m_currentActivity != None:
			isActivityDone = False
			Global.Logger.LogDebug("danilo "+self.m_role+" "+str(self.m_currentActivity.IsDone())+" "+str(self.m_currentActivity.m_status == Common.ACT_STATUS_SUSPEND)+"\n")
			Global.Logger.LogDebug("runtime act = "+str(self.m_currentActivity.m_runningTime)+" duration = "+str(self.m_currentActivity.m_duration)+"\n")
			if self.m_currentActivity.IsDone() or self.m_currentActivity.m_status == Common.ACT_STATUS_SUSPEND:
				Global.Logger.LogDebug("stop2\n")
				isActivityDone = self.m_currentActivity.IsDone()
				if self.m_currentActivity.m_currentInteractAgent != None and self.m_currentActivity.m_followerActivity != "-":
					self.m_currentActivity.m_currentInteractAgent.SetFollowing(self, False)
					# self.m_currentActivity.m_currentInteractAgent.m_currentActivity.Stop()
				self.m_currentActivity.Stop()
				self.ActivityLog("Finish activity Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
				if not self.m_currentActivity.m_auto and self.m_target != None and self.m_target.m_powerCons > 0:
					self.m_target.StopUsage(self.m_role)
				# self.m_currentRoom.m_countAgent -= 1
				self.SetUseCoordRoom(False)
				self.m_prevActivity = self.m_currentActivity
				if self.m_target != None:
					self.m_target.SetAvailable(True)
					self.m_target = None
				if isActivityDone:
					self.m_currentActivity.CalculateEffects(self)
				self.ClearSuspendForNextActivity()
				if self.m_currentActivity.m_ID == self.m_bioActivityToTrigger:
					self.m_bioActivityToTrigger = ""
				self.m_lastActivity = self.m_currentActivity.m_ID
				if (isActivityDone and self.m_currentActivity.m_next != "-"):
					Global.Logger.LogDebug("set activity "+self.m_role+" by 6\n")
					self.m_currentActivity = self.GetActivityById(self.m_currentActivity.m_next)
					Global.Logger.LogDebug("Go go nexon ranger "+self.m_currentActivity.m_ID+"\n")
					Global.Logger.LogDebug("sertatu1 "+self.m_currentActivity.m_ID+" "+str(self.m_currentActivity.m_status)+"\n")
				else:
					Global.Logger.LogDebug("set activity "+self.m_role+" by 5\n")
					self.m_currentActivity = None
					if self.m_pendingActivity != None:
						if self.m_pendingActivity.m_status == Common.ACT_STATUS_PAUSED:
							Global.Logger.LogDebug("set activity "+self.m_role+" by 4\n")
							self.m_currentActivity = self.m_pendingActivity
							Global.Logger.LogDebug("goto d31\n")
							self.m_currentActivity.GoTo()
							self.ActivityLog("Switch activity to "+self.m_currentActivity.m_ID+" at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
						self.m_pendingActivity = None
				for property in self.m_bioProperty:
					if property == None:
						continue
					property.m_relatedActivity = None		
		
		if self.m_bioActivityToTrigger == "" and not inStair and (self.m_currentActivity == None or self.m_currentActivity.IsDone() or self.m_currentActivity.m_status == Common.ACT_STATUS_SUSPEND or self.m_currentActivity.m_interrupt[Common.INT_CAN_BE_INTERRUPTED]):
			interruptChecking = self.m_bioActivityToTrigger == "" and self.m_currentActivity != None and (not self.m_currentActivity.IsDone()) and self.m_currentActivity.m_interrupt[Common.INT_CAN_BE_INTERRUPTED]
			actList = []
			for act in self.m_activityList:
				custard = self.m_activityList[act].CanStart(self)
				# Global.Logger.LogDebug("acut "+act+" "+str(custard)+"\n")
				if custard and not self.m_activityList[act].m_isBioActivity and self.IsMultiValid(act):# and (not interruptChecking or self.m_activityList[act].m_interrupt[Common.INT_CAN_INTERRUPT]):
					actList.append(self.m_activityList[act])
			
			Global.Logger.LogDebug("Activity Calculation: Timed:"+Global.g_timer.GetFormattedHour()+"\n")
			self.Log("Activity Calculation:\n")
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
					
					bioDelta += (PROPERTY_CODE[i]+":"+Fmt(delta) +" - ")
				
				act.m_score /= 8
				
				act.m_emotionalScore = 0
				actDebugStr += (" FisioDelta:"+bioDelta+" FisioScore:"+Fmt(act.m_score)+"\n")#+" EmoFactor:"+Fmt(self.m_emotionalTotal)+" EmoStd:"+Fmt(act.m_emotionalStandard)
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
				self.Log(actDebugStr)
			
			for act in actToRemove:
				actList.remove(act)
			
			actList.sort(key = lambda x: x.m_emotionalScore, reverse = True)
			
			Global.Logger.LogDebug("Activity Emotional Multiplication:\n")
			self.Log("Activity Emotional Multiplication:\n")
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
				# Global.Logger.LogDebug("lasto "+(self.m_lastActivity if self.m_lastActivity != None else "Neona")+"\n")
				# if self.m_lastActivity != None:
					# Global.Logger.LogDebug(str(self.GetActivityById(self.m_lastActivity).m_matrix)+"\n")
				actDebugStr = "Activity: "+act.m_ID
				actDebugStr += " EmoScore:"+Fmt(act.m_emotionalScore)+" Multiplier:"+Fmt(curMultiplier)
				# if self.m_lastActivity != None:
					# Global.Logger.LogDebug(str(self.GetActivityById(self.m_lastActivity).m_matrix.keys()))
				Global.Logger.LogDebug("Calc avatar "+self.m_lastActivity+" "+act.m_ID+"\n")
				advantage = act.m_planProperty[Common.PLAN_PROPERTY_ADVANTAGE] + (0 if self.m_lastActivity == None else self.GetActivityById(self.m_lastActivity).m_matrix[act.m_ID])
				act.m_planScore += act.m_planProperty[Common.PLAN_PROPERTY_ADVANTAGE] + (0 if self.m_lastActivity == None else self.GetActivityById(self.m_lastActivity).m_matrix[act.m_ID])
				rule = (act.m_planProperty[Common.PLAN_PROPERTY_AUTHORITY] * act.m_planProperty[Common.PLAN_PROPERTY_OBEDIENCE] * 0) #dummy value 0; fill it with agent existance at home
				act.m_planScore += (act.m_planProperty[Common.PLAN_PROPERTY_AUTHORITY] * act.m_planProperty[Common.PLAN_PROPERTY_OBEDIENCE]) #dummy value 0; fill it with agent existance at home
				need = act.m_planProperty[Common.PLAN_PROPERTY_URGENCY]
				envUrgency = act.CalculateEnvUrgency(self)
				act.m_planScore += (act.m_planProperty[Common.PLAN_PROPERTY_URGENCY] + envUrgency)
				act.m_planScore /= 4
				
				actDebugStr += " Wish: "+Fmt(wish)+" Advantage: "+Fmt(advantage)+" Rule: "+Fmt(rule)+" Need: "+Fmt(need)+" PlanScore: "+Fmt(act.m_planScore)+" EnvironmentUrgency: "+Fmt(envUrgency)
				
				act.m_score += act.m_timeScore + act.m_planScore
				
				if act.m_ID == "A61":
					act.m_score *= 5
				elif act.m_ID == "A45":
					act.m_score *= 10
				
				actDebugStr += " TotalScore:"+Fmt(act.m_score)+"\n"
				
				# act.m_score *= curMultiplier
				lastEmoScore = act.m_emotionalScore
				Global.Logger.LogDebug(actDebugStr)
				self.Log(actDebugStr)
			
			actList.sort(key = lambda x: x.m_score,reverse = True)
			
			Global.Logger.LogDebug("Activity sorted by score:\n")
			self.Log("Activity sorted by score:\n")
			for act in actList:
				Global.Logger.LogDebug(act.m_ID+" score "+str(act.m_score)+"\n")
				self.Log(act.m_ID+" score "+str(act.m_score)+"\n")
			
			while(len(actList) > 0):
				debugStr = "Check ability:"+actList[0].m_ID+" Standard:"+Fmt(actList[0].m_physicalStandard)+" Current:"+Fmt(self.m_currentAbility)
				if self.m_currentAbility < actList[0].m_physicalStandard and (self.m_currentActivity == None or self.m_currentActivity.m_ID != actList[0].m_ID):
					actList[0].SetToIncidental()
					debugStr += " Move to incidental\n"
					Global.Logger.LogDebug(debugStr)
					self.Log(debugStr)
					incidentalAct.append(actList.pop(0))
				else:
					Global.Logger.LogDebug(debugStr+" OK\n")
					self.Log(debugStr+" OK\n")
					
					lastActID = self.m_currentActivity.m_ID if self.m_currentActivity != None else "-"
					Global.Logger.LogDebug("Alast "+lastActID+" "+actList[0].m_activitySet+"\n")
					if (actList[0].m_activitySet == "-"):
						if self.m_currentActivity == None or lastActID != actList[0].m_ID:
							Global.Logger.LogDebug("set activity "+self.m_role+" by 3\n")
							if self.m_currentActivity == None or self.m_currentActivity.m_status < Common.ACT_STATUS_RUN:
								self.SetState(STATE_IDLE)
								# self.ActivityLog("Idle 8\n")
							if self.m_currentActivity != None and not self.m_currentActivity.IsDone():
								self.m_pendingActivity = self.m_currentActivity
								self.m_pendingActivity.Pause()
							self.m_currentActivity = actList[0]
					else:
						traceAct = actList[0]
						actSet = actList[0].m_activitySet[:3]
						if self.m_currentActivity == None or (not self.m_currentActivity.m_activitySet.startswith(actSet)):
							if len(traceAct.m_prequisite) > 0:
								parentAct = self.GetActivityById(traceAct.m_prequisite[0])
								while (parentAct != None and parentAct.m_activitySet.startswith(actSet)):
									traceAct = parentAct
									parentAct = None
									for pAct in traceAct.m_prequisite:
										testAct = self.GetActivityById(pAct)
										if testAct.m_activitySet.startswith(actSet):
											parentAct = testAct
											break
									if parentAct != None and parentAct.m_isBioActivity:
										break
								if parentAct != None and parentAct.m_isBioActivity:
									actList.pop(0)
									continue
							Global.Logger.LogDebug("set activity "+self.m_role+" by 2\n")
							if self.m_currentActivity == None or self.m_currentActivity.m_status < Common.ACT_STATUS_RUN:
								self.SetState(STATE_IDLE)
							if self.m_currentActivity != None and not self.m_currentActivity.IsDone():
								self.m_pendingActivity = self.m_currentActivity
								# self.ActivityLog("Idle 7\n")
							self.m_currentActivity = traceAct
					if lastActID != self.m_currentActivity.m_ID:
						# if self.GetActivityById(lastActID).m_isIncidental:
							# self.m_lastActivity = lastActID
						self.SetState(STATE_WAIT)
					
					break
			
			# if len(actList) > 0:
				# lastActID = self.m_currentActivity.m_ID if self.m_currentActivity != None else "-"
				# Global.Logger.LogDebug("Alast "+lastActID+" "+actList[0].m_activitySet+"\n")
				# if (actList[0].m_activitySet == "-"):
					# if self.m_currentActivity == None or lastActID != actList[0].m_ID:
						# Global.Logger.LogDebug("set activity "+self.m_role+" by 3\n")
						# if self.m_currentActivity == None or self.m_currentActivity.m_status < Common.ACT_STATUS_RUN:
							# self.SetState(STATE_IDLE)
							# # self.ActivityLog("Idle 8\n")
						# if self.m_currentActivity != None and not self.m_currentActivity.IsDone():
							# self.m_pendingActivity = self.m_currentActivity
						# self.m_currentActivity = actList[0]
				# else:
					# traceAct = actList[0]
					# actSet = actList[0].m_activitySet[:3]
					# if self.m_currentActivity == None or (not self.m_currentActivity.m_activitySet.startswith(actSet)):
						# if len(traceAct.m_prequisite) > 0:
							# parentAct = self.GetActivityById(traceAct.m_prequisite[0])
							# while (parentAct != None and parentAct.m_activitySet.startswith(actSet)):
								# traceAct = parentAct
								# parentAct = None
								# for pAct in traceAct.m_prequisite:
									# testAct = self.GetActivityById(pAct)
									# if testAct.m_activitySet.startswith(actSet):
										# parentAct = testAct
										# break
						# Global.Logger.LogDebug("set activity "+self.m_role+" by 2\n")
						# if self.m_currentActivity == None or self.m_currentActivity.m_status < Common.ACT_STATUS_RUN:
							# self.SetState(STATE_IDLE)
						# if self.m_currentActivity != None and not self.m_currentActivity.IsDone():
							# self.m_pendingActivity = self.m_currentActivity
							# # self.ActivityLog("Idle 7\n")
						# self.m_currentActivity = traceAct
				# if lastActID != self.m_currentActivity.m_ID:
					# # if self.GetActivityById(lastActID).m_isIncidental:
						# # self.m_lastActivity = lastActID
					# self.SetState(STATE_WAIT)
		# Global.Logger.LogDebug("act statt "+self.m_currentActivity.m_ID+" "+str(self.m_currentActivity.m_status)+" "+str(self.m_currentActivity.IsDone())+"\n")
		if self.m_currentActivity != None  and (not self.m_currentActivity.IsDone()) and (not self.m_currentActivity.IsRunning()) and self.m_state != STATE_MOVE and self.m_state != STATE_MOVE_PA and self.m_currentActivity.m_status != Common.ACT_STATUS_GOTO:
			Global.Logger.LogDebug("goto 4 "+self.m_currentActivity.m_ID+" "+str(self.m_currentActivity.m_status)+"\n")
			self.m_currentActivity.GoTo()
			Global.Logger.LogDebug("Cinteract "+self.m_currentActivity.m_ID+" "+str(self.m_currentActivity.m_currentInteractAgent != None)+"\n")
			if self.m_currentActivity.m_currentInteractAgent != None:
				Global.Logger.LogDebug("Iraque "+self.m_currentActivity.m_currentInteractAgent.m_role+" follow "+str(self.m_currentActivity.m_currentInteractAgent.m_followedAgent != None)+"\n")
				if self.m_currentActivity.m_currentInteractAgent.m_followedAgent != None:
					Global.Logger.LogDebug("Follow role "+self.m_currentActivity.m_currentInteractAgent.m_followedAgent.m_role+"\n")
					
			if self.m_currentActivity.m_currentInteractAgent != None and self.m_currentActivity.m_currentInteractAgent.m_followedAgent != None and self.m_currentActivity.m_currentInteractAgent.m_followedAgent.m_role != self.m_role:
				self.m_currentActivity.Suspend()
				self.m_currentActivity.SetToIncidental()
				self.ActivityLog("Set "+self.m_currentActivity.m_ID+" to incidental due interact agent still interact with other agent at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
			else:
				self.ActivityLog("Switch activity to "+self.m_currentActivity.m_ID+" at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
				self.CheckFollowingAgent()
				if self.m_state != STATE_CHECK_PA and self.m_state != STATE_PREMOVE_PA and self.m_state != STATE_MOVE_PA and self.m_pendingActivity == None:
					self.SetState(STATE_CHECK_PA)
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
			Global.Logger.LogDebug("setbound "+self.m_role+" "+str(area)+"\n")
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
	
	def GeneratePath(self, start, end, stair = None, exactEnd = False, insertCurPos = True):
		curFloor = PathFinding.Map.FindPointInFloor(start)
		nextFloor = PathFinding.Map.FindPointInFloor(end)
		
		if curFloor != -1 and nextFloor != -1:
			if curFloor == nextFloor:
				stair = None
			else:
				self.needStair = True
				stairIndex = "STAIR_"+str(curFloor)
				stair = next(entry for entry in Agent.s_entryPointList if entry.target.m_id == stairIndex)
		
		if stair != None:
			end = stair.pos
			Global.Logger.LogDebug("have stair "+str(stair.pos)+"\n")
		else:
			Global.Logger.LogDebug("no stair\n")
		
		path = []
		if start == end:
			path.append(start)
			path.append(start)
			Global.Logger.LogDebug("start end saming\n")
		else:
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
			return []
		
		#path found
		if self.oldEntryPoint != None and path[0] != self.pos and insertCurPos:
			path.insert(0,self.pos)
		
		if self.needStair:
			path.append(stair.target.m_targetPoint)
		elif not exactEnd and (self.m_targetRoom == None or self.m_targetRoom.IsInRoom(self.pos)) and self.entryPoint.pos != self.entryPoint.target.m_targetPoint:
			path.append(self.entryPoint.target.m_targetPoint)
		# self.m_pathIndex = 1
		#print path
		Global.Logger.LogDebug(self.m_role+" Path "+str(path)+"\n")
		Global.Logger.DumpDebug()
		return path
	
	def CheckStartMovement(self):
		if self.m_currentActivity == None:
			Global.Logger.LogDebug("StartCheckmove no activity\n")
			return
		if not self.m_shouldUpdate:
			Global.Logger.LogDebug("StartCheckmove waiting shouldupdate\n")
			return
		Global.Logger.LogDebug(self.m_role + " StartCheckMove "+self.m_currentActivity.m_ID+" "+str(self.m_state)+" "+str(self.m_following)+"\n")
		if self.m_currentActivity.m_status == Common.ACT_STATUS_GOTO and self.m_state != STATE_MOVE and self.m_state != STATE_MOVE_PA:
			if self.m_following and self.m_followedAgent.m_currentActivity.m_followMovement:
				self.m_targetRoom = self.m_followedAgent.m_targetRoom
				self.ActivityLog("Moving to "+self.m_targetRoom.m_name+"\n")
			elif self.m_followedAgent != None:
				return
			else:
				roomName = self.m_currentActivity.GetTargetRoom()
				Global.Logger.LogDebug("Check startmove "+self.m_currentActivity.m_ID+" "+roomName+"\n")
				if (roomName == "Agent"):
					interactAgent = self.m_currentActivity.GetInteractAgent()#next((agent for agent in Agent.agentList if (agent.m_role == self.m_currentActivity.m_interactAgent)), None)
					if interactAgent != None:
						self.m_targetRoom = interactAgent.m_currentRoom
						Global.Logger.LogDebug("Interact agen room "+self.m_targetRoom.m_name)
					else:
						Global.Logger.LogDebug("Interact agen kopongga\n")
				else:
					# Global.Logger.LogDebug("Rukiane = "+self.m_currentActivity.m_ID+"|"+str(roomName)+"|"+str(self.m_currentActivity.m_rooms)+" "+"\n")
					# Global.Logger.DumpDebug()
					#print "rumina "+roomName
					self.m_targetRoom = next((room for room in Global.g_myHouse.m_rooms if room.m_name == roomName),None)
					Global.Logger.LogDebug("Normal room "+self.m_targetRoom.m_name)
			self.m_targetType = TARGET_ROOM
			Global.Logger.LogDebug("kapurt cadf "+str(self.m_targetRoom.IsInRoom(self.pos)))
			if not self.m_targetRoom.IsInRoom(self.pos):
				Global.Logger.LogDebug("kapurt assu "+str(self.m_state))
				if self.m_state == STATE_CHECK_PA:
					self.m_postActivityStops = self.CheckPostActivity()
					Global.Logger.LogDebug("kapurt dsfsfw "+str(len(self.m_postActivityStops)))
					if len(self.m_postActivityStops) > 0:
						self.myPath = []
						if self.entryPoint.pos != self.pos:
							self.myPath.append(self.pos)
							start = self.entryPoint.pos
						else:
							start = self.pos
						
						for stop in self.m_postActivityStops:
							path = self.GeneratePath(start,stop)
							start = stop
							self.myPath.extend(path)
						self.m_pathIndex = 1
						self.recalculateMoveDir()
						self.SetState(STATE_PREMOVE_PA)
					elif self.m_preState == STATE_MOVE:
						self.SetState(STATE_MOVE)
					else:
						self.SetState(STATE_IDLE)
						# self.ActivityLog("Idle 6\n")
				Global.Logger.LogDebug("kapurt cuodd "+str(self.m_state))
				if self.m_state != STATE_CHECK_PA and self.m_state != STATE_PREMOVE_PA and self.m_state != STATE_MOVE_PA:
					Global.Logger.LogDebug(self.m_role+" state fintar "+str(self.m_state)+"\n")
					start = self.pos
					# shouldUseOldEntry = self.oldEntryPoint != None
					self.FindTargetAndEntryPointForObject(CommonEnum.CP_ROOM)
					# stateOk = (self.m_state == STATE_MOVE or self.m_preState == STATE_MOVE)
					# if self.oldEntryPoint != None and self.myPath != None:
						# oldEntry = TranslateToGridPos(self.oldEntryPoint.pos,self.m_myFloorIndex)
						# oldEntry = PathFinding.TranslateToRealPos(oldEntry,self.m_myFloorIndex)
						# pointForOldEntry = Point3d(oldEntry[0],oldEntry[1],0)
						# Global.Logger.LogDebug("eldunari "+str(pointForOldEntry)+" "+str(self.m_pathIndex)+"\n")
						# Global.Logger.LogDebug("patikong "+str(self.myPath)+"\n")
						# shouldUseOldEntry = pointForOldEntry in self.myPath
						# Global.Logger.LogDebug("sudarsoa "+str(shouldUseOldEntry)+"\n")
						# if shouldUseOldEntry:
							# indexOldEntry = self.myPath.index(pointForOldEntry)
							# shouldUseOldEntry = indexOldEntry == 1 and indexOldEntry >= self.m_pathIndex
					# if self.oldEntryPoint != None and ((shouldUseOldEntry and not stateOk) or (not shouldUseOldEntry and stateOk)):
						# start = self.oldEntryPoint.pos
					
					self.needStair = (self.m_targetRoom.m_floorIndex != self.m_myFloorIndex)
					Global.Logger.LogDebug("RoomName "+self.m_targetRoom.m_name+" Coord "+str(self.m_targetRoom.GetTargetCoord(self.m_roomCoordIndex))+"\n")
					Global.Logger.LogDebug("Floor "+str(self.m_targetRoom.m_floorIndex)+" "+str(self.m_myFloorIndex)+"\n")
					Global.Logger.LogDebug("NeedStair "+str(self.needStair)+"\n")
					
					# self.m_roomCoordIndex = self.m_targetRoom.GetAvailableCoord()
					targetCoord = self.m_targetRoom.GetTargetCoord(self.m_roomCoordIndex)
					self.SetUseCoordRoom(True)
					if self.needStair:
						stairIndex = "STAIR_"+str(self.m_myFloorIndex)
						stairEntry = next(entry for entry in Agent.s_entryPointList if entry.target.m_id == stairIndex)
						self.myPath = self.GeneratePath(start,targetCoord, stairEntry)
					else:
						self.myPath = self.GeneratePath(start,targetCoord)
					
					if self.myPath == None or len(self.myPath) == 0:
						Global.Logger.LogDebug("path da nehi, recal with oldie\n")
						if self.oldEntryPoint != None:
							start = self.oldEntryPoint.pos
							if self.needStair:
								stairIndex = "STAIR_"+str(self.m_myFloorIndex)
								stairEntry = next(entry for entry in Agent.s_entryPointList if entry.target.m_id == stairIndex)
								self.myPath = self.GeneratePath(start,targetCoord, stairEntry)
							else:
								self.myPath = self.GeneratePath(start,targetCoord)
							Global.Logger.LogDebug("nupaterp "+str(self.myPath)+"\n")
					
					self.m_pathIndex = 1
					self.recalculateMoveDir()
					self.SetState(STATE_PRE_MOVE)
			else:
				cancel, recalculatePath, newPath = self.CheckTerms(True)
				if cancel:
					return
				# if not self.CheckReqResource():
					# return
				if recalculatePath:
					self.myPath = newPath
					self.m_pathIndex = 1
					self.recalculateMoveDir()
					Global.Logger.LogDebug("recalcio")
					self.m_targetType = TARGET_POINT
					self.SetUseCoordRoom(False)
					self.SetState(STATE_MOVE)
				else:
					self.m_targetType = TARGET_NONE
					self.m_currentActivity.Start(self.m_role)
					self.ActivityLog("Starting "+self.m_currentActivity.m_ID+" at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
					if not self.m_currentActivity.m_auto and self.m_target != None and self.m_target.m_powerCons > 0:
						self.m_target.StartUsage(self.m_currentActivity.m_ID, agent = self.m_role)
					self.SetState(STATE_WAIT)
				# self.m_currentRoom.m_countAgent += 1
		# Global.Logger.LogDebug("EndCheckMove\n")
	
	#update pergerakan dan posisi agent
	def UpdateAgentMovement(self, dt):
		print(self.pos)
		if self.m_currentActivity != None and self.m_currentActivity.m_status == Common.ACT_STATUS_SUSPEND:
			Global.Logger.LogDebug("activity agent "+self.m_role+" suspended, no move\n")
			return
		
		self.CheckStartMovement()
		Global.Logger.LogDebug(self.m_role+" Update movement dt = "+str(dt)+" state "+str(self.m_state)+"\n")
		Global.Logger.DumpDebug()
		# if ((self.m_currentActivity == None or self.m_currentActivity.m_status == Common.ACT_STATUS_GOTO) and not self.m_shouldUpdate):
			# return
		if self.m_state != STATE_MOVE and self.m_state != STATE_MOVE_PA:
			if self.m_state == STATE_PRE_MOVE:
				self.SetState(STATE_MOVE)
				if not (self.m_following and self.m_followedAgent.m_currentActivity.m_followMovement):
					self.ActivityLog("Moving to "+self.m_targetRoom.m_name+"\n")
			if self.m_state == STATE_PREMOVE_PA:
				self.SetState(STATE_MOVE_PA)
			return
		# self.CheckDoor()
		# if not doorOk:
			# return
		
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
				Global.Logger.LogDebug("bokcahuu "+str(blockDir.X)+" " +str(blockDir.Y)+"\n")
				blockDir = Vector3f.Divide(blockDir,blockDir.Length)
				dotP = (blockDir.X*self.moveDir.X) + (blockDir.Y*self.moveDir.Y)
				Global.Logger.LogDebug("modar "+str(self.moveDir.X)+" " +str(self.moveDir.Y)+"\n")
				Global.Logger.LogDebug("datas "+str(dotP)+"\n")
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
					self.SetUseCoordRoom(True)
				midPath = self.GeneratePath(self.pos,myNextDest)
				
				#No path found. Wait a moment
				if midPath == None:
					self.blockCounter += 1
					if self.blockCounter > 10 and self.m_myIndex > self.m_blockedBy and self.m_pathIndex > 2:
						Global.Logger.LogDebug("presepos 5 "+str(self.pos)+" "+str(self.moveDir)+" "+str(self.m_speedFactor)+ "\n")
						self.pos = rs.PointAdd(self.pos,(Vector3d.Multiply(self.moveDir,self.m_speedFactor) * (-1)))
						Global.Logger.LogDebug("sepos 5 "+str(self.pos)+"\n")
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
			Global.Logger.LogDebug("presepos 4 "+str(self.pos)+" "+str(self.moveDir)+" "+str(distanceCovered)+ "\n")
			endPos = rs.PointAdd(self.pos,Vector3d.Multiply(self.moveDir,distanceCovered))
			door = self.CheckIntersectDoor(self.pos, endPos)
			ok = True
			if door != None:
				ok = self.CheckOpenDoor(door)
			if not ok:
				return
			self.pos = endPos
			Global.Logger.LogDebug("sepos 4 "+str(self.pos)+ "\n")
		else:
			#already close with destination
			remainingDistance = distanceCovered - distance
			while (remainingDistance > 0) and (self.m_pathIndex < len(self.myPath)):
				Global.Logger.LogDebug("presepos 3 "+str(self.pos)+" "+str(destination)+ "\n")
				endPos = destination
				door = self.CheckIntersectDoor(self.pos, endPos)
				ok = True
				if door != None:
					ok = self.CheckOpenDoor(door)
				if not ok:
					return
				self.pos = endPos
				Global.Logger.LogDebug("sepos 3 "+str(self.pos)+ "\n")
				self.m_pathIndex+=1
				if self.m_pathIndex < len(self.myPath):
					self.recalculateMoveDir()
					destination  = self.myPath[self.m_pathIndex]
					distance = self.pos.DistanceTo(destination)
					if remainingDistance < distance:
						Global.Logger.LogDebug("presepos 2 "+str(self.pos)+" "+str(self.moveDir)+" "+str(remainingDistance)+ "\n")
						endPos = rs.PointAdd(self.pos,Vector3d.Multiply(self.moveDir,remainingDistance))
						door = self.CheckIntersectDoor(self.pos, endPos)
						ok = True
						if door != None:
							ok = self.CheckOpenDoor(door)
						if not ok:
							return
						self.pos = endPos
						Global.Logger.LogDebug("sepos 2 "+str(self.pos)+"\n")
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
					destination  = self.myPath[self.m_pathIndex]
					self.recalculateMoveDir()
					self.needStair = False
					distance = self.pos.DistanceTo(destination)
					if remainingDistance < distance:
						Global.Logger.LogDebug("presepos 1 "+str(self.pos)+" "+str(self.moveDir)+" "+str(remainingDistance)+ "\n")
						endPos = rs.PointAdd(self.pos,Vector3d.Multiply(self.moveDir,remainingDistance))
						door = self.CheckIntersectDoor(self.pos, endPos)
						ok = True
						if door != None:
							ok = self.CheckOpenDoor(door)
						if not ok:
							return
						self.pos = endPos
						Global.Logger.LogDebug("sepos 1 "+str(self.pos)+"\n")
					remainingDistance = remainingDistance - distance
				else:
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
							
						self.m_currentActivity.Start(self.m_role)
						self.ActivityLog("Starting "+self.m_currentActivity.m_ID+" at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
						hasEffectOverride = False
						if self.m_target != None:
							for effect in self.m_currentActivity.m_effect[self.m_currentActivity.m_targetRoom]:
								if effect[0] == self.m_target.m_id:
									hasEffectOverride = True
									break
						
						if not self.m_currentActivity.m_auto and self.m_target != None and self.m_target.m_powerCons > 0 and not hasEffectOverride:
							self.m_target.StartUsage(self.m_currentActivity.m_ID, agent = self.m_role)
						# self.m_currentRoom.m_countAgent += 1
						self.SetState(STATE_WAIT)
						
						Global.Logger.LogDebug("Try starting activity DONE\n")
					else:
						self.SetState(STATE_WAIT)
						return
		# for room in Global.g_myHouse.m_rooms:
			# if room.IsInRoom(self.pos):
				# self.m_currentRoom = room
				# Global.Logger.LogDebug("akorom "+self.m_role+" "+str(self.pos)+" "+self.m_currentRoom.m_name+"\n")
				# break
		Global.Logger.LogDebug(self.m_role+" Target type "+str(self.m_targetType))
		if(self.m_targetType == TARGET_ROOM):
			Global.Logger.LogDebug(" target room "+self.m_targetRoom.m_name)
		Global.Logger.LogDebug("\n")
		
		Global.Logger.LogDebug("apira "+str(self.IsArriveInRoom())+" "+str(self.m_shouldUpdate))
		if self.IsArriveInRoom():# and self.m_shouldUpdate:
			cancel, recalculatePath, newPath = self.CheckTerms(False)
			if cancel:
				return
			# recalculatePath = False
			# cancel, stopPlaces = self.m_currentActivity.CheckTerms(self)
			# if cancel:
				# self.m_currentActivity.NextTargetRoom()
				# if (self.m_currentActivity.GetTargetRoom() == "None"):
					# self.m_currentActivity.Suspend()
					# self.SetUseCoordRoom(False)
					# Global.Logger.LogDebug("lonker1\n")
					# self.m_currentActivity.SetToIncidental()
					# self.ClearSuspendForNextActivity(self.m_currentActivity.m_ID)
				# else:
					# Global.Logger.LogDebug("goto 3\n")
					# self.m_currentActivity.GoTo()
					# self.CheckFollowingAgent()
					# self.SetState(STATE_WAIT)
				# return
			
			# start = self.pos
			# Global.Logger.LogDebug("Sophian "+str(self.pos)+"\n")
			# newPath = []
			# if len(stopPlaces) > 0:
				# for stops in stopPlaces:
					# for ep in Agent.s_entryPointList:
						# if ep.target.m_id == stops:
							# if ep.target.m_type == "Lamp":
								# self.m_targetRoom.SetLampTurn(self, stops, True)
							# elif ep.target.m_type == "Fan":
								# ep.target.StartUsage(self.m_currentActivity.m_ID, agent = self.m_role)
							# path = self.GeneratePath(start,ep.pos)
							# newPath.extend(path)
							# start = ep.pos
							# recalculatePath = True
							# break
				
			
			# Global.Logger.LogDebug("act device "+str(self.m_currentActivity.m_device)+"\n")
			# hasDevice, device = self.m_targetRoom.HasAndAvailable(self.m_currentActivity.m_device[self.m_currentActivity.m_targetRoom])
			# Global.Logger.LogDebug("device "+str(hasDevice)+" "+str(device)+"\n")
			# Global.Logger.DumpDebug()
			# if hasDevice:
				# for ep in Agent.s_entryPointList:
					# if ep.target.m_id == device:
						# self.FindTargetAndEntryPointForObject(ep.target.m_id)
						# self.SetUseCoordRoom(False)
						# path = self.GeneratePath(start,ep.pos)
						# newPath.extend(path)
						# start = ep.pos
						# recalculatePath = True
						# self.m_target = ep.target
						# self.m_target.SetAvailable(False)
						# break
			# elif (self.m_currentActivity.m_device[self.m_currentActivity.m_targetRoom] != "-"):
				# self.m_currentActivity.NextTargetRoom()
				# if (self.m_currentActivity.GetTargetRoom() == "None"):
					# self.m_currentActivity.Suspend()
					# self.m_currentActivity.SetToIncidental()
					# self.SetUseCoordRoom(False)
					# Global.Logger.LogDebug("lonker3\n")
					# self.ClearSuspendForNextActivity(self.m_currentActivity.m_ID)
				# else:
					# Global.Logger.LogDebug("goto 2\n")
					# self.m_currentActivity.GoTo()
					# self.CheckFollowingAgent()
					# self.SetState(STATE_WAIT)
				# return
				# # path = self.GeneratePath(start,self.m_targetRoom.m_targetCoord)
			# elif recalculatePath:
				# Global.Logger.LogDebug("pukawan "+self.m_role+" "+str(self.m_useCoordRoom)+"\n")
				# Global.Logger.LogDebug("pokato "+self.m_role+" "+str(newPath[-1])+" "+str(self.myPath[-1])+"\n")
				# path = self.GeneratePath(newPath[-1],self.myPath[-1])
				# newPath.extend(path)
				# #newPath = self.GeneratePath(start,self.m_targetRoom.m_targetCoord)
			# Global.Logger.LogDebug("newpath "+str(newPath)+" reek "+str(recalculatePath)+"\n")
			
			# if not self.CheckReqResource():
				# return
			
			if recalculatePath:
				self.myPath = newPath
				self.m_pathIndex = 1
				self.recalculateMoveDir()
				Global.Logger.LogDebug("recalc")
				self.m_targetType = TARGET_POINT
				self.SetUseCoordRoom(False)
				self.SetState(STATE_MOVE)
		# if self.m_targetType == TARGET_ROOM and self.IsArriveInRoom():
			# self.GenerateAndCheckPreActivityList()
		
	def CheckReqResource(self):
		Global.Logger.LogDebug("req resource "+str(self.m_currentActivity.m_requiredResource)+"\n")
		if len(self.m_currentActivity.m_requiredResource[self.m_currentActivity.m_targetRoom]) > 0:
			if not self.m_currentActivity.CheckResource(self.m_targetRoom, self):
				self.m_currentActivity.NextTargetRoom()
				if (self.m_currentActivity.GetTargetRoom() != "None"):
					# self.m_currentActivity.Suspend()
					# self.m_currentActivity.SetToIncidental()
					# self.ActivityLog("Set "+self.m_currentActivity.m_ID+" to incidental at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
					# self.SetUseCoordRoom(False)
					# self.ClearSuspendForNextActivity(self.m_currentActivity.m_ID)
					# Global.Logger.LogDebug("suspend\n")
					# if self.m_currentActivity.m_ID == self.m_bioActivityToTrigger:
						# self.m_bioActivityToTrigger = ""
					# return True
				# else:
					Global.Logger.LogDebug("goto 1\n")
					self.m_currentActivity.GoTo()
					self.ActivityLog("Move to next room "+self.m_currentActivity.GetTargetRoom()+" at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
					self.CheckFollowingAgent()
					self.SetState(STATE_IDLE)
				# self.ActivityLog("Idle 5\n")
				return False
		return True
	
	def CheckTerms(self, startInRoom):
		if self.m_currentActivity.m_status == Common.ACT_STATUS_SUSPEND:
			return True, False, []
			
		Global.Logger.LogDebug("ageranta "+str(startInRoom)+"\n")
		recalculatePath = False
		cancel, stopPlaces = self.m_currentActivity.CheckTerms(self)
		cancel |= (not self.CheckReqResource())
		if cancel:
			self.m_currentActivity.NextTargetRoom()
			if (self.m_currentActivity.GetTargetRoom() == "None"):
				self.m_currentActivity.Suspend()
				self.SetUseCoordRoom(False)
				if not self.m_currentActivity.m_auto and self.m_target != None:
					self.m_target.SetAvailable(True)
					self.m_target = None
				Global.Logger.LogDebug("goto c31\n")
				self.m_currentActivity.SetToIncidental()
				self.ActivityLog("Set "+self.m_currentActivity.m_ID+" to incidental at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
				self.ClearSuspendForNextActivity(self.m_currentActivity.m_ID)
				if self.m_currentActivity.m_ID == self.m_bioActivityToTrigger:
					self.m_bioActivityToTrigger = ""
			else:
				Global.Logger.LogDebug("goto 3\n")
				self.m_currentActivity.GoTo()
				self.ActivityLog("Move to next room "+self.m_currentActivity.GetTargetRoom()+" at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
				self.CheckFollowingAgent()
			# self.ActivityLog("Idle 4\n")
			self.SetState(STATE_IDLE)
			return True, recalculatePath, []
		
		start = self.pos
		if startInRoom and self.pos != self.entryPoint.pos:
			start = self.entryPoint.pos
		Global.Logger.LogDebug("Sophian "+str(self.pos)+"\n")
		newPath = []
		if len(stopPlaces) > 0:
			for stops in stopPlaces:
				for ep in Agent.s_entryPointList:
					if ep.target.m_id == stops:
						if ep.target.m_type == "Lamp":
							self.m_targetRoom.SetLampTurn(self, stops, True)
						elif ep.target.m_type == "Fan":
							ep.target.StartUsage(self.m_currentActivity.m_ID, agent = self.m_role)
						path = self.GeneratePath(start,ep.pos, exactEnd=True)
						Global.Logger.LogDebug("Extending path for device "+stops+" "+str(path)+"\n")
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
					self.SetUseCoordRoom(False)
					path = self.GeneratePath(start,ep.pos, insertCurPos = not recalculatePath)
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
				self.ActivityLog("Set "+self.m_currentActivity.m_ID+" to incidental at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
				self.SetUseCoordRoom(False)
				Global.Logger.LogDebug("goto b31\n")
				self.ClearSuspendForNextActivity(self.m_currentActivity.m_ID)
				if self.m_currentActivity.m_ID == self.m_bioActivityToTrigger:
					self.m_bioActivityToTrigger = ""
			else:
				Global.Logger.LogDebug("goto 2\n")
				self.m_currentActivity.GoTo()
				self.CheckFollowingAgent()
			# self.ActivityLog("Idle 3\n")
			self.SetState(STATE_IDLE)
			return True, recalculatePath, newPath
			# path = self.GeneratePath(start,self.m_targetRoom.m_targetCoord)
		elif recalculatePath:
			Global.Logger.LogDebug("nuparta "+str(newPath)+"\n")
			Global.Logger.LogDebug("pukawan "+self.m_role+" "+str(self.m_useCoordRoom)+"\n")
			if self.myPath != None:
				Global.Logger.LogDebug("pokato "+self.m_role+" "+str(newPath[-1])+" "+str(self.myPath[-1])+"\n")
				isTarget = False
				for ep in Agent.s_entryPointList:
					if ep.target.m_targetPoint == self.myPath[-1] and ep.pos != self.myPath[-1]:
						isTarget = True
						break
				newPathEnd = self.myPath[-1]
				if isTarget:
					newPathEnd = self.myPath[-2]
				path = self.GeneratePath(newPath[-1],newPathEnd, insertCurPos = False)
				newPath.extend(path)
				if isTarget:
					newPath.append(self.myPath[-1])
			#newPath = self.GeneratePath(start,self.m_targetRoom.m_targetCoord)
		Global.Logger.LogDebug("newpath "+str(newPath)+" reek "+str(recalculatePath)+"\n")
		return False, recalculatePath, newPath
		
	def FindTargetAndEntryPointForObject(self, ID):
		if self.m_state != STATE_MOVE or self.m_state != STATE_MOVE_PA:
			self.oldEntryPoint = self.entryPoint
		if ID == CommonEnum.CP_ROOM:
			self.m_roomCoordIndex = self.m_targetRoom.GetAvailableCoord()
			targetCoord = self.m_targetRoom.GetTargetCoord(self.m_roomCoordIndex)
			self.SetUseCoordRoom(True)
			self.entryPoint = EntryPoint.EntryPoint(targetCoord,self.m_targetRoom.m_floorIndex)
			self.entryPoint.target = Target.Target(self.m_targetRoom.m_floorIndex,CommonEnum.RF_NONE, "-", targetCoord,"TMP_CENTER")
		else:
			self.entryPoint = next(entry for entry in Agent.s_entryPointList if entry.target.m_id == ID)
		Global.Logger.LogDebug(self.m_role+" find entry for "+ID+" "+str(self.entryPoint.pos)+"\n")
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
			Global.Logger.LogDebug("pekadut "+effect[0].m_name+" "+effect[1]+" "+str(effect[2])+" "+str(effect[3]))
			effect[3] -= 1
			if effect[3] <= 0:
				if effect[1] in effect[0].m_resource.keys():
					effect[0].m_resource[effect[1]][0] += effect[2]
				else:
					generalRoom = Global.g_myHouse.FindGeneralRoomForResource(effect[1])
					if generalRoom != None:
						generalRoom.m_resource[effect[1]][0] += effect[2]
			
			Activity.Activity.s_pendingEffect.remove(effect)
	
	def CheckPostActivity(self):
		Global.Logger.LogDebug("Checkpostact\n")
		stops = []
		if self.m_prevActivity != None:
			room = self.m_currentRoom
			postActivity = self.m_prevActivity.GetPostActivity()
			Global.Logger.LogDebug("Campia "+self.m_prevActivity.m_ID+" "+str(postActivity)+"\n")
			if len(self.m_prevActivity.m_rooms) > 0:
				roomName = self.m_prevActivity.m_rooms[self.m_prevActivity.m_lastUsedRoom]
				Global.Logger.LogDebug("cingkasu "+str(self.m_prevActivity.m_lastUsedRoom)+" "+roomName+"\n")
				actRoom = next((rom for rom in Global.g_myHouse.m_rooms if(rom.m_name == roomName)), None)
				if actRoom != None:
					room = actRoom
			for postAct in postActivity:
				Global.Logger.LogDebug("Posta "+postAct+"\n")
				if postAct == "L2":
					Global.Logger.LogDebug("Cumatra "+room.m_name+" "+str(room.CountAgentInRoom())+"\n")
					if room.CountAgentInRoom() <= 1:
						lamps = room.GetLampToTurn(False)
						self.Log("Post Activity: Turn OFF lamp "+str(lamps)+"\n")
						for lampId in lamps:
							objLamp = next((entry for entry in Agent.s_entryPointList if entry.target.m_id == lampId), None)
							if objLamp != None:
								stops.append(objLamp.pos)
								room.SetLampTurn(self, lampId, False)
				elif postAct == "D2" or postAct == "E2":
					hasDevice, active, device = room.HasAndActive(self.m_prevActivity.m_device[self.m_prevActivity.m_targetRoom])
					if hasDevice and active:
						deviceObj = next((trgt for trgt in Agent.s_possibleTarget if trgt.m_id == device), None)
						if deviceObj != None and postAct == "E2":
							self.Log("Post Activity: Turn OFF device "+device+"\n")
							deviceObj.StopUsage(self.m_role)
		
			hasFan, active, fanDevice = room.HasAndActive("Fan")
			if hasFan and active:
				fanObj = next((entry for entry in Agent.s_entryPointList if entry.target.m_id == fanDevice), None)
				self.Log("Post Activity: Turn OFF Fan "+fanDevice+"\n")
				fanObj.target.StopUsage(self.m_role)
				stops.append(fanObj.pos)
		
		return stops
	
	def SetFollowing(self, agent, following):
		Global.Logger.LogDebug("Set following to "+str(following)+" by "+agent.m_role+"\n")
		self.m_following = following
		self.m_followedAgent = agent if following else None
	
	def ForceStartActivity(self, activity):
		self.SetUseCoordRoom(False)
		if self.m_currentActivity != None and not self.m_currentActivity.m_auto and self.m_target != None:
			self.m_target.SetAvailable(True)
			self.m_target = None
		if self.m_currentActivity != None:
			if not self.m_currentActivity.m_auto and self.m_target != None:
				self.m_target.SetAvailable(True)
				self.m_target = None
			self.m_currentActivity.Stop()
		Global.Logger.LogDebug("set activity "+self.m_role+" by 1\n")
		self.m_currentActivity = self.GetActivityById(activity)
		for property in self.m_bioProperty:
			if activity == property.m_relatedActivityId:
				property.m_relatedActivity = self.m_currentActivity
		self.m_currentActivity.GoTo()
		self.ActivityLog("Switch activity to "+self.m_currentActivity.m_ID+" due "+self.m_followedAgent.m_role+" at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
		Global.Logger.LogDebug("Forcing start activity "+self.m_role+" "+activity+"\n")
		Global.Logger.DumpDebug()
		Global.Logger.LogDebug("Forcing start activityw "+self.m_currentActivity.m_ID+"\n")
		Global.Logger.DumpDebug()
		# self.ActivityLog("Idle 2\n")
		self.SetState(STATE_IDLE)
	
	def SetUseCoordRoom(self, use):
		Global.Logger.LogDebug("cuorum "+self.m_role+" "+str(self.m_useCoordRoom)+" "+str(use)+"\n")
		if use:
			if len(self.m_useCoordRoom) > 0:
				coordRoom = next((room for room in Global.g_myHouse.m_rooms if room.m_name == self.m_useCoordRoom[0]), None)
				if coordRoom:
					coordRoom.SetUseCoord(self.m_useCoordRoom[1], False)
			self.m_targetRoom.SetUseCoord(self.m_roomCoordIndex, use)
			self.m_useCoordRoom = [self.m_targetRoom.m_name, self.m_roomCoordIndex]
		elif len(self.m_useCoordRoom) > 0:
			coordRoom = next((room for room in Global.g_myHouse.m_rooms if room.m_name == self.m_useCoordRoom[0]), None)
			if coordRoom:
				coordRoom.SetUseCoord(self.m_useCoordRoom[1], use)
			self.m_useCoordRoom = []
			self.m_roomCoordIndex = -1
		Global.Logger.LogDebug("endosko "+self.m_role+" "+str(self.m_useCoordRoom)+" "+str(use)+"\n")
		
	def CheckFollowingAgent(self):
		Global.Logger.LogDebug("Check following agent "+("None" if self.m_currentActivity.m_currentInteractAgent == None else self.m_currentActivity.m_currentInteractAgent.m_role)+"\n")
		if self.m_currentActivity.m_currentInteractAgent != None:
			Global.Logger.LogDebug("Follower act = "+self.m_currentActivity.m_followerActivity)
		if self.m_currentActivity.m_currentInteractAgent != None and self.m_currentActivity.m_followerActivity != "-":
			self.m_currentActivity.m_currentInteractAgent.SetFollowing(self, True)
			self.m_currentActivity.m_currentInteractAgent.ForceStartActivity(self.m_currentActivity.m_followerActivity)
	
	def WriteBioReport(self):
		outputFilePath = reportPath+self.m_role+"_fis_report.csv"
		columnName = []
		for property in self.m_bioProperty:
			if property == None:
				continue
			columnName.extend(property.K_COLUMN_NAME)
		
		with open(outputFilePath, mode='w+') as outputFile:
			outputWriter = csv.writer(outputFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
			outputWriter.writerow(columnName)
			for record in self.m_bioRecord:
				outputWriter.writerow(record)
		
		self.ExportLog()
	
	def Log(self, logText):
		self.m_log.append(logText)
	
	def ActivityLog(self, logText):
		self.m_activityLog += logText
	
	def ExportLog(self):
		outputFilePath = reportPath+self.m_role+"_log.txt"
		with open(outputFilePath, mode='w+') as outputFile:
			for log in self.m_log:
				outputFile.write(log)
		outputFilePath = reportPath+self.m_role+"_activity_log.txt"
		with open(outputFilePath, mode='w+') as outputFile:
			outputFile.write(self.m_activityLog)
	
	def IsMultiValid(self, actId):
		multiValid = True
		if actId in Activity.Activity.s_multiAgent:
			multiValid = Activity.Activity.s_multiAgent[actId]
		
		if not multiValid:
			for agent in Agent.agentList:
				if agent != self:
					if agent.m_currentActivity != None and agent.m_currentActivity.m_ID == actId:
						return False
		
		return True
	
	def CheckDoor(self):
		if self.m_passingDoor != None:
			if self.m_passingDoor.m_frameBB.Contains(self.pos) != Rhino.Geometry.PointContainment.Inside:
				if "R2" in self.m_currentActivity.GetPostActivity():
					self.m_passingDoor.Close()
					self.m_passingDoor = None
			# return True
		
		# if self.m_targetRoom != None and self.m_targetRoom.IsInRoom(self.pos):
			# for door in Global.g_myHouse.m_doors:
				# if door.m_room == self.m_targetRoom.m_name:
					# if self.m_currentActivity != None:
						# act = self.m_currentActivity.m_doorAct[self.m_currentActivity.m_targetRoom]
						# if door.IsClosed() and act != "-":
							# if act == "CC":
								# self.m_currentActivity.NextTargetRoom()
								# if (self.m_currentActivity.GetTargetRoom() == "None"):
									# self.m_currentActivity.Suspend()
									# self.SetUseCoordRoom(False)
									# Global.Logger.LogDebug("goto a31\n")
									# self.m_currentActivity.SetToIncidental()
									# self.ActivityLog("Set "+self.m_currentActivity.m_ID+" to incidental at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
									# self.ClearSuspendForNextActivity(self.m_currentActivity.m_ID)
									# if self.m_currentActivity.m_ID == self.m_bioActivityToTrigger:
										# self.m_bioActivityToTrigger = ""
								# else:
									# Global.Logger.LogDebug("goto 31\n")
									# self.m_currentActivity.GoTo()
									# self.ActivityLog("Move to next room "+self.m_currentActivity.GetTargetRoom()+" at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
									# self.CheckFollowingAgent()
									# # self.ActivityLog("Idle 1\n")
									# self.SetState(STATE_IDLE)
								# return False
							# else:
								# self.m_passingDoor = door
								# door.Open()
								# return True
				# elif door.IsClosed():
					# door.Open()
					# return True
				# break
		# return True
		
		# for door in Global.g_myHouse.m_doors:
			# if door.m_frameBB.Contains(self.pos):
				# if self.m_targetRoom != None and self.m_targetRoom.m_name == door.m_room and self.m_currentActivity != None:
					# act = self.m_currentActivity.m_doors[self.m_currentActivity.m_targetRoom]
					# if door.IsClosed() and act != "-":
						# if act == "CC":
							# self.m_currentActivity.NextTargetRoom()
							# if (self.m_currentActivity.GetTargetRoom() == "None"):
								# self.m_currentActivity.Suspend()
								# self.SetUseCoordRoom(False)
								# Global.Logger.LogDebug("goto a31\n")
								# self.m_currentActivity.SetToIncidental()
								# self.ActivityLog("Set "+self.m_currentActivity.m_ID+" to incidental at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
								# self.ClearSuspendForNextActivity(self.m_currentActivity.m_ID)
								# if self.m_currentActivity.m_ID == self.m_bioActivityToTrigger:
									# self.m_bioActivityToTrigger = ""
							# else:
								# Global.Logger.LogDebug("goto 31\n")
								# self.m_currentActivity.GoTo()
								# self.ActivityLog("Move to next room "+self.m_currentActivity.GetTargetRoom()+" at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
								# self.CheckFollowingAgent()
								# # self.ActivityLog("Idle 1\n")
								# self.SetState(STATE_IDLE)
							# return False
						# else:
							# self.m_passingDoor = door
							# door.Open()
					# return True
				# elif door.IsClosed():
					# door.Open()
					# return True
				# break
		# return True
	
	def CheckIntersectDoor(self, start, end):
		Global.Logger.LogDebug("Check intersect door "+str(start)+" "+str(end)+"\n")
		line = Line(start, end)
		for door in Global.g_myHouse.m_doors:
			locStr = ""
			for poin in door.m_frameBB.Points:
				locStr += (str(poin.Location) + " ")
			Global.Logger.LogDebug("Box checki "+door.m_room+" "+locStr+" "+str(Rhino.Geometry.Intersect.Intersection.CurveCurve(line.ToNurbsCurve(), door.m_frameBB, 0, 0).Count)+"\n")
			intersect = Rhino.Geometry.Intersect.Intersection.CurveCurve(line.ToNurbsCurve(), door.m_frameBB, 0, 0)
			for ii in intersect:
				Global.Logger.LogDebug("isect "+str(ii)+"\n")
			if intersect.Count > 0 or door.m_frameBB.Contains(start) == Rhino.Geometry.PointContainment.Inside or door.m_frameBB.Contains(end) == Rhino.Geometry.PointContainment.Inside:
				Global.Logger.LogDebug("cross the door\n")
				Global.Logger.DumpDebug()
				return door
		Global.Logger.DumpDebug()
		return None
	
	def CheckOpenDoor(self, door):
		if self.m_targetRoom != None and door.m_room == self.m_targetRoom.m_name:
			act = self.m_currentActivity.m_doorAct[self.m_currentActivity.m_targetRoom]
			if door.IsClosed() and act != "-":
				if act == "CC":
					self.m_currentActivity.NextTargetRoom()
					if (self.m_currentActivity.GetTargetRoom() == "None"):
						self.m_currentActivity.Suspend()
						self.SetUseCoordRoom(False)
						Global.Logger.LogDebug("goto a31\n")
						self.m_currentActivity.SetToIncidental()
						self.ActivityLog("Set "+self.m_currentActivity.m_ID+" to incidental at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
						self.ClearSuspendForNextActivity(self.m_currentActivity.m_ID)
						if self.m_currentActivity.m_ID == self.m_bioActivityToTrigger:
							self.m_bioActivityToTrigger = ""
					else:
						Global.Logger.LogDebug("goto 31\n")
						self.m_currentActivity.GoTo()
						self.ActivityLog("Move to next room "+self.m_currentActivity.GetTargetRoom()+" at Day "+str(Global.g_timer.GetDay())+" at "+Global.g_timer.GetFormattedHour()+"\n")
						self.CheckFollowingAgent()
						# self.ActivityLog("Idle 1\n")
						self.SetState(STATE_IDLE)
					return False
				else:
					Global.Logger.LogDebug("Set passing door "+self.m_role+" by act "+self.m_currentActivity.m_ID+" room "+door.m_room+"\n")
					self.m_passingDoor = door
					door.Open()
				return True
			elif not door.IsClosed():
				self.m_passingDoor = door
				Global.Logger.LogDebug("Set passing door not closed "+self.m_role+" by act "+self.m_currentActivity.m_ID+" room "+door.m_room+"\n")
		else:
			door.Open()
		return True

	def GetCurrentRoomSocial(self):
		val = 0
		for agent in Agent.agentList:
			if agent != self and agent.m_currentRoom == self.m_currentRoom:
				Global.Logger.LogDebug("social "+str(self.m_socialValue)+"\n")
				Global.Logger.DumpDebug()
				val += self.m_socialValue[agent.m_role]
		val /= len(Agent.agentList)
		return val
		
#-----------------------------------------------------------------------------------------------------------------------------------------
def LoadSocialization():
	Global.Logger.LogDebug("Load social\n")
	socialFile = resPath+"social.csv"
	with open(socialFile) as csvfile:
		reader = csv.reader(csvfile)
		roles = []
		for row in reader:
			if row[0] == "ID":
				for val in row:
					if val == "ID":
						continue
					roles.append(val)
				continue
			curRole = row[0]
			socialValue = {}
			for i in range(0, len(roles)):
				socialValue[roles[i]] = float(row[i + 1])
			Global.Logger.LogDebug("Socava "+curRole +" "+str(socialValue)+"\n")
			for agent in Agent.agentList:
				Global.Logger.LogDebug("cekira "+agent.m_role+" "+curRole+"\n")
				if agent.m_role == curRole:
					agent.m_socialValue = socialValue
					Global.Logger.LogDebug("Mestaika "+agent.m_role +" "+str(agent.m_socialValue)+"\n")
	Global.Logger.LogDebug("Demonia\n")
	Global.Logger.DumpDebug()

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