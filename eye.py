#!/usr/bin/python
# coding: utf8
# Eyes Module
# P20 Camila.Arias

#--import Adafruit_ADS1x15  =========================
import argparse
import math
import pi3d
import random
#--import thread=======================
import time
#--import RPi.GPIO as GPIO ==================
from svg.path import Path, parse_path
from xml.dom.minidom import parse
from gfxutil import *

#---------- : controller OLED
import controller


# Set up display and initialize pi3d ---------------------------------------
# Here ! dimensions change [Dimensions 128x4,128x2]
DISPLAY = pi3d.Display.create(w=512,h=256,samples=4) 
DISPLAY.set_background(0, 0, 0, 1) # r,g,b,alpha

# eyeRadius is the size, in pixels, at which the whole eye will be rendered
# onscreen.  eyePosition, also pixels, is the offset (left or right) from
# the center point of the screen to the center of each eye.  This geometry
# is explained more in-depth in fbx2.c.
eyePosition = DISPLAY.width / 4
eyeRadius   = 96  

# A 2D camera is used, mostly to allow for pixel-accurate eye placement,
# but also because perspective isn't really helpful or needed here, and
# also this allows eyelids to be handled somewhat easily as 2D planes.
# Line of sight is down Z axis, allowing conventional X/Y cartesion
# coords for 2D positions.
cam    = pi3d.Camera(is_3d=False, at=(0,0,0), eye=(0,0,-1000))
shader = pi3d.Shader("uv_light")
light  = pi3d.Light(lightpos=(0, -500, -500), lightamb=(0.2, 0.2, 0.2))

# Layers configuration to obtain the 2D point list. Name of each layer is
# the same as SVG image. "id": [numPoints,closedSurface ?,reverse ?]
layers = [("pupilMin"      ,32, True , True),
         ("pupilMax"       ,32, True , True),
         ("iris"           ,32, True , True),
         ("scleraFront"    , 0, False, False),
         ("scleraBack"     , 0, False, False),
         ("upperLidClosed" ,33, False, True),
         ("upperLidOpen"   ,33, False, True) ,
         ("upperLidEdge"   ,33, False, False),
         ("lowerLidClosed" ,33, False, False),
         ("lowerLidOpen"   ,33, False, False),
         ("lowerLidEdge"   ,33, False, False)]

dom               = parse("graphics/cyclops-eye.svg")
vb                = getViewBox(dom)
points = []
for l in layers:
   #convert to point lists --------------------
   points.append(getPoints(dom,l[0],l[1],l[2],l[3]))
   # Transform point lists to eye dimensio
   scalePoints(points[-1],vb,eyeRadius)


#Dictionary to obtain the number of layer
to = {  "pupilMinPts": 0,
         "pupilMaxPts": 1,
         "irisPts":2,
         "scleraFrontPts":3,
         "scleraBackPts":4,
         "upperLidClosedPts":5,
         "upperLidOpenPts" :6,
         "upperLidEdgePts":7,
         "lowerLidClosedPts":8,
         "lowerLidOpenPts":9,
         "lowerLidEdgePts":10 }

class Eye:  

   def generate_sclera(self, eyeRadius):
      global points,to
      # Generate scleras for each eye...start with a 2D shape for lathing...
      angle1 = zangle(points[to["scleraFrontPts"]], eyeRadius)[1] # Sclera front angle
      angle2 = zangle(points[to["scleraBackPts"]], eyeRadius)[1] # " back angle
      aRange = 180 - angle1 - angle2
      pts    = []
      for i in range(24):
         ca, sa = pi3d.Utility.from_polar((90 - angle1) - aRange * i / 23)
         pts.append((ca * eyeRadius, sa * eyeRadius))
      return pts


   def __init__(self,eyePosition,eyeRadius,id):
      global points,to
      self.eyePosition = eyePosition
      self.eyeRadius = eyeRadius
      #Load texture maps --------------------------------------------------------
      irisMap   = pi3d.Texture("./graphics/iris_blue.jpg"  , mipmap=False,
                  filter=pi3d.GL_LINEAR)
      scleraMap = pi3d.Texture("./graphics/sclera.png", mipmap=False,
                  filter=pi3d.GL_LINEAR, blend=True)
      lidMap    = pi3d.Texture("./graphics/lid.png"   , mipmap=False,
                  filter=pi3d.GL_LINEAR, blend=True)
      #init iris
      self.iris = meshInit(32, 4, True, 0, 0.5/irisMap.iy, False)
      self.iris.set_textures([irisMap])
      self.iris.set_shader(shader)      
      #init sclera
      self.eye = pi3d.Lathe(path=self.generate_sclera(eyeRadius), sides=64)
      self.eye.set_textures([scleraMap])
      self.eye.set_shader(shader)
     
      self.irisZ = zangle(points[to["irisPts"]], eyeRadius)[0] * 0.99 # Get iris Z depth, for later
      #init upperlid
      self.upperEyelid = meshInit(33, 5, False, 0, 0.5/lidMap.iy, True)
      self.upperEyelid.set_textures([lidMap])
      self.upperEyelid.set_shader(shader)
      #init lowerlid
      self.lowerEyelid = meshInit(33, 5, False, 0, 0.5/lidMap.iy, True)
      self.lowerEyelid.set_textures([lidMap])
      self.lowerEyelid.set_shader(shader)
       #LEFT 0
      if id == 0:
          self.eye.positionX(eyePosition)
          self.iris.positionX(eyePosition)
          self.upperEyelid.positionX(eyePosition)
          self.lowerEyelid.positionX(eyePosition)
          reAxis(self.eye, 0)
      else:
         self.eye.positionX(-eyePosition)
         self.iris.positionX(-eyePosition)
         self.upperEyelid.positionX(-eyePosition)
         self.lowerEyelid.positionX(-eyePosition)
         reAxis(self.eye, 0.5)

      #initial position
      self.upperEyelid.positionZ(-eyeRadius - 42)      
      self.lowerEyelid.positionZ(-eyeRadius - 42)

      self.irisRegenThreshold = self.get_iris_change()
      self.prevPupilScale = 0.5
      
      ##blinking
      self.luRegen = True
      self.prevLid = 0.5
      self.prevPts = pointsInterp(points[to["upperLidOpenPts"]], points[to["upperLidClosedPts"]],0.5)
      self.timeOfLastBlink = 0.0
      self.timeToNextBlink = 1.0
      self.trackingPos = 0.3
      self.blinkState = 0
      self.blinkDuration   = 0.1
      self.blinkStartTime  = 0
      self.limit  = 0
      self.get_upper_limit()
      self.regenerate_iris(0.5)
      self.regenerate_upper_lid(0.4,True)
      self.regenerate_lower_lid(0.2)
      self.n            = math.sqrt(900.0 - 15 * 15)
     
   
   def draw(self):
      self.eye.draw()
      self.iris.draw()
      self.upperEyelid.draw()
      self.lowerEyelid.draw()

   def get_iris_change(self):
      irisRegenThreshold = 0.0
      a = pointsBounds(points[to["pupilMinPts"]]) # Bounds of pupil at min size (in pixels)
      b = pointsBounds(points[to["pupilMaxPts"]]) # " at max size
      maxDist = max(abs(a[0] - b[0]), abs(a[1] - b[1]), # Determine distance of max
                  abs(a[2] - b[2]), abs(a[3] - b[3])) # variance around each edge
      # maxDist is motion range in pixels as pupil scales between 0.0 and 1.0.
      # 1.0 / maxDist is one pixel's worth of scale range.  Need 1/4 that...
      if maxDist > 0: irisRegenThreshold = 0.25 / maxDist
      return irisRegenThreshold
   
   def get_upper_limit(self):
      p1 = points[to["upperLidOpenPts"]][len(points[to["upperLidOpenPts"]]) // 2]
      p2 = points[to["upperLidClosedPts"]][len(points[to["upperLidClosedPts"]]) // 2]
      dx = p2[0] - p1[0]
      dy = p2[1] - p1[1]
      d  = dx * dx + dy * dy
      if d > 0: self.limit = 0.25 / math.sqrt(d)

   def regenerate_iris(self,p):
      global points,to
      # Interpolate points between min and max pupil sizes
      interPupil = pointsInterp(points[to["pupilMinPts"]], points[to["pupilMaxPts"]], p)
      # Generate mesh between interpolated pupil and iris bounds
      mesh = pointsMesh(None, interPupil, points[to["irisPts"]], 4, -self.irisZ, True)
      # Assign to both eyes
      self.iris.re_init(pts=mesh)
      #return previous
      return p
   
   def regenerate_upper_lid(self,p,case):
      global points,to
      # Interpolate points between min and max pupil sizes
      interUpperNew = pointsInterp(points[to["upperLidOpenPts"]], points[to["upperLidClosedPts"]], p)
      # Generate mesh between interpolated pupil and iris bounds
      if case:
         mesh = pointsMesh(points[to["upperLidEdgePts"]], self.prevPts,interUpperNew, 5, 0, False,True)
      else:
         mesh = pointsMesh(points[to["upperLidEdgePts"]],interUpperNew,self.prevPts, 5, 0, False,True)

      #return previous
      self.upperEyelid.re_init(pts=mesh)
      self.prevPts    = interUpperNew
      return p

   def regenerate_lower_lid(self,p):
      global points,to
      # Interpolate points between min and max pupil sizes
      interUpper = pointsInterp(points[to["lowerLidOpenPts"]], points[to["lowerLidClosedPts"]],0.5)
      interUpperNew = pointsInterp(points[to["lowerLidOpenPts"]], points[to["lowerLidClosedPts"]], p)
      # Generate mesh between interpolated pupil and iris bounds
      mesh = pointsMesh(points[to["lowerLidEdgePts"]], interUpper,interUpperNew, 5, 0, False,True)
      #return previous
      self.lowerEyelid.re_init(pts=mesh)
      return p
   
   def regenerate_map(self,color,p):     
      self.iris.set_material(color)
      self.regenerate_iris(p)
   
   def animation(self,duration):
      startTime = time.time()
      isMoving = True
      while True:
         dt = time.time() - startTime
         if dt >= duration: break 
         self.frame(isMoving,startTime)

   def frame(self,now):  
      self.blink(now)
      
   
   def blink(self,now):
      #check final
      if (now - self.timeOfLastBlink) >= self.timeToNextBlink:
         self.timeOfLastBlink = now
         duration        = 0.7
         if self.blinkState != 1:
            self.blinkState = 1
            self.blinkStartTime = now
            self.blinkDuration = duration
         self.timeToNextBlink = duration * 5 
      
      if self.blinkState:
         if (now - self.blinkStartTime) >= self.blinkDuration:
            self.blinkState += 1           
            if self.blinkState > 2:
               self.blinkState = 0 # NOBLINK               
            else:
               self.blinkDuration *= 2.5
               self.blinkStartTime = now
         else:
            self.n = (now - self.blinkStartTime) / self.blinkDuration
            if self.n > 1.0: self.n = 1.0
            if self.blinkState == 2: self.n = 1.0 - self.n
      else:
         self.n = 0.0
     
      newLid =  self.trackingPos + (self.n * (1.0 - self.trackingPos))     
      if (self.luRegen or (abs(newLid - self.prevLid) >= self.limit)):
         if newLid > self.prevLid:
            #change prevpts
            self.regenerate_upper_lid(newLid,True)
         else:
            #change prevpts
            self.regenerate_upper_lid(newLid,False)
         self.prevLid = newLid
         self.luRegen = True
      else:
         self.luRegen = False
   
   
      
   def rotate(self,curX,curY):
      self.iris.rotateToX(curY)
      self.iris.rotateToY(curX + 2)
      self.eye.rotateToX(curY) 
      self.eye.rotateToY(curX + 2)
      


      
class eyes:


   def __init__(self):
      
      self.right = Eye(eyePosition,eyeRadius,0.5)
      self.left = Eye(eyePosition,eyeRadius,0)

       #Variables to describe movement
      self.startTime = 0.0
      self. startX       = random.uniform(-20.0, 20.0)      
      self.startY       = random.uniform(-20, 10)
      self.destX        = self.startX
      self.destY        = self.startY
      self.curX         = self.startX
      self.curY         = self.startY
      self.moveDuration = random.uniform(0.09, 0.2)
      self.holdDuration = random.uniform(0.5, 1.5)
      self.isMoving     = False
      
   def draw(self):
      self.right.draw()
      self.left.draw()
   
   def color(self,color,p):
      self.right.regenerate_map(color,p)
      self.left.regenerate_map(color,p)
   
   def blink(self):         
      now = time.time()
      self.left.frame(now)
      self.right.frame(now)
      self.move(now)
      self.left.rotate(self.curX,self.curY)
      self.right.rotate(self.curX,self.curY)

   def move(self,now):
      dt  = now - self.startTime
      # Autonomous eye position
      if self.isMoving == True:
         if dt <= self.moveDuration:
            scale        = (now - self.startTime) / self.moveDuration
            scale = scale * scale
            self.curX         = self.startX + (self.destX - self.startX) * scale
            self.curY         = self.startY + (self.destY - self.startY) * scale
         else:
            self.startX       = self.destX
            self.startY       = self.destY
            self.curX         = self.destX
            self.curY         = self.destY
            self.holdDuration = random.uniform(0.5, 1.5)
            self.startTime    = now
            self.isMoving     = False
      else:
         if dt >= self.holdDuration:
            self.destX        = random.uniform(-20.0, 20.0)
            self.n            = math.sqrt(900.0 - self.destX * self.destX)
            self.destY        = random.uniform(-20,10)
            self.moveDuration = random.uniform(0.09, 0.2)
            self.startTime    = now
            self.isMoving     = True

mykeys = pi3d.Keyboard() # For capturing key presse 
x = eyes()
while DISPLAY.loop_running():
   x.draw()
   k = mykeys.read()
   if k==27:
      mykeys.close()
      DISPLAY.stop()
      #---------------------close process to OLED
      #controller.close_OLED()
      #-----------------------------------------
      exit(0)
   elif k == 97:
        x.color((1,0,0),1)
   elif k == 98:
        x.color((0,1,0),0.3)
   elif k == 99:
        x.color((0.5,0.5,0.5),0.5)
   x.blink()
   






