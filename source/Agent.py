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
class Agent:
	possibleTarget = []
	entryPointList = []
	hasErr = False
	agentList = []
	
	def __init__(self,position,targetPoint,index,state = STATE_IDLE):
		self.pos = position
		self.targetPoint = targetPoint
		self.entryPoint = None
		self.oldEntryPoint = None
		self.state = state
		self.initialPos = position
		self.hasNewTarget = False
		self.waitTime = (Schedule.SCHEDULE[index][0][1] * 5)
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
		
		self.objectList = []
		
		self.speedFactor = 0.15
	
	def setTarget(self,newTarget):
		self.target = newTarget
		self.hasNewTarget = True
		if newTarget != None:
			self.target.available = False
	
	def update(self):
		# if Agent.hasErr:
			# i = 0
			# while i<10000:
				# i+=1
		print "initializuuuuuu "+str(self.initialized)
		if not self.initialized:
			self.AssignToClosestTarget()
			self.initialized = True
		if self.state != STATE_MOVE:
			self.pathIndex = 1
			print "ma waite "+ str(self.waitTime)
			if self.waitTime > 0:
				self.waitTime -=1
				return self.pos
			# if not self.pathCalculated:
			if self.canGetNewTarget:
				self.calculateNextTarget()
			if self.target == None:
				print "cannot find targetimo"
				return self.pos
			self.canGetNewTarget = False
			start = None
			print "tariga "+str(self.target.targetPoint)
			if self.oldEntryPoint != None:
				start = TranslateToGridPos(self.oldEntryPoint.pos)
			else:
				start = TranslateToGridPos(self.pos)
			end = TranslateToGridPos(self.entryPoint.pos)
			print "estar"
			# print start
			# print end
			# if not self.pathCalculated:
			self.myPath = PathFinding.astarv3(start,end,self.myIndex)
			
			#No path found. Wait a moment
			if self.myPath == None:
				return self.pos
			
			if self.oldEntryPoint != None and self.myPath[0] != self.pos:# and not self.pathCalculated:
				print "inserting "+str(self.pos)+" "+str(self.myPath[0])+"endis"
				self.myPath.insert(0,self.pos)
			
			# print "kokota"
			# print self.entryPoint
			# print self.entryPoint.pos
			# print self.entryPoint.target
			# print self.entryPoint.target.targetPoint
			if self.entryPoint.pos != self.entryPoint.target.targetPoint:# and not self.pathCalculated:
				print "appendix "+str(self.entryPoint.target.targetPoint)
				self.myPath.append(self.entryPoint.target.targetPoint)
			# self.pathCalculated = True
			print "parat"
			for pata in self.myPath:
				print TranslateToGridPos(pata)
			print "petok"
			#print self.myPath
			self.pathIndex = 1
			self.recalculateMoveDir()
			self.state = STATE_MOVE
			return self.pos
		else:
			print "movettgffgx"
			#TODO: implement movement
			#pa = Point3d(0,0,0)
			# print TranslateToGridPos(self.pos)
			# print TranslateToGridPos(self.entryPoint.pos)
			#print self.pathIndex
			print len(self.myPath)
			
			destination  = self.myPath[self.pathIndex]
			#self.moveDir = Vector3f.Subtract(Vector3f(destination.X,destination.Y,destination.Z),Vector3f(self.pos.X,self.pos.Y,self.pos.Z))
			distance = self.pos.DistanceTo(destination)
			
			#print str(self.pos) +"               "+ str(destination)
			#print distance
			#print self.moveDir
			
			if distance > self.speedFactor:
				myGrid = TranslateToGridPos(self.pos)
				self.blockedBy,blocked = PathFinding.IsBlocked(myGrid)
				if blocked:
					blockPos = PathFinding.TranslateToRealPos(PathFinding.Map.liveBlock[self.blockedBy])
					print blockPos
					blockDir = Vector3f.Subtract(Vector3f(blockPos[0],blockPos[1],0),Vector3f(self.pos.X,self.pos.Y,0))
					# normalMoveDir = Vector3f.Divide(self.moveDir,self.moveDir.Length)
					blockDir = Vector3f.Divide(blockDir,blockDir.Length)
					dotP = (blockDir.X*self.moveDir.X) + (blockDir.Y*self.moveDir.Y)
					angle = math.acos(dotP)
					print "radongle "+str(angle)
					angle = math.degrees(angle)
					print "dedengle "+str(angle)
					if angle > 60 and (abs(myGrid[0]-PathFinding.Map.liveBlock[self.blockedBy][0]) > PathFinding.OVERLAP_LIMIT or abs(myGrid[1]-PathFinding.Map.liveBlock[self.blockedBy][1]) > PathFinding.OVERLAP_LIMIT):
						blocked = False
					if self.entryPoint.pos != self.entryPoint.target.targetPoint and self.pathIndex == (len(self.myPath) - 1):
						blocked = False
				if blocked:
					if self.blockCounter < 10 and self.myIndex > self.blockedBy:
						if not self.hasWait:
							print "waiteo"
							self.blockCounter += 1
							return self.pos
						else:
							self.hasWait = True
					print "kalukulatimo "+str(myGrid[0])+" "+str(myGrid[1])
					# if self.pathIndex+1 < len(self.myPath):
						# myNextDestGrid = TranslateToGridPos(self.myPath[self.pathIndex+1])
					# else:
						# myNextDestGrid = TranslateToGridPos(self.myPath[self.pathIndex])
					myNextDestGrid = TranslateToGridPos(self.entryPoint.pos)
					midPath = PathFinding.astarv3(myGrid,myNextDestGrid,self.myIndex,True)
					
					#No path found. Wait a moment
					if midPath == None:
						print "waiteo"
						self.blockCounter += 1
						if self.blockCounter > 10 and self.myIndex > self.blockedBy and self.pathIndex > 2:
							self.pos = rs.PointAdd(self.pos,(Vector3d.Multiply(self.moveDir,self.speedFactor) * (-1)))
						return self.pos
					
					if self.entryPoint.pos != self.entryPoint.target.targetPoint:
						print "appendix "+str(self.entryPoint.target.targetPoint)
						midPath.append(self.entryPoint.target.targetPoint)
					#del midPath[-1]
					del self.myPath[self.pathIndex-1:]
					#errPause = True
					#print "ompat"
					#print midPath
					#return self.pos
					self.myPath.extend(midPath)
					# self.myPath[self.pathIndex:self.pathIndex] = midPath
					# self.pathIndex+=1
					self.hasWait = False
					self.recalculateMoveDir()
				else:
					self.blockCounter = 0
					self.blockedBy = -1
				# print "parat"
				# for pata in self.myPath:
					# print TranslateToGridPos(pata)
				# print "petok"
				self.pos = rs.PointAdd(self.pos,Vector3d.Multiply(self.moveDir,self.speedFactor))
			else:
				self.pos = destination
				self.pathIndex+=1
				self.canGetNewTarget = True
				if self.pathIndex < len(self.myPath):
					self.recalculateMoveDir()
				else:
					self.state = STATE_WAIT
					self.waitTime = (Schedule.SCHEDULE[self.myIndex][self.targetIndex][1] * 5)
			self.hasWait = False
			return self.pos
	
	def calculateNextTarget(self):
		#print "abalabalsuuuzzziccc"
		if self.targetIndex == len(Schedule.SCHEDULE[self.myIndex]) - 1:
			print "rettainoi"
			self.setTarget(None)
			return
			
		if self.target != None:
			self.target.available = True
			
		nextSchedule = Schedule.SCHEDULE[self.myIndex][self.targetIndex + 1]
		print nextSchedule
		availableTarget = [target for target in Agent.possibleTarget if target.available and target.hasActivity(nextSchedule[0])]
		print "hole target"
		print availableTarget
	
		specificTarget = [target for target in availableTarget if target.isSpecificToAgent(self.myIndex)]
		print "daspecifica"
		print specificTarget
		
		if specificTarget != None and len(specificTarget) > 0:
			availableTarget = specificTarget
		else:
			availableTarget = [target for target in availableTarget if target.notHaveSpecific()]
			print "non despio"
			print availableTarget
		
		if len(availableTarget) > 0:
				
			if self.target != None:
				self.targetIndex += 1
			print availableTarget
			ron = random.randint(0,len(availableTarget)-1)
			print ron
			self.setTarget(availableTarget[ron])
		else:
			self.setTarget(None)
			return
			
			
		# self.setTarget(availableTarget[random.randrange(len(availableTarget))])
		
		
		entryPointL = []#[ep for ep in Agent.entryPointList if (ep.target.targetPoint == self.target)]
		# print Agent.entryPointList
		for ep in Agent.entryPointList:
			# print ep.target
			# print self.target
			if ep.target == self.target:
				entryPointL.append(ep)
			# print "appen"
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
		#print self.myPath
		destination  = self.myPath[self.pathIndex]
		self.moveDir = Vector3f.Subtract(Vector3f(destination.X,destination.Y,destination.Z),Vector3f(self.pos.X,self.pos.Y,self.pos.Z))
		self.moveDir.Unitize()
		# self.moveDir = Vector3f.Divide(self.moveDir,self.moveDir.Length*20)
		
	def AssignToClosestTarget(self):
		print "targetasukof"
		distanceMin = float(sys.maxint)
		targetIndex = 0
		for (i,target) in enumerate(Agent.possibleTarget):
			curDistance = self.pos.DistanceTo(target.targetPoint)
			if curDistance < distanceMin:
				distanceMin = curDistance
				targetIndex = i
		print Agent.possibleTarget[targetIndex]
		print Agent.possibleTarget[targetIndex].targetPoint
		epList = []#[ep for ep in Agent.entryPointList if ep.target == Agent.possibleTarget[targetIndex]]
		for (i,ep) in enumerate(Agent.entryPointList):
			print "check epo "+str(i)
			print ep.target
			print ep.target.targetPoint
			if ep.target == Agent.possibleTarget[targetIndex]:
				print "inklading"
				epList.append(ep)
		self.setTarget(Agent.possibleTarget[targetIndex])
		self.entryPoint = epList[0]
		
	def setBoundArea(self,area):
		self.boundArea = area
		
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

def TranslateToGridPos(pos):
	#print "aa"
	#print pos
	#print PathFinding.Map.topPos.GetType()
	try:
		gridX = int(math.floor((pos.X - PathFinding.Map.topPos.X)/0.08))
		gridY = int(math.floor((PathFinding.Map.topPos.Y - pos.Y)/0.08))
		posGrid = (gridX,gridY)
	except Exception as e:
		print e
		print pos
		Agent.hasErr = True
		posGrid = (0,0)
	return posGrid