import random

import csv
import os
#find resources path
# sourceFilePath	= ghenv.Component.OnPingDocument().FilePath
sourceFilePath	= os.path.dirname(os.path.abspath(__file__))
sourceDirPath	= sourceFilePath[0:sourceFilePath.rfind('\\')+1]
resPath			= sourceDirPath+"..\\res\\"


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
		self.m_runningTimeLeft = 0
	
	def UpdateTimeLeft(self, dt):
		if self.m_runningTimeLeft > 0:
			self.m_runningTimeLeft -= dt
		if self.m_runningTimeLeft < 0:
			self.m_runningTimeLeft = 0
	
	def Start(self, runTime):
		self.m_runningTimeLeft = runTime
	
	def IsDone(self):
		return (self.m_runningTimeLeft <= 0)

	def GetDescription():
		return g_ActivityDB[self.m_ID]
#------------------------------------------------------------------------------------------------------------
#-------------------Core Activity Class----------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
class CoreActivity(Activity):
	def __init__(self, ID, interruptProperty, timeProperty, planProperty, biologicalEffect, esFactor, agent):
		Activity.__init__(self, ID)
		self.m_interruptProperty = interruptProperty
		self.m_timeProperty = timeProperty
		self.m_planProperty = planProperty
		self.m_biologicalEffect = biologicalEffect
		self.m_esFactor = esFactor
		self.m_agent = agent
		self.m_score = 0
	
	#version using from rangkuma formula
	def CalculateActivityScore(self):
		self.m_score = 0
		factorCount = 0
		
		#calculating plan
		for i in range(0,PLAN_TOTAL):
			self.m_score += self.m_planProperty[i]
			factorCount += (1 if self.m_planProperty[i] != 0 else 0)
		
		#calculating biological factor
		for i in range(0,BIO_TOTAL):
			self.m_score += self.m_biologicalEffect[i] * self.m_agent.m_myBioStatus[i]
			factorCount += abs(self.m_biologicalEffect[i])
		self.m_score /= factorCount
		
		#calculating emotional effect
		for i in range(0,ES_TOTAL):
			if m_esFactor[i] != 0:
				self.m_score *= m_esFactor[i]

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
g_SupportActivityBeforeDB = {}
g_SupportActivityAfterDB = {}

def LoadGeneralActivityDB():
	tableFileName = resPath+"table_activity.csv"
	with open(tableFileName) as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			if row[TABLE_ID] == "ID":
				continue
			g_ActivityDB[row[MAIN_ACTIVITY_ID]] = [row[MAIN_ACTIVITY_DESC]]

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