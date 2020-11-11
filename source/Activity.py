from enum import Enum
import random

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
	def __init__(self, ID, description):
		self.m_ID = ID
		self.m_description = description

#------------------------------------------------------------------------------------------------------------
#-------------------Core Activity Class----------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
class CoreActivity(Activity):
	def __init__(self, ID, description, interruptProperty, timeProperty, rooms, planProperty, biologicalEffect, esFactor)
		Activity.__init__(self, ID, description)
		self.m_interruptProperty = interruptProperty
		self.m_timeProperty = timeProperty
		self.m_rooms = rooms
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
class SupportActivity(Activity):
	def __init__(self, ID, description, duration, habitFactor):
		Activity.__init__(self, ID, description)
		self.m_duration = duration
		self.m_habitFactor = habitFactor
	
	def IsActivityExecuted(self):
		return random.random() < self.m_habitFactor
