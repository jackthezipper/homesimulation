from enum import Enum
import random

import csv
#find resources path
sourceFilePath	= ghenv.Component.OnPingDocument().FilePath
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

	def GetDescription():
		return g_ActivityDB[self.m_ID]
#------------------------------------------------------------------------------------------------------------
#-------------------Core Activity Class----------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
class CoreActivity(Activity):
	def __init__(self, ID, interruptProperty, timeProperty, planProperty, biologicalEffect, esFactor)
		Activity.__init__(self, ID)
		self.m_interruptProperty = interruptProperty
		self.m_timeProperty = timeProperty
		self.m_planProperty = planProperty
		self.m_biologicalEffect = biologicalEffect
		self.m_esFactor = esFactor
	
	#version using bio effect from agent
	def CalculateActivityScore(self, agentBiologicalEffect, agentESFactor):
		#current formula is:
		# (SUM(bio effect)/COUNT(bio effect))*MULTIPLY(es factor)
		totalScore = 0
		bioFactorCount = BIO_TOTAL
		for i in range(0,BIO_TOTAL):
			if (self.m_biologicalEffect[i] == 0):
				bioFactorCount -= 1
			else
				totalScore += agentBiologicalEffect[i]
		
		totalScore /= bioFactorCount
		
		for i in range(0,ES_TOTAL):
			if self.m_esFactor[i] > 0:
				totalScore *= agentESFactor[i]
		
		return totalScore
	
	#version using embedded in activity
	def CalculateActivityScore(self):
		#current formula is:
		# (SUM(bio effect)/COUNT(bio effect))*MULTIPLY(es factor)
		totalScore = 0
		bioFactorCount = BIO_TOTAL
		for i in range(0,BIO_TOTAL):
			totalScore += self.m_biologicalEffect[i]
			if (self.m_biologicalEffect[i] == 0):
				bioFactorCount -= 1
		
		totalScore /= bioFactorCount
		
		for i in range(0,ES_TOTAL):
			if self.m_esFactor[i] > 0:
				totalScore *= m_esFactor[i]
		
		return totalScore

#------------------------------------------------------------------------------------------------------------
#-------------------Support Activity Class-------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

#support activity type
SA_TYPE_BEFORE	= 0
SA_TYPE_AFTER	= SA_TYPE_BEFORE + 1

class SupportActivity(Activity):
	def __init__(self, ID, habitFactor, type):
		Activity.__init__(self, ID)
		self.m_habitFactor = habitFactor
		self.m_type = type
	
	def IsActivityExecuted(self):
		return random.random() < self.m_habitFactor
	
	def GetDuration(self):
		return type == SA_TYPE_BEFORE ? g_SupportActivityBeforeDB[self.m_ID][DB_SUPPORT_ACTIVITY_DURATION] : g_SupportActivityAfterDB[self.m_ID][DB_SUPPORT_ACTIVITY_DURATION]

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

def LoadGeneralActivityDB()
	tableFileName = resPath+"table_activity.csv"
	with open(tableFileName) as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			if row[TABLE_ID] == "ID"
				continue
			g_ActivityDB[row[MAIN_ACTIVITY_ID]] = [row[MAIN_ACTIVITY_DESC]]

def LoadSupportActivityDB()
	#support activity before
	tableFileName = resPath+"support_activity_before.csv"
	with open(tableFileName) as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			if row[TABLE_ID] == "ID"
				continue
			g_SupportActivityBeforeDB[TABLE_SUPPORT_ACTIVITY_ID] = [row[TABLE_SUPPORT_ACTIVITY_DESC],row[TABLESUPPORT_ACTIVITY_DURATION]]
	
	#support activity after
	tableFileName = resPath+"support_activity_after.csv"
	with open(tableFileName) as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			if row[TABLE_ID] == "ID"
				continue
			g_SupportActivityBeforeDB[TABLE_SUPPORT_ACTIVITY_ID] = [row[TABLE_SUPPORT_ACTIVITY_DESC],row[TABLE_SUPPORT_ACTIVITY_DURATION]]