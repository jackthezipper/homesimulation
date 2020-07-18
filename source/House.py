import time
SCALE_TIME = 1

ENERGY_USER = 0
ENERGY_RATE = ENERGY_USER + 1
ENERGY_STARTTIME = ENERGY_RATE + 1
class Energy:
	def __init__(self,type,supply,price):
		self.m_energyType = type
		self.m_maxSupply = supply
		self.m_price = price
		self.m_currentUser = []
		self.m_totalUsage = 0;
	
	def startUse(self,user,rate):
		startTime = int(time.time() * 1000)
		currentUse = self.getCurrentUsage()
		if (currentUse + rate) > self.m_maxSupply:
			return False
		self.m_currentUser.Append((user,rate,startTime))
		return True
	
	def doneUse(self,user):
		elm = next(item for item in self.m_currentUser if item[ENERGY_USER] == user)
		curTime = int(time.time() * 1000)
		self.m_totalUsage += ((elm[ENERGY_STARTTIME] - curTime) * elm[ENERGY_RATE] * SCALE_TIME)
		self.m_currentUser.remove(elm)
	
	def getCurrentUsage(self):
		currentUse = 0
		for elm in m_currentUser:
			currentUse += elm[ENERGY_RATE]
		return currentUse
	
	def getCurrentMoneySpent(self):
		totalUsage = self.m_totalUsage + self.getCurrentUsage()
		return totalUsage * self.m_price
	
	def resetUsage(self):
		self.m_totalUsage = 0;
		self.m_currentUser = []

class House:
	def __init__(self):
		self.m_energies = []