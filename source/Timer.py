import math

import Common
import Config
import scriptcontext as sc

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
	
	def GetHour(self, time = -1):
		if time == -1:
			time = self.m_time
		return int(math.floor(time / MINUTE_IN_HOUR) % HOUR_IN_DAY)
	
	def GetHourForTime(self,time):
		return int(math.floor(time / MINUTE_IN_HOUR) % HOUR_IN_DAY)
	
	def GetMinute(self, time = -1):
		if time == -1:
			time = self.m_time
		return (time % MINUTE_IN_HOUR)
	
	def GetDay(self, time = -1):
		if time == -1:
			time = self.m_time
		return int(time / (HOUR_IN_DAY * MINUTE_IN_HOUR))
	
	def GetWeek(self):
		return int(self.m_time / (HOUR_IN_DAY * MINUTE_IN_HOUR * 7))
	
	def Update(self, dt):
		if "SimulationSpeed" in sc.sticky:
			dt *= sc.sticky["SimulationSpeed"]
		self.m_elapsedAdjuster += dt
		if self.m_elapsedAdjuster > K_ADJUSTER:
			self.m_time += 1
			self.m_elapsedAdjuster -= K_ADJUSTER
	
	def GetTodayTime(self):
		return int(self.m_time % (HOUR_IN_DAY * MINUTE_IN_HOUR))
	
	def GetFormattedHour(self, time = -1):
		if time == -1:
			time = self.m_time
		return "{:02d}:{:02d}".format(self.GetHour(time), self.GetMinute(time))
	
	def GetFullFormattedTime(self, time = -1):
		if time == -1:
			time = self.m_time
		return "Day {} at {:02d}:{:02d}".format(self.GetDay(time), self.GetHour(time), self.GetMinute(time))
	
	def Reset(self):
		self.m_time = MINUTE_IN_HOUR
	
	@staticmethod
	def GetDayForTime(time):
		return int(time / (HOUR_IN_DAY * MINUTE_IN_HOUR))
	
	@staticmethod
	def GetFormattedHourInDay(time):
		hour = int(math.floor(time / MINUTE_IN_HOUR) % HOUR_IN_DAY)
		minute = (time % MINUTE_IN_HOUR)
		return "{:02d}:{:02d}".format(hour, minute)
	
	def ResetTimer(self):
		self.m_time = 0
		K_ADJUSTER = TIMEFACTOR / TIMECONVERSION
		if "SimulationSpeed" in sc.sticky:
			K_ADJUSTER /= sc.sticky["SimulationSpeed"]
		self.m_elapsedAdjuster = K_ADJUSTER
		self.m_time = MINUTE_IN_HOUR

def CreateInstance():
	Timer.s_timerInstance = Timer(Common.FORMAT_TIME_MINUTE)

def GetInstance():
	if Timer.s_timerInstance == None:
		CreateInstance()
	return Timer.s_timerInstance

def ResetTimer():
	Timer.s_timerInstance = None