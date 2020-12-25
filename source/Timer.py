import math
#30 min -> 15 sec
TIMECONVERSION	= 2 #to multiply dt
TIMEFACTOR		= 1000 #to multiply waitTime

MINUTE_IN_HOUR	= 60
HOUR_IN_DAY		= 24

class Timer:
	def __init__(self):
		self.m_time = 0
	
	def Update(self, dt):
		self.m_time += dt
	
	def GetDay(self, time):
		return math.floor((time * TIMECONVERSION) / (TIMEFACTOR * MINUTE_IN_HOUR * HOUR_IN_DAY))
	
	def GetHour(self, time):
		return math.floor(((time * TIMECONVERSION) / (TIMEFACTOR * MINUTE_IN_HOUR)) % HOUR_IN_DAY)
	
	def GetMinute(self, time):
		return math.floor( ((time * TIMECONVERSION) / TIMEFACTOR) % MINUTE_IN_HOUR )
	
	def GetReadableTime(self, time):
		return self.GetDay(time), self.GetHour(time), self.GetMinute(time)
	
	def GetCurrentReadableTime(self):
		return self.GetReadableTime(self.m_time)
	
	def ConvertTime(self, day, hour, min):
		return ((((day * HOUR_IN_DAY) + hour) * MINUTE_IN_HOUR) + min) * TIMEFACTOR / TIMECONVERSION