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
	
	def GetDay(self):
		return math.floor((self.m_time * TIMECONVERSION) / (TIMEFACTOR * MINUTE_IN_HOUR * HOUR_IN_DAY))
	
	def GetHour(self):
		return math.floor(((self.m_time * TIMECONVERSION) / (TIMEFACTOR * MINUTE_IN_HOUR)) % HOUR_IN_DAY)
	
	def GetMinute(self):
		return math.floor( ((self.m_time * TIMECONVERSION) / TIMEFACTOR) % MINUTE_IN_HOUR )