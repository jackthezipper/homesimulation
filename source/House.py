import time
import CommonEnum
import csv
import os

import Target
import Global

import Rhino as rh
from Rhino.Geometry import Curve, Point3d

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
	def __init__(self,name,temperature,light, curve, lamps, resource, floorIndex = 0):
		self.m_name = name
		self.m_temperature = temperature
		self.m_light = light
		self.m_targetCoord = Point3d(0,0,0)
		self.m_curve = curve
		self.m_floorIndex = floorIndex
		self.m_items = []
		self.m_lamps = self.InitLamps(lamps)
		self.m_object = []
		self.m_resource = resource
		
	def InitLamps(self, lamps):
		if lamps != None:
			lampList = lamps.split(";")
			lampStat = []
			for lamp in lampList:
				lampStat.append([lamp,False])
			return lampStat
		return None
	
	def SetTargetCoord(self, coord):
		Global.Logger.LogDebug("Add coord "+self.m_name+" "+str(coord)+"\n")
		self.m_targetCoord = coord
	
	def IsInRoom(self, point):
		return (self.m_curve.Contains(point) == rh.Geometry.PointContainment.Inside)
	
	def CheckAndAddItem(self, item):
		# print "vojo"
		# print item
		# print item.m_targetPoint
		# print("Room "+self.m_name+" check item "+str(item.m_id))
		# Global.Logger.LogDebug("Room "+self.m_name+" check item "+item.m_id+" "+str(item.m_type)+" "+str(item.m_targetPoint))
		# Global.Logger.LogDebug(" containment "+str(self.IsInRoom(item.m_targetPoint)))
		if self.IsInRoom(item.m_targetPoint):
			self.m_items.append(item)
			Global.Logger.LogDebug("Add "+item.m_id+" inside "+self.m_name+"\n")
			Global.Logger.DumpDebug()
			return True
		# Global.Logger.LogDebug(" outside\n")
		# Global.Logger.DumpDebug()
		return False
	
	def HasAndAvailable(self, itemType):
		items = itemType.split(";")
		Global.Logger.LogDebug("Checking item "+str(itemType)+" in room "+self.m_name+" itemlength +"+str(len(self.m_items))+"\n")
		for item in items:
			foundItem = next((roomItem for roomItem in self.m_item if roomItem.m_type.equals(item) and roomItem.m_available), None)
			if foundItem:
				return True, foundItem.m_id
		
		# for item in self.m_items:
			# Global.Logger.LogDebug("\titem "+str(item.m_type)+" "+str(item.m_available)+"\n")
			# if item.m_type == itemType and item.m_available:
				# Global.Logger.DumpDebug()
				# return True,item.m_id
		Global.Logger.DumpDebug()
		return False, None
	
	def GetLampToTurn(self, turnOn = True):
		if self.m_lamps != None:
			lampToTurn = []
			for lamp in self.m_lamps:
				if lamp[1] != turnOn:
					lampToTurn.append(lamp[0])
			return lampToTurn
		return None
		
	def SetLampTurn(self, lampId, turnOn):
		for lamp in self.m_lamps:
			if lamp[0] == lampId:
				lamp[1] = turnOn
				break
	
	def CheckResource(self, resource, amount):
		return (resource in self.m_resource.keys()) and (amount >= self.m_resource[resource])

#--------------------------------------------------------------------------------------------------------------
#-------------House Class--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
TMPL_ENERGY_TYPE	= 0
TMPL_ENERGY_SUPPLY	= TMPL_ENERGY_TYPE + 1
TMPL_ENERGY_PRICE	= TMPL_ENERGY_SUPPLY + 1

class House:
	def __init__(self):
		self.m_energies = []
		self.m_resources = [0 for i in range(0,CommonEnum.RES_TOTAL)]
		self.loadHouseEnergy()
		self.m_rooms = []
		self.m_envObj = {}
	
	def loadHouseEnergy(self):
		#cFPath = ghenv.Component.OnPingDocument().FilePath
		sourceFilePath	= os.path.dirname(os.path.abspath(__file__))
		sourceDirPath	= sourceFilePath[0:sourceFilePath.rfind('\\')+1]
		filename = sourceDirPath+'\\res\\energy.csv'
		with open(filename) as csvfile:
			reader = csv.reader(csvfile)
			for row in reader:
				self.m_energies.append(Energy(row[TMPL_ENERGY_TYPE],row[TMPL_ENERGY_SUPPLY],row[TMPL_ENERGY_PRICE]))
	
	def GetResourceAmount(self, resourceType):
		amount = 0
		for room in self.m_rooms:
			if room.CheckResource(resourceType,0):
				amount += room.m_resource[resourceType]
		return amount
	
	def GetResourceM(self, resourceType):
		amount = 0
		for room in self.m_rooms:
			if room.CheckResource(resourceType,0):
				amount += room.m_resource[resourceType]
		return amount