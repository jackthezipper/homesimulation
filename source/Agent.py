#import from python lib
import random
import math
import sys
import os

#import custom file
import Target
import PathFinding
import Schedule
Schedule = reload(Schedule)
import csv
import Activity
Activity = reload(Activity)
import CommonEnum
import Term
Term = reload(Term)
import Global
import EntryPoint

from Rhino.Geometry import Point3d, Vector3f,Vector3d,Line,Polyline
import rhinoscriptsyntax as rs

import scriptcontext as sc
import Rhino.Geometry

PathFinding = reload(PathFinding)

#agent state
STATE_IDLE = 0
STATE_PRE_MOVE = STATE_IDLE + 1
STATE_MOVE = STATE_PRE_MOVE + 1
STATE_WAIT = STATE_MOVE + 1

#target type
TARGET_NONE		= -1
TARGET_ROOM		= 0
TARGET_POINT	= TARGET_ROOM + 1

TERM_ENVI		= 0
TERM_ROOM		= TERM_ENVI + 1
TERM_COUNT		= TERM_ROOM + 1

AGENT_PREACT_ID		= 0
AGENT_PREACT_OBJ	= AGENT_PREACT_ID + 1
AGENT_PREACT_LOC	= AGENT_PREACT_OBJ + 1

errPause = False

#30 min -> 15 sec
TIMECONVERSION = 2 #to multiply dt
TIMEFACTOR = 1000 #to multiply waitTime

#find resources path
# sourceFilePath	= ghenv.Component.OnPingDocument().FilePath
sourceFilePath	= os.path.dirname(os.path.abspath(__file__))
sourceDirPath	= sourceFilePath[0:sourceFilePath.rfind('\\')+1]
resPath			= sourceDirPath+"res\\"+sc.sticky["MapName"]+"\\"

#---------------------------------------------------------------------------------------
class Agent:
	s_possibleTarget = []
	s_entryPointList = []
	hasErr = False
	agentList = []
	s_scaleSpeed = 1.0
	# s_debugStr = ""
	# s_debugActive = True
	
	# @staticmethod
	# def LogDebug(debugLog):
		# if Agent.s_debugActive:
			# Agent.s_debugStr += debugLog
	
	# @staticmethod
	# def ResetDebug():
		# Agent.s_debugStr = ""
	
	# @staticmethod
	# def DumpDebug():
		# if not Agent.s_debugActive:
			# return
		# dFile = open(resPath+"dmp.txt","a+")
		# dFile.write(Agent.s_debugStr)
		# dFile.close()
		# Agent.s_debugStr = ""
	
	def __init__(self,position,m_targetPoint,index,role = "ayah",state = STATE_IDLE):
		self.pos = position
		self.m_targetPoint = m_targetPoint
		self.entryPoint = None
		self.oldEntryPoint = None
		self.m_state = state
		self.initialPos = position
		self.hasNewTarget = False
		self.waitTime = (Schedule.SCHEDULE[index][0][1] * TIMEFACTOR)
		self.myPath = None
		self.m_pathIndex = 0
		self.m_target = None
		self.moveDir = Vector3f(0,1,0)
		self.pathCalculated = False
		self.m_myIndex = index
		self.m_blockedBy = -1
		self.blockCounter = 0
		self.m_hasWait = False
		self.targetIndex = 0
		self.initialized = False
		self.m_canGetNewTarget = True
		self.boundArea = None
		self.curveBoundArea = None
		self.diagonalBound = 0
		
		self.objectList = []
		
		self.m_speedFactor = 0.15
		self.m_myFloorIndex = 0
		self.needStair = False
		
		self.m_active = False
		self.m_role = role
		
		self.m_activity = []
		self.m_supportActivity = []
		self.m_terms = []
		
		self.m_myBioStatus = []
		self.m_myBioEffectRate = []
		self.m_myESStatus = []
		self.m_myESNormal = []
		self.m_myESRate = []
		self.m_environmentThreshold = []
		
		self.m_currentActivity = None
		self.m_currentTerm = None
		self.m_currentSupportActivity = None
		self.m_targetRoom = None
		self.m_targetType = TARGET_NONE
		self.m_termChecklist = [0] * TERM_COUNT\
		self.m_preActivityList = []
		
		self.LoadActivityList()
		self.LoadSupportActivity()
		self.LoadTerms()
		
	
	def setTarget(self,newTarget):
		self.m_target = newTarget
		self.hasNewTarget = True
		if newTarget != None:
			self.m_target.m_available = False
	
	def Update(self,dt):
		if not self.initialized:
			self.AssignToClosestTarget()
			self.initialized = True
		
		if not self.m_active:
			return self.pos
		
		self.UpdateBioStatus(dt)
		self.UpdateESStatus(dt)
		self.UpdateActivityOrder()
		self.UpdateAgentActivity(dt)
		self.UpdateAgentMovement(dt)
		
		Global.Logger.LogDebug("\n agent pos "+str(self.pos)+"\n")
		Global.Logger.DumpDebug()
		return self.pos
		
		
	
	def update(self, dt):
		if not self.initialized:
			self.AssignToClosestTarget()
			self.initialized = True
		
		if not self.m_active:
			return self.pos
		
		self.UpdateBioStatus(dt)
		self.UpdateActivityOrder()
		
		if self.m_state != STATE_MOVE:
			self.m_pathIndex = 1
			if self.waitTime > 0:
				self.waitTime -= (dt * Agent.s_scaleSpeed * TIMECONVERSION)
				return self.pos
			
			#getting new target
			if self.m_canGetNewTarget:
				self.calculateNextTarget()
			if self.m_target == None:
				return self.pos
			self.m_canGetNewTarget = False
			
			#calculating path
			start = None
			if self.oldEntryPoint != None:
				start = TranslateToGridPos(self.oldEntryPoint.pos,self.m_myFloorIndex)
			else:
				start = TranslateToGridPos(self.pos,self.m_myFloorIndex)
			
			self.needStair = (self.m_target.m_floorIndex != self.m_myFloorIndex)
			
			if self.needStair:
				stairIndex = "STAIRS_"+str(self.m_myFloorIndex)
				stairTarget = next(trgt for trgt in Agent.s_possibleTarget if trgt.hasActivity(stairIndex))
				stairEntry = next(entry for entry in Agent.s_entryPointList if entry.target == stairTarget)
				end = TranslateToGridPos(stairEntry.pos,self.m_myFloorIndex)
			else:
				end = TranslateToGridPos(self.entryPoint.pos,self.m_myFloorIndex)
			self.myPath = PathFinding.astarv3(start,end,self.m_myIndex,self.m_myFloorIndex)
			
			#No path found. Wait a moment
			if self.myPath == None:
				return self.pos
			
			#path found
			if self.oldEntryPoint != None and self.myPath[0] != self.pos:
				self.myPath.insert(0,self.pos)
			
			if self.needStair:
				self.myPath.append(stairEntry.target.m_targetPoint)
			elif self.entryPoint.pos != self.entryPoint.target.m_targetPoint:
				self.myPath.append(self.entryPoint.target.m_targetPoint)
			self.m_pathIndex = 1
			self.recalculateMoveDir()
			self.m_state = STATE_MOVE
			return self.pos
		else:
			destination  = self.myPath[self.m_pathIndex]
			distance = self.pos.DistanceTo(destination)
			distanceCovered = float(dt) * Agent.s_scaleSpeed / 1000
			if distance > distanceCovered:#self.m_speedFactor:
				#there still distance within the path
				myGrid = TranslateToGridPos(self.pos,self.m_myFloorIndex)
				self.m_blockedBy,blocked = PathFinding.IsBlocked(myGrid,self.m_myFloorIndex)
				
				if blocked:
					#path maybe blocked
					blockPos = PathFinding.TranslateToRealPos(PathFinding.Map.liveBlock[self.m_blockedBy][0],self.m_myFloorIndex)
					blockDir = Vector3f.Subtract(Vector3f(blockPos[0],blockPos[1],0),Vector3f(self.pos.X,self.pos.Y,0))
					blockDir = Vector3f.Divide(blockDir,blockDir.Length)
					dotP = (blockDir.X*self.moveDir.X) + (blockDir.Y*self.moveDir.Y)
					angle = math.acos(dotP)
					angle = math.degrees(angle)
					if angle > 60 and (abs(myGrid[0]-PathFinding.Map.liveBlock[self.m_blockedBy][0][0]) > PathFinding.OVERLAP_LIMIT or abs(myGrid[1]-PathFinding.Map.liveBlock[self.m_blockedBy][0][1]) > PathFinding.OVERLAP_LIMIT):
						blocked = False
					if self.entryPoint.pos != self.entryPoint.target.m_targetPoint and self.m_pathIndex == (len(self.myPath) - 1):
						blocked = False
				
				
				if blocked:
					#path is blocked
					if self.blockCounter < 10 and self.m_myIndex > self.m_blockedBy:
						if not self.m_hasWait:
							self.blockCounter += 1
							return self.pos
						else:
							self.m_hasWait = True
					
					if self.needStair:
						stairIndex = "STAIRS_"+str(self.m_myFloorIndex)
						stairEntry = next(trgt for trgt in Agent.s_possibleTarget if trgt.hasActivity(stairIndex))
						myNextDestGrid = TranslateToGridPos(stairEntry.pos,self.m_myFloorIndex)
					else:
						myNextDestGrid = TranslateToGridPos(self.entryPoint.pos,self.m_myFloorIndex)
					midPath = PathFinding.astarv3(myGrid,myNextDestGrid,self.m_myIndex,self.m_myFloorIndex,True)
					
					#No path found. Wait a moment
					if midPath == None:
						self.blockCounter += 1
						if self.blockCounter > 10 and self.m_myIndex > self.m_blockedBy and self.m_pathIndex > 2:
							self.pos = rs.PointAdd(self.pos,(Vector3d.Multiply(self.moveDir,self.m_speedFactor) * (-1)))
						return self.pos
					
					if self.entryPoint.pos != self.entryPoint.target.m_targetPoint:
						midPath.append(self.entryPoint.target.m_targetPoint)
					del self.myPath[self.m_pathIndex-1:]
					self.myPath.extend(midPath)
					self.m_hasWait = False
					self.recalculateMoveDir()
				else:
					#not blocked, continue to move
					self.blockCounter = 0
					self.m_blockedBy = -1
				
				#update agent position
				self.pos = rs.PointAdd(self.pos,Vector3d.Multiply(self.moveDir,distanceCovered))
			else:
				#already close with destination
				remainingDistance = distanceCovered - distance
				while (remainingDistance > 0):
					self.pos = destination
					self.m_pathIndex+=1
					if self.m_pathIndex < len(self.myPath):
						self.recalculateMoveDir()
						destination  = self.myPath[self.m_pathIndex]
						distance = self.pos.DistanceTo(destination)
						if remainingDistance < distance:
							self.pos = rs.PointAdd(self.pos,Vector3d.Multiply(self.moveDir,remainingDistance))
						remainingDistance = remainingDistance - distance
					elif self.needStair:
						nextStairIndex = "STAIRS_"+str(self.m_target.m_floorIndex)
						nextStairTarget = next(trgt for trgt in Agent.s_possibleTarget if trgt.hasActivity(nextStairIndex))
						nextStairEntry = next(entry for entry in Agent.s_entryPointList if entry.target == nextStairTarget)
						self.m_myFloorIndex = self.m_target.m_floorIndex
						start = TranslateToGridPos(nextStairEntry.pos,self.m_myFloorIndex)
						end = TranslateToGridPos(self.entryPoint.pos,self.m_myFloorIndex)
						
						self.myPath = PathFinding.astarv3(start,end,self.m_myIndex,self.m_myFloorIndex)
						self.pos = nextStairTarget.m_targetPoint
						self.myPath.insert(0,self.pos)
						if self.entryPoint.pos != self.entryPoint.target.m_targetPoint:
							self.myPath.append(self.entryPoint.target.m_targetPoint)
						self.m_pathIndex = 1
						self.recalculateMoveDir()
						self.needStair = False
						distance = self.pos.DistanceTo(destination)
						if remainingDistance < distance:
							self.pos = rs.PointAdd(self.pos,Vector3d.Multiply(self.moveDir,remainingDistance))
						remainingDistance = remainingDistance - distance
					else:
						self.m_canGetNewTarget = True
						self.m_state = STATE_WAIT
						self.waitTime = (Schedule.SCHEDULE[self.m_myIndex][self.targetIndex][1] * TIMEFACTOR)
						remainingDistance = 0
			self.m_hasWait = False
			return self.pos
	
	def calculateNextTarget(self):
		if self.targetIndex == len(Schedule.SCHEDULE[self.m_myIndex]) - 1:
			self.setTarget(None)
			return
			
		if self.m_target != None:
			self.m_target.m_available = True
			
		nextSchedule = Schedule.SCHEDULE[self.m_myIndex][self.targetIndex + 1]
		availableTarget = [target for target in Agent.s_possibleTarget if target.m_available and target.hasActivity(nextSchedule[0])]
	
		specificTarget = [target for target in availableTarget if target.isSpecificToAgent(self.m_myIndex)]
		
		if specificTarget != None and len(specificTarget) > 0:
			availableTarget = specificTarget
		else:
			availableTarget = [target for target in availableTarget if target.notHaveSpecific()]
		
		if len(availableTarget) > 0:
			if self.m_target != None:
				self.targetIndex += 1
			ron = random.randint(0,len(availableTarget)-1)
			self.setTarget(availableTarget[ron])
		else:
			self.setTarget(None)
			return
			
		entryPointL = []
		for ep in Agent.s_entryPointList:
			if ep.target == self.m_target:
				entryPointL.append(ep)
		selectedEntry = 0
		distanceMin = float(sys.maxint)
		for (i,ep) in enumerate(entryPointL):
			curDistance = self.pos.DistanceTo(ep.pos)
			if curDistance < distanceMin:
				curDistance = distanceMin
				selectedEntry = i
		self.oldEntryPoint = self.entryPoint
		self.entryPoint = entryPointL[selectedEntry]

	def recalculateMoveDir(self):
		destination  = self.myPath[self.m_pathIndex]
		self.moveDir = Vector3f.Subtract(Vector3f(destination.X,destination.Y,destination.Z),Vector3f(self.pos.X,self.pos.Y,self.pos.Z))
		self.moveDir.Unitize()
		
	def AssignToClosestTarget(self):
		distanceMin = float(sys.maxint)
		targetIndex = 0
		for (i,target) in enumerate(Agent.s_possibleTarget):
			curDistance = self.pos.DistanceTo(target.m_targetPoint)
			if curDistance < distanceMin:
				distanceMin = curDistance
				targetIndex = i
		print Agent.s_possibleTarget[targetIndex]
		print Agent.s_possibleTarget[targetIndex].m_targetPoint
		epList = []
		for (i,ep) in enumerate(Agent.s_entryPointList):
			if ep.target == Agent.s_possibleTarget[targetIndex]:
				epList.append(ep)
		self.setTarget(Agent.s_possibleTarget[targetIndex])
		self.entryPoint = epList[0]
		self.m_myFloorIndex = self.m_target.m_floorIndex
		
	def setBoundArea(self,area):
		if area != self.boundArea:
			self.boundArea = area
			self.curveBoundArea = rs.coercecurve(area)
			self.diagonalBound = Vector3d.Subtract(Vector3d(self.curveBoundArea.Points[0].Location),Vector3d(self.curveBoundArea.Points[2].Location)).Length
			
	def getBoundArea(self):
		return self.curveBoundArea,self.diagonalBound
		
	def updateView(self):
		print "vrtijo"
		print self.boundArea
		curveBound = rs.coercecurve(self.boundArea)
		rc,pl = curveBound.TryGetPolyline()
		
		diagL = Vector3d.Subtract(Vector3d(curveBound.Points[0].Location),Vector3d(curveBound.Points[2].Location)).Length
		
		vec1 = rs.VectorRotate(self.moveDir,-60,(0,0,1))
		endl1 = Point3d.Add(self.pos,(vec1*diagL))
		mLine1 = Line(self.pos,endl1)
		
		vec2 = rs.VectorRotate(self.moveDir,60,(0,0,1))
		endl2 = Point3d.Add(self.pos,(vec2*diagL))
		mLine2 = Line(self.pos,endl2)
		#Line.to
		iSect1 = Rhino.Geometry.Intersect.Intersection.CurveCurve(curveBound,mLine1.ToNurbsCurve(),0,0)
		iSect2 = Rhino.Geometry.Intersect.Intersection.CurveCurve(curveBound,mLine2.ToNurbsCurve(),0,0)
		
		for inte in iSect1:
			point1 = inte.PointA
			
		for inte in iSect2:
			point2 = inte.PointA
			
		vpointList = []
		for poin in curveBound.Points:
			vect = Vector3d.Subtract(Vector3d(poin.Location),Vector3d(self.pos))
			vect.Unitize()
			angle = math.degrees(math.atan2(vect.Y,vect.X)-math.atan2(vec1.Y,vec1.X))
			if angle >= 0 and angle <= 120:
				vpointList.append((vect,poin.Location))
		
		vpointList.sort(key = lambda x: math.degrees(math.atan2(x[0].Y,x[0].X)-math.atan2(vec1.Y,vec1.X)),reverse = True)
		
		#print vpointList
		pointList = []
		pointList.append(self.pos)
		pointList.append(point2)
		for vpoint in vpointList:
			pointList.append(vpoint[1])
		pointList.append(point1)
		pointList.append(self.pos)
		
		view = sc.doc.Views.ActiveView.ActiveViewport      
		self.objectList = Rhino.RhinoDoc.ActiveDoc.Objects.FindByCrossingWindowRegion(view,pointList,True,Rhino.DocObjects.InstanceObject)
		print olist
		print self.objectList

	def LoadActivityList(self):
		tableFileName = resPath+"table_"+self.m_role+".csv"
		with open(tableFileName) as csvfile:
			reader = csv.reader(csvfile)
			for row in reader:
				if row[CommonEnum.TABLE_ACTIVITY_ID] == "ID":
					continue
				#read per row
				id = row[CommonEnum.TABLE_ACTIVITY_ID]
				chance = float(row[CommonEnum.TABLE_ACTIVITY_CHANCE])
				interruptProperty = []
				for i in range(0,CommonEnum.INTERRUPT_PROPERTY_COUNT):
					interruptProperty.append(int(row[CommonEnum.TABLE_ACTIVITY_CANINTERRUPT + i]))
				
				timeProperty = []
				for i in range(0,CommonEnum.TIME_PROPERTY_COUNT):
					if (i == CommonEnum.TIME_PROPERTY_COUNT - 1):
						timeProperty.append(int(row[CommonEnum.TABLE_ACTIVITY_STARTTIMECANSTART + i]))
					else:
						timeStr = row[CommonEnum.TABLE_ACTIVITY_STARTTIMECANSTART + i]
						if timeStr == "-":
							timeProperty.append([-1,-1])
						else:
							timeArr = timeStr.split(':')
							timeProperty.append([int(timeArr[0]),int(timeArr[1])])
				
				planProperty = []
				for i in range(0,CommonEnum.PLAN_PROPERTY_COUNT):
					column = CommonEnum.TABLE_ACTIVITY_PLAN + i
					if column < CommonEnum.TABLE_ACTIVITY_AUTHORITY:
						planProperty.append(float(row[column]))
					else:
						planProperty.append(float(row[column])*float(row[column + 1]))
						break
				
				bioEffect = []
				for i in range(0,CommonEnum.BIOLOGICAL_PROPERTY_COUNT):
					bioEffect.append(int(row[CommonEnum.TABLE_ACTIVITY_EXHAUST + i]))
				
				esFactor = []
				for i in range(0, CommonEnum.ES_PROPERTY_COUNT):
					esFactor.append(float(row[CommonEnum.TABLE_ACTIVITY_EMOTION + i]))
				
				self.m_activity.append(Activity.CoreActivity(id, chance, interruptProperty, timeProperty, planProperty, bioEffect, esFactor, self))
	
	def LoadSupportActivity(self):
		tableFileName = resPath+"table_support_activity_before_"+self.m_role+".csv"
		with open(tableFileName) as csvfile:
			reader = csv.reader(csvfile)
			for row in reader:
				if row[CommonEnum.TABLE_SA_ID] == "ID":
					continue
				self.m_supportActivity.append(Activity.SupportActivity(row[CommonEnum.TABLE_SA_ID], float(row[CommonEnum.TABLE_SA_HABIT]), int(row[CommonEnum.TABLE_SA_DURATION]), Activity.SA_TYPE_BEFORE))
		tableFileName = resPath+"table_support_activity_after_"+self.m_role+".csv"
		with open(tableFileName) as csvfile:
			reader = csv.reader(csvfile)
			for row in reader:
				if row[CommonEnum.TABLE_SA_ID] == "ID":
					continue
				print("komata "+row[CommonEnum.TABLE_SA_HABIT])
				self.m_supportActivity.append(Activity.SupportActivity(row[CommonEnum.TABLE_SA_ID], float(row[CommonEnum.TABLE_SA_HABIT]), int(row[CommonEnum.TABLE_SA_DURATION]), Activity.SA_TYPE_AFTER))
	
	def LoadTerms(self):
		tableFileName = resPath+"table_terms_"+self.m_role+".csv"
		with open(tableFileName) as csvfile:
			reader = csv.reader(csvfile)
			for row in reader:
				if row[CommonEnum.TABLE_TERM_ID] == "ID":
					continue
				id = row[CommonEnum.TABLE_TERM_ID]
				ability = row[CommonEnum.TABLE_TERM_ABILITY]
				
				#environment factor
				enviFactor = []
				for i in range(0,CommonEnum.TERM_ENVI_TOTAL):
					factor = []
					factor.append(int(row[CommonEnum.TABLE_TERM_LIGHT + (i * 2)]))
					factor.append(row[CommonEnum.TABLE_TERM_LIGHTOBJECT + (i * 2)].split(";"))
					enviFactor.append(factor)
				
				#resource factor
				resFactor = []
				for i in range(0, CommonEnum.RES_COUNT):
					res = row[CommonEnum.TABLE_TERM_RESOURCE1 + (i * 2)]
					if res == "-":
						continue
					factor = []
					factor.append(CommonEnum.ResourceToID(res))
					factor.append(row[CommonEnum.TABLE_TERM_FAILRESOURCE1 + (i * 2)])
					resFactor.append(factor)
				
				roomFactor = []
				for i in range(0, CommonEnum.RF_COUNT):
					res = row[CommonEnum.TABLE_TERM_ROOMFACTOR1 + (i * 2)]
					if res == "-":
						continue
					factor = []
					rf = row[CommonEnum.TABLE_TERM_ROOMFACTOR1 + (i * 2)].split(";")
					rfId = []
					for rfObj in rf:
						rfId.append(CommonEnum.RoomFactorToID(rfObj))
					factor.append(rfId)
					factor.append(row[CommonEnum.TABLE_TERM_FAILROOMFACTOR1 + (i * 2)].split(";"))
					roomFactor.append(factor)
				
				roomPrio = []
				for i in range(0, CommonEnum.ROOM_PRIO_COUNT):
					room = row[CommonEnum.TABLE_TERM_ROOMPRIO1 + i]
					if room != "-":
						roomPrio.append(room)
				self.m_terms.append(Term.ActivityTerm(id, ability, enviFactor, resFactor, roomFactor, roomPrio))
	
	#update status biologis
	def UpdateBioStatus(self, dt):
		elapseTime = (dt * Agent.s_scaleSpeed * TIMECONVERSION) / TIMEFACTOR
		
		for i in range(0,len(self.m_myBioStatus)):
			self.m_myBioStatus[i] += elapseTime * self.m_myBioEffectRate[i]
		#TODO: implement activity effect on bio status
			
	#update status emosi sosial
	def UpdateESStatus(self, dt):
		elapseTime = (dt * Agent.s_scaleSpeed * TIMECONVERSION) / TIMEFACTOR
		
		for i in range(0,len(self.m_myESStatus)):
			self.m_myESStatus[i] = self.m_myESNormal[i] if (abs(self.m_myESNormal[i] - self.m_myESRate[i]) < self.m_myESRate[i]) else (self.m_myESStatus[i] + (elapseTime * self.m_myESRate[i]) * (-1 if (self.m_myESNormal[i] < self.m_myESRate[i]) else 1))
		
		#TODO: implement activity effect on ES
	
	#menghitung nilai tiap aktivitas lalu diurutkan
	def UpdateActivityOrder(self):
		for activity in self.m_activity:
			activity.CalculateActivityScore()
		
		self.m_activity.sort(key = lambda x: x.m_score, reverse = True)
	
	def SetupInitialBioStatusAndRate(self, initialBioStatus, bioEffectRate):
		self.m_myBioStatus = initialBioStatus
		self.m_myBioEffectRate = bioEffectRate
	
	def SetupInitialES(self, initial, normal, rate):
		self.m_myESStatus = initial
		self.m_myESNormal = normal
		self.m_myESRate = rate
	
	def GeneratePath(self, start, end, stair = None):
		pStart = TranslateToGridPos(start,self.m_myFloorIndex)
		pEnd = TranslateToGridPos(end,self.m_myFloorIndex)
		print "start "+str(pStart)+" "+str(start)
		print "end "+str(pEnd)+" "+str(end)
		path = PathFinding.astarv3(pStart,pEnd,self.m_myIndex,self.m_myFloorIndex)
		
		#No path found. Wait a moment
		if path == None:
			print "nopopak"
			return
		
		#path found
		if self.oldEntryPoint != None and path[0] != self.pos:
			path.insert(0,self.pos)
		
		if self.needStair:
			path.append(stair.target.m_targetPoint)
		elif (self.m_targetRoom == None or self.m_targetRoom.IsInRoom(self.pos)) and self.entryPoint.pos != self.entryPoint.target.m_targetPoint:
			path.append(self.entryPoint.target.m_targetPoint)
		self.m_pathIndex = 1
		print path
		return path
	
	#update aktivitas agent
	def UpdateAgentActivity(self, dt):
		firstID = self.m_activity[0].m_ID
		
		Global.Logger.LogDebug("Updating activity : current is "+("None" if self.m_currentActivity == None else self.m_currentActivity.m_ID)+"\n")
		# if self.m_currentActivity != None:
			
		if self.m_currentActivity != None and (firstID == self.m_currentActivity.m_ID or (not self.m_activity[0].CanInterrupt()) or (not self.m_currentActivity.CanBeInterrupted())):
			if self.m_state == STATE_WAIT:
				if self.m_currentSupportActivity != None and (not self.m_currentSupportActivity.IsDone()):
					self.m_currentSupportActivity.UpdateTimer(dt)
					
					Global.Logger.LogDebug("Check support activity done "+str(self.m_currentSupportActivity.IsDone())+"\n")
					if self.m_currentSupportActivity.IsDone():
						#aktivitas pendukung selesai dijalankan, memeriksa apakah masih ada aktivitas pendukung lain yang perlu dijalankan
						self.m_currentSupportActivity.Stop()
						Global.Logger.LogDebug("Support activity done\n")
						self.m_currentSupportActivity = None
						self.CheckSupportPreActivity2()
						if self.m_currentSupportActivity == None:
							Global.Logger.LogDebug("No more support activity needed. Starting activity\n")
							self.m_currentActivity.Start()
				
				else:
					self.m_currentActivity.UpdateTimer(dt)
					if self.m_currentActivity.IsDone():
						#aktivitas selesai dijalankan
						Global.Logger.LogDebug("Activity done\n")
						self.m_currentActivity.Stop()
						self.m_currentActivity = None
			return
		
		#ada aktivitas baru	yang akan dikerjakan
		Global.Logger.LogDebug("New activity found ID : "+firstID+"\n")
		self.m_currentTerm = next((trm for trm in self.m_terms if trm.m_activityID == firstID),None)
		if self.m_currentTerm != None:
			roomName = self.m_currentTerm.m_roomPrio[0]
			isSameRoom = (self.m_targetRoom != None) and (roomName == self.m_targetRoom.m_name)
			print "koranum 8"+roomName+"8 "
			Global.Logger.LogDebug("Room is "+("same\n" if isSameRoom else "different\n"))
			if not isSameRoom:
				print "nosmora"
				self.m_targetRoom = next((room for room in Global.g_myHouse.m_rooms if room.m_name == roomName),None)
				self.oldEntryPoint = self.entryPoint
				self.entryPoint = None
				print self.m_targetRoom
			else:
				# print "errant "+firstID
				# self.FindTargetAndEntryPointForActivity(firstID)
				self.CheckSupportPreActivity2()
			
			self.m_pathIndex = 1
			
			start = None
			if self.oldEntryPoint != None:
				start = self.oldEntryPoint.pos
			else:
				start = self.pos
			Global.Logger.LogDebug("Path start at "+str(start))
			self.needStair = self.m_targetRoom.m_floorIndex != self.m_myFloorIndex
			
			stairEntry = None
			end = self.pos
			if self.needStair:
				stairIndex = "STAIRS_"+str(self.m_myFloorIndex)
				stairTarget = next(trgt for trgt in Agent.s_possibleTarget if trgt.hasActivity(stairIndex))
				stairEntry = next(entry for entry in Agent.s_entryPointList if entry.target == stairTarget)
				end = stairEntry.pos
				self.m_targetType = TARGET_ROOM
				self.m_termChecklist = [0] * TERM_COUNT
			elif isSameRoom:
				if self.pos != self.entryPoint.target.m_targetPoint:
					end = self.entryPoint.pos
					self.m_targetType = TARGET_POINT
			else:
				end = self.m_targetRoom.m_targetCoord
				self.entryPoint = EntryPoint.EntryPoint(self.m_targetRoom.m_targetCoord,self.m_targetRoom.m_floorIndex)
				self.m_targetType = TARGET_ROOM
				self.m_termChecklist = [0] * TERM_COUNT
			
			Global.Logger.LogDebug(" end at "+str(end)+"\n")
			
			#jika aktivitas baru akan dilakukan di tempat yang berbeda dengan posisi agent sekarang, maka mencari jalur untuk bergerak
			if not isSameRoom or self.pos != end:
				self.myPath = self.GeneratePath(start, end, stairEntry)
				Global.Logger.LogDebug("Generated path : ")
				for path in self.myPath:
					Global.Logger.LogDebug("["+str(path.X)+","+str(path.Y)+"],")
				Global.Logger.LogDebug("\n")
				self.m_state = STATE_PRE_MOVE
			
			self.m_currentActivity = self.m_activity[0]
			
			if self.m_currentSupportActivity == None and isSameRoom:
				Global.Logger.LogDebug("No support activity needed. Starting activity\n")
				self.m_currentActivity.Start()
			
			Global.Logger.LogDebug("Activity set to "+self.m_currentActivity.m_ID+"\n")
	
	#update pergerakan dan posisi agent
	def UpdateAgentMovement(self, dt):
		if self.m_state != STATE_MOVE:
			if self.m_state == STATE_PRE_MOVE:
				self.m_state = STATE_MOVE
			return
		
		Global.Logger.LogDebug("Update movement dt = "+str(dt)+"\n")
		Global.Logger.LogDebug("Path : ")
		for path in self.myPath:
			Global.Logger.LogDebug("["+str(path.X)+","+str(path.Y)+"],")
		Global.Logger.LogDebug("\ncurrent index "+str(self.m_pathIndex)+"\n")
		
		destination  = self.myPath[self.m_pathIndex]
		distance = self.pos.DistanceTo(destination)
		distanceCovered = float(dt) * Agent.s_scaleSpeed / 1000
		Global.Logger.LogDebug("Distance "+str(distance)+" covered "+str(distanceCovered)+"\n")
		if distance > distanceCovered:
#		and (self.m_targetRoom == None or (not self.m_targetRoom.IsInRoom(self.pos))):
			#masih ada jarak yang perlu ditempuh
			myGrid = TranslateToGridPos(self.pos,self.m_myFloorIndex)
			self.m_blockedBy,blocked = PathFinding.IsBlocked(myGrid,self.m_myFloorIndex)
			
			if blocked:
				#jalur kemungkinan terhalang
				blockPos = PathFinding.TranslateToRealPos(PathFinding.Map.liveBlock[self.m_blockedBy][0],self.m_myFloorIndex)
				blockDir = Vector3f.Subtract(Vector3f(blockPos[0],blockPos[1],0),Vector3f(self.pos.X,self.pos.Y,0))
				blockDir = Vector3f.Divide(blockDir,blockDir.Length)
				dotP = (blockDir.X*self.moveDir.X) + (blockDir.Y*self.moveDir.Y)
				angle = math.acos(dotP)
				angle = math.degrees(angle)
				if angle > 60 and (abs(myGrid[0]-PathFinding.Map.liveBlock[self.m_blockedBy][0][0]) > PathFinding.OVERLAP_LIMIT or abs(myGrid[1]-PathFinding.Map.liveBlock[self.m_blockedBy][0][1]) > PathFinding.OVERLAP_LIMIT):
					blocked = False
				if self.entryPoint.pos != self.entryPoint.target.m_targetPoint and self.m_pathIndex == (len(self.myPath) - 1):
					blocked = False
			
			if blocked:
				#jalur terhalang
				if self.blockCounter < 10 and self.m_myIndex > self.m_blockedBy:
					if not self.m_hasWait:
						self.blockCounter += 1
						return
					else:
						self.m_hasWait = True
				
				if self.needStair:
					stairIndex = "STAIRS_"+str(self.m_myFloorIndex)
					stairEntry = next(trgt for trgt in Agent.s_possibleTarget if trgt.hasActivity(stairIndex))
					myNextDest = stairEntry.pos
				elif self.m_targetRoom.IsInRoom(self.pos):
					myNextDest = self.entryPoint.pos
				else:
					myNextDest = self.m_targetRoom.m_targetCoord
				midPath = GeneratePath(self.pos,myNextDest)
				
				#No path found. Wait a moment
				if midPath == None:
					self.blockCounter += 1
					if self.blockCounter > 10 and self.m_myIndex > self.m_blockedBy and self.m_pathIndex > 2:
						self.pos = rs.PointAdd(self.pos,(Vector3d.Multiply(self.moveDir,self.m_speedFactor) * (-1)))
					return
				
				del self.myPath[self.m_pathIndex-1:]
				self.myPath.extend(midPath)
				self.m_hasWait = False
				self.recalculateMoveDir()
			else:
				#not blocked, continue to move
				self.blockCounter = 0
				self.m_blockedBy = -1
			
			#update agent position
			self.pos = rs.PointAdd(self.pos,Vector3d.Multiply(self.moveDir,distanceCovered))
			
			
		else:
			#already close with destination
			remainingDistance = distanceCovered - distance
			while (remainingDistance > 0):
				self.pos = destination
				self.m_pathIndex+=1
				if self.m_pathIndex < len(self.myPath):
					self.recalculateMoveDir()
					destination  = self.myPath[self.m_pathIndex]
					distance = self.pos.DistanceTo(destination)
					if remainingDistance < distance:
						self.pos = rs.PointAdd(self.pos,Vector3d.Multiply(self.moveDir,remainingDistance))
					remainingDistance = remainingDistance - distance
				elif self.needStair:
					nextStairIndex = "STAIRS_"+str(self.m_target.m_floorIndex)
					nextStairTarget = next(trgt for trgt in Agent.s_possibleTarget if trgt.hasActivity(nextStairIndex))
					nextStairEntry = next(entry for entry in Agent.s_entryPointList if entry.target == nextStairTarget)
					self.m_myFloorIndex = self.m_target.m_floorIndex
					start = TranslateToGridPos(nextStairEntry.pos,self.m_myFloorIndex)
					end = TranslateToGridPos(self.entryPoint.pos,self.m_myFloorIndex)
					
					self.myPath = PathFinding.astarv3(start,end,self.m_myIndex,self.m_myFloorIndex)
					self.pos = nextStairTarget.m_targetPoint
					self.myPath.insert(0,self.pos)
					if self.entryPoint.pos != self.entryPoint.target.m_targetPoint:
						self.myPath.append(self.entryPoint.target.m_targetPoint)
					self.m_pathIndex = 1
					self.recalculateMoveDir()
					self.needStair = False
					distance = self.pos.DistanceTo(destination)
					if remainingDistance < distance:
						self.pos = rs.PointAdd(self.pos,Vector3d.Multiply(self.moveDir,remainingDistance))
					remainingDistance = remainingDistance - distance
				else:
					self.m_state = STATE_WAIT
					
					#tiba di tempat, mulai menjalankan aktivitas (pendukung ataupun utama)
					remainingDistance = 0
					Global.Logger.LogDebug("Try starting activity...\n")
					if self.m_currentSupportActivity != None:
						self.m_currentSupportActivity.Start()
					else:
						self.m_currentActivity.Start()
					Global.Logger.LogDebug("Try starting activity DONE\n")
		Global.Logger.LogDebug("Target type "+str(self.m_targetType))
		if(self.m_targetType == TARGET_ROOM):
			Global.Logger.LogDebug(" target room "+self.m_targetRoom.m_name)
		Global.Logger.LogDebug("\n")
		if self.m_targetType == TARGET_ROOM and self.IsArriveInRoom():
			self.GenerateAndCheckPreActivityList()
		
	def FindTargetAndEntryPointForObject(self, ID):
		self.oldEntryPoint = self.entryPoint
		self.entryPoint = next(entry for entry in Agent.s_entryPointList if entry.target.m_id == ID)
		
	#memeriksa jika agent telah tiba di ruang untuk melakukan aktivitas
	def IsArriveInRoom(self):
		return self.m_targetType == TARGET_ROOM and self.m_targetRoom.IsInRoom(self.pos)
	
	def GenerateAndCheckPreActivityList(self):
		self.m_preActivityList = self.m_currentTerm.CheckEnvironmentTerm(self.m_environmentThreshold, self.m_targetRoom)
		stay, roomTerm = self.m_currentTerm.CheckRoomTerm(self.m_targetRoom)
		if stay:
			self.m_preactivityList.append(roomTerm)
			self.CheckSupportPreActivity2()
		else:
			if len(self.m_currentTerm.m_roomPrio) > 1 and self.m_targetRoom.m_name != self.m_currentTerm.m_roomPrio[1]:
				self.m_targetRoom = next((room for room in Global.g_myHouse.m_rooms if room.m_name == self.m_currentTerm.m_roomPrio[1]),None)
				self.entryPoint = EntryPoint.EntryPoint(self.m_targetRoom.m_targetCoord,self.m_targetRoom.m_floorIndex)
				self.m_targetType = TARGET_ROOM
				self.myPath = self.GeneratePath(self.pos, self.entryPoint.pos)
				self.setTarget(self.entryPoint.target)
			else:
				self.m_currentActivity.Suspend()
				
	def CheckSupportPreActivity2(self):
		if len(self.m_preActivityList) > 0:
			preAct = self.m_preActivityList.pop(0)
			self.FindTargetAndEntryPointForObject(preAct[AGENT_PREACT_OBJ])
			self.m_currentSupportActivity = next(sActivity for sActivity in self.m_supportActivity if sActivity.m_ID == preAct[AGENT_PREACT_ID])
			self.myPath = self.GeneratePath(self.pos, self.entryPoint.pos)
			self.setTarget(self.entryPoint.target)
	
	#memeriksa aktivitas pendukung sebelum
	def CheckSupportPreActivity(self):
		#memeriksa faktor lingkungan dan ruang
		Global.Logger.LogDebug("Checking pre activity\n")
		satisfiedEnvi = self.m_termChecklist[TERM_ENVI]
		satisfiedRoom = False
		preActivity = None
		objectID = None
		if not self.m_termChecklist[TERM_ENVI]:
			self.m_termChecklist[TERM_ENVI], preActivity, objectID = self.m_currentTerm.CheckEnvironmentSatisfied(self.m_environmentThreshold, self.m_targetRoom)
		
		if self.m_targetType == TARGET_ROOM:
			self.entryPoint = None
		
		if self.m_termChecklist[TERM_ENVI] and not self.m_termChecklist[TERM_ROOM]:
			print "cokiroom"
			self.m_termChecklist[TERM_ENVI] = True
			satisfiedRoom, preActivity, objectID = self.m_currentTerm.CheckRoomSatisfied(self.m_targetRoom)
		Global.Logger.LogDebug("Cond satisfied envi "+str(self.m_termChecklist[TERM_ENVI])+" "+str(self.m_currentTerm.m_activityID)+" room "+str(satisfiedRoom)+" "+str(preActivity)+" "+str(objectID))
		if (not self.m_termChecklist[TERM_ENVI]) or (satisfiedRoom and self.m_termChecklist[TERM_ENVI] and not self.m_termChecklist[TERM_ROOM]):
			if preActivity != None:
				#ada aktivitas pendukung yang harus dilakukan sebelum bisa memulai aktivitas
				self.FindTargetAndEntryPointForObject(objectID)
				self.m_currentSupportActivity = next(sActivity for sActivity in self.m_supportActivity if sActivity.m_ID == preActivity)
				self.m_termChecklist[TERM_ROOM] = True
				Global.Logger.LogDebug(" checking pread\n")
			self.m_targetType = TARGET_POINT
		elif not satisfiedRoom and not self.m_termChecklist[TERM_ROOM]:
			Global.Logger.LogDebug(" len room prio "+str(len(self.m_currentTerm.m_roomPrio)))
			if(len(self.m_currentTerm.m_roomPrio) > 1):
				Global.Logger.LogDebug(" cur target name "+self.m_targetRoom.m_name+" prio 1 "+self.m_currentTerm.m_roomPrio[1])
			#tidak memungkinkan untuk melakukan aktivitas yang dituju di ruang tersebut, memeriksa apakah bisa di ruangan lain, atau menunda aktivitas
			if len(self.m_currentTerm.m_roomPrio) > 1 and self.m_targetRoom.m_name != self.m_currentTerm.m_roomPrio[1]:
				self.m_targetRoom = next((room for room in Global.g_myHouse.m_rooms if room.m_name == self.m_currentTerm.m_roomPrio[1]),None)
				self.entryPoint = EntryPoint.EntryPoint(self.m_targetRoom.m_targetCoord,self.m_targetRoom.m_floorIndex)
				self.m_targetType = TARGET_ROOM
				self.m_termChecklist = [0] * TERM_COUNT
				Global.Logger.LogDebug(" should move away\n")
			else:
				self.m_currentActivity.Suspend()
				Global.Logger.LogDebug(" suspend\n")
				Global.Logger.DumpDebug()
				return
		else:
			if len(self.m_currentTerm.m_roomFactor) == 0:
				self.entryPoint = EntryPoint.EntryPoint(self.m_targetRoom.m_targetCoord,self.m_targetRoom.m_floorIndex)
				self.m_targetType = TARGET_POINT
			else:
				Global.Logger.LogDebug("Stay here\n")
				Global.Logger.DumpDebug()
				return
			
		Global.Logger.DumpDebug()
		self.myPath = self.GeneratePath(self.pos, self.entryPoint.pos)
		self.setTarget(self.entryPoint.target)
		Global.Logger.LogDebug("Generatepath pre activity : ")
		for path in self.myPath:
			s = "["+str(path.X)+","+str(path.Y)+"],"
			Global.Logger.LogDebug(s)
		Global.Logger.LogDebug("\n")
		Global.Logger.DumpDebug()
#-----------------------------------------------------------------------------------------------------------------------------------------

def TranslateToGridPos(pos,mazeIndex):
	try:
		gridX = int(math.floor((pos.X - PathFinding.Map.topPos[mazeIndex].X)/0.08))
		gridY = int(math.floor((PathFinding.Map.topPos[mazeIndex].Y - pos.Y)/0.08))
		posGrid = (gridX,gridY)
	except Exception as e:
		print e
		print pos
		Agent.hasErr = True
		posGrid = (0,0)
	return posGrid