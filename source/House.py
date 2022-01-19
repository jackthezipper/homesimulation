import time
import CommonEnum
import csv
import os

import Target
import Global
import Timer
import Agent

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
		self.m_targetCoord = []
		self.m_curve = curve
		self.m_floorIndex = floorIndex
		self.m_items = []
		self.m_lamps = self.InitLamps(lamps)
		self.m_object = []
		self.m_resource = self.InitResource(resource)
		self.m_value = 0
		self.m_usage = 0
		self.m_tableLight = []
		self.m_tableTemperature = []
		self.m_countAgent = 0
	
	def SetLightAndTemperatureTable(self, tableLight, tableTemperature):
		self.m_light = tableLight
		self.m_temperature = tableTemperature
	
	def InitResource(self, resStr):
		resource = {}
		if resStr != None:
			resList = resStr.split("|")
			for res in resList:
				resComp = res.split(";")
				resource[resComp[0]] = [int(resComp[1]), len(resComp) > 2]
		return resource
		
	def InitLamps(self, lamps):
		if lamps != None:
			lampList = lamps.split(";")
			lampStat = []
			for lamp in lampList:
				lampStat.append([lamp,False])
			return lampStat
		return None
	
	def AddTargetCoord(self, coord):
		self.m_targetCoord.append([coord, False])
	
	def GetAvailableCoord(self):
		for i in range(0,len(self.m_targetCoord)):
			if not self.m_targetCoord[i][1]:
				return i
		return -1
	
	def SetUseCoord(self, index, use):
		Global.Logger.LogDebug("Set use "+self.m_name+" "+str(index)+" "+str(use)+"\n")
		if index != -1:
			self.m_targetCoord[index][1] = use
	
	def GetTargetCoord(self, index):
		return None if ((index == -1) or (index > len(self.m_targetCoord))) else self.m_targetCoord[index][0]
	
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
	
	def HasItem(self, itemType):
		items = itemType.split(";")
		Global.Logger.LogDebug("Checking item "+str(itemType)+" in room "+self.m_name+" itemlength +"+str(len(self.m_items))+"\n")
		Global.Logger.LogDebug("bleki "+str(self.m_items))
		for item in items:
			foundItem = next((roomItem for roomItem in self.m_items if roomItem.m_type == item), None)
			if foundItem:
				return True, foundItem
		return False, None
	
	def HasAndAvailable(self, itemType):
		hasItem, item = self.HasItem(itemType)
		
		if not hasItem or (not item.m_available):
			return False, None
		
		return hasItem, item.m_id
	
	def HasAndActive(self, itemType):
		Global.Logger.LogDebug("hagger "+itemType+"\n")
		hasItem, item = self.HasItem(itemType)
		if hasItem and item.m_usageStartTime > 0:
			return True, True, item.m_id
		return hasItem, False, (item.m_id if hasItem else None)
	
	def GetLampToTurn(self, turnOn = True):
		if self.m_lamps != None:
			lampToTurn = []
			for lamp in self.m_lamps:
				if lamp[1] != turnOn:
					lampToTurn.append(lamp[0])
			return lampToTurn
		return None
		
	def SetLampTurn(self, agent, lampId, turnOn):
		for lamp in self.m_lamps:
			if lamp[0] == lampId:
				lamp[1] = turnOn
				
				lampTarget = next((trgt for trgt in Agent.Agent.s_possibleTarget if trgt.m_id == lampId), None)
				if lampTarget != None:
					if turnOn:
						lampTarget.StartUsage("L1", agent = agent.m_role)
					else:
						lampTarget.StopUsage()
				
				break
	
	def CheckResource(self, resource, amount):
		# Global.Logger.LogDebug("RKey "+str(self.m_resource.keys())+"\n");
		# Global.Logger.LogDebug("RAmount "+resource+" "+str(amount)+"\n")
		# Global.Logger.LogDebug("Res "+str(self.m_resource)+"\n")
		return (resource in self.m_resource.keys()) and (amount <= self.m_resource[resource][0])
	
	def IsGeneralForResource(self, resourceType):
		Global.Logger.LogDebug("Check general room "+self.m_name+" res "+resourceType)
		Global.Logger.LogDebug("my res "+str(self.m_resource.keys())+"\n")
		Global.Logger.LogDebug("is in "+str(resourceType in self.m_resource.keys())+"\n")
		if (resourceType in self.m_resource.keys()):
			Global.Logger.LogDebug("is gen "+str(self.m_resource[resourceType][1])+"\n")
		return (resourceType in self.m_resource.keys()) and self.m_resource[resourceType][1]
	
	def ReportCurrentResource(self):
		Global.Logger.LogDebug("Resource for room "+self.m_name+"\n")
		if self.m_resource == None or len(self.m_resource) == 0:
			Global.Logger.LogDebug("No resource\n")
		else:
			for res in self.m_resource.keys():
				Global.Logger.LogDebug(res+" "+str(self.m_resource[res][0])+"\n")
	
	def UpdateLightAndTemperature(self):
		index = Global.g_timer.m_time / Timer.MINUTE_IN_HOUR
		self.m_temperature = self.m_tableTemperature[index]
		self.m_light = self.m_tableLight[index]
		
		hasLight, active, lightDevice = self.HasAndActive("Lamp")
		if hasLight and active:
			self.m_light += next(trgt for trgt in Agent.s_possibleTarget if trgt.m_id == lightDevice).m_envEffect[Common.EFFECT_LIGHT]
		
		hasFan, active, fanDevice = self.HasAndActive("Fan")
		if hasFan and active:
			self.m_temperature += next(trgt for trgt in Agent.s_possibleTarget if trgt.m_id == fanDevice).m_envEffect[Common.EFFECT_TEMPERATURE]
	
	def CountAgentInRoom(self):
		count = 0
		for agent in Agent.Agent.agentList:
			if self.IsInRoom(agent.pos):
				count += 1
		return count

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
		self.m_energyUsage = []
	
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
				amount += room.m_resource[resourceType][0]
		return amount
	
	def UseResource(self, resourceType, amount):
		roomWithResource = filter(lambda room: room.CheckResource(resourceType,0), self.m_rooms)
		roomWithResource.sort(key = lambda room: room.m_resource[resourceType][0], reverse = True)
		index = 0
		while amount > 0 and index < len(roomWithResource):
			roomWithResource[index].m_resource[resourceType][0] -= amount
			if roomWithResource[index].m_resource[resourceType][0] < 0:
				amount = -roomWithResource[index].m_resource[resourceType][0]
			else:
				amount = 0
			index += 1
	
	def CheckGeneralResource(self, resourceType, amount):
		roomWithResource = next((room for room in self.m_rooms if room.CheckResource(resourceType,amount) and room.IsGeneralForResource(resourceType)), None)
		return roomWithResource
	
	def RegisterEnergyUsage(self, usage):
		self.m_energyUsage.append(usage)
	
	def ReportEnergyUsage(self):
		for usage in self.m_energyUsage:
			Global.Logger.LogDebug("usage "+str(usage)+"\n")
	
	def FindGeneralRoomForResource(self, resourceType):
		roomWithResource = next((room for room in self.m_rooms if room.IsGeneralForResource(resourceType)), None)
		return roomWithResource
	
	def ReportResource(self):
		for room in self.m_rooms:
			room.ReportCurrentResource()
		Global.Logger.DumpDebug()