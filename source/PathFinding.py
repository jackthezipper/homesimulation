import sys
from Rhino.Geometry import Point3d

STATE_FREE = 0
STATE_BLOCKED = STATE_FREE + 1
STATE_ENTRY = STATE_BLOCKED + 1

STATUS_UNCHECKED = 0
STATUS_INCHECK = STATUS_UNCHECKED + 1
STATUS_CHECKED = STATUS_INCHECK + 1

OVERLAP_LIMIT = 6

class Node():
	"""A node class for A* Pathfinding"""

	def __init__(self, parent=None, position=None, selfReference=False):
		self.position = position

		self.reset()
		self.parent = parent
		if selfReference:
			self.parent = self

	def equals(self, other):
		if other == None:
			return False
		return self.position == other.position
		
	def makeSelfReference(self):
		self.parent = self
		
	def reset(self):
		self.g = 0
		self.h = 0
		self.f = 0
		self.isClosed = False
		self.isOpen = False
		self.parent = None
		
class Map():
	topPos = None
	maze = []
	additionalWeight = []
	liveBlock = []
	allNode = None

def euclidian(posA,posB):
	diffX = posA[0] - posB[0]
	diffY = posA[1] - posB[1]
	return (diffX*diffX)+(diffY*diffY)

def TranslateToRealPos(pos):
	realX = Map.topPos.X + ((pos[0]*0.08) + 0.04)
	realY = Map.topPos.Y - ((pos[1]*0.08) + 0.04)
	return (realX,realY)

DIR_UP = 0
DIR_UPRIGHT = DIR_UP + 1
DIR_RIGHT = DIR_UPRIGHT + 1
DIR_DOWNRIGHT = DIR_RIGHT + 1
DIR_DOWN = DIR_DOWNRIGHT + 1
DIR_DOWNLEFT = DIR_DOWN + 1
DIR_LEFT = DIR_DOWNLEFT + 1
DIR_UPLEFT = DIR_LEFT + 1

def getDir(nodeA,nodeB):
	diffX = nodeB.position[0] - nodeA.position[0]
	diffY = nodeB.position[1] - nodeA.position[1]
	
	if diffX > 0:
		return DIR_UPRIGHT if diffY > 0 else (DIR_RIGHT if diffY == 0 else DIR_DOWNRIGHT)
		
	if diffX == 0:
		return DIR_UP if diffY > 0 else DIR_DOWN
		
	if diffX < 0:
		return DIR_UPLEFT if diffY > 0 else (DIR_LEFT if diffY == 0 else DIR_DOWNLEFT)

def astarv3(start, end,ignoreIndex,liveBlocker = False):
	"""Returns a list of tuples as a path from the given start to the given end in the given maze"""
	
	if Map.allNode == None:
		Map.allNode = [[None for i in range(len(Map.maze[0]))] for j in range(len(Map.maze))]
		for i in range(len(Map.maze)):
			for j in range(len(Map.maze[0])):
				Map.allNode[i][j] = Node(None, (i,j))
	for i in range(len(Map.maze)):
		for j in range(len(Map.maze[0])):
			Map.allNode[i][j].reset()
	# allHailNode = [[None for i in range(len(Map.maze[0]))] for j in range(len(Map.maze))]
	# for i in range(len(Map.maze)):
		# for j in range(len(Map.maze[0])):
			# allHailNode[i][j] = Node(None, (i,j))
	# Create start and end node
	# start_node = allHailNode[start[0]][start[1]]
	start_node = Map.allNode[start[0]][start[1]]
	start_node.makeSelfReference()
	start_node.g = start_node.h = start_node.f = 0
	# end_node = allHailNode[end[0]][end[1]]
	end_node = Map.allNode[end[0]][end[1]]
	end_node.g = end_node.h = end_node.f = 0
	
	# Initialize both open and closed list
	open_list = []
	# closed_list = []
	
	# Add the start node
	open_list.append(start_node)
	start_node.isOpen = True
	
	# Loop until you find the end
	# iter = 0
	while len(open_list) > 0:
		current_node = open_list[0]
		current_index = 0
		#pop from openlist and add to closed list
		open_list.pop(current_index)
		current_node.isOpen = False
		current_node.isClosed = True
		if current_node.equals(end_node):
			return reconstructPathv2(current_node,liveBlocker)
			break
	
		for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
			coord = (current_node.position[0]+new_position[0],current_node.position[1]+new_position[1])
			if (coord[0] < 0) or (coord[1] < 0) or (coord[0] >= len(Map.maze)) or (coord[1] >= len(Map.maze[0])):
				continue
			if (Map.maze[coord[0]][coord[1]] == STATE_BLOCKED):
				continue
			if (Map.maze[coord[0]][coord[1]] == STATE_ENTRY and (coord[0] != end_node.position[0] or coord[1] != end_node.position[1])):
				continue
			
			liveBlockerWeight = 0
			if liveBlocker:
				overlapWithOther = False
				for index,block in enumerate(Map.liveBlock):
					if index == ignoreIndex:
						continue
					diffTile = max(abs(coord[0] - block[0]),abs(coord[1] - block[1]))
					overlapWithOther = diffTile < OVERLAP_LIMIT
					if overlapWithOther:
						break
					if (diffTile < 10):
						liveBlockerWeight = (10-diffTile)*5
						break
				if overlapWithOther:
					continue
			nodeCheck = allHailNode[coord[0]][coord[1]]
			if not (nodeCheck.isClosed):
				isOldNode = nodeCheck.isOpen
				if not isOldNode:
					nodeCheck.g = sys.maxint
				newG = current_node.g + (Map.additionalWeight[nodeCheck.position[0]][nodeCheck.position[1]]+liveBlockerWeight)**2# + euclidian(current_node.position,nodeCheck.position)
				if newG < nodeCheck.g:
					
					nodeCheck.g = newG
					nodeCheck.parent = current_node
				nodeCheck.f = nodeCheck.g + euclidian(nodeCheck.position,end)
				if not isOldNode:
					InsertNode(nodeCheck,open_list)
	return None

def InsertNode(node,list):
	listLen = len(list)
	limitUp = listLen - 1
	limitDown = 0
	mid = 0
	while (limitUp - limitDown) > 1:
		mid = (limitUp + limitDown)/2
		if list[mid].f > node.f:
			limitUp = mid
		else:
			limitDown = mid
	list.insert(mid,node)
	node.isOpen = True


def reconstructPathv2(node,liveBlocker = False):
	curNode = node
	path = []
	nodePath = []
	# realPos = TranslateToRealPos(curNode.position)
	# point = Point3d(realPos[0],realPos[1],0)
	# path.append(point)
	nodePath.insert(0,curNode)
	while not curNode.parent.equals(curNode):
		# print ('mnode ',curNode.position)
		curNode = curNode.parent
		#realPos = TranslateToRealPos(curNode.position)
		#point = Point3d(realPos[0],realPos[1],0)
		nodePath.insert(0,curNode)
	nodePath = simplifyPathv3(nodePath,liveBlocker)
	for node in nodePath:
		realPos = TranslateToRealPos(node.position)
		point = Point3d(realPos[0],realPos[1],0)
		path.append(point)
	# return nodePath
	return path

def simplifyPathv3(path,liveBlocker = False):
	index = len(path) - 2
	while index > 0:
		if lineInSightv2(path[index + 1].position[0],path[index + 1].position[1],path[index - 1].position[0],path[index - 1].position[1],liveBlocker):
			path.remove(path[index])
		# else:
		index-=1
	return path
	
BLOCKER_FREE = 0
BLOCKER_IN = BLOCKER_FREE + 1
BLOCKER_BETWEEN = BLOCKER_IN + 1
BLOCKER_FIRST = BLOCKER_BETWEEN + 1
BLOCKER_FIRST_FREE = BLOCKER_FIRST + 1
def lineInSightv2(startX,startY,endX,endY,ignoreIndex,liveBlocker = False):
	#print "deva "+toExcel((startX,startY))+" "+toExcel((endX,endY))
	#print "deva "+str(startX)+" "+str(startY)+" "+str(endX)+" "+str(endY)
	diffX = (endX-startX)
	diffY = (endY-startY)
	dirX = 1 if diffX > 0 else -1#(endX-startX)>0?1:-1
	dirY = 1 if diffY > 0 else -1
	
	diffX = abs(diffX)
	diffY = abs(diffY)
	
	blockerState = BLOCKER_FREE
	if (diffX >= diffY):
		for i in range(1,diffX):
			#print("check ",(startY + (diffY*i/diffX*dirY)),",",(startX + i*dirX)," is ",maze[startY + (diffY*i/diffX*dirY)][startX + i*dirX])
			checkX = startY + (diffY*i/diffX*dirY)
			checkY = startX + i*dirX
			#print "ceka "+str(checkY)+" "+str(checkX)
			#print "ceka "+toExcel((checkY,checkX))
			if (Map.maze[checkY][checkX] == STATE_BLOCKED) or ((Map.additionalWeight[checkY][checkX] > 10)):
				return False
			if liveBlocker:
				for index,block in enumerate(Map.liveBlock):
					if index == ignoreIndex:
						continue
					if (abs(checkY - block[0]) < OVERLAP_LIMIT) and (abs(checkX - block[1]) < OVERLAP_LIMIT):
						print "at live block "+str(checkY)+" "+str(checkX)
						return False

			if Map.additionalWeight[checkY][checkX] > 0:
				if i == 0:
					blockerState = BLOCKER_FIRST
				elif blockerState == BLOCKER_FREE:
					blockerState = BLOCKER_IN
				elif blockerState == BLOCKER_FIRST_FREE:
					blockerState = BLOCKER_BETWEEN
					return False
			elif blockerState == BLOCKER_FIRST:
				blockerState = BLOCKER_FIRST_FREE
			elif blockerState == BLOCKER_IN:
				blockerState = BLOCKER_BETWEEN
				return False
	else:
		for i in range(1,diffY):
			checkX = startY + i*dirY
			checkY = startX + (diffX*i/diffY*dirX)
			#print "cekb "+toExcel((checkY,checkX))
			# print "cekb "+str(checkY)+" "+str(checkX)
			#print('check2 ',(startY + i*dirY),',',(startX + (diffX*i/diffY*dirX)),' is ',maze[startY + i*dirY][startX + (diffX*i/diffY*dirX)])
			if (Map.maze[checkY][checkX] == STATE_BLOCKED) or ((Map.additionalWeight[checkY][checkX] > 10)):
				return False
			if liveBlocker:
				for index,block in enumerate(Map.liveBlock):
					if index == ignoreIndex:
						continue
					if (abs(checkY - block[0]) < OVERLAP_LIMIT) and (abs(checkX - block[1]) < OVERLAP_LIMIT):
						return False
			
			if Map.additionalWeight[checkY][checkX] > 0:
				if i == 0:
					blockerState = BLOCKER_FIRST
				elif blockerState == BLOCKER_FREE:
					blockerState = BLOCKER_IN
				elif blockerState == BLOCKER_FIRST_FREE:
					blockerState = BLOCKER_BETWEEN
					return False
			elif blockerState == BLOCKER_FIRST:
				blockerState = BLOCKER_FIRST_FREE
			elif blockerState == BLOCKER_IN:
				blockerState = BLOCKER_BETWEEN
				return False
	return True

def IsBlocked(pos):
	for (index,blocker) in enumerate(Map.liveBlock):
		if blocker[0] == pos [0] and blocker[1] == pos[1]:
			continue
		if abs(blocker[0] - pos[0]) < 10 and abs(blocker[1] - pos[1]) < 10:
			return index,True
	return -1,False
	