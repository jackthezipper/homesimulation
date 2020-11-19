import time
import csv

SCALE_TIME = 1

ENERGY_USER			= 0
ENERGY_RATE			= ENERGY_USER + 1
ENERGY_STARTTIME	= ENERGY_RATE + 1
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

#--------------------------------------------------------------------------------------------------------------
#-------------Room Class---------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------

class Room:
	def __init__(self,name,temperature,light):
		m_name = name
		self.m_temperature = temperature
		self.m_light = light

#--------------------------------------------------------------------------------------------------------------
#-------------House Class--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
TMPL_ENERGY_TYPE	= 0
TMPL_ENERGY_SUPPLY	= TMPL_ENERGY_TYPE + 1
TMPL_ENERGY_PRICE	= TMPL_ENERGY_SUPPLY + 1

#resource enum
RES_WATER		= 0
RES_ELECTRICITY	= RES_WATER + 1
RES_GAS			= RES_ELECTRICITY + 1
RES_FOOD		= RES_GAS + 1
RES_FOOD_MTRIAL	= RES_FOOD + 1
RES_READ_MTRIAL	= RES_FOOD_MTRIAL + 1
RES_TOTAL		= RES_READ_MTRIAL + 1

class House:
	def __init__(self):
		self.m_energies = []
		self.m_resources = [0 for i in range(0,RES_TOTAL)]
		self.loadHouseEnergy()
	
	def loadHouseEnergy(self):
		cFPath = ghenv.Component.OnPingDocument().FilePath
		cpath = cFPath[0:cFPath.rfind('\\')+1]
		my_path = cpath+'..\\res\\energy.csv'
		with open(filename) as csvfile:
			reader = csv.reader(csvfile)
			for row in reader:
				m_energies.Append(Energy(row[TMPL_ENERGY_TYPE],row[TMPL_ENERGY_SUPPLY],row[TMPL_ENERGY_PRICE]))