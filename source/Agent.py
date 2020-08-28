#import from python lib
import random
import math
import sys

#import custom file
import Target
import PathFinding
import Schedule
Schedule = reload(Schedule)

from Rhino.Geometry import Point3d, Vector3f,Vector3d,Line,Polyline
import rhinoscriptsyntax as rs

import scriptcontext as sc
import Rhino.Geometry

PathFinding = reload(PathFinding)

STATE_IDLE = 0
STATE_MOVE = STATE_IDLE + 1
STATE_WAIT = STATE_MOVE + 1
errPause = False

#30 min -> 15 sec
TIMECONVERSION = 2 #to multiply dt
TIMEFACTOR = 1000 #to multiply waitTime

class Agent:
	possibleTarget = []
	entryPointList = []
	hasErr = False
	agentList = []
	s_scaleSpeed = 1.0
	
	def __init__(self,position,targetPoint,index,state = STATE_IDLE):
		self.pos = position
		self.targetPoint = targetPoint
		self.entryPoint = None
		self.oldEntryPoint = None
		self.state = state
		self.initialPos = position
		self.hasNewTarget = False
		self.waitTime = (Schedule.SCHEDULE[index][0][1] * TIMEFACTOR)
		self.myPath = None
		self.pathIndex = 0
		self.target = None
		self.moveDir = Vector3f(0,1,0)
		self.pathCalculated = False
		self.myIndex = index
		self.blockedBy = -1
		self.blockCounter = 0
		self.hasWait = False
		self.targetIndex = 0
		self.initialized = False
		self.canGetNewTarget = True
		self.boundArea = None
		self.curveBoundArea = None
		self.diagonalBound = 0
		
		self.objectList = []
		
		self.speedFactor = 0.15
		self.myFloorIndex = 0
		self.needStair = False
		
		self.m_active = False
	
	def setTarget(self,newTarget):
		self.target = newTarget
		self.hasNewTarget = True
		if newTarget != None:
			self.target.available = False
	
	def update(self, dt):
		if not self.initialized:
			self.AssignToClosestTarget()
			self.initialized = True
		
		if not self.m_active:
			return self.pos
		
		if self.state != STATE_MOVE:
			self.pathIndex = 1
			if self.waitTime > 0:
				self.waitTime -= (dt * Agent.s_scaleSpeed * TIMECONVERSION)
				return self.pos
			
			#getting new target
			if self.canGetNewTarget:
				self.calculateNextTarget()
			if self.target == None:
				return self.pos
			self.canGetNewTarget = False
			
			#calculating path
			start = None
			if self.oldEntryPoint != None:
				start = TranslateToGridPos(self.oldEntryPoint.pos,self.myFloorIndex)
			else:
				start = TranslateToGridPos(self.pos,self.myFloorIndex)
			
			self.needStair = (self.target.floorIndex != self.myFloorIndex)
			
			if self.needStair:
				stairIndex = "STAIRS_"+str(self.myFloorIndex)
				stairTarget = next(trgt for trgt in Agent.possibleTarget if trgt.hasActivity(stairIndex))
				stairEntry = next(entry for entry in Agent.entryPointList if entry.target == stairTarget)
				end = TranslateToGridPos(stairEntry.pos,self.myFloorIndex)
			else:
				end = TranslateToGridPos(self.entryPoint.pos,self.myFloorIndex)
			self.myPath = PathFinding.astarv3(start,end,self.myIndex,self.myFloorIndex)
			
			#No path found. Wait a moment
			if self.myPath == None:
				return self.pos
			
			#path found
			if self.oldEntryPoint != None and self.myPath[0] != self.pos:
				self.myPath.insert(0,self.pos)
			
			if self.needStair:
				self.myPath.append(stairEntry.target.targetPoint)
			elif self.entryPoint.pos != self.entryPoint.target.targetPoint:
				self.myPath.append(self.entryPoint.target.targetPoint)
			self.pathIndex = 1
			self.recalculateMoveDir()
			self.state = STATE_MOVE
			return self.pos
		else:
			destination  = self.myPath[self.pathIndex]
			distance = self.pos.DistanceTo(destination)
			distanceCovered = float(dt) * Agent.s_scaleSpeed / 1000
			if distance > distanceCovered:#self.speedFactor:
				#there still distance within the path
				myGrid = TranslateToGridPos(self.pos,self.myFloorIndex)
				self.blockedBy,blocked = PathFinding.IsBlocked(myGrid,self.myFloorIndex)
				
				if blocked:
					#path maybe blocked
					blockPos = PathFinding.TranslateToRealPos(PathFinding.Map.liveBlock[self.blockedBy][0],self.myFloorIndex)
					blockDir = Vector3f.Subtract(Vector3f(blockPos[0],blockPos[1],0),Vector3f(self.pos.X,self.pos.Y,0))
					blockDir = Vector3f.Divide(blockDir,blockDir.Length)
					dotP = (blockDir.X*self.moveDir.X) + (blockDir.Y*self.moveDir.Y)
					angle = math.acos(dotP)
					angle = math.degrees(angle)
					if angle > 60 and (abs(myGrid[0]-PathFinding.Map.liveBlock[self.blockedBy][0][0]) > PathFinding.OVERLAP_LIMIT or abs(myGrid[1]-PathFinding.Map.liveBlock[self.blockedBy][0][1]) > PathFinding.OVERLAP_LIMIT):
						blocked = False
					if self.entryPoint.pos != self.entryPoint.target.targetPoint and self.pathIndex == (len(self.myPath) - 1):
						blocked = False
				
				
				if blocked:
					#path is blocked
					if self.blockCounter < 10 and self.myIndex > self.blockedBy:
						if not self.hasWait:
							self.blockCounter += 1
							return self.pos
						else:
							self.hasWait = True
					
					if self.needStair:
						stairIndex = "STAIRS_"+str(self.myFloorIndex)
						stairEntry = next(trgt for trgt in Agent.possibleTarget if trgt.hasActivity(stairIndex))
						myNextDestGrid = TranslateToGridPos(stairEntry.pos,self.myFloorIndex)
					else:
						myNextDestGrid = TranslateToGridPos(self.entryPoint.pos,self.myFloorIndex)
					midPath = PathFinding.astarv3(myGrid,myNextDestGrid,self.myIndex,self.myFloorIndex,True)
					
					#No path found. Wait a moment
					if midPath == None:
						self.blockCounter += 1
						if self.blockCounter > 10 and self.myIndex > self.blockedBy and self.pathIndex > 2:
							self.pos = rs.PointAdd(self.pos,(Vector3d.Multiply(self.moveDir,self.speedFactor) * (-1)))
						return self.pos
					
					if self.entryPoint.pos != self.entryPoint.target.targetPoint:
						midPath.append(self.entryPoint.target.targetPoint)
					del self.myPath[self.pathIndex-1:]
					self.myPath.extend(midPath)
					self.hasWait = False
					self.recalculateMoveDir()
				else:
					#not blocked, continue to move
					self.blockCounter = 0
					self.blockedBy = -1
				
				#update agent position
				self.pos = rs.PointAdd(self.pos,Vector3d.Multiply(self.moveDir,distanceCovered))
			else:
				#already close with destination
				remainingDistance = distanceCovered - distance
				while (remainingDistance > 0):
					self.pos = destination
					self.pathIndex+=1
					if self.pathIndex < len(self.myPath):
						self.recalculateMoveDir()
						destination  = self.myPath[self.pathIndex]
						distance = self.pos.DistanceTo(destination)
						if remainingDistance < distance:
							self.pos = rs.PointAdd(self.pos,Vector3d.Multiply(self.moveDir,remainingDistance))
						remainingDistance = remainingDistance - distance
					elif self.needStair:
						nextStairIndex = "STAIRS_"+str(self.target.floorIndex)
						nextStairTarget = next(trgt for trgt in Agent.possibleTarget if trgt.hasActivity(nextStairIndex))
						nextStairEntry = next(entry for entry in Agent.entryPointList if entry.target == nextStairTarget)
						self.myFloorIndex = self.target.floorIndex
						start = TranslateToGridPos(nextStairEntry.pos,self.myFloorIndex)
						end = TranslateToGridPos(self.entryPoint.pos,self.myFloorIndex)
						
						self.myPath = PathFinding.astarv3(start,end,self.myIndex,self.myFloorIndex)
						self.pos = nextStairTarget.targetPoint
						self.myPath.insert(0,self.pos)
						if self.entryPoint.pos != self.entryPoint.target.targetPoint:
							self.myPath.append(self.entryPoint.target.targetPoint)
						self.pathIndex = 1
						self.recalculateMoveDir()
						self.needStair = False
						distance = self.pos.DistanceTo(destination)
						if remainingDistance < distance:
							self.pos = rs.PointAdd(self.pos,Vector3d.Multiply(self.moveDir,remainingDistance))
						remainingDistance = remainingDistance - distance
					else:
						self.canGetNewTarget = True
						self.state = STATE_WAIT
						self.waitTime = (Schedule.SCHEDULE[self.myIndex][self.targetIndex][1] * TIMEFACTOR)
						remainingDistance = 0
			self.hasWait = False
			return self.pos
	
	def calculateNextTarget(self):
		if self.targetIndex == len(Schedule.SCHEDULE[self.myIndex]) - 1:
			self.setTarget(None)
			return
			
		if self.target != None:
			self.target.available = True
			
		nextSchedule = Schedule.SCHEDULE[self.myIndex][self.targetIndex + 1]
		availableTarget = [target for target in Agent.possibleTarget if target.available and target.hasActivity(nextSchedule[0])]
	
		specificTarget = [target for target in availableTarget if target.isSpecificToAgent(self.myIndex)]
		
		if specificTarget != None and len(specificTarget) > 0:
			availableTarget = specificTarget
		else:
			availableTarget = [target for target in availableTarget if target.notHaveSpecific()]
		
		if len(availableTarget) > 0:
			if self.target != None:
				self.targetIndex += 1
			ron = random.randint(0,len(availableTarget)-1)
			self.setTarget(availableTarget[ron])
		else:
			self.setTarget(None)
			return
			
		entryPointL = []
		for ep in Agent.entryPointList:
			if ep.target == self.target:
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
		destination  = self.myPath[self.pathIndex]
		self.moveDir = Vector3f.Subtract(Vector3f(destination.X,destination.Y,destination.Z),Vector3f(self.pos.X,self.pos.Y,self.pos.Z))
		self.moveDir.Unitize()
		
	def AssignToClosestTarget(self):
		distanceMin = float(sys.maxint)
		targetIndex = 0
		for (i,target) in enumerate(Agent.possibleTarget):
			curDistance = self.pos.DistanceTo(target.targetPoint)
			if curDistance < distanceMin:
				distanceMin = curDistance
				targetIndex = i
		print Agent.possibleTarget[targetIndex]
		print Agent.possibleTarget[targetIndex].targetPoint
		epList = []
		for (i,ep) in enumerate(Agent.entryPointList):
			if ep.target == Agent.possibleTarget[targetIndex]:
				epList.append(ep)
		self.setTarget(Agent.possibleTarget[targetIndex])
		self.entryPoint = epList[0]
		self.myFloorIndex = self.target.floorIndex
		
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