#import from python lib
import random
import math
import sys

#import custom file
import Target
import PathFinding

from Rhino.Geometry import Point3d, Vector3f
import rhinoscriptsyntax as rs

PathFinding = reload(PathFinding)

STATE_IDLE = 0
STATE_MOVE = STATE_IDLE + 1
STATE_WAIT = STATE_MOVE + 1

class Agent:
	possibleTarget = []
	entryPointList = []
	
	def __init__(self,position,targetPoint,state = STATE_IDLE):
		self.pos = position
		self.targetPoint = targetPoint
		self.entryPoint = None
		self.oldEntryPoint = None
		self.state = state
		self.initialPos = position
		self.hasNewTarget = False
		self.waitTime = 0
		self.myPath = None
		self.pathIndex = 0
		self.target = None
		self.moveDir = Vector3f(0,0,0)
		self.pathCalculated = False
	
	def setTarget(self,newTarget):
		self.target = newTarget
		self.hasNewTarget = True
		self.target.available = False
	
	def update(self):
		if self.state != STATE_MOVE:
			self.pathIndex = 1
			if self.waitTime > 0:
				self.waitTime -=1
				return self.pos
			#if not self.pathCalculated:
			self.calculateNextTarget()
			start = None
			if self.oldEntryPoint != None:
				start = TranslateToGridPos(self.oldEntryPoint.pos)
			else:
				start = TranslateToGridPos(self.pos)
			end = TranslateToGridPos(self.entryPoint.pos)
			print "estar"
			print start
			print end
			#if not self.pathCalculated:
			self.myPath = PathFinding.thetastarv2(start,end)
			
			if self.oldEntryPoint != None:
				self.myPath.insert(0,self.pos)
			
			if self.entryPoint.pos != self.entryPoint.target.targetPoint:# and not self.pathCalculated:
				self.myPath.append(self.entryPoint.target.targetPoint)
			#self.pathCalculated = True
			print self.myPath
			self.pathIndex = 1
			self.recalculateMoveDir()
			self.state = STATE_MOVE
			return self.pos
		else:
			print "movettggg"
			#TODO: implement movement
			#pa = Point3d(0,0,0)
			print TranslateToGridPos(self.pos)
			print TranslateToGridPos(self.entryPoint.pos)
			print self.pathIndex
			print self.myPath
			destination  = self.myPath[self.pathIndex]
			#self.moveDir = Vector3f.Subtract(Vector3f(destination.X,destination.Y,destination.Z),Vector3f(self.pos.X,self.pos.Y,self.pos.Z))
			distance = self.pos.DistanceTo(destination)
			
			print str(self.pos) +"               "+ str(destination)
			print distance
			#print self.moveDir
			
			if distance > 0.1:
				self.pos = rs.PointAdd(self.pos,self.moveDir)
			else:
				self.pos = destination
				self.pathIndex+=1
				if self.pathIndex < len(self.myPath):
					self.recalculateMoveDir()
				else:
					self.state = STATE_WAIT
					self.waitTime = 20
			
			return self.pos
	
	def calculateNextTarget(self):
		print "abalabalsuuuzzziii"
		availableTarget = [target for target in Agent.possibleTarget if target.available]
		if self.target != None:
			self.target.available = True
		self.setTarget(availableTarget[random.randrange(len(availableTarget))])
		entryPointL = []#[ep for ep in Agent.entryPointList if (ep.target.targetPoint == self.target)]
		print Agent.entryPointList
		for ep in Agent.entryPointList:
			print ep.target
			print self.target
			if ep.target == self.target:
				entryPointL.append(ep)
				print "appen"
		selectedEntry = 0
		distanceMin = float(sys.maxint)
		for (i,ep) in enumerate(entryPointL):
			curDistance = self.pos.DistanceTo(ep.pos)
			if curDistance == distanceMin:
				curDistance = distanceMin
				selectedEntry = i
		self.oldEntryPoint = self.entryPoint
		self.entryPoint = entryPointL[selectedEntry]
		
	def recalculateMoveDir(self):
		destination  = self.myPath[self.pathIndex]
		self.moveDir = Vector3f.Subtract(Vector3f(destination.X,destination.Y,destination.Z),Vector3f(self.pos.X,self.pos.Y,self.pos.Z))
		self.moveDir = Vector3f.Divide(self.moveDir,self.moveDir.Length*20)

def TranslateToGridPos(pos):
	#print "aa"
	#print pos
	#print PathFinding.Map.topPos.GetType()
	gridX = int(math.floor((pos.X - PathFinding.Map.topPos.X)/0.1))
	gridY = int(math.floor((PathFinding.Map.topPos.Y - pos.Y)/0.1))
	posGrid = (gridX,gridY)
	return posGrid