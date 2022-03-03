import time
import CommonEnum
import csv
import os

import Target
import Global
import Timer
import Agent
import Common

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
		Global.Logger.LogDebug("liksato "+str(tableLight)+"\n")
		Global.Logger.LogDebug("etmpato "+str(tableTemperature)+"\n")
		Global.Logger.DumpDebug()
		self.m_tableLight = tableLight
		self.m_tableTemperature = tableTemperature
	
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
		return self.m_targetCoord[0][0] if ((index == -1) or (index > len(self.m_targetCoord))) else self.m_targetCoord[index][0]
	
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
		# Global.Logger.LogDebug("Checking item "+str(itemType)+" in room "+self.m_name+" itemlength +"+str(len(self.m_items))+"\n")
		# Global.Logger.LogDebug("bleki "+str(self.m_items))
		for item in items:
			foundItem = next((roomItem for roomItem in self.m_items if roomItem.m_type == item), None)
			if foundItem != None:
				return True, foundItem
		return False, None

	def FindItem(self, itemType):
		items = itemType.split(";")
		# Global.Logger.LogDebug("Checking item "+str(itemType)+" in room "+self.m_name+" itemlength +"+str(len(self.m_items))+"\n")
		for item in items:
			foundItem = filter(lambda roomItem: roomItem.m_type == item, self.m_items)# [(roomItem for roomItem in self.m_items if roomItem.m_type == item)]
			# Global.Logger.LogDebug("bleki "+str(foundItem)+"\n")
			if len(foundItem) > 0:
				return True, foundItem
		return False, None
	
	def HasAndAvailable(self, itemType):
		hasItem, items = self.FindItem(itemType)
		
		if not hasItem:
			return False, None
		
		for item in items:
			Global.Logger.LogDebug("Hatsuka "+item.m_id+" "+str(item.m_available))
			if item.m_available:
				return hasItem, item.m_id
		
		return False, None
	
	def HasAndActive(self, itemType):
		# Global.Logger.LogDebug("hagger "+itemType+"\n")
		hasItem, items = self.FindItem(itemType)
		if hasItem:
			# Global.Logger.LogDebug("tems "+str(items)+"\n")
			for item in items:
				# Global.Logger.LogDebug("teng "+str(item)+"\n")
				if item.m_usageStartTime > 0:
					return True, True, item.m_id
		return hasItem, False, (item.m_id if hasItem else None)
	
	def GetLampToTurn(self, turnOn = True):
		if self.m_lamps != None:
			lampToTurn = []
			for lamp in self.m_lamps:
				if lamp[1] != turnOn:
					lampToTurn.append(lamp[0])
			return lampToTurn
		return []
		
	def SetLampTurn(self, agent, lampId, turnOn):
		Global.Logger.LogDebug("Selamput "+agent.m_role+" room "+self.m_name+" "+str(lampId)+" "+str(turnOn)+"\n")
		for lamp in self.m_lamps:
			if lamp[0] == lampId:
				lamp[1] = turnOn
				
				lampTarget = next((trgt for trgt in Agent.Agent.s_possibleTarget if trgt.m_id == lampId), None)
				if lampTarget != None:
					if turnOn:
						lampTarget.StartUsage(agent.m_currentActivity.m_ID, agent = agent.m_role)
					else:
						lampTarget.StopUsage()
				
				break
	
	def CheckResource(self, resource, amount):
		# Global.Logger.LogDebug("RKey "+str(self.m_resource.keys())+"\n");
		# Global.Logger.LogDebug("RAmount "+resource+" "+str(amount)+"\n")
		# Global.Logger.LogDebug("Res "+str(self.m_resource)+"\n")
		return (resource in self.m_resource.keys()) and (amount <= self.m_resource[resource][0])
	
	def IsGeneralForResource(self, resourceType):
		# Global.Logger.LogDebug("Check general room "+self.m_name+" res "+resourceType)
		# Global.Logger.LogDebug("my res "+str(self.m_resource.keys())+"\n")
		# Global.Logger.LogDebug("is in "+str(resourceType in self.m_resource.keys())+"\n")
		# if (resourceType in self.m_resource.keys()):
			# Global.Logger.LogDebug("is gen "+str(self.m_resource[resourceType][1])+"\n")
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
		self.m_temperature = self.m_tableTemperature[index] if len(self.m_tableTemperature) > 0 else 21
		# Global.Logger.LogDebug("Update temperature "+self.m_name+" "+str(self.m_temperature))
		self.m_light = self.m_tableLight[index] if len(self.m_tableLight) > 0 else 666
		
		hasLight, active, lightDevice = self.HasAndActive("Lamp")
		if hasLight and active:
			self.m_light += next(trgt for trgt in Agent.Agent.s_possibleTarget if trgt.m_id == lightDevice).m_envEffect[Common.EFFECT_LIGHT]
		
		hasFan, active, fanDevice = self.HasAndActive("Fan")
		if hasFan and active:
			self.m_temperature += next(trgt for trgt in Agent.Agent.s_possibleTarget if trgt.m_id == fanDevice).m_envEffect[Common.EFFECT_TEMPERATURE]
		# Global.Logger.LogDebug(" afterfan "+str(self.m_temperature)+"\n")
	
	def CountAgentInRoom(self):
		count = 0
		for agent in Agent.Agent.agentList:
			if self.IsInRoom(agent.pos):
				count += 1
		return count
	
	def StopAllUsage(self):
		for item in self.m_items:
			if item.m_usageStartTime > 0:
				item.StopUsage()

#--------------------------------------------------------------------------------------------------------------
#-------------House Class--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
import scriptcontext as sc
TMPL_ENERGY_TYPE	= 0
TMPL_ENERGY_SUPPLY	= TMPL_ENERGY_TYPE + 1
TMPL_ENERGY_PRICE	= TMPL_ENERGY_SUPPLY + 1

sourceFilePath	= os.path.dirname(os.path.abspath(__file__))
sourceDirPath	= sourceFilePath[0:sourceFilePath.rfind('\\')+1]
reportPath			= sourceDirPath+"report\\"+sc.sticky["MapName"]+"\\"

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
	
	def ExportEnergyUsageReport(self):
		self.StopAllUsage()
		electricityUsage = filter(lambda usage: usage[0] == Common.ENERGY_TYPE_ELECTRICITY, self.m_energyUsage)
		outputFilePath = reportPath+"electricity_report.csv"
		columnName = ["DeviceID","User", "Activity", "DayStart", "HourStart","Duration(Minute)","PowerConsumption"]
		with open(outputFilePath, mode='w+') as outputFile:
			outputWriter = csv.writer(outputFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
			outputWriter.writerow(columnName)
			for usage in electricityUsage:
				duration = usage[5]-usage[4]
				row = [usage[1], usage[2], usage[3], Timer.Timer.GetDayForTime(usage[4]), Timer.Timer.GetFormattedHourInDay(usage[4]), duration, duration*usage[6]/60]
				outputWriter.writerow(row)
		
		waterUsage = filter(lambda usage: usage[0] == Common.ENERGY_TYPE_WATER, self.m_energyUsage)
		outputFilePath = reportPath+"water_report.csv"
		columnName = ["User", "Activity", "Room", "Time", "Amount"]
		with open(outputFilePath, mode='w+') as outputFile:
			outputWriter = csv.writer(outputFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
			outputWriter.writerow(columnName)
			for usage in waterUsage:
				row = [usage[1], usage[2], usage[3], Timer.Timer.GetFormattedHourInDay(usage[4]), usage[5]]
				outputWriter.writerow(row)
		
		gasUsage = filter(lambda usage: usage[0] == Common.ENERGY_TYPE_GAS, self.m_energyUsage)
		outputFilePath = reportPath+"gas_report.csv"
		columnName = ["User", "Activity", "Time", "Amount"]
		with open(outputFilePath, mode='w+') as outputFile:
			outputWriter = csv.writer(outputFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
			outputWriter.writerow(columnName)
			for usage in gasUsage:
				row = [usage[1], usage[2], Timer.Timer.GetFormattedHourInDay(usage[3]), usage[4]]
				outputWriter.writerow(row)
	
	def ResetEnergyUsage(self):
		self.m_energyUsage = []
	
	def FindGeneralRoomForResource(self, resourceType):
		roomWithResource = next((room for room in self.m_rooms if room.IsGeneralForResource(resourceType)), None)
		return roomWithResource
	
	def ReportResource(self):
		for room in self.m_rooms:
			room.ReportCurrentResource()
		Global.Logger.DumpDebug()
	
	def UpdateHouse(self):
		for room in self.m_rooms:
			room.UpdateLightAndTemperature()
		for target in Agent.Agent.s_possibleTarget:
			if target != None:
				target.UpdateUsage()
	
	def StopAllUsage(self):
		for room in self.m_rooms:
			room.StopAllUsage()