from enum import Enum

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

class BiologicalEnum(Enum):
	EXHAUSTED	= 0
	SLEEPY		= 1
	DIRTY		= 2
	URINATE		= 3
	DEFECATE	= 4
	ENERGY		= 5
	HUNGER		= 6
	THIRSTY		= 7
	ABILITY		= 8

class Activity:
	def __init__(self, ID, description):
		self.m_ID = ID
		self.m_desxription = description

class CoreActivity(Activity):
	def __init__(self, interruptProperty, timeProperty, rooms, planProperty, biologicalEffect)
		self.m_interruptProperty = interruptProperty
		self.m_timeProperty = timeProperty
		self.m_rooms = rooms
		self.m_planProperty = planProperty
		self.m_biologicalEffect = biologicalEffect
	
	#def SetBiologicalEffect(se)