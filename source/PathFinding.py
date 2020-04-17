import sys
from Rhino.Geometry import Point3d

STATE_FREE = 0
STATE_BLOCKED = STATE_FREE + 1
STATE_ENTRY = STATE_BLOCKED + 1

STATUS_UNCHECKED = 0
STATUS_INCHECK = STATUS_UNCHECKED + 1
STATUS_CHECKED = STATUS_INCHECK + 1

class Node():
	"""A node class for A* Pathfinding"""

	def __init__(self, parent=None, position=None, selfReference=False):
		self.parent = parent
		if selfReference:
			self.parent = self
		self.position = position

		self.g = 0
		self.h = 0
		self.f = 0

	def equals(self, other):
		if other == None:
			return False
		return self.position == other.position
		
	def makeSelfReference(self):
		self.parent = self
		
class Map():
	topPos = None
	maze = []
	additionalWeight = []

def thetastar(start, end):
	"""Returns a list of tuples as a path from the given start to the given end in the given maze"""

	# Create start and end node
	start_node = Node(None, start,True)
	start_node.g = start_node.h = start_node.f = 0
	end_node = Node(None, end)
	end_node.g = end_node.h = end_node.f = 0
	
	# Initialize both open and closed list
	open_list = []
	closed_list = []
	
	# Add the start node
	mazeStatus = [[STATUS_UNCHECKED for i in range(len(Map.maze[0]))] for j in range(len(Map.maze))]
	open_list.append(start_node)
	#print len(Map.maze[0])
	mazeStatus[start_node.position[0]][start_node.position[1]] = STATUS_INCHECK
	
	
	# Loop until you find the end
	while len(open_list) > 0:
		# Get the current node
		# find node with least f
		current_node = open_list[0]
		current_index = 0
		for index, item in enumerate(open_list):
			if item.f < current_node.f:
				current_node = item
				current_index = index
		print "take node at "+str(current_node.position[0]) +" "+str(current_node.position[1]) +" with f "+str(current_node.f)
	
		#pop from openlist and add to closed list
		open_list.pop(current_index)
		closed_list.append(current_node)
		#print('evaluating ',current_node.position)
		if current_node.equals(end_node):
			print('Path found')
			return reconstructPath(current_node)
			break
	
		mazeStatus[current_node.position[0]][current_node.position[1]] == STATUS_CHECKED
	
		for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
			coord = (current_node.position[0]+new_position[0],current_node.position[1]+new_position[1])
			if (coord[0] < 0) or (coord[1] < 0) or (coord[0] >= len(Map.maze)) or (coord[1] >= len(Map.maze[0])):
				continue
			if (Map.maze[coord[0]][coord[1]] == STATE_BLOCKED):
				continue
			if (Map.maze[coord[0]][coord[1]] == STATE_ENTRY and (coord[0] != end_node.position[0] or coord[1] != end_node.position[1])):
				continue
			if mazeStatus[coord[0]][coord[1]] != STATUS_CHECKED:
				neighbor = None
			
				print "checking neighbor at "+str(coord[0])+" "+str(coord[1])
				
				for node in open_list:
					if node.position == coord:
						neighbor = node
						print "node in open list"
				if neighbor == None:
					neighbor = Node(None,coord)
					neighbor.g = sys.maxint
					print "this is new node"
	
				#print('evaluatng neighbor ',neighbor.position)
				#update_vertex(maze,mazeStatus,current_node,new_node,open_list)
			
				if lineInSight(current_node.parent.position[0],current_node.parent.position[1],neighbor.position[0],neighbor.position[1]):
					newG = current_node.parent.g + euclidian(current_node.parent.position,neighbor.position) + Map.additionalWeight[neighbor.position[0]][neighbor.position[1]]*Map.additionalWeight[neighbor.position[0]][neighbor.position[1]]
					if (newG < neighbor.g):
						print "replacing linesight from " + str(neighbor.parent.position[0])+","+str(neighbor.parent.position[1])+" to "+str(current_node.position[0])+","+str(current_node.position[1])
						neighbor.g = newG
						neighbor.parent = current_node.parent
						#TODO:: calculating f value!!!!!
					print "awer "+str(len(Map.additionalWeight))+" "+str(len(Map.additionalWeight[0]))
					print "nepor "+str(neighbor.position[0])+" "+str(neighbor.position[1])
					neighbor.f = neighbor.g + euclidian(neighbor.position,end)# + Map.additionalWeight[neighbor.position[0]][neighbor.position[1]]
				else:
					newG = current_node.g + euclidian(current_node.position,neighbor.position) + Map.additionalWeight[neighbor.position[0]][neighbor.position[1]]*Map.additionalWeight[neighbor.position[0]][neighbor.position[1]]
					if newG < neighbor.g:
						print "replacing the unseen from " + str(neighbor.parent.position[0])+","+str(neighbor.parent.position[1])+" to "+str(current_node.position[0])+","+str(current_node.position[1])
						neighbor.g = newG
						neighbor.parent = current_node
					neighbor.f = neighbor.g + euclidian(neighbor.position,end)# + Map.additionalWeight[neighbor.position[0]][neighbor.position[1]]
				if mazeStatus[neighbor.position[0]][neighbor.position[1]] == STATUS_UNCHECKED:
					open_list.append(neighbor)
					mazeStatus[neighbor.position[0]][neighbor.position[1]] = STATUS_INCHECK
					#print('add to open list ',neighbor.position)
	return None

def thetastarv2(start, end):
	"""Returns a list of tuples as a path from the given start to the given end in the given maze"""

	allHailNode = [[None for i in range(len(Map.maze[0]))] for j in range(len(Map.maze))]
	for i in range(len(Map.maze)):
		for j in range(len(Map.maze[0])):
			allHailNode[i][j] = Node(None, (i,j))
	# Create start and end node
	start_node = allHailNode[start[0]][start[1]]
	start_node.makeSelfReference()
	start_node.g = start_node.h = start_node.f = 0
	end_node = allHailNode[end[0]][end[1]]
	end_node.g = end_node.h = end_node.f = 0
	
	# Initialize both open and closed list
	open_list = []
	closed_list = []
	
	# Add the start node
	open_list.append(start_node)
	
	# Loop until you find the end
	while len(open_list) > 0:
		# Get the current node
		# find node with least f
		current_node = open_list[0]
		current_index = 0
		for index, item in enumerate(open_list):
			if item.f < current_node.f:
				current_node = item
				current_index = index
		#print "take node at "+str(current_node.position[0]) +" "+str(current_node.position[1]) +" with f "+str(current_node.f)
	
		#pop from openlist and add to closed list
		open_list.pop(current_index)
		closed_list.append(current_node)
		#print('evaluating ',current_node.position)
		if current_node.equals(end_node):
			#print('Path found')
			return reconstructPath(current_node)
			break
	
		#mazeStatus[current_node.position[0]][current_node.position[1]] == STATUS_CHECKED
	
		for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
			coord = (current_node.position[0]+new_position[0],current_node.position[1]+new_position[1])
			nodeCheck = allHailNode[coord[0]][coord[1]]
			if (coord[0] < 0) or (coord[1] < 0) or (coord[0] >= len(Map.maze)) or (coord[1] >= len(Map.maze[0])):
				continue
			if (Map.maze[coord[0]][coord[1]] == STATE_BLOCKED):
				continue
			if (Map.maze[coord[0]][coord[1]] == STATE_ENTRY and (coord[0] != end_node.position[0] or coord[1] != end_node.position[1])):
				continue
				
			if not (nodeCheck in closed_list):
				if not (nodeCheck in open_list):
					nodeCheck.g = sys.maxint
				
				if lineInSight(current_node.parent.position[0],current_node.parent.position[1],nodeCheck.position[0],nodeCheck.position[1]):
					newG = current_node.parent.g + euclidian(current_node.parent.position,nodeCheck.position) + Map.additionalWeight[nodeCheck.position[0]][nodeCheck.position[1]]*Map.additionalWeight[nodeCheck.position[0]][nodeCheck.position[1]]
					if (newG < nodeCheck.g):
						#if nodeCheck.parent != None:
							#print "prev linesight parent " +str(nodeCheck.parent.position[0])+","+str(nodeCheck.parent.position[1])
						nodeCheck.g = newG
						nodeCheck.parent = current_node.parent
						#print "replacing linesight parent to " + str(nodeCheck.parent.position[0])+","+str(nodeCheck.parent.position[1])
						#TODO:: calculating f value!!!!!
					#print "awer "+str(len(Map.additionalWeight))+" "+str(len(Map.additionalWeight[0]))
					#print "nepor "+str(nodeCheck.position[0])+" "+str(nodeCheck.position[1])
					nodeCheck.f = nodeCheck.g + euclidian(nodeCheck.position,end)# + Map.additionalWeight[neighbor.position[0]][neighbor.position[1]]
				else:
					newG = current_node.g + euclidian(current_node.position,nodeCheck.position) + Map.additionalWeight[nodeCheck.position[0]][nodeCheck.position[1]]*Map.additionalWeight[nodeCheck.position[0]][nodeCheck.position[1]]
					if newG < nodeCheck.g:
						#if nodeCheck.parent != None:
							#print "prev unseen parent " +str(nodeCheck.parent.position[0])+","+str(nodeCheck.parent.position[1])
						
						nodeCheck.g = newG
						nodeCheck.parent = current_node
						#print "replacing unseen parent to " + str(nodeCheck.parent.position[0])+","+str(nodeCheck.parent.position[1])
					nodeCheck.f = nodeCheck.g + euclidian(nodeCheck.position,end)# + Map.additionalWeight[neighbor.position[0]][neighbor.position[1]]
				if not (nodeCheck in open_list):
					open_list.append(nodeCheck)
					#print('add to open list ',neighbor.position)
	return None

def euclidian(posA,posB):
	diffX = posA[0] - posB[0]
	diffY = posA[1] - posB[1]
	return (diffX*diffX)+(diffY*diffY)

def lineInSight(startX,startY,endX,endY):
	#print('check insight ',startX,' ',startY,' to ',endX,' ',endY)
	lenx = len(Map.maze[0])
	leny = len(Map.maze)

	diffX = (endX-startX)
	diffY = (endY-startY)
	dirX = 1 if diffX > 0 else -1#(endX-startX)>0?1:-1
	dirY = 1 if diffY > 0 else -1

	diffX = abs(diffX)
	diffY = abs(diffY)

	if (diffX >= diffY):
		for i in range(diffX):
		#print("check ",(startY + (diffY*i/diffX*dirY)),",",(startX + i*dirX)," is ",maze[startY + (diffY*i/diffX*dirY)][startX + i*dirX])
			if Map.maze[startX + i*dirX][startY + (diffY*i/diffX*dirY)] == STATE_BLOCKED:
				return False
	else:
		for i in range(diffY):
		#print('check2 ',(startY + i*dirY),',',(startX + (diffX*i/diffY*dirX)),' is ',maze[startY + i*dirY][startX + (diffX*i/diffY*dirX)])
			if Map.maze[startX + (diffX*i/diffY*dirX)][startY + i*dirY] == STATE_BLOCKED:
				return False
	return True

def reconstructPath(node):
	curNode = node
	path = []
	#path.append(curNode)
	realPos = TranslateToRealPos(curNode.position)
	point = Point3d(realPos[0],realPos[1],0)
	path.insert(0,point)
	while not curNode.parent.equals(curNode):
		print ('mnode ',curNode.position)
		curNode = curNode.parent
		realPos = TranslateToRealPos(curNode.position)
		point = Point3d(realPos[0],realPos[1],0)
		path.insert(0,point)
	return path

def TranslateToRealPos(pos):
	realX = Map.topPos.X + ((pos[0]*0.1) + 0.05)
	realY = Map.topPos.Y - ((pos[1]*0.1) + 0.05)
	return (realX,realY)