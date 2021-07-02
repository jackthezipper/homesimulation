import math

import Common
import Config

HOUR_IN_DAY		= 24
MINUTE_IN_HOUR	= 60

#30 min -> 15 sec
TIMECONVERSION	= 2 #to multiply dt
TIMEFACTOR		= 1000 #to multiply waitTime

K_ADJUSTER = TIMEFACTOR / TIMECONVERSION

class Timer():
	s_timerInstance = None
	def __init__(self, format = Common.FORMAT_TIME_HOUR):
		self.m_format = format
		self.m_time = 0
		self.m_elapsedAdjuster = K_ADJUSTER
		self.m_time = MINUTE_IN_HOUR
	
	def GetHour(self):
		return int(math.floor(self.m_time / MINUTE_IN_HOUR) % HOUR_IN_DAY)
	
	def GetHourForTime(self,time):
		return int(math.floor(time / MINUTE_IN_HOUR) % HOUR_IN_DAY)
	
	def GetMinute(self):
		return (self.m_time % MINUTE_IN_HOUR)
	
	def GetDay(self):
		return int(self.m_time / (HOUR_IN_DAY * MINUTE_IN_HOUR))
	
	def Update(self, dt):
		self.m_elapsedAdjuster += dt
		if self.m_elapsedAdjuster > K_ADJUSTER:
			self.m_time += 1
			self.m_elapsedAdjuster -= K_ADJUSTER
	
	def GetFormattedHour(self):
		return "{:02d}:{:02d}".format(self.GetHour(), self.GetMinute())

def CreateInstance():
	Timer.s_timerInstance = Timer(Common.FORMAT_TIME_MINUTE)

def GetInstance():
	if Timer.s_timerInstance == None:
		CreateInstance()
	return Timer.s_timerInstance