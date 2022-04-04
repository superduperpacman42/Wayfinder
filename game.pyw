import pygame
import os, sys, math, random
from PIL import Image
from constants import *
from grid import Grid
from util import *

class Game:

    responses = ("I went that way last time!", "Hey, what's going on here?",\
        "We're going in circles!", "You're not fooling me this time!", "Darn GPS is broken again...", \
        "I'm not going that way again...", "This is getting ridiculous!", "Maybe I can ask for directions...", \
        "Next time I'm buying a real map", "I'm not falling for that twice!")
    levels = ("School Zone", "Getting to Work","Getting Groceries", "Trip to the Mall", "Dining Out", "Road Trip!", "The GPS Store")
    levelText = (("Alright Sally, let's drop","you off in time for class at 8"), \
        ("My boss will be furious", "if I'm not there by 9"), \
        ("I hope I make it to the store", "before they close at 7..."), \
        ("The sale starts at 2,", "I gotta beat the lines!"), \
        ("My reservation's at 8,", "I've got plenty of time"), \
        ("This is a long trip, I'd like", "to get there by sundown at 6"),
        ("Time to replace,","this useless GPS!"))
    levelTimes = (8, 9, 7, 2, 8, 6, 12)
    levelDurations = (4, 5, 8, 8, 10, 20, 10)
    levelSpeeds = (1,1.5,2,2,2,2,2)
    levelW = (3, 5, 7, 6, 8, 20, 10)
    levelH = (4, 5, 5, 8, 8, 3, 10)
    levelSpawn = ((0,0), (2,4), (3,2), (5,7), (0,7), (0,2), (2,5))
    levelGoal = ((2,3), (2,0), (6,0), (0,4), (4,3), (19,2), (8,3))
    levelTimeScale = (1,1,1,1,1,1,1)

    def reset(self, respawn=False):
        ''' Resets the game state '''
        self.t = 0
        self.captionText1 = ""
        self.lastResponse = -1
        self.captionTime1 = 0
        self.captionText2 = ""
        self.captionTime2 = 0
        self.grid = Grid(self.levelW[self.level-1], self.levelH[self.level-1], self.levelSpeeds[self.level-1], self.levelSpawn[self.level-1], self.levelGoal[self.level-1])
        self.driver = self.grid.driver
        self.camera = self.driver.vertex*SCALE
        self.cars = self.grid.cars
        self.sprites = self.grid.sprites + self.cars + [self.driver]
        self.time = self.levelTimes[self.level-1]*60 - self.levelDurations[self.level-1]

    def clock(self):
        h = ((int(self.time)//60-1) %12)+1
        m = int(self.time)%60
        if self.t%1000 > 400 or self.state == "shutdown":
            time = f"{h//10}{h%10}:{m//10}{m%10}"
        else:
            time = f"{h//10}{h%10} {m//10}{m%10}"
        caption = self.font4.render(time, True, (255,255,255))
        x = WIDTH-118 - caption.get_width()/2
        y = 60 - caption.get_height()/2
        self.screen.blit(caption, (x, y))

    def ui(self):
        ''' Draws the user interface overlay '''
        if self.state == "goal":
            caption1 = self.font3.render("YOU HAVE ARRIVED", True, (63,0,214))
            caption2 = self.font3.render("AT YOUR DESTINATION", True, (63,0,214))
            x1 = WIDTH/2-caption1.get_width()/2-110
            y1 = HEIGHT/2 - caption1.get_height()
            x2 = WIDTH/2-caption2.get_width()/2-110
            y2 = HEIGHT/2
            b = 10
            pygame.draw.rect(self.screen, (255,255,255), (min(x1,x2)-b, y1, max(caption1.get_width(),caption2.get_width())+2*b, caption1.get_height()+caption2.get_height()))
            pygame.draw.rect(self.screen, (63,0,214), (min(x1,x2)-b, y1, max(caption1.get_width(),caption2.get_width())+2*b, caption1.get_height()+caption2.get_height()),2)
            self.screen.blit(caption1, (x1, y1))
            self.screen.blit(caption2, (x2, y2))

            t = int(self.time) - self.levelTimes[self.level-1]*60 # positive = late
            if t > 5: # very late
                text = f"{t} minutes late??? Darn GPS... "
            elif t > 1: # late
                text = f"Oh no! I'm {t} minutes late!"
            elif t == 1: # one minute late
                text = "Almost made it, just a minute late"
            elif t == 0: # exact
                text = "Right on time!"
            elif t == -1: # one minute early
                text = "Made it with a minute to spare!"
            else: # early
                text = f"{-t} minutes ahead of schedule!"
            if self.level == len(self.levels):
                if t > 0: # late
                    text = "Goodbye, my deceitful friend"
                else: # early
                    text = "Time for an upgrade!"
            caption = self.font2.render('"'+text+'"', True, (0,0,0))
            x = WIDTH/2-caption.get_width()/2-110
            y = HEIGHT-50-caption.get_height()
            b = 10
            b2 = 3
            pygame.draw.rect(self.screen, (255,255,255), (x-b, y+b2, caption.get_width()+2*b, caption.get_height()+b2),border_radius=20)
            pygame.draw.rect(self.screen, (0,0,0), (x-b, y+b2, caption.get_width()+2*b, caption.get_height()+b2), 2,border_radius=20)
            self.screen.blit(caption, (x, y))
            return
        if self.captionText1:#self.captionTime1 > 0:
            caption = self.font1.render(self.captionText1, True, (63,0,214))
            x = WIDTH/2-caption.get_width()/2-110
            y = 50
            b = 10
            pygame.draw.rect(self.screen, (255,255,255), (x-b, y, caption.get_width()+2*b, caption.get_height()))
            pygame.draw.rect(self.screen, (63,0,214), (x-b, y, caption.get_width()+2*b, caption.get_height()), 2)
            self.screen.blit(caption, (x, y))
        if self.captionTime2 > 0:
            caption = self.font2.render('"'+self.captionText2+'"', True, (0,0,0))
            x = WIDTH/2-caption.get_width()/2-110
            y = HEIGHT-50-caption.get_height()
            b = 10
            b2 = 3
            pygame.draw.rect(self.screen, (255,255,255), (x-b, y+b2, caption.get_width()+2*b, caption.get_height()+b2),border_radius=20)
            pygame.draw.rect(self.screen, (0,0,0), (x-b, y+b2, caption.get_width()+2*b, caption.get_height()+b2), 2,border_radius=20)
            self.screen.blit(caption, (x, y))

    def drawLevel(self):
        t = self.levelText[self.level-1]
        caption1 = self.font2.render('"'+t[0]+" ", True, (0,0,0))
        caption2 = self.font2.render(" "+t[1]+'"', True, (0,0,0))
        x1 = WIDTH/2-caption1.get_width()/2-110
        x2 = WIDTH/2-caption2.get_width()/2-110
        y2 = HEIGHT-50-caption2.get_height()
        y1 = y2 - caption1.get_height()
        b = 10
        b2 = 3
        pygame.draw.rect(self.screen, (255,255,255), (min(x1,x2)-b, y1+b2, max(caption1.get_width(),caption2.get_width())+2*b, caption1.get_height()+caption2.get_height()+b2),border_radius=20)
        pygame.draw.rect(self.screen, (0,0,0), (min(x1,x2)-b, y1+b2, max(caption1.get_width(),caption2.get_width())+2*b, caption1.get_height()+caption2.get_height()+b2),2,border_radius=20)
        self.screen.blit(caption1, (x1, y1))
        self.screen.blit(caption2, (x2, y2))

        caption = self.font5.render(f"LEVEL {self.level}", True, (255,255,255))
        x = WIDTH/2-caption.get_width()/2-110
        y = HEIGHT/3
        self.screen.blit(caption, (x, y))
        y += caption.get_height()+20
        caption = self.font3.render(self.levels[self.level-1], True, (255,255,255))
        x = WIDTH/2-caption.get_width()/2-110
        self.screen.blit(caption, (x, y))


    def update(self, dt, keys):
        ''' Updates the game by a timestep and redraws graphics '''
        self.t += dt
        if self.state == "instructions":
            self.screen.blit(self.instructions[0], (0,0))
            self.clock()
            return
        if self.state == "off":
            self.screen.blit(self.off[0], (0,0))
            if self.t > 500:
                self.t = 0
                playSound("Enter.wav")
                self.state = "splash"
            return
        if self.state == "splash":
            self.screen.blit(self.splash[0], (0,0))
            if self.t > 3000:
                self.t = 0
                self.state = "instructions"
                playSound("Enter.wav")
            return
        if self.state == "win":
            self.screen.blit(self.win[0], (0,0))
            caption = self.font6.render(str(int(self.total)), True, (255,255,255))
            x = WIDTH/2-caption.get_width()/2-110
            y = HEIGHT*0.58
            self.screen.blit(caption, (x, y))
            self.clock()
            return
        if self.state == "shutdown":
            self.screen.blit(self.off[0], (0,0))
            self.shutdown[0].set_alpha(max(0,255-int(self.t*(255/1000))))
            self.screen.blit(self.shutdown[0], (0,0))
            if self.t > 2000:
                self.state = "off"
                self.level = 1
                self.total = 0
                self.reset()
            return
        if self.state == "level":
            self.screen.blit(self.blank[0], (0,0))
            self.drawLevel()
            self.clock()
            if self.t > 3000:
                self.t = 0
                self.state = "play"
                setVolume(V_HIGH)
            return
        if self.state == "play":
            self.time += dt*TIME_SCALE/1000 * self.levelTimeScale[self.level-1]
            # self.total += dt*TIME_SCALE/1000 * self.levelTimeScale[self.level-1]
        self.captionTime1 -= dt
        self.captionTime2 -= dt
        if self.driver.angry:
            self.driver.angry = False
            i = random.randint(0,len(self.responses)-1)
            if self.lastResponse < 0:
                i = 0
            elif self.lastResponse == i:
                i = (self.lastResponse+1)%len(self.responses)
            self.setCaption2(self.responses[i])
            self.lastResponse = i
        if CAMERA_KP*dt > 1 or (CAMERA_KP*(self.driver.pos - self.camera - Pose(WIDTH-220, HEIGHT)/2)*dt).norm() < 1:
            self.camera = self.driver.pos.int() - Pose(WIDTH-220, HEIGHT)//2
        else:
            self.camera += (CAMERA_KP*(self.driver.pos - self.camera - Pose(WIDTH-220, HEIGHT)/2)*dt).int()
        surface = pygame.Surface((WIDTH, HEIGHT))
        surface.fill((206,195,152))
        self.grid.draw(surface, self.camera, self.t)

        if self.state == "play":
            self.driver.update(dt)
            self.displayInstruction()
        for car in self.cars:
            car.update(dt)

        if self.state == "play" and self.driver.vertex == self.grid.goal:
            playSound("Enter.wav")
            setVolume(V_LOW)
            self.state = "goal"

        self.sprites = sorted(self.sprites, key=lambda s:s.layer)
        for s in self.sprites:
            if s.onscreen(self.camera, WIDTH, HEIGHT):
                s.draw(surface, self.camera, self.t)

        if self.state == "play":
            d = Pose(-math.sin(math.radians(self.driver.angle)), math.cos(math.radians(self.driver.angle)))
            p = self.driver.pos + d*0 - self.camera
            d2 = ~(self.grid.goal*SCALE - self.driver.pos)*40
            ind = pygame.transform.rotate(self.indicator[0], -d2.angle())
            surface.blit(ind, (p.x+d2.x-12, p.y+d2.y-12))

        surface.blit(self.overlay[0], (0,0))
        self.screen.blit(surface, (0,0))
        self.ui()
        self.clock()

    def keyPressed(self, key):
        ''' Respond to a key press event '''
        if key==pygame.K_RETURN:
            if self.state == "instructions":
                self.state = "level"
                self.t = 0
                playSound("Enter.wav")
            elif self.state == "splash":
                self.state = "instructions"
                self.t = 0
                playSound("Enter.wav")
            elif self.state == "goal":
                self.t = 0
                self.total += self.time - (self.levelTimes[self.level-1]*60 - self.levelDurations[self.level-1])
                if int(self.time) > self.levelTimes[self.level-1]*60 or self.level == len(self.levels):
                    self.level += 1
                self.state = "level"
                if self.level > len(self.levels):
                    self.state = "win"
                    self.t = 0
                else:
                    self.reset()
                playSound("Enter.wav")
            elif self.state == "level":
                setVolume(V_HIGH)
                self.state = "play"
                playSound("Enter.wav")
            elif self.state == "win":
                self.t = 0
                self.state = "shutdown"
                playSound("Shutdown.wav")
        elif self.state == "play":
            if key==pygame.K_RIGHT or key==pygame.K_d:
                self.setInstruction(Pose(1,0))
                playSound("Beep.wav")
            elif key==pygame.K_LEFT or key==pygame.K_a:
                self.setInstruction(Pose(-1,0))
                playSound("Beep.wav")
            elif key==pygame.K_UP or key==pygame.K_w:
                self.setInstruction(Pose(0,-1))
                playSound("Beep.wav")
            elif key==pygame.K_DOWN or key==pygame.K_s:
                self.setInstruction(Pose(0,1))
                playSound("Beep.wav")
            elif key==pygame.K_SPACE:
                self.setInstruction(None)
                playSound("Beep.wav")

    def setCaption1(self, text):
        self.captionText1 = text
        self.captionTime1 = CAPTION_TIME1

    def setCaption2(self, text):
        self.captionText2 = text
        self.captionTime2 = CAPTION_TIME2

    def setInstruction(self, pose):
        self.driver.instruction = pose

    def displayInstruction(self):
        if not self.driver.instruction:
            self.setCaption1("RECALCULATING...")
            return
        i1 = self.grid.neighbors.index(self.driver.edge)
        i2 = self.grid.neighbors.index(self.driver.instruction)
        if (i2 - i1)%4 == 2:
            self.setCaption1("MAKE A U-TURN IF POSSIBLE")
        elif (i2-i1)%4 == 1:
            self.setCaption1("TURN LEFT")
        elif (i2-i1)%4 == 3:
            self.setCaption1("TURN RIGHT")
        else:
            self.setCaption1("CONTINUE STRAIGHT")

################################################################################
    
    def __init__(self, name):
        ''' Initialize the game '''
        pygame.init()
        os.environ['SDL_VIDEO_WINDOW_POS'] = '0, 30'
        pygame.display.set_caption(name)
        self.screen = pygame.display.set_mode([WIDTH, HEIGHT])
        self.overlay = loadImage("Overlay.png")
        self.instructions = loadImage("Instructions.png")
        self.off = loadImage("Off.png")
        self.blank = loadImage("Blank.png")
        self.win = loadImage("Win.png")
        self.shutdown = loadImage("Shutdown.png")
        self.splash = loadImage("Splash.png")
        self.indicator = loadImage("Indicator.png")
        self.level = 1
        self.total = 0
        icon = loadImage("Icon.png", scale=1)[0]
        icon.set_colorkey((255,0,0))
        pygame.display.set_icon(icon)
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        playMusic("Taking_the_Scenic_Route.wav")
        setVolume(V_LOW)
        playSound("Beep.wav", False, 0.05)
        playSound("Enter.wav", False, 0.2)
        playSound("Shutdown.wav", False, 0.2)

        self.font1 = pygame.font.SysFont("Arial", 60)
        self.font2 = pygame.font.Font("font/ComicSansMS3.ttf", 40)
        self.font3 = pygame.font.SysFont("Arial", 70)
        self.font4 = pygame.font.Font("font/LCD_Solid.ttf", 60)
        self.font5 = pygame.font.SysFont("Arial", 80)
        self.font6 = pygame.font.SysFont("Arial", 140)

        self.state = "off"
        self.reset()
        self.run()

    def run(self):
        ''' Iteratively call update '''
        clock = pygame.time.Clock()
        self.pause = False
        while not self.pause:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    self.keyPressed(event.key)
                if event.type == pygame.QUIT:
                    pygame.display.quit()
                    sys.exit()
            dt = clock.tick(TIME_STEP)
            self.update(dt, pygame.key.get_pressed())
            pygame.display.update()


if __name__ == '__main__':
    game = Game("Wayfinder")
