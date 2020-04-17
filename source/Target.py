class Target:
    def __init__(self,tp = None):
        self.targetPoint = tp
        self.available = True
    def setTargetPoint(self,point):
        self.targetPoint = point
    