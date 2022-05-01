#import Agent
import Global
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino as rh
from Rhino.Geometry import Vector3d
from ghpythonlib.componentbase import executingcomponent as component


#DISTANCE_TOLERANCE
DOOR_OPEN	= 0
DOOR_CLOSE	= DOOR_OPEN + 1

#panel parameter
PANEL_OBJ			= 0
PANEL_ROT_CENTER	= PANEL_OBJ + 1
PANEL_ROT_DIR		= PANEL_ROT_CENTER + 1

class Door:
	def __init__(self, panels, frameBB, room, status = DOOR_OPEN):
		self.m_panels = panels
		self.m_frameBB = frameBB #doorframe bounding box
		self.m_status = status
		self.m_room = room
		self.m_lock = False
		self.m_rectTest = None
		self.m_openAngle = []#= rotDir * 90
		for panel in self.m_panels:
			self.m_openAngle = panel[PANEL_ROT_DIR] * 90
		
		Global.Logger.LogDebug("Create door with bound "+str(frameBB)+"\n")
	
	#this basic function 
	def ShouldOpen(self, rect):
		if self.m_lock:
			return False
		
	def Open(self):
		if self.m_status == DOOR_CLOSE:
			sc.doc = rh.RhinoDoc.ActiveDoc
			for i in range(0, len(self.m_panels)):
				rs.RotateObject(self.m_panels[i][PANEL_OBJ],self.m_panels[i][PANEL_ROT_CENTER],self.m_openAngle[i],Vector3d.ZAxis)
			self.m_status = DOOR_OPEN
			sc.doc = component.ghdoc
	
	def Close(self):
		if self.m_status == DOOR_OPEN:
			sc.doc = rh.RhinoDoc.ActiveDoc
			for i in range(0, len(self.m_panels)):
				rs.RotateObject(self.m_panels[i][PANEL_OBJ],self.m_panels[i][PANEL_ROT_CENTER],-self.m_openAngle[i],Vector3d.ZAxis)
			self.m_status = DOOR_CLOSE
			sc.doc = component.ghdoc
	
	def IsClosed(self):
		return self.m_status == DOOR_CLOSE
	# def Update(self):
		# for agent in Agent.agentList:
			