import scriptcontext as sc

import CommonEnum
import Global

import random
import csv
import os
#find resources path
# sourceFilePath	= ghenv.Component.OnPingDocument().FilePath
sourceFilePath	= os.path.dirname(os.path.abspath(__file__))
sourceDirPath	= sourceFilePath[0:sourceFilePath.rfind('\\')+1]
resPath			= sourceDirPath+"res\\"+sc.sticky["MapName"]+"\\"


class InterruptProperty:
	def __init__(self, canInterrupt, canBeInterrupted):
		self.m_canInterrupt = canInterrupt
		self.m_canBeInterrupted = canBeInterrupted

class TimeProperty:
	def __init__(self, timeCanStartBegin, timeCanStartEnd, duration):
		self.m_timeCanStartBegin = timeCanStartBegin
		self.m_timeCanStartEnd = timeCanStartEnd
		self.m_duration = duration

class PlanningProperty:
	def __init__(self, planned, urgency, habit, rule):
		self.m_planned = planned
		self.m_urgency = urgency
		self.m_habit = habit
		self.m_rule = rule

#plan
PLAN_PLANNED	= 0
PLAN_HABIT		= PLAN_PLANNED + 1
PLAN_RULE		= PLAN_HABIT + 1
PLAN_TOTAL		= PLAN_RULE + 1

#biological effect index
BIO_EXHAUSTED	= 0
BIO_SLEEPY		= BIO_EXHAUSTED + 1
BIO_DIRTY		= BIO_SLEEPY + 1
BIO_URINATE		= BIO_DIRTY + 1
BIO_DEFECATE	= BIO_URINATE + 1
BIO_ENERGY		= BIO_DEFECATE + 1
BIO_HUNGER		= BIO_ENERGY + 1
BIO_THIRSTY		= BIO_HUNGER + 1
BIO_ABILITY		= BIO_THIRSTY + 1
BIO_TOTAL		= BIO_ABILITY + 1

#emotional-social index
ES_STRESS		= 0
ES_EMOTION		= ES_STRESS + 1
ES_MOOD			= ES_EMOTION + 1
ES_LONELINESS	= ES_MOOD + 1
ES_TOTAL		= ES_LONELINESS + 1

#------------------------------------------------------------------------------------------------------------
#-------------------Base Activity Class----------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
class Activity:
	def __init__(self, ID):
		self.m_ID = ID
		self.m_duration = 0
		self.m_runningTime = 0
	
	def UpdateTimer(self, dt):
		self.m_runningTime += dt
	
	def Start(self, runTime):
		self.m_runningTimeLeft = runTime
	
	def IsDone(self):
		return (self.m_runningTime <= self.m_duration)

	def GetDescription():
		return g_ActivityDB[self.m_ID]
#------------------------------------------------------------------------------------------------------------
#-------------------Core Activity Class----------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
class CoreActivity(Activity):
	def __init__(self, ID, chance, interruptProperty, timeProperty, planProperty, biologicalEffect, esFactor, agent):
		Activity.__init__(self, ID)
		self.m_chance = chance
		self.m_interruptProperty = interruptProperty
		self.m_timeProperty = timeProperty
		self.m_planProperty = planProperty
		self.m_biologicalEffect = biologicalEffect
		self.m_esFactor = esFactor
		self.m_agent = agent
		self.m_score = 0
	
	#menghitung skor aktivitas
	def CalculateActivityScore(self):
		self.m_score = 0
		factorCount = 0
		
		if not self.CanStartBase():
			return
		
		#kalkulasi rencana
		for i in range(0,PLAN_TOTAL):
			self.m_score += self.m_planProperty[i]
			factorCount += (1 if self.m_planProperty[i] != 0 else 0)
		
		#kalkulasi faktor biologi
		for i in range(0,BIO_TOTAL):
			self.m_score += self.m_biologicalEffect[i] * self.m_agent.m_myBioStatus[i]
			factorCount += abs(self.m_biologicalEffect[i])
		self.m_score /= factorCount
		
		#peluang
		self.m_score *= self.m_chance
		
		#kalkulasi faktor emosi-sosial
		for i in range(0,CommonEnum.ES_PROPERTY_COUNT):
			if self.m_esFactor[i] != 0:
				self.m_score *= self.m_agent.m_myESStatus[i]
	
	def CanInterrupt(self):
		return self.m_interruptProperty[CommonEnum.INTERRUPT_CAN_INTERRUPT]
	
	def CanBeInterrupted(self):
		return self.m_interruptProperty[CommonEnum.INTERRUPT_CAN_BE_INTERRUPTED]
	
	def Start(self, duration = 0):
		if duration == 0:
			duration = self.m_timeProperty[TIME_PROPERTY_DURATION]
		Activity.Start(self, duration)
	
	def CanStartBase(self):
		if self.m_timeProperty[CommonEnum.TIME_PROPERTY_STARTTIME_CANSTART][0] == -1:
			#can start any time
			return True
		
		startTime = Global.g_timer.ConvertTime(Global.g_timer.GetCurrentDay(), self.m_timeProperty[CommonEnum.TIME_PROPERTY_STARTTIME_CANSTART][0], self.m_timeProperty[CommonEnum.TIME_PROPERTY_STARTTIME_CANSTART][1])
		endTime = Global.g_timer.ConvertTime(Global.g_timer.GetCurrentDay(), self.m_timeProperty[CommonEnum.TIME_PROPERTY_ENDTIME_CANSTART][0], self.m_timeProperty[CommonEnum.TIME_PROPERTY_ENDTIME_CANSTART][1])
		return (Global.g_timer.m_time > startTime and Global.g_timer.m_time < endTime)

#------------------------------------------------------------------------------------------------------------
#-------------------Support Activity Class-------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

#support activity type
SA_TYPE_BEFORE	= 0
SA_TYPE_AFTER	= SA_TYPE_BEFORE + 1

class SupportActivity(Activity):
	def __init__(self, ID, habitFactor, duration, type):
		Activity.__init__(self, ID)
		self.m_habitFactor = habitFactor
		self.m_type = type
		self.m_duration = duration
	
	def IsActivityExecuted(self):
		return random.random() < self.m_habitFactor
	
	def GetDuration(self):
		return type == g_SupportActivityBeforeDB[self.m_ID][DB_SUPPORT_ACTIVITY_DURATION] if SA_TYPE_BEFORE else g_SupportActivityAfterDB[self.m_ID][DB_SUPPORT_ACTIVITY_DURATION]

#------------------------------------------------------------------------------------------------------------
#------------------General Stuff_----------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

#main activity
MAIN_ACTIVITY_ID	= 0
MAIN_ACTIVITY_DESC	= MAIN_ACTIVITY_ID + 1

#table support activty
TABLE_SUPPORT_ACTIVITY_ID		= 0
TABLE_SUPPORT_ACTIVITY_DESC		= TABLE_SUPPORT_ACTIVITY_ID + 1
TABLE_SUPPORT_ACTIVITY_DURATION	= TABLE_SUPPORT_ACTIVITY_DESC + 1

#DB support activty
DB_SUPPORT_ACTIVITY_DESC		= 0
DB_SUPPORT_ACTIVITY_DURATION	= TABLE_SUPPORT_ACTIVITY_DESC + 1

g_ActivityDB = {}
g_ActivityEffectRun = {}
g_ActivityEffectPending = {}
g_SupportActivityBeforeDB = {}
g_SupportActivityAfterDB = {}

def LoadGeneralActivityDB():
	tableFileName = resPath+"table_activity.csv"
	with open(tableFileName) as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			if row[MAIN_ACTIVITY_ID] == "ID":
				continue
			g_ActivityDB[row[MAIN_ACTIVITY_ID]] = [row[MAIN_ACTIVITY_DESC]]

def LoadActivityEffect():
	tableFileName = resPath+"table_effect_run.csv"
	with open(tableFileName) as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			if row[CommonEnum.TABLE_EFFECT_ID] == "ID":
				continue
			data = []
			for i in range(CommonEnum.TABLE_EFFECT_BIO_START, CommonEnum.TABLE_EFFECT_ES_START):
				data.append(float(row[i]))
			env = []
			for i in range(0,CommonEnum.EFFECT_ENVI_COUNT):
				obj = row[CommonEnum.TABLE_EFFECT_ENV_OBJ1 + i*2]
				if obj != "-":
					env.append([obj,int(row[CommonEnum.TABLE_EFFECT_ENV_VAL1 + i*2])])
			data.append(env)
			g_ActivityEffectRun[row[CommonEnum.TABLE_EFFECT_ID]] = data
	tableFileName = resPath+"table_effect_pending.csv"
	with open(tableFileName) as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			if row[CommonEnum.TABLE_EFFECT_ID] == "ID":
				continue
			data = []
			for i in range(CommonEnum.TABLE_EFFECT_BIO_START, CommonEnum.TABLE_EFFECT_ES_START):
				data.append(float(row[i]))
			env = []
			for i in range(0,CommonEnum.EFFECT_ENVI_COUNT):
				obj = row[CommonEnum.TABLE_EFFECT_ENV_OBJ1 + i*2]
				if obj != "-":
					env.append([obj,int(row[CommonEnum.TABLE_EFFECT_ENV_VAL1 + i*2])])
			data.append(env)
			g_ActivityEffectPending[row[CommonEnum.TABLE_EFFECT_ID]] = data

def GetActivityBioEffect(activityId, effect, run):
	if run:
		return g_ActivityEffectRun[activityId][effect]
	else:
		return g_ActivityEffectPending[activityId][effect]

def GetActivityESEffect(activityId, run):
	if run:
		return g_ActivityEffectRun[activityId][CommonEnum.BIOLOGICAL_PROPERTY_COUNT]
	else:
		return g_ActivityEffectPending[activityId][CommonEnum.BIOLOGICAL_PROPERTY_COUNT]

def GetActivityEnviEffect(activityId, run):
	if run:
		return g_ActivityEffectRun[activityId][len(g_ActivityEffectRun) - 1]
	else:
		return g_ActivityEffectPending[activityId][len(g_ActivityEffectPending) - 1]

def LoadSupportActivityDB():
	#support activity before
	tableFileName = resPath+"support_activity_before.csv"
	with open(tableFileName) as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			if row[TABLE_ID] == "ID":
				continue
			g_SupportActivityBeforeDB[TABLE_SUPPORT_ACTIVITY_ID] = [row[TABLE_SUPPORT_ACTIVITY_DESC],row[TABLESUPPORT_ACTIVITY_DURATION]]
	
	#support activity after
	tableFileName = resPath+"support_activity_after.csv"
	with open(tableFileName) as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			if row[TABLE_ID] == "ID":
				continue
			g_SupportActivityBeforeDB[TABLE_SUPPORT_ACTIVITY_ID] = [row[TABLE_SUPPORT_ACTIVITY_DESC],row[TABLE_SUPPORT_ACTIVITY_DURATION]]