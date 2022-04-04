from util import *
import random

class Sprite:
    def __init__(self, pos, image, frames=1, flip=False, layer=0):
        self.pos = pos
        self.image = loadImage(image+".png", number=frames, flip=flip)
        self.imw = self.image[0].get_width()
        self.imh = self.image[0].get_height()
        self.layer = layer
        self.frames = frames
        self.t0 = random.random()*FRAME_RATE*frames

    def draw(self, surface, camera, t):
        i = int((t-self.t0)*FRAME_RATE/1000) % self.frames
        surface.blit(self.image[i], (self.pos.x-camera.x-self.imw/2, self.pos.y-camera.y-self.imh/2))

    def onscreen(self, camera, w, h):
        dp = self.pos - camera
        return bounds(self.pos - camera - (w/2, h/2), w + self.imw, h + self.imh)