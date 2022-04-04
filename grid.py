from car import Car, Driver
from sprite import Sprite
from constants import *
from util import *
import random

class Grid:
    neighbors = (Pose(1, 0), Pose(0, -1), Pose(-1, 0), Pose(0, 1))

    def __init__(self, W, H, speed, spawn, goal):
        self.cars = []
        self.sprites = []
        self.traversed = {}
        self.W = W
        self.H = H
        self.origin = Pose(*spawn)
        self.goal = Pose(*goal)
        self.generate()
        self.clean()
        self.driver = Driver(self, self.origin, speed=speed)
        self.spawnHouses()
        self.sprites.append(Sprite(self.goal*SCALE, "Goal", layer=-1))
        self.roadImgx = loadImage("Road.png")[0]
        self.roadImgy = pygame.transform.rotate(self.roadImgx, 90)
        self.deadend = [loadImage("Deadend.png")[0]]
        for i in range(3):
            self.deadend.append(pygame.transform.rotate(self.deadend[0], 90*(i+1)))
        self.fourway = loadImage("Fourway.png")[0]
        self.threeway = [loadImage("Troad.png")[0]]
        for i in range(3):
            self.threeway.append(pygame.transform.rotate(self.threeway[0], 90*(i+1)))
        self.turn = [loadImage("Turn.png")[0]]
        for i in range(3):
            self.turn.append(pygame.transform.rotate(self.turn[0], 90*(i+1)))

        for i in range(int(N_CARS*(self.W*self.H/100))):
            p = Pose(random.randint(0, self.W), random.randint(0, self.H))
            if self.getNode(p) > 0:
                self.cars.append(Car(self, p, speed=speed))

    def generate(self):
        self.nodes = [[-1 for y in range(self.H)] for x in range(self.W)] # distance to destination
        self.xedges = [[random.random() < EDGE_RATE for y in range(self.H)] for x in range(self.W-1)] # does edge exist
        self.yedges = [[random.random() < EDGE_RATE for y in range(self.H-1)] for x in range(self.W)] # does edge exist
        self.traversedIntersections = [[[0,0,0,0] for y in range(self.H)] for x in range(self.W)] # does edge exist
        self.expandNode(self.goal)
        if self.getNode(self.origin) < 0:
            self.generate() # Ensure a path exists

    def spawnHouses(self):
        for x in range(-1,self.W):
            for y in range(-1,self.H):
                pose = Pose(x,y)
                p = pose*SCALE + (SCALE//2, SCALE//2)
                fill = [[0 for i in range(5)] for j in range(5)]
                up = self.getEdge(pose, pose+(1,0))
                left = self.getEdge(pose, pose+(0,1))
                right = self.getEdge(pose+(1,0), pose+(1,1))
                down = self.getEdge(pose+(0,1), pose+(1,1))
                for i in range(5):
                    if left:
                        fill[1][i] = 1
                    if right:
                        fill[3][i] = 1
                    if up:
                        fill[i][1] = 1
                    if down:
                        fill[i][3] = 1
                for i in range(5):
                    if left:
                        fill[0][i] = 0
                    if right:
                        fill[4][i] = 0
                    if up:
                        fill[i][0] = 0
                    if down:
                        fill[i][4] = 0
                for i in range(5):
                    for j in range(5):
                        if fill[i][j]:
                            dp = Pose((i-2)*(SCALE-ROAD_SCALE*2)//3, (j-2)*(SCALE-ROAD_SCALE*2)//3)
                            self.sprites.append(Sprite(p+dp, "Roof"))

    def clean(self):
        for x in range(self.W):
            for y in range(self.H):
                if self.getNode(Pose(x, y)) < 0:
                    if x < self.W-1:
                        self.xedges[x][y] = False
                    if y < self.H-1:
                        self.yedges[x][y] = False

    def draw(self, surface, camera, t):
        for x in range(self.W):
            for y in range(self.H):
                if x < self.W-1:
                    self.drawXroad(surface, camera, Pose(x, y))
                if y < self.H-1:
                    self.drawYroad(surface, camera, Pose(x, y))
        for x in range(self.W):
            for y in range(self.H):
                self.drawIntersection(surface, camera, Pose(x, y))
        s = pygame.Surface(surface.get_size())  # the size of your rect
        s.set_colorkey((255,0,0))
        s.fill((255,0,0))
        s.set_alpha(128)
        for x in range(self.W):
            for y in range(self.H):
                if x < self.W-1:
                    self.drawXroad(s, camera, Pose(x, y), highlight=True)
                if y < self.H-1:
                    self.drawYroad(s, camera, Pose(x, y), highlight=True)
                self.highlightIntersection(s, camera, Pose(x, y))
        surface.blit(s, (0,0))

    def drawIntersection(self, surface, camera, pose):
        n = self.countEdges(pose)
        edges = [self.getEdge(pose, pose+edge) for edge in self.neighbors]
        image = None
        if n == 1: # dead end
            for i, edge in enumerate(edges):
                if edge:
                    image = self.deadend[i]
        elif n == 2: # turn
            for i, edge in enumerate(edges):
                edge2 = edges[(i+1)%4]
                if edge and edge2:
                    image = self.turn[i]
        elif n == 3: # three-way
            for i, edge in enumerate(edges):
                if not edge:
                    image = self.threeway[i]
        elif n == 4: # four-way
            image = self.fourway
        if not image:
            return
        w = image.get_width()
        h = image.get_height()
        p = pose*SCALE - camera
        if bounds(p - (WIDTH/2, HEIGHT/2), w + WIDTH, h + HEIGHT): # onscreen
            surface.blit(image, (p.x-w/2, p.y-h/2, w, h))

    def highlightIntersection(self, surface, camera, pose):
        p = pose*SCALE - camera
        r = ROAD_SCALE
        if bounds(p - (WIDTH/2, HEIGHT/2), r + WIDTH, r + HEIGHT):
            if self.traversedIntersections[pose.x][pose.y][0]: # bottom left
                pygame.draw.rect(surface, HIGHLIGHT_COLOR, (p.x-r, p.y, r, r))
            if self.traversedIntersections[pose.x][pose.y][1]: # bottom right
                pygame.draw.rect(surface, HIGHLIGHT_COLOR, (p.x, p.y, r, r))
            if self.traversedIntersections[pose.x][pose.y][2]: # top right
                pygame.draw.rect(surface, HIGHLIGHT_COLOR, (p.x, p.y-r, r, r))
            if self.traversedIntersections[pose.x][pose.y][3]: # top left
                pygame.draw.rect(surface, HIGHLIGHT_COLOR, (p.x-r, p.y-r, r, r))

    def drawXroad(self, surface, camera, pose, highlight=False):
        w = 0
        w2 = 0
        h = ROAD_SCALE
        p = pose*SCALE - camera + (SCALE/2, 0)
        if bounds(p - (WIDTH/2, HEIGHT/2), w + WIDTH + SCALE, h + HEIGHT): # onscreen
            if self.xedges[pose.x][pose.y]: # road exists
                if highlight:
                    if (pose.x, pose.y, 1, 0) in self.traversed: # lower (right)
                        k = self.traversed[(pose.x, pose.y, 1, 0)]
                        pygame.draw.rect(surface, HIGHLIGHT_COLOR, (p.x-w2-SCALE/2, p.y, w2*2+SCALE*k, h))
                    
                    if (pose.x+1, pose.y, -1, 0) in self.traversed: # upper (left)
                        k = self.traversed[(pose.x+1, pose.y, -1, 0)]
                        pygame.draw.rect(surface, HIGHLIGHT_COLOR, (p.x-w2-SCALE/2+(1-k)*SCALE, p.y-h, w2*2+SCALE*k, h))
                else:
                    # pygame.draw.rect(surface, (0,0,0), (p.x-w-SCALE/2, p.y-h, w*2+SCALE, h))
                    # pygame.draw.rect(surface, (0,0,0), (p.x-w-SCALE/2, p.y, w*2+SCALE, h))
                    surface.blit(self.roadImgx, (p.x-w-SCALE/2, p.y-h, w*2+SCALE, h*2))

    def drawYroad(self, surface, camera, pose, highlight=False):
        w = ROAD_SCALE
        h = 0
        h2 = 0
        p = pose*SCALE - camera + (0, SCALE/2)
        if bounds(p - (WIDTH/2, HEIGHT/2), w + WIDTH, h + HEIGHT + SCALE): # onscreen
            if self.yedges[pose.x][pose.y]: # road exists
                if highlight:
                    if (pose.x, pose.y, 0, 1) in self.traversed: # left (down)
                        k = self.traversed[(pose.x, pose.y, 0, 1)]
                        pygame.draw.rect(surface, HIGHLIGHT_COLOR, (p.x-w, p.y-h2-SCALE/2, w, 2*h2+SCALE*k))
                    if (pose.x, pose.y+1, 0, -1) in self.traversed: # right (up)
                        k = self.traversed[(pose.x, pose.y+1, 0, -1)]
                        pygame.draw.rect(surface, HIGHLIGHT_COLOR, (p.x, p.y-h2-SCALE/2+(1-k)*SCALE, w, 2*h2+SCALE*k))
                else:
                    # pygame.draw.rect(surface, (0,0,0), (p.x-w, p.y-h-SCALE/2, w, 2*h+SCALE))
                    # pygame.draw.rect(surface, (0,0,0), (p.x, p.y-h-SCALE/2, w, 2*h+SCALE))
                    surface.blit(self.roadImgy, (p.x-w, p.y-h-SCALE/2, w*2, 2*h+SCALE))


    def getEdge(self, pose1, pose2):
        if self.inBounds(pose1) and self.inBounds(pose2):
            if pose1.y == pose2.y:
                return self.xedges[(pose1.x+pose2.x-1)//2][pose1.y]
            elif pose1.x == pose2.x:
                return self.yedges[pose1.x][(pose1.y+pose2.y-1)//2]
        return False

    def getEdgeScore(self, pose1, pose2):
        if not self.getEdge(pose1, pose2):
            return NaN
        return self.getNode(pose1) - self.getNode(pose2)

    def getBestEdge(self, pose, direction=None):
        bestEdge = None
        if self.inBounds(pose):
            bestScore = 0
            for edge in self.neighbors:
                if not self.getEdge(pose, pose + edge):
                    continue
                if direction and -direction == edge:
                    continue
                score = self.getEdgeScore(pose, pose + edge) + random.random()*0.1
                if not bestEdge or score > bestScore:
                    bestScore = score
                    bestEdge = edge
        return bestEdge

    def countEdges(self, pose):
        edges = 0
        for edge in self.neighbors:
            if self.getEdge(pose, pose + edge):
                edges += 1
        return edges

    def getRandomEdge(self, pose, direction=None):
        bestEdge = None
        if self.inBounds(pose):
            bestScore = 0
            for edge in self.neighbors:
                if not self.getEdge(pose, pose + edge):
                    continue
                if direction and -direction == edge:
                    continue
                score = random.random()
                if not bestEdge or score > bestScore:
                    bestScore = score
                    bestEdge = edge
        return bestEdge

    def getNode(self, pose):
        if self.inBounds(pose):
            return self.nodes[pose.x][pose.y]
        return -1

    def inBounds(self, pose):
        return pose.x >= 0 and pose.y >= 0 and pose.x < self.W and pose.y < self.H

    def onGrid(self, pose):
        return self.inBounds(pose) and self.getNode(pose) >= 0

    def expandNode(self, pose, cost=0):
        self.nodes[pose.x][pose.y] = cost
        for edge in self.neighbors:
            if self.getEdge(pose, pose+edge):
                if self.getNode(pose+edge) < 0 or self.getNode(pose+edge) > cost+1:
                    self.expandNode(pose+edge, cost+1)