from sprite import Sprite
import random, math
from util import *
import random

class Car(Sprite):
    def __init__(self, grid, pos, speed=2, version=-1):
        if version < 0:
            version = random.randint(1, 5)
        super().__init__(pos, "Car" + str(version))
        self.grid = grid
        self.vertex = pos
        self.speed = speed
        self.progress = 0
        self.edge = grid.getRandomEdge(pos)
        self.angle = self.edge.angle()
        self.image0 = self.image[0]
        self.image = [pygame.transform.rotate(self.image0, -self.angle)]

    def update(self, dt):
        if abs(self.angle - 360 - self.edge.angle()) < abs(self.angle-self.edge.angle()):
            self.angle -= 360
        if abs(self.angle + 360 - self.edge.angle()) < abs(self.angle-self.edge.angle()):
            self.angle += 360
        if self.angle != self.edge.angle():
            dtheta = self.edge.angle() - self.angle
            if abs(dtheta) < abs(ANG_VEL*dt/1000):
                self.angle = self.edge.angle()
            else:
                self.angle += math.copysign(ANG_VEL, dtheta)*dt/1000
            self.image = [pygame.transform.rotate(self.image0, -self.angle)]
        else:
            self.progress += self.speed*dt/1000

        if self.progress >= 1:
            self.progress -= 1
            self.vertex += self.edge
            self.edge = self.choose(self.vertex)
        d = Pose(-math.sin(math.radians(self.angle)), math.cos(math.radians(self.angle)))*24
        self.pos = self.vertex*SCALE + self.edge*self.progress*SCALE + d
        # self.pos.x -= math.sin(math.radians(self.angle))*24
        # self.pos.y += math.cos(math.radians(self.angle))*24

    def choose(self, vertex):
        edge = self.grid.getRandomEdge(vertex, direction=self.edge)
        return edge if edge else -self.edge

    # def collide(self, car):
    #     if self.

class Driver(Car):
    RECALCULATING = 0
    STRAIGHT = 1
    LEFT = 2
    RIGHT = 3
    UTURN = 4

    def __init__(self, grid, pos, speed=2):
        super().__init__(grid=grid, pos=pos, speed=speed, version=0)
        self.instruction = False#self.STRAIGHT
        self.grid.traversed[(self.vertex.x, self.vertex.y, self.edge.x, self.edge.y)] = 0
        self.angry = False

    def update(self, dt):
        if abs(self.angle - 360 - self.edge.angle()) < abs(self.angle-self.edge.angle()):
            self.angle -= 360
        if abs(self.angle + 360 - self.edge.angle()) < abs(self.angle-self.edge.angle()):
            self.angle += 360
        if self.angle != self.edge.angle():
            dtheta = self.edge.angle() - self.angle
            if abs(dtheta) < 5:
                self.angle = self.edge.angle()
            else:
                self.angle += math.copysign(ANG_VEL, dtheta)*dt/1000
            self.image = [pygame.transform.rotate(self.image0, -self.angle)]
        else:
            self.progress += self.speed*dt/1000
        if self.progress >= 1:
            v = (self.vertex.x, self.vertex.y, self.edge.x, self.edge.y)
            if v in self.grid.traversed:
                self.grid.traversed[v] = 1
            self.progress -= 1
            self.vertex += self.edge
            edge = self.choose(self.vertex)

            i1 = self.grid.neighbors.index(self.edge)
            i2 = self.grid.neighbors.index(edge)
            if (i2 - i1)%4 == 2: # U-turn
                self.grid.traversedIntersections[self.vertex.x][self.vertex.y][0] = True
                self.grid.traversedIntersections[self.vertex.x][self.vertex.y][1] = True
                self.grid.traversedIntersections[self.vertex.x][self.vertex.y][2] = True
                self.grid.traversedIntersections[self.vertex.x][self.vertex.y][3] = True
            elif (i2 - i1)%4 == 1: # left
                self.grid.traversedIntersections[self.vertex.x][self.vertex.y][i1] = True
                self.grid.traversedIntersections[self.vertex.x][self.vertex.y][(i1+1)%4] = True
                self.grid.traversedIntersections[self.vertex.x][self.vertex.y][(i1+2)%4] = True
            elif (i2 - i1)%4 == 0: # straight
                self.grid.traversedIntersections[self.vertex.x][self.vertex.y][i1] = True
                self.grid.traversedIntersections[self.vertex.x][self.vertex.y][(i1+1)%4] = True
            elif (i2 - i1)%4 == 3: # right
                self.grid.traversedIntersections[self.vertex.x][self.vertex.y][i1] = True

            self.edge = edge
        d = Pose(-math.sin(math.radians(self.angle)), math.cos(math.radians(self.angle)))*24
        self.pos = self.vertex*SCALE + self.edge*self.progress*SCALE + d
        # self.pos.x -= math.sin(math.radians(self.angle))*24
        # self.pos.y += math.cos(math.radians(self.angle))*24
        v = (self.vertex.x, self.vertex.y, self.edge.x, self.edge.y)
        if v in self.grid.traversed:
            self.grid.traversed[v] = min(max(self.progress, self.grid.traversed[v]), 1)

    def choose(self, vertex):
        edge = None
        # if self.instruction == self.STRAIGHT:
        #     edge = self.edge.copy()
        # elif self.instruction == self.LEFT:
        #     edge = self.edge.ccw()
        # elif self.instruction == self.RIGHT:
        #     edge = self.edge.cw()
        # elif self.instruction == self.UTURN:
        #     edge = -self.edge
        if self.instruction:
            edge = self.instruction
        if edge and not self.grid.getEdge(vertex, vertex+edge): # go straight if no turn available
            edge = self.edge
        if edge and edge == -self.edge and self.grid.countEdges(vertex) < 3:
            edge = self.edge


        if edge and (vertex.x, vertex.y, edge.x, edge.y) in self.grid.traversed: # ignore GPS if retracing steps
            if self.grid.countEdges(vertex) > 2:
                if edge != self.grid.getBestEdge(vertex, direction=self.edge):
                    self.angry = True
                self.instruction = None
            edge = None

        if edge and self.grid.getEdge(vertex, vertex+edge): # success
            if not (vertex.x, vertex.y, edge.x, edge.y) in self.grid.traversed:
                self.grid.traversed[(vertex.x, vertex.y, edge.x, edge.y)] = 0
            if edge and self.instruction and self.edge != edge: # reset instruction after turning
                self.instruction = None
            return edge
        
        edge = self.grid.getBestEdge(vertex, direction=self.edge)
        if not edge:
            edge = -self.edge
        if not (vertex.x, vertex.y, edge.x, edge.y) in self.grid.traversed:
            self.grid.traversed[(vertex.x, vertex.y, edge.x, edge.y)] = 0
        if self.edge != edge: # reset instruction after turning
            self.instruction = None
        return edge