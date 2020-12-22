#import Agent
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino as rh
from Rhino.Geometry import Vector3d
from ghpythonlib.componentbase import executingcomponent as component


#DISTANCE_TOLERANCE
DOOR_OPEN	= 0
DOOR_CLOSE	= DOOR_OPEN + 1

class Door:
	def __init__(self, panel, frameBB, rotationCenter, rotDir, status = DOOR_OPEN):
		self.m_panel = panel
		self.m_frameBB = frameBB #doorframe bounding box
		self.m_status = status
		self.m_rotationCenter = rotationCenter
		self.m_lock = False
		self.m_rectTest = None
		self.m_openAngle = rotDir * 90
		
		print(self.m_frameBB)
	
	#this basic function 
	def ShouldOpen(self, rect):
		if self.m_lock:
			return False
		
	def Open(self):
		if self.m_status == DOOR_CLOSE:
			sc.doc = rh.RhinoDoc.ActiveDoc
			rs.RotateObject(self.m_panel,self.m_rotationCenter,self.m_openAngle,Vector3d.ZAxis)
			self.m_status = DOOR_OPEN
			sc.doc = component.ghdoc
	
	def Close(self):
		if self.m_status == DOOR_OPEN:
			sc.doc = rh.RhinoDoc.ActiveDoc
			rs.RotateObject(self.m_panel,self.m_rotationCenter,-self.m_openAngle,Vector3d.ZAxis)
			self.m_status = DOOR_CLOSE
			sc.doc = component.ghdoc
	# def Update(self):
		# for agent in Agent.agentList:
			