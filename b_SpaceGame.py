#Isaiah smith
#cs140a
#6/6/2016
#SpaceGame.py

import os;
import sys;
import pygame;
import time;
import random;
import math;
#a little library that I created to help out with common video game math
from ezmath import *;

#used for compiling with pyinstaller
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS);

#display
size = (600,600);
screen = None;
#the titlescreen image, is only loaded when in use due to it's relatively large memory consumption
titlesprite = None;

#delay between frames in seconds
framerate = 0.01666667;
#catches the time lost in lag and later uses it to catch up if it accumulates too much
lagcatch = 0;

#fonts
font = None;
tinyfont = None;

#menu mode and selection, defines GUI
mode = 0;       #0 = main, 1 = in game, 2 = name entry, 3 = scoreboard
selection = 0;

#the main camera object - used to transform the world view
maincam = None;
p1 = None;
enemyspawndelay = 0;
cowspawndelay = 0;
score = 0;
scoredrop = 500;
scoredropper = None;
hi = 0;
iteration = 0;

#collision groups for optomization
colcheck0 = list();
colcheck1 = list();
colcheck2 = list();
#entity lists
enemies = list();
projectiles = list();
items = list();
particles = list();
stars = list();
#data lists
powersprites = list();
sounds = list();

#used for handling input
lastkeyspr = None;          #used when for name entry, shows which keys were pressed last frame, so not to repeat keystrokes
activecontr = [False, False, False, False, False, False];   #controls being actively held down
lastactivec = [False, False, False, False, False, False];   #controls that were held down last frame, used for menu navigation

#default controls:
controls = [      \
  pygame.K_UP,    \
  pygame.K_DOWN,  \
  pygame.K_RIGHT, \
  pygame.K_LEFT,  \
  pygame.K_c,     \
  pygame.K_SPACE  \
  ];

class particle:
  def __init__(this, pos, vel, color = (255,255,0), thickness = 2):
    '''initializes a particle instance'''
    this.pos = pos;
    this.vel = vel;
    this.radius = 0;
    this.color = color;
    this.life = 10;
    this.thickness = thickness;
    this.damping = 1;

  def update(this):
    '''handles logic for a particle instance'''
    if(this.life <= 0 or distance(p1.pos, this.pos) > 500):
      particles.remove(this);
      return;
      
    this.vel = multPoint(this.vel, this.damping);
    this.pos = addPoints(this.pos, this.vel);
    this.life -= 1;

  def draw(this):
    '''handles rendering for a particle instance'''
    #particles are rendered as a line whose length is dependent upon their speed
    length = (distance(this.vel));
    #kills the particle if it is less than a pixel long
    if(length < 1):
      life = 0;
    #tform is the temporary form the particle takes during renduring to give the camera an object to render
    tform = poly((0,0),(length,0));
    tform.pos = this.pos;
    tform.angle = direction(this.vel);
    tform.color = this.color;
    tform.thickness = this.thickness;
    maincam.toDraw(tform);

class motherCowDeath(particle):
  def __init__(this, pos, vel):
    particle.__init__(this, pos, vel, (255, 255, 0), 2);
    this.life = 25;

  def update(this):
    if(this.life <= 0 or distance(p1.pos, this.pos) > 500):
      particles.remove(this);
      return;
    if(this.life % 3 == 0):
      this.burst();
    this.life -= 1;
      
  def burst(this):
    blast = circ(random.randrange(20, 35));
    if(randChance(50)):
      blast.color = (255, 150, 0);
    else:
      blast.color = (255, 255, 0);      
    tpos = addPoints(this.pos, randPoint(20));
    blast.pos = tpos;
    maincam.toDraw(blast);
    for p in range(6):
      part = particle(addPoints(tpos, randCirc(blast.scale / 2)), randCirc(5), blast.color, 3);
      part.life = randRange(30, 10);
      particles.append(part);
    
  def draw(this):
    0;
class shape:
  def __init__(this):
    '''initializes a shape object, used by the camera to render to the screen'''
    this.color = (255,255,255);
    this.pos = (0,0);
    this.angle = 0;
    this.thickness = 0;
    this.scale = 1;
    this.fill = None;

class img(shape):
  def __init__(this, surface):
    '''initializes an img instance, an image type shape that can be rendered in the world'''
    shape.__init__(this);
    this.surface = surface;

class poly(shape):
  def __init__(this, *verts):
    '''initializes a poly object, basically polygon data that is given to the camera'''
    shape.__init__(this);
    this.verts = list();
    for v in verts:
      this.verts.append(v);
    
  def getAbsVerts(this):
    '''gets the world position of the poly's vertices'''
    result = list();
    for vert in this.verts:
      av = multPoint(vert, this.scale);
      result.append(transform(av, this.pos, this.angle));
    return result;
      
  def draw(this, cam):
    '''adds the poly to the camera's draw query'''
    cam.toDraw(this);
  def circleGon(points, radius):
    '''returns a circular polygon with specified amount of points'''
    form = poly();
    form.scale = radius;
    for i in range(points):
      form.verts.append(xyComponent((math.pi * 2) * (i / points)));
    return form;
  
class circ(shape):
  def __init__(this, size = 10):
    '''initializes a circ object, not used very often because pygame handles rendering circle outlines very poorly'''
    shape.__init__(this);
    this.scale = size;
    
  def draw(this, cam):
    '''adds the circ object to the camera's draw query'''
    maincam.toDraw(this);

#cameras are used to render world objects from a dynamic point of view
class camera:
  def __init__(this):
    '''initiales a camera object'''
    this.drawQuery = list();
    this.pos = (0,0);
    this.angle = 0;
  
  def orient(this, pos, angle):
    '''orients the camera to the specified settings'''
    this.pos = addPoints(pos, (size[0] / -2, size[1] / -2));
    this.pos = pos;
    this.angle = angle;

  def center(this):
    '''returns the coordinates of the center of the camera'''
    return addPoints(this.pos, (size[0] / -2, size[1] / -2));

  def getViewPoint(this, worldpoint):
    '''takes a point in the world and returns the position it will show up on screen'''
    av = worldpoint;
    av = transform(av, multPoint(this.pos, -1), 0);
    av = transform(av, (0,0), -this.angle);
    av = addPoints(av, multPoint(size, .5));
    return av;
    
  def render(this, screen):
    '''transforms the shapes in it's drawQuery to it's orientation and then renders them to the screen'''
    for dshape in this.drawQuery:
      if(type(dshape) is poly):
        this.renderPoly(dshape);
      if(type(dshape) is circ):
        this.renderCirc(dshape);
      if(type(dshape) is img):
        this.renderImg(dshape);
    #renews the draw query so it does not redraw the items from the previous frame
    this.drawQuery = list();

  def renderImg(this, dimg):
    '''renders an img object'''
    rect = dimg.surface.get_rect();
    rect.center = this.getViewPoint(dimg.pos);
    screen.blit(dimg.surface, rect);
  
  def renderPoly(this, dpoly):
    '''renders a poly object'''
    absverts = list();
    for vert in dpoly.getAbsVerts():
      #transforms the poly's vertices to the correct screen coordinates
      #for rendering purposes, we must first translate the vertex and then rotate it
      av = vert;
      av = transform(av, multPoint(this.pos, -1), 0);
      av = transform(av, (0,0), -this.angle);
      av = addPoints(av, multPoint(size, .5));
      absverts.append(av);
    if(dpoly.fill != None):
      #fills a polygon if it has a specified fill color
      pygame.draw.polygon(screen, dpoly.fill, absverts, 0);
    pygame.draw.polygon(screen, dpoly.color, absverts, dpoly.thickness);

  def renderCirc(this, dcirc):
    '''renders a circ object'''
    pygame.draw.circle(screen, dcirc.color, roundPoint(this.getViewPoint(dcirc.pos)), round(dcirc.scale), dcirc.thickness);
    
  def toDraw(this, dshape):
    '''adds a shape to the draw query if it is a shape object'''
    if(not baseIs(dshape, shape)):
      return; #returns if it is not a shape type
    this.drawQuery.append(dshape);

#weapons store data relevant to what the player's fire control will do
class weapon:
  def __init__(this):
    '''initializes a weapon object'''
    this.fireDelay = 10;
    this.firewait = 0;
    this.ammo = 10;

  def update(this):
    if(this.firewait > 0):
      this.firewait -= 1;

  def draw(this):
    0;

  def trigger(this, pos, aim, vel):
    if(this.ammo <= 0):
      return False;
    if(this.firewait <= 0):
      sounds[2].play();
      this.fire(pos, aim, vel);
      this.firewait = this.fireDelay;
      return True;
    return False;
  
  def fire(this, pos, aim, vel):
    proj = projectile(True, pos, aim);
    proj.vel = addPoints(proj.vel, vel);
    projectiles.append(proj);

#a high-damage power weapon that locks onto nearby enemies
class missileLauncher(weapon):
  def __init__(this):
    '''initializes the missileLauncher'''
    weapon.__init__(this);
    this.fireDelay = 15;
    this.ammo = 45;

  def draw(this):
    #draws the reticle of the missileLauncher
    col = (255, 100, 0);
    verts1 = [(0,0),(0,1),(2,0)];
    verts2 = [(0,0),(0,-1),(2,0)];
    ret1 = poly();
    tpos = transform((20, 10), (0,0), p1.angle);
    ret1.pos = addPoints(tpos, p1.pos);
    ret1.angle = p1.angle;
    ret1.verts = verts1;
    ret1.scale = 7 * (this.ammo / 45);
    ret1.thickness = 3;
    ret1.color = col;
    ret2 = poly();
    tpos = transform((20, -10), (0,0), p1.angle);
    ret2.pos = addPoints(tpos, p1.pos);
    ret2.angle = p1.angle;
    ret2.verts = verts2;
    ret2.scale = 7 * (this.ammo / 45);
    ret2.thickness = 3;
    ret2.color = col;
    maincam.toDraw(ret2);
    maincam.toDraw(ret1);
  
  def fire(this, pos, aim, vel):
    '''releases a missile projectile'''
    this.ammo -= 1;
    proj = missile(pos, aim, 10);
    proj.vel = addPoints(proj.vel, vel);
    proj.damage = 3;
    projectiles.append(proj);
  def trigger(this, pos, aim, vel):
    if(this.ammo <= 0):
      return False;
    if(this.firewait <= 0):
      sounds[6].play();
      this.fire(pos, aim, vel);
      this.firewait = this.fireDelay;
      return True;
    return False;
#a rapid-fire gatling gun
class rapidGun(weapon):
  def __init__(this):
    '''initializes the rapid gun'''
    weapon.__init__(this);
    this.fireDelay = 3;
    this.ammo = 140;
    
  def draw(this):
    '''draws the reticle for the rapid gun'''
    thick = 2;
    col = (255, 230, 20);
    ret1 = poly((0,0), (1,0));
    tpos = transform((20,10), (0,0), p1.angle);
    ret1.pos = addPoints(tpos, p1.pos);
    ret1.thickness = thick;
    ret1.color = col;
    ret1.scale = this.ammo / 7;
    ret1.angle = p1.angle;
    ret2 = poly((0,0), (1,0));
    tpos = transform((20,-10), (0,0), p1.angle);
    ret2.pos = addPoints(tpos, p1.pos);
    ret2.thickness = thick;
    ret2.color = col;
    ret2.scale = this.ammo / 7;
    ret2.angle = p1.angle;
    maincam.toDraw(ret1);
    maincam.toDraw(ret2);

  def trigger(this, pos, aim, vel):
    if(this.ammo <= 0):
      return False;
    if(this.firewait <= 0):
      sounds[3].play();
      this.fire(pos, aim, vel);
      this.firewait = this.fireDelay;
      return True;
    return False;

  def fire(this, pos, aim, vel):
    '''releases a projectile within a small radius'''
    this.ammo -= 1;
    proj = projectile(True, pos, aim, 15);
    proj.vel = addPoints(proj.vel, vel);
    proj.pos = addPoints(proj.pos, randCirc(5));
    proj.damage = 0.7;
    projectiles.append(proj);

#a gun that shoots 5 fast moving projectiles that spread out and hit multiple targets
class spreadGun(weapon):
  def __init__(this):
    '''initializes the spreadgun'''
    weapon.__init__(this);
    this.fireDelay = 15;
    this.ammo = 50;

  def draw(this):
    '''draws the spreadgun reticle'''
    thick = 4;
    col = (0, 100, 255);
    
    ret1 = poly((0,0), (1,.6));
    tpos = transform((20,10), (0,0), p1.angle);
    ret1.pos = addPoints(tpos, p1.pos);
    ret1.thickness = thick;
    ret1.color = col;
    ret1.scale = this.ammo / 3;
    ret1.angle = p1.angle;
    ret2 = poly((0,0), (1,-.6));
    tpos = transform((20,-10), (0,0), p1.angle);
    ret2.pos = addPoints(tpos, p1.pos);
    ret2.thickness = thick;
    ret2.color = col;
    ret2.scale = this.ammo / 3;
    ret2.angle = p1.angle;
    
    maincam.toDraw(ret1);
    maincam.toDraw(ret2);
  
  def fire(this, pos, aim, vel):
    '''releases 5 evenly spread projectiles'''
    this.ammo -= 1;
    for i in range(5):
      spr = (i - 2) * 0.2;
      proj = projectile(True, pos, aim + spr, 15);
      proj.life = 20;
      proj.damage = 0.5;
      proj.vel = addPoints(proj.vel, vel);
      proj.form = poly((0,-3), (0,3));
      proj.form.color = (0, 200, 255);
      proj.form.thickness = 4;
      projectiles.append(proj);
  def trigger(this, pos, aim, vel):
    if(this.ammo <= 0):
      return False;
    if(this.firewait <= 0):
      sounds[5].play();
      this.fire(pos, aim, vel);
      this.firewait = this.fireDelay;
      return True;
    return False;
#the ion cannon fires a fast traveling steady beam of projectiles
class ionCannon(weapon):
  def __init__(this):
    '''initializes the ion cannon'''
    weapon.__init__(this);
    this.fireDelay = 1;
    this.ammo = 300;

  def draw(this):
    '''draws the ion cannon's reticle'''
    thick = 3;
    col = (0, 255, 255);
    
    ret1 = poly((0,0), (1,0));
    tpos = transform((20,5), (0,0), p1.angle);
    ret1.pos = addPoints(tpos, p1.pos);
    ret1.thickness = thick;
    ret1.color = col;
    ret1.scale = this.ammo / 10;
    ret1.angle = p1.angle;
    ret2 = poly((0,0), (1,0));
    tpos = transform((20,-5), (0,0), p1.angle);
    ret2.pos = addPoints(tpos, p1.pos);
    ret2.thickness = thick;
    ret2.color = col;
    ret2.scale = this.ammo / 10;
    ret2.angle = p1.angle;
    
    maincam.toDraw(ret1);
    maincam.toDraw(ret2);
  
  def fire(this, pos, aim, vel):
    '''fires a part of the beam'''
    this.ammo -= 1;
    proj = ionBullet(pos, aim, 25);
    proj.vel = addPoints(proj.vel, vel);
    proj.life = 20;
    proj.damage = .4;
    proj.radius = 20;
    proj.color = (0,255,155);
    proj.thickness = 4;
    projectiles.append(proj);
  def trigger(this, pos, aim, vel):
    if(this.ammo <= 0):
      return False;
    if(this.firewait <= 0):
      sounds[4].play();
      this.fire(pos, aim, vel);
      this.firewait = this.fireDelay;
      return True;
    return False;
  
class projectile:
  def __init__(this, friendly, pos = (0,0), aim = 0, spd = 10):
    '''initializes a projectile instance'''
    this.cck = False;
    this.pos = pos;
    this.vel = multPoint(xyComponent(aim), spd);
    this.radius = 10;
    this.life = 100;
    this.friendly = friendly;
    this.damage = 1;
    this.color = (255,255,0);
    this.thickness = 2;
    this.form = None;

  def update(this):
    '''handles the projectile update logic of the current instance'''
    this.cck = False;
    this.pos = addPoints(this.pos, this.vel);
    this.life -= 1;
    if(this.friendly):
      0;
      #this.checkEnemyCollisions();
      #this.checkBogeyBulletCollisions();

  def removeCheck(this):
    '''removes the projectile if it's time is up'''
    if(this.life <= 0):
      if(this in projectiles):
        projectiles.remove(this);

  def checkBogeyBulletCollisions(this):
    '''handles collisions with enemy projectiles'''
    for bul in projectiles:
      if(bul.friendly):
        continue; #skips this instance if does not need to check collision
      if(collision(this, bul)):
        this.burst();
        projectiles.remove(bul);
        if(this in projectiles):
          this.life = 0;
    
  def checkEnemyCollisions(this):
    '''checks for collisions with enemies'''
    for en in enemies:
      if(collision(this, en)):
        this.hit(en);

  def checkAsteroidCollisions(this):
    '''checks for collisions only with asteriod objects, used for enemy bullets colliding with asteroids'''
    for ast in enemies:
      if(not type(ast) is asteroid):
        continue; #skips the instance if it is not an asteroid
      if(collision(ast, this)):
        this.hit(ast);
  
  def hit(this, en):
    if(not this.friendly):
      if(baseIs(en, projectile)):
        if(this.friendly == en.friendly):
          return;
        en.hit(this);
      else:
        return;
    this.life = 0;
    this.burst();
    if(baseIs(en, enemy)):
      this.enHit(en);
      
  def enHit(this, en):
    '''hits a specified enemy'''
    #damages the enemy instance it collides with
    if(en.dead()):
      return;
    en.health -= this.damage;
    if(en.health <= 0):
      en.kill();
    
  def burst(this):
    '''the visual effect of the projectile's collision'''
    if(this.damage >= 1):
      sounds[12].play();
    else:
      sounds[14].play();
    for i in range(random.randrange(4,8)):
      #add some pretty particles
      part = particle(this.pos, randPoint(5), (255,255,0));
      part.damping = 0.9;
      particles.append(part);
  
  def draw(this):
    '''adds the projectile to the main drawQuery'''
    if(this.form == None):
      #creates a temporary form to render if it has no previously defined form
      tform = poly();
      tform.color = this.color;
      tform.thickness = this.thickness;
      tform.verts = [(0,0),(distance(subtractPoints(this.vel, p1.vel)),0)];
      tform.pos = this.pos;
      tform.angle = direction(subtractPoints(this.vel, p1.vel));
      maincam.toDraw(tform);
      return;
    this.form.pos = this.pos;
    this.form.angle = direction(this.vel);
    maincam.toDraw(this.form);
  def dead(this):
    return this.life <= 0;
class ionBullet(projectile):
  def __init__(this, pos, aim, speed):
    '''initializes an ionBullet projectile, used for the ionCannon weapon'''
    projectile.__init__(this,True,pos,aim,speed);

  def burst(this):
    '''the bullet produces a small green flash when it collides'''
    for i in range(2):
      part = particle(this.pos, randPoint(30), (0, 255, 50));
      part.damping = 0.8;
      part.thickness = 4;
      particles.append(part);
    blast = circ();
    blast.pos = this.pos;
    blast.scale = 10;
    blast.color = (0, 255, 100);
    maincam.toDraw(blast);

class missile(projectile):
  def __init__(this, pos, aim, speed):
    '''initializes a missile projectile, used for the missileLauncher weapon'''
    projectile.__init__(this, True, pos, aim, speed);
    this.form = poly((10,0),(-5,5),(-5,-5));
    this.form.color = (255, 180, 0);
    this.form.thickness = 2;
    this.life = 110;
    this.lock = None;

  def update(this):
    '''handles the logic step for the current instance'''
    projectile.update(this);
    if(this.life <= 100):
      if(this.lock == None):
        this.search();
      else:
        this.seek(this.lock);
      if(not this.lock in enemies):
        this.lock = None;
  
  def search(this):
    '''seeks out an enemy to lock onto'''
    for en in enemies:
      if(distance(en.pos, this.pos) <= 150):
        this.lock = en;
    
  def seek(this, en):
    '''homes in to an enemy'''
    if(not en in enemies):
      return;
    #dampens the velocity to account for course readjustment
    this.vel = multPoint(this.vel, 0.92);
    #adds velocity toward the target
    this.vel = addPoints(this.vel, multPoint(normal(this.pos, en.pos), 1));
    this.thrustParticle();
    
  def thrustParticle(this):
    '''emits particles to show that it is seeking an enemy'''
    force = multPoint(xyComponent(this.form.angle - math.pi), 0.7);
    part = particle(addPoints(this.pos, randPoint(randRange(4,6))), multPoint(force, 5), (255, 255, 0));
    part.vel = addPoints(part.vel, this.vel);
    part.life = random.randrange(5, 10);
    part.damping = 0.8;
    if(randChance(50)):
      part.color = (200, 200, 0);
    part.thickness = 2
    particles.append(part);

  def hit(this, en):
    '''collides with the specified enemy'''
    projectile.hit(this, en);
    for cols in collidingColchecks(this.pos, 30):
      for en in cols:
        if(not baseIs(en, enemy) or en.dead()):
          continue;
      #damages other enemies in within a radius, acts as splash damage
        if(distance(this.pos, en.pos) < 30):
          en.health -= 2;
        if(en.health <= 0):
          en.kill();
    
  def burst(this):
    '''creates a small flash and emits some explosion particles'''
    sounds[13].play();
    for i in range(random.randrange(5,10)):
      part = particle(this.pos, randCirc(5), (255,255,0));
      particles.append(part);
    blast = circ();
    blast.pos = this.pos;
    blast.scale = 30;
    blast.color = (255, 255, 100);
    maincam.toDraw(blast);

class enemyBullet(projectile):
  def __init__(this, pos, aim, speed):
    '''initializes an enemy bullet instance, used by alien objects to fire at the player'''
    projectile.__init__(this, False, pos, aim, speed);
    this.form = poly((3,0), (0,3), (-5,0), (0,-3));

  def update(this):
    '''handles the logic step for the current instance'''
    projectile.update(this);
    #this.checkAsteroidCollisions(); #collides with asteroids, but not other enemies
    #if(collision(this, p1)):
      #checks for collision with the player
      #if(this in projectiles):
        #projectiles.remove(this);
        #p1.damage(1);
        #p1.powerEvent(0, this);

  def draw(this):
    '''handles the rendering logic for the current instance'''
    this.form.pos = this.pos;
    this.form.angle = direction(this.vel);
    if(this.life % 6 > 2): #flashes between yellow and red every 3 frames
      this.form.color = (255,255,0);
    else:
      this.form.color = (255, 0, 0);
    maincam.toDraw(this.form);
  def hit(this, en):
    if(type(en) is player):
      this.life = 0;
      this.burst;
      return;
    elif(type(en) is asteroid):
      this.life = 0;
      this.burst;
    projectile.hit(this, en);
#the enemy base class for all enemy type objects
class enemy:
  def __init__(this, pos):
    '''initializes an enemy object'''
    this.cck = False;
    this.pos = pos;
    this.vel = (0,0);
    this.health = 1;
    this.radius = 10;

  def kill(this):
    '''kills the enemy instance'''
    this.itemDrop(); #handles dropping powerups
    this.health = None; #removes the enemy from the world
    
  def itemDrop(this):
    '''has a chance to drop an item'''
    if(len(items) > 1):
      return;
    if(not randChance(5)):
      #95% of the time nothing is dropped
      return;
    #~1 in every 20 kills an item is dropped
    power = item.randItem(this.pos);
    items.append(power);
    
  def update(this):
    '''handles the logic step for the current enemy instance'''
    if(this.health == None):
      return;
    this.cck = False;
    this.pos = addPoints(this.pos, this.vel);

  def draw(this):
    '''default rendering for an enemy base type is to not render anything'''
    0;
  def hit(this, ob):
    if(baseIs(ob, projectile)):
      this.projHit(ob);
  def projHit(this, proj):
    proj.hit(this);
  def dead(this):
    return this.health == None;
#asteroid is an enemy type that is passive but kills the player on contact
#breaks into smaller peices on death unless it has a radius of 10 pixels or smaller
class asteroid(enemy):
  def __init__(this, pos, radius):
    '''initializes an asteroid object'''
    enemy.__init__(this, pos);
    this.radius = radius;
    this.health = this.radius / 10 + 1;
    this.form = poly.circleGon(7, radius);
  
  def kill(this):
    '''destroys the asteroid object'''
    enemy.kill(this);
    global score;
    if(this.radius > 10):
      sounds[8].play();
      #splits into 3 smaller pieces
      for i in range(3):
        p = randPoint(1);
        a1 = asteroid(addPoints(this.pos, multPoint(p, this.radius)), this.radius / 2);
        a1.vel = multPoint(p, 2);
        enemies.append(a1);
    else:
      sounds[9].play();
    for i in range(3 + int(this.radius / 5)):
      #emits particles of death
      part = particle(addPoints(this.pos, randPoint(this.radius)), 0, (200, 120, 90), 4);
      if(randChance(50)):
        part.color = (130, 100, 50);
      part.vel = multPoint(subtractPoints(part.pos, this.pos), 0.3);
      part.life = random.randrange(50, 75);
      particles.append(part);
    getPoints(math.ceil(this.radius / 20) * 10); #worth more points the bigger the asteroid
    
  def itemDrop(this):
    '''only has a chance to drop an item if is large enough'''
    if(this.radius > 10):
      enemy.itemDrop(this);
  
  def draw(this):
    '''renders the current asteroid instance'''
    this.form.pos = this.pos;
    this.form.fill = (75, 50, 25);
    this.form.thickness = 2;
    this.form.color = (150, 100, 50);
    maincam.toDraw(this.form);

#alien is an enemy type that flyies around and fires projectile at the player
class alien(enemy):
  def __init__(this, pos):
    '''initializes an alien enemy'''
    enemy.__init__(this, pos);
    this.form = poly((5,0),(3,3),(0,5),(-3,5),(-4,3),(-1,2),(-6,0),\
                         (-1,-2),(-4,-3),(-3,-5),(0,-5),(3,-3));
    this.form.scale = 2;
    this.health = 1;
    ang = direction(subtractPoints(p1.pos, this.pos)) + randRange(1, -1);
    this.vel = multPoint(xyComponent(ang), 2.5);
    this.firedelay = 60;
  
  def update(this):
    '''handles the logic step for the current alien instance'''
    enemy.update(this);
    this.firedelay -= 1;
    if(distance(subtractPoints(this.pos, p1.pos)) < 300):
      #only fires if it is within a certain distance of the player
      if(this.firedelay <= 0):
        this.fire();
        
  def kill(this):
    '''kills the alien instance'''
    enemy.kill(this);
    sounds[10].play();
    global score;
    getPoints(100); #adds points to the player's score
    for i in range(10):
      #releases some particles to make frags more satisfying
      off = randPoint(5);
      part = particle(addPoints(this.pos, off), addPoints(this.vel, off), (255,0,0), 3);
      part.life = randRange(10, 25);
      if(randChance(50)):
        part.color = (150, 0, 0);
      particles.append(part);
  
  def fire(this):
    '''fires a projectile at the player'''
    #resets the fire delay to a second so it doesn't fire a large amount of projectiles
    this.firedelay = 60;
    sounds[15].play();
    #initializes a projectile but makes it so the alien doesn't have perfect accuracy
    proj = enemyBullet(this.pos, direction(subtractPoints(p1.pos, this.pos)) + randRange(-.3, .3), 4);
    projectiles.append(proj);
    #the alien turns in a random direction when it fires
    ang = direction(this.vel);
    mag = distance(this.vel)
    ang += randRange(1, -1); 
    this.vel = multPoint(xyComponent(ang), mag);
  
  def draw(this):
    '''renders the alien'''
    this.form.pos = this.pos;
    this.form.angle = direction(this.vel);
    this.form.fill = (100, 0, 0);
    this.form.thickness = 2;
    this.form.color = (255,0,0);
    maincam.toDraw(this.form);

#the basher is a bogey that charges the player
class basher(enemy):
  def __init__(this, pos):
    enemy.__init__(this, pos);
    this.form = poly((5,0),(3,3),(0,5),(-5,4),(-2,0),(-5,-4),(0,-5),(3,-3));
    this.form.scale = 3;
    this.health = 6;

  def kill(this):
    enemy.kill(this);
    sounds[10].play();
    getPoints(200);
    this.burst();
    
  def burst(this):
    for i in range(20):
      if(randChance(50)):
        vel = multPoint(xyComponent(direction(this.vel) - (math.pi / 2) * randRange(1)), randRange(4, 1));
      else:
        vel = multPoint(xyComponent(direction(this.vel) + (math.pi / 2) * randRange(1)), randRange(4, 1));
      if(randChance(50)):
        col = (255, 150, 0);
      else:
        col = (255, 255, 0);
      part = particle(this.pos, vel, col, 4);
      part.life = randRange(30, 10);
      particles.append(part);

  def update(this):
    enemy.update(this);
    acc = 0.3;
    if(distance(this.pos, p1.pos) > 300):
      acc = 0.1;
    this.vel = multPoint(this.vel, 0.94);
    this.vel = addPoints(this.vel, multPoint(normal(this.pos, p1.pos), acc));

  def draw(this):
    '''renders the basher'''
    this.form.pos = this.pos;
    this.form.angle = direction(this.vel);
    this.form.fill = (100, 20, 0);
    this.form.color = (255, 50, 0);
    this.form.thickness = 2;
    maincam.toDraw(this.form);
  def hit(this, ob):
    enemy.hit(this, ob);
    if(not baseIs(ob, projectile)):
      this.kill();
#the motherCow is an enemy that fires in eight different directions and releases alien enemies
class motherCow(enemy):
  def __init__(this, pos):
    enemy.__init__(this, pos);
    this.buildForm();
    this.radius = 45;
    this.health = 25;
    this.angle = 0;
    this.spawnwait = 60;
    this.vel = randCirc(1);
    if(randChance(50)):
      this.rot = -.01;
    else:
      this.rot = .01;

  def buildForm(this):
    this.form = poly();
    verts = [ \
      (20,0),(19,1),(18,1),(16,3),(16,5),(17,6),(17,7),(16,7),(15,6),(13,6),(11,8),(11,9),(10,10),(9,9),(9,8),(7,6),(5,6),(4,7),(3,7),(3,6),(4,5),(4,3),(2,1),(1,1),(0,0), \
      (1,-1),(2,-1),(4,-3),(4,-5),(3,-6),(3,-7),(4,-7),(5,-6),(7,-6),(9,-8),(9,-9),(10,-10),(11,-9),(11,-8),(13,-6),(15,-6),(16,-7),(17,-7),(17,-6),(16,-5),(16,-3),(18,-1),(19,-1)  \
      ];
    for vert in verts:
      this.form.verts.append(subtractPoints(vert, (10,0)));

  def kill(this):
    enemy.kill(this);
    sounds[11].play();
    getPoints(750);
    body = motherCowDeath(this.pos, this.vel);
    particles.append(body);
  def update(this):
    enemy.update(this);
    this.angle += this.rot;
    this.spawnwait -= 1;
    if(this.spawnwait <= 0):
      sounds[16].play();
      this.spawnwait = 120;
      al = alien(this.pos);
      enemies.append(al);
      for i in range(8):
        ang = math.pi * 2 * (i / 8) + this.angle;
        pos = multPoint(xyComponent(ang), this.radius);
        pos = addPoints(this.pos, pos);
        proj = enemyBullet(pos, ang, 4);
        projectiles.append(proj);
      
  
  def draw(this):
    this.form.angle = this.angle;
    this.form.pos = this.pos;
    this.form.color = (255, 150, 0);
    this.form.thickness = 2;
    this.form.fill = (50, 20, 0);
    this.form.scale = 5;
    maincam.toDraw(this.form);
  
#the player object, what the user is controlling
class player:
  def __init__(this):
    '''initializes the player'''
    this.primaryWep = weapon(); #starts with the default weapon
    this.powerWep = None;
    this.pos = (0,0);
    this.vel = (0,0);
    this.angle = math.pi / -2;
    this.rotvel = 0;
    this.radius = 10;
    this.health = 1;
    this.powerups = [];

  def update(this):
    '''updates the player instance'''
    if(this.health == None):
      return;
    if(this.health <= 0):
      this.kill();
    this.pos = addPoints(this.pos, this.vel);
    this.angle += this.rotvel;
    this.control();
    this.wepCheck();
    this.applySpeedLimit();
    this.curWep().update();
    #this.collisionCheck();
    this.updatePowers();

  def updatePowers(this):
    for pow in this.powerups:
      pow.pUpdate();
  def drawPowers(this):
    for pow in this.powerups:
      pow.pDraw();
  def powerEvent(this, event, params = None):
    '''tells the player's powerups that an event has been triggered'''
    for pow in this.powerups:
      pow.doPower(event, params);
  def wepCheck(this):
    '''checks if the current weapon is out of ammo and switches back to the primary when necessary'''
    if(this.curWep().ammo <= 0):
      if(this.powerWep != None):
        this.powerWep = None;
      else:
        this.curWep = weapon();
  
  def damage(this,dmg):
    '''damages the player a specified amount'''
    if(this.health == None):
      return;
    sounds[17].play();
    this.health -= dmg;
  
  def kill(this):
    '''kills the player'''
    global iteration;
    this.vel = (0, 0);
    this.health = None; #a health of None is used to determine that the player has been dead for more than a frame, used so the dead player isn't constantly exploding
    for i in range(20):
      #shoots out green particles on death
      off = randPoint(10);
      part = particle(addPoints(this.pos, off), off, (0, 255, 0))
      part.thickness = 4;
      part.life = random.randrange(40, 100);
      if(randChance(50)):
        #chance the the partcle will be a darker green
        part.color = (0, 150, 0);
      particles.append(part);
    iteration = 0; #resets the global iteration to act as a makeshift timer so the transition to the end game menu isn't instantaneous
    
  def applySpeedLimit(this):
    '''makes sure the player doesn't go faster than a certain amount as this can cause unforseen consequences'''
    this.rotvel *= 0.93;
    if(distance(this.vel) > 5):
      this.vel = multPoint(this.vel, 0.97);
    
  def control(this):
    '''handles the player controls'''
    acceleration = 0.15; #speed of movement
    rotspd = 0.005;      #speed of aiming
    if(activecontr[0]): #up
      this.vel = addPoints(this.vel, multPoint(xyComponent(this.angle), acceleration));
      this.thrustParticle(math.pi);
    if(activecontr[1]): #down
      this.vel = addPoints(this.vel, multPoint(xyComponent(this.angle), -1 * acceleration));
      thrang = 1;
      if(randChance(50)):
        thrang *= -1;
      this.thrustParticle(thrang);
    if(activecontr[2]): #right
      this.rotvel += rotspd;
    if(activecontr[3]): #left
      this.rotvel -= rotspd;
    if(activecontr[4]): #fire
      this.fire();

  def thrustParticle(this, reldir):
    '''emits particles to show acceleration'''
    force = multPoint(xyComponent(this.angle + reldir), 0.7);
    part = particle(addPoints(this.pos, randPoint(5)), multPoint(force, 5), (255, 150, 0));
    part.vel = addPoints(part.vel, this.vel);
    part.life = random.randrange(5, 10);
    if(randChance(50)):
      part.color = (200, 200, 0);
    part.thickness = 3
    particles.append(part);
  
  def curWep(this):
    '''returns a power weapon if the player has one equipped, otherwise returns it's primary weapon'''
    if(this.powerWep == None):
      return this.primaryWep;
    return this.powerWep;
  
  def fire(this):
    '''triggers the currently equipped weapon'''
    wepfire = this.curWep();
    if(wepfire.trigger(this.pos, this.angle, this.vel)):
      this.powerEvent(1, wepfire);
  
  def draw(this):
    '''draws the player to the global cam query'''
    if(this.health == None):
      return;
    this.drawPowers();
    this.curWep().draw();
    #outline
    pshape = poly();
    pshape.color = (0, 255, 0);
    pshape.verts = [(-10,10), (-10,-10), (15, 0)];
    pshape.pos = this.pos;
    pshape.angle = this.angle;
    pshape.thickness = 2;
    #fill
    fshape = poly();
    fshape.color = (0, 100, 0);
    fshape.verts = pshape.verts;
    fshape.pos = pshape.pos
    fshape.angle = pshape.angle;
    fshape.thickness = 0;
    fshape.draw(maincam);
    pshape.draw(maincam);

#items are powerups that are dropped from enemies and the player can pick up
class item:
  def __init__(this, pos, power):
    '''initializes an item object'''
    this.pos = pos;
    this.form = poly((10,0), (7,7), (0,10), (-7,7), (-10,0), (-7,-7), (0,-10), (7,-7));
    this.form.color = (0,0,255);
    this.form.scale = 1.5;
    this.life = 600;
    this.pow = power;
    this.radius = 20;
    this.powersprite = power;

  def randItem(pos):
    '''static: returns a random item'''
    rand = random.randrange(-3, 4);
    if(rand >= 0):
      return item(pos, rand);
    else:
      if(rand == -1):
        return overShield(pos);
      if(rand == -2):
        return deflectorShield(pos);
      if(rand == -3):
        return quadShooter(pos);
  
  def grab(this):
    '''gives the item to the specified player'''
    if(this in items):
      items.remove(this);
      sounds[7].play();
    if(this.pow == -1):
      this.tryAddPower();
    if(this.pow == 0):
      p1.powerWep = spreadGun();
    if(this.pow == 1):
      p1.powerWep = ionCannon();
    if(this.pow == 2):
      p1.powerWep = rapidGun();
    if(this.pow == 3):
      p1.powerWep = missileLauncher();

  def tryAddPower(this):
    for pow in p1.powerups:
      if(type(this) is type(pow)):
        pow.replenish();
        return;
    p1.powerups.append(this);

  def update(this):
    '''handles the logic step for the current instance'''
    if(this.life <= 0):
      if(this in items):
        items.remove(this);
    if(collision(this, p1)):
       this.grab();
    this.life -= 1;
    
  def draw(this):
    '''renders the item object'''
    col = (0,0,255);
    incol = (0,0, 150);
    if(this.life % 10 < 5): #makes the item blink
      incol = (0,100, 70);
    if(this.life <= 200):
      if(this.life % 10 < 5): #item blinking intensifies if it close to dissapearing
        col = (0,0,0);
    
    this.form.pos = this.pos;
    this.form.fill = incol;
    this.form.color = col;
    this.form.thickness = 4;
    maincam.toDraw(this.form);
    #the power's icon image
    vecimg = img(powersprites[this.powersprite]);
    vecimg.pos = this.pos;
    maincam.toDraw(vecimg);

  def doPower(this, event, params = []):
    0;
  def pDraw(this):
    0;
  def pUpdate(this):
    0;
  def replenish(this):
    0;
#overshield creates a protective barrier around the player
class overShield(item):
  def __init__(this, pos):
    '''initializes an overshield item'''
    item.__init__(this, pos, -1);
    this.powersprite = 4;

  def grab(this):
    '''gives the player an overshield'''
    item.grab(this);
    p1.health = 2;
    this.life = 1;

  def doPower(this, event, params):
    '''deflects the damage if the player initiates a '0' power event(takes damage)'''
    if(event == 0):
      if(this in p1.powerups):
        p1.powerups.remove(this);
        this.burst();
      len = (params.radius + p1.radius) - distance(p1.pos, params.pos);
      norm = normal(params.pos, p1.pos);
      p1.pos = addPoints(p1.pos, multPoint(norm, len));
      p1.vel = multPoint(norm, 3);
      p1.health = 1;

  def pDraw(this):
    tform = poly.circleGon(8, 20);
    tform.color = (0,100,255);
    tform.angle = p1.angle;
    tform.pos = p1.pos;
    tform.thickness = 3;
    maincam.toDraw(tform);
  def burst(this):
    for i in range(15):
      part = particle(this.pos, p1.vel, (0, 200, 255), 3);
      off = randCirc(10);
      part.vel = addPoints(part.vel, off);
      part.damping = 0.95;
      particle.life = 100;
      part.pos = addPoints(p1.pos,off * 3);
      particles.append(part);

#deflector shield creates a matrix of projectile resistant forcefields around the player
class deflectorShield(item):
  def __init__(this, pos):
    item.__init__(this, pos, -1);
    this.matrix = [True, True, True, True, True, True];
    this.powersprite = 5;

  def pUpdate(this):
    if(not(this.matrix[0] or this.matrix[1] or this.matrix[2] or this.matrix[3] or this.matrix[4] or this.matrix[5])):
      if(this in p1.powerups):
        p1.powerups.remove(this);
    
    for i in range(6):
      if(not this.matrix[i]):
        continue;
      fpos = multPoint(xyComponent(math.pi * 2 * (i / 6)), 30);
      fpos = addPoints(fpos, p1.pos);
      for bullet in projectiles:
        if(bullet.friendly):
          continue;
        if(distance(bullet.pos, fpos) <= 15):
          bullet.life = 0;
          this.matrix[i] = False;
          this.burst(fpos);
          break;
  def burst(this, pos):
    sounds[18].play();
    tform = circ(20);
    tform.pos = pos;
    tform.color = (0, 255, 200);
    maincam.toDraw(tform);

  def pDraw(this):
    itr = 0;
    for field in this.matrix:
      if(field):
        anginc = math.pi * 2 * (itr / 6);
        tform = poly((30, -10), (30, 10), (30, 10));
        tform.angle = anginc;
        tform.pos = p1.pos;
        tform.color = (0, 0, 255);
        tform.thickness = 3;
        maincam.toDraw(tform);
      itr += 1;
      
  def replenish(this):
    item.replenish(this);
    this.matrix = [True, True, True, True, True, True];
    
#quadShooter fires your weapon in four different directions
class quadShooter(item):
  def __init__(this, pos):
    item.__init__(this,pos, -1);
    this.life = 500;
    this.powersprite = 6;

  def doPower(this, event, params):
    if(this.life <= 0):
      if(this in p1.powerups):
        p1.powerups.remove(this);
      return;
    if(event == 1):
      if(params.fireDelay > 0):
        this.life -= params.fireDelay;
      else:
        this.life -= 1;
      pammo = params.ammo;
      params.ammo = 1000;
      ang = math.pi / 2;
      for i in range(3):
        params.fire(p1.pos, p1.angle + ang, p1.vel);
        ang += math.pi / 2;
      params.ammo = pammo;

  def pDraw(this):
    ang = p1.angle + math.pi / 2;
    for i in range(3):
      tpos = xyComponent(ang);
      tpos = multPoint(tpos, 30);
      tpos = addPoints(tpos, p1.pos);
      tform = poly((0, 0), (1, 0), (0, 0));
      tform.scale = this.life / 30;
      tform.pos = tpos;
      tform.angle = ang;
      tform.color = (255,255,0);
      tform.thickness = 2;
      maincam.toDraw(tform);
      ang += math.pi / 2;
  def replenish(this):
    item.replenish(this);
    this.life = 500;
  def grab(this):
    item.grab(this);
    this.life = 500;

def handleInput():
  '''handles receiving input from the keyboard'''
  #pump() must be called before you attempt to get the keyboard state
  #this is due to the get_pressed function being called after the SDL_GetKeyState() in the
  #gamepy engine, which pump() resets
  pygame.event.pump();
  
  #stops the function if the game does not have focus
  if(not pygame.key.get_focused()):
    return;
  global activecontr;
  global lastactivec;
  
  itr = 0;
  for pressed in activecontr:
    lastactivec[itr] = pressed;
    itr += 1;
  keyspressed = pygame.key.get_pressed();
  activecontr[0] = keyspressed[controls[0]];
  activecontr[1] = keyspressed[controls[1]];
  activecontr[2] = keyspressed[controls[2]];
  activecontr[3] = keyspressed[controls[3]];
  activecontr[4] = keyspressed[controls[4]];
  activecontr[5] = keyspressed[controls[5]] or keyspressed[pygame.K_RETURN];
  
  handleGlobalControls(keyspressed);

def getTappedKeys():
  '''returns they keys that are being pressed on the first frame they are being pressed'''
  global lastkeyspr;
  if(lastkeyspr == None):
    #if lastkeyspr is not defined, it sets and returns it to avoid errors
    lastkeyspr = pygame.key.get_pressed();
    return lastkeyspr;
  r = list();
  keyspr = pygame.key.get_pressed();
  itr = 0;
  for key in keyspr:
    '''compares the new keypress list to the keys that were presed last frame and stores them in the return list if they are new keypresses'''
    if(key and not lastkeyspr[itr]):
      r.append(itr);
    itr += 1;
  
  lastkeyspr = keyspr;
  return r;

def loadHiscore():
  '''loads the highscore from the score file into the global hi variable'''
  global hi;
  file = open(compilePath('scores'), 'r');
  scs = file.read();
  hi = int(scs.split('\n')[0].split(':')[1]);

def init():
  '''initializes the program'''
  print("initializing...", end = "");
  global screen;
  global font;
  global tinyfont;

  #initializes pygame:
  pygame.mixer.pre_init(44100, -16, 2, 512);
  pygame.init();
  pygame.display.set_icon(pygame.image.load(compilePath(os.path.join("graphics","icon.png"))));
  pygame.display.set_caption("SPACEGAME.EXE");
  pygame.mouse.set_visible(False);
  screen = pygame.display.set_mode(size);
  font = pygame.font.Font(compilePath("font.ttf"), 32);  
  tinyfont = pygame.font.Font(compilePath("font.ttf"), 16);
  loadSprites();
  loadSounds();
  loadHiscore();
  gotoMode(0);
  
  print("Done!");

def startGame():
  '''starts a new round'''
  global maincam;
  global p1;
  global mode;
  global score;
  global scoredrop;
  global scoredropper;
  global enemies;
  global stars;
  global projectiles;
  global items;
  global particles;
  global enemyspawndelay;
  global cowspawndelay;
  
  enemies = list();
  stars = list();
  projectiles = list();
  items = list();
  particles = list();
  
  gotoMode(1);
  score = 0;
  scoredrop = 500;
  enemyspawndelay = 0;
  cowspawndelay = 0;
  scoredropper = None;
  maincam = camera();
  p1 = player();
  
  #testpow = item((0, 40), 2);
  #items.append(testpow);
  #testbas = basher((100,100));
  #enemies.append(testbas);
  #testmtc = motherCow((100,100));
  #enemies.append(testmtc);
  
  #fills in the stars
  for i in range(200):
    stars.append(randPoint(500));

def getPoints(pts):
  global score;
  global scoredrop;
  global scoredropper;
  score += pts;
  if(score >= scoredrop):
    scoredropper = 60;
    if(scoredrop <= 500):
      scoredrop += 500;
    else:
      scoredrop += 1000;

def scoreDrops():
  global scoredropper;
  if(scoredropper == None):
    return;
  ppos = multPoint(xyComponent(p1.angle), 100);
  ppos = addPoints(ppos, p1.pos);
  if(scoredropper <= 0):
    scoredropper = None;
    bonus = item.randItem(ppos);
    items.append(bonus);
  else:
    col = (255,255,255);
    if(scoredropper % 8 > 3):
      col = (100, 100, 100);
    pdraw = poly.circleGon(8, 15);
    pdraw.thickness = 3;
    pdraw.color = col;
    pdraw.pos = ppos;
    maincam.toDraw(pdraw);
    scoredropper -= 1;

def lose():
  '''goes to the endgame screen'''
  gotoMode(2);

def loadSprites():
  '''loads the item icon sprites'''
  powersprites.append(pygame.image.load(compilePath(os.path.join("graphics","power_spread.png"))));
  powersprites.append(pygame.image.load(compilePath(os.path.join("graphics","power_ioncannon.png"))));
  powersprites.append(pygame.image.load(compilePath(os.path.join("graphics","power_rapid.png"))));
  powersprites.append(pygame.image.load(compilePath(os.path.join("graphics","power_missiles.png"))));
  powersprites.append(pygame.image.load(compilePath(os.path.join("graphics","power_overshield.png"))));
  powersprites.append(pygame.image.load(compilePath(os.path.join("graphics","power_deflectorshield.png"))));
  powersprites.append(pygame.image.load(compilePath(os.path.join("graphics","power_quadshooter.png"))));

def loadSounds():
  '''loads the sound files'''
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","MenuNavigate.wav")));
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","MenuSelect.wav")));
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","Shoot_Default.wav"))); #2) weapon firing
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","Shoot_RapidGun.wav")));
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","Shoot_IonCannon.wav"))); 
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","Shoot_SpreadGun.wav")));
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","Shoot_MissileLauncher.wav")));
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","PowerUp.wav")));
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","Death_LargeAsteroid.wav"))); #8) deaths
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","Death_SmallAsteroid.wav")));
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","Death_Alien.wav")));
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","Death_MotherCow.wav")));
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","Hit_Default.wav"))); #12) weapon hits
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","Hit_MissileLauncher.wav")));
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","Hit_RapidGun.wav")));
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","Attack_Alien.wav"))); #15) enemy attacks
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","Attack_MotherCow.wav")));
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","TakeDamage.wav")));
  sounds.append(pygame.mixer.Sound(os.path.join("sounds","ShieldDeflect.wav")));

def handleGlobalControls(keys):
  '''handles the global controls that work anywhere in the gameloop'''
  if(keys[pygame.K_ESCAPE]):
    pygame.quit();

def handleMenuControls():
  '''handles GUI navigation in the menu screens'''
  global selection;
  if(activecontr[5] and (not lastactivec[5])):
    select(selection);
    sounds[1].play();
    sounds[1].play();
  if(activecontr[1] and (not lastactivec[1])):
    selection += 1;
    sounds[0].play();
  if(activecontr[0] and (not lastactivec[0])):
    selection -= 1;
    sounds[0].play();
  if(selection < 0):
    selection = 0;

def select(selection):
  '''performs an action depending on the currently selected option in the menu'''
  if(mode == 0):
    if(selection == 0):
      startGame();
    if(selection == 1):
      gotoMode(3);
    if(selection == 2):
      pygame.mixer.stop();
      pygame.quit();
      raise();
  elif (mode == 3):
    if(selection == 0):
      startGame();
    if(selection == 1):
      gotoMode(0);

def saveScore(name, points):
  '''saves a score under a specified name to the scoreboard'''
  scores = loadScoreboard();
  newscores = list();  
  itr = 0;
  pt = points;
  for scor in scores:
    if(pt >= scor[1]):
      newscores.append((name, pt));
      pt = 0;
    newscores.append(scor);
    itr += 1;

  while(True):
    try:
      newscores.remove(newscores[5]);
    except:
      break;
  
  sbfile = open(compilePath('scores'), 'w');
  for scor in newscores:
    sbfile.write(scor[0] + ':' + str(scor[1]) + '\n');

def gotoMode(modenum):
  '''goes to a specified mode and performs necessary actions before and after'''
  global mode;
  global iteration;
  global selection;

  if(modenum == 0):
    loadTitlesprite();
  if(mode == 0):
    disposeTitlesprite();
  
  selection = 0;
  mode = modenum;
  iteration = 0;

def loadTitlesprite():
  '''loads the title screen background image'''
  global titlesprite;
  titlesprite = pygame.image.load(compilePath(os.path.join("Graphics","title.png")));
  
def disposeTitlesprite():
  '''disposes the title screen background image'''
  titlesprite = None;

def loop():
  '''defines the call order of the game loop'''
  global lagcatch;
  start = time.time() #stores the time at the beginning if the step
  #lagcatch dissipates over time
  if(lagcatch > 0):
    lagcatch -= 0.01;
  elif (lagcatch < 0):
    lagcatch = 0;
  handleInput();
  update();
  draw();
  elapsed = time.time() - start; #compares the time at the beginning of the step to now
  sltime = framerate - elapsed; #calculates how much time is left before the next step is called
  if(sltime >= 0):              #if that time is above zero, it suspends the thread until the next step is to be called
    time.sleep(sltime);
  else:                         #if that time is below zero, a lag has occured, this is where the lag is handled
    #print("lag" + str(sltime) + "s");
    lagcatch -= sltime;
    handleLag();

def update():
  '''main game logic is handled here'''
  global iteration;
  updateMode();
  iteration += 1;

def updateMode():
  '''handles update logic based on the current game mode'''
  if(mode == 0):    #main menu
    updateMenu();
  elif(mode == 1):  #gameplay 
    updateGameplay();
  elif(mode == 2):  #name entry
    updateNameEntry();
  elif(mode == 3):  #scoreboard
    updateScoreboard();

def updateMenu():
  '''handles update logic for the main menu'''
  global selection;
  handleMenuControls();
  if(selection > 2):
    selection = 2;

def updateGameplay():
  '''handles the update logic for in-game'''
  for part in particles:    
    part.update();  #updates all the particles
  for proj in projectiles:
    proj.update();  #updates all the projectiles
  for en in enemies:
    en.update();    #updates all the enemies
  for power in items:
    power.update(); #updates all the items
  p1.update();      #updates the player
  handleCollisions();
  scoreDrops();
  maincam.orient(p1.pos, p1.angle + math.pi/2); #orients the camera to follow the player
  #removes necessary projectiles. they are not removed as the projectile list is updating because it causes an iteration skip which results in some projectiles not getting updated
  for proj in projectiles:
    proj.removeCheck();
  spawnEnemies();   #spawns/despawns enemies into the world
  spawnStars();     #spawns/despawns stars around the player as they move
  if(p1.health == None and iteration > 60): #acts as a makeshift timer to tell the screen to transition to the end screen after the player has been dead for a second
    lose();
  
def updateNameEntry():
  '''updates the name entry screen'''
  global p1;
  #turns the player object into a string that the name on the scoreboard will be saved as so we don't have to create a new variable
  if(not type(p1) is str):
    scores = loadScoreboard();
    if(score < scores[4][1]):
      gotoMode(3);
      return;
    p1 = "";
  tkeys = getTappedKeys();
  #parses the keyboard input into ascii characterss
  for k in tkeys:
    if(k == pygame.K_BACKSPACE):
      p1 = p1[:len(p1) - 1];
    if(k == pygame.K_SPACE):
      p1 += ' ';
    if(k >= 48 and k <= 57):
      num = "0123456789";
      p1 += num[k-48];
    if(k >= 97 and k <= 122):
      alph = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
      p1 += alph[k-97];

  #limits the name length to 12 characters
  if(len(p1) > 12):
    p1 = p1[:12];

  #if enter is pressed, finish name entry
  if(pygame.K_RETURN in tkeys):
    saveScore(p1, score);
    gotoMode(3);
  
def updateScoreboard():
  '''updates the scoreboard menu screen'''
  global selection;
  handleMenuControls();
  if (selection > 1):
    selection = 1;
  
def draw():
  '''rendering logic handled here'''
  if(screen == None):
    print("Cannot draw to screen because screen is not initialized!");
    return;
  screen.fill((0,0,0));
  drawMode();
  pygame.display.flip();

def drawMode():
  '''renders certain ways depending on the game mode'''
  if(mode == 0):  #mainmenu
    drawMenu();
  elif(mode == 1):  #in game
    drawGameplay();
  elif(mode == 2):  #name entry
    drawNameEntry();
  elif(mode == 3):  #score board
    drawScoreboard();
  
def drawMenu():
  '''draws the main title screen'''
  buttonpos = (200,450);
  selcol = (0,255,0);
  if(iteration % 10 >= 5): #selcol flashes btween green and dark green every 5 frames
    selcol = (0,100,0);

  #creates the selectable buttons, the flash if they are selcted
  if(selection == 0):
    startButton = font.render("START GAME", False, selcol);
  else:
    startButton = font.render("START GAME", False, (255,255,255));
  if(selection == 1):
    scoresButton = font.render("SCOREBOARD", False, selcol);
  else:
    scoresButton = font.render("SCOREBOARD", False, (255,255,255));
  if(selection == 2):
    exitButton = font.render("EXIT", False, selcol);
  else:
    exitButton = font.render("EXIT", False, (255,255,255));
  selector = font.render(">", False, (255,255,255));

  #renders the background
  screen.blit(titlesprite, (0,0));
  screen.blit(selector, addPoints(buttonpos, (-15, selection * 40)));
  screen.blit(startButton, addPoints(buttonpos, (0, 0))); 
  screen.blit(scoresButton, addPoints(buttonpos, (0, 40))); 
  screen.blit(exitButton, addPoints(buttonpos, (0, 80)));
  
def drawGameplay():
  '''draws the gameplay'''
  drawStars();
  for part in particles:
    part.draw();  #draws all the particles
  for power in items:
    power.draw(); #draws all the items
  for proj in projectiles:
    proj.draw();  #draws all the projectiles
  for en in enemies:
    en.draw();    #draws all the enemies
  p1.draw(); #renders the player
  maincam.render(screen); #renders the world objects throught the camera's point of view
  drawScore();

  ##
  #col0 = circ(200);
  #col0.pos = p1.pos;
  #col0.thickness = 1;
  #col1 = circ(300);
  #col1.pos = p1.pos;
  #col1.thickness = 1;
  #maincam.renderCirc(col0);
  #maincam.renderCirc(col1);
  ##
def drawNameEntry():
  '''draws the name entry screen'''
  global p1;
  if(not type(p1) is str):
    return;
  sccol = (255,255,0);
  ncol = (0, 255,255);
  if(iteration % 10 >= 5):
    sccol = (255, 150, 0);
    ncol = (0, 100, 255);
  title1 = font.render("YOU PLACED IN THE ", False, (255,255,255));
  title2 = font.render("SCOREBOARD!", False, sccol);
  title3 = font.render("ENTER YOUR NAME BELOW:", False, (255,255,255));
  
  screen.blit(title1, (10, 300));
  screen.blit(title2, (350, 300));
  screen.blit(title3, (85, 340));
  ntex = p1;
  if(len(p1) < 12):
    ntex += '_';
  nametext = font.render(ntex, False, ncol);
  screen.blit(nametext,(180, 400));
  
def drawScoreboard():
  '''draws the scoreoard screen'''
  buttonpos = (200, 450);
  scores = loadScoreboard();
  col = (255, 150, 0);
  selcol = (0,255,0);
  ycol = (0,255,255);
  if(iteration % 10 >= 5):
    col = (255,255,0);
    selcol = (0, 100, 0);
    ycol = (0, 100, 255);
  title = font.render("---SCOREBOARD---", False, col);
  scoretext = font.render("YOU:                   " + str(score), False, ycol);
  if(selection == 0):
    startButton = font.render("START GAME", False, selcol);
  else:
    startButton = font.render("START GAME", False, (255,255,255));
  if(selection == 1):
    menuButton = font.render("MAIN MENU", False, selcol);
  else:
    menuButton = font.render("MAIN MENU", False, (255,255,255));
  
  selector = font.render(">", False, (255,255,255));
  
  itr = 0;
  for scor in scores:
    scoreentry = font.render(str(itr + 1) + '. ' + scor[0], False, (0,255,0));
    screen.blit(scoreentry, (100, 150 + itr * 40));
    scoreentry = font.render(str(scor[1]), False, (0,255,0));
    screen.blit(scoreentry, (450, 150 + itr * 40));
    itr += 1;

  screen.blit(title, (150, 50));   
  screen.blit(selector, addPoints(buttonpos, (-15, selection * 40)));
  if(score > 0):
    screen.blit(scoretext, (150, 380));
  screen.blit(startButton, addPoints(buttonpos, (0, 0)));
  screen.blit(menuButton, addPoints(buttonpos, (0, 40)));

def drawScore():
  '''draws the score and high score in the upper left of the screen'''
  pygame.sysfont
  text = font.render("SCORE: " + str(int(score)), False, (255,255,255));
  hitext = tinyfont.render("HI: " + str(hi), False, (200,200,200));
  screen.blit(text, (4,4));
  screen.blit(hitext,(4,40));

def loadScoreboard():
  '''loads the scores from the score file'''
  loadHiscore();
  r = list();
  file = open(compilePath('scores'), 'r');
  dat = file.read();
  spldat = dat.split('\n');
  for scor in spldat:
    if(scor == ""):
      continue;
    splscor = scor.split(':');
    r.append((splscor[0],int(splscor[1])));
  return r;

def handleLag():
  '''handles the lag by removing non essential game assets'''
  if(mode != 1):
    return;
  catchup();
  
  partsr = 0;
  asterr = 0;
  for part in particles:
    if(randChance(50)):
      part.life = 0;
      partsr += 1;
  for en in enemies:
    if(type(en) is asteroid):
      if(en.radius <= 10):
        if(distance(en.pos, p1.pos) > 400):
          enemies.remove(en);
          asterr += 1;
  #print("cleaned up " + str(partsr) + " particles, " +str(asterr) + " asteroids");

def catchup():
  '''updates the game without rendering to save time'''
  global lagcatch;
  itr = 0;
  while (lagcatch >= framerate):
    lagcatch -= framerate;
    start = time.time();
    update();
    elapsed = time.time() - start;
    lagcatch += elapsed;
    itr += 1;
  maincam.drawQuery = list();
  #print("caught up " + str(itr) + " frames");
  
def collidingColchecks(pos, radius):
  r = [];
  dist = distance(pos, p1.pos);
  if(dist <= 200):
    r.append(colcheck0);
    if(dist + radius > 200):
      r.append(colcheck1);
  elif(dist <= 300):
    r.append(colcheck1);
    if(dist - radius <= 200):
      r.append(colcheck0);
    if(dist + radius > 300):
      r.append(colcheck2);
  else:
    r.append(colcheck2);
    if(dist - radius <= 300):
      r.append(colcheck1);
  return r;

def handleCollisions():
  handleColLists();
  itr = 0;
  for op in colcheck0:
    typ = projectile;
    if(baseIs(op, enemy)):
      typ = enemy;
    opCheckColList(op, colcheck0, itr, typ);
    if(collision(p1, op)):
      if(baseIs(op, projectile)):
        if(not op.friendly):
          p1.damage(1);
          p1.powerEvent(0, op);
          op.hit(p1);
      else:  
        p1.damage(1);
        p1.powerEvent(0, op);
        op.hit(p1);
    itr += 1;
  itr = 0;
  for op in colcheck1:
    typ = projectile;
    if(baseIs(op, enemy)):
      typ = enemy;
    opCheckColList(op, colcheck1, itr, typ);
    itr += 1;
  itr = 0;
  for op in colcheck2:
    typ = projectile;
    if(baseIs(op, enemy)):
      typ = enemy;
    opCheckColList(op, colcheck2, itr, typ);
    itr += 1;
  collectBodies();
def opCheckColList(op, clist, itr, optype):
  if(op.cck or op.dead()):
    return;
  op.cck = True;
  for i in range(itr + 1, len(clist)):
    if(clist[i].dead()):
      continue;
    if(baseIs(clist[i], optype)):
      if(optype is projectile):
        if(clist[i].friendly == op.friendly):
          continue;
      else:
        continue;
    if(collision(op, clist[i])):
      op.hit(clist[i]);
      if(type(clist[i]) is enemyBullet):
        clist[i].hit(op);

def collectBodies():
  itr = 0;
  while(itr < len(enemies)):
    if(enemies[itr].dead()):
      del enemies[itr];
      continue;
    itr += 1;
  itr = 0;
  while(itr < len(projectiles)):
    if(projectiles[itr].dead()):
      del projectiles[itr];
      continue;
    itr += 1;
      
def handleColLists():
  global colcheck0;
  global colcheck1;
  global colcheck2;
  colcheck0 = list();
  colcheck1 = list();
  colcheck2 = list();
  for en in enemies:
    sortToColList(en);
  for proj in projectiles:
    sortToColList(proj);
def sortToColList(obj):
  dist = distance(obj.pos, p1.pos);
  if(dist <= 200):
    colcheck0.append(obj);
    if(dist + obj.radius > 200):
      colcheck1.append(obj);
  elif(dist <= 300):
    colcheck1.append(obj);
    if(dist - obj.radius <= 200):
      colcheck0.append(obj);
    if(dist + obj.radius > 300):
      colcheck2.append(obj);
  else:
    colcheck2.append(obj);
    if(dist - obj.radius <= 300):
      colcheck1.append(obj);
def spawnStars():
  '''spawns/despawns the stars around the player'''
  for star in stars:
    if(distance(subtractPoints(star, p1.pos)) > 405):
      stars.remove(star);

  while(len(stars) < 200):
    stars.append(addPoints(multPoint(xyComponent(random.random() * math.pi * 2), 400), p1.pos));

def spawnEnemies():
  #spawns/despawns the enemies around the player
  global enemyspawndelay;
  global cowspawndelay;

  for en in enemies:
    if(distance(subtractPoints(p1.pos, en.pos)) > 800):
      enemies.remove(en);

  #astsize = iteration / 10000;
  astsize = 1;
  aliencount = (iteration - 1800) / 1800 + 1;
  bashercount = (iteration - 2000) / 2500 + 1;
  if(aliencount < 0):
    aliencount = 0;

  if(enemyspawndelay <= 0):
    enemyspawndelay = 300;
    for i in range(3):
      en = asteroid(addPoints(randCirc(500), p1.pos), randRange(randRange(randRange(120 * astsize + 10))) + 8);
      en.vel = randPoint(3);
      enemies.append(en);

    for i in range(int(aliencount)):
      en = alien(addPoints(randCirc(500), p1.pos));
      enemies.append(en);
    
    if(int(bashercount) > 0):
      for i in range(random.randrange(int(bashercount))):
        bs = basher(addPoints(randCirc(randRange(600, 500)), p1.pos));
        enemies.append(bs);
  enemyspawndelay -= 1;
  if(iteration > 3500):
    cowspawndelay -= 1;
    if(cowspawndelay <= 0):
      cowspawndelay = 1200;
      cow = motherCow(addPoints(randCirc(500), p1.pos));
      enemies.append(cow);

def compilePath(path):
  '''ignore, used for compiling to a standalone exe with pyinstaller, ended up not doing it'''
  if hasattr(sys, "_MEIPASS"):
      return os.path.join(sys._MEIPASS, path);
  return os.path.join(os.path.abspath('.'),path);

def drawStars():
  '''draws the stars'''
  itr = 0;
  for star in stars:
    pol = poly();
    pol.color = (140, 140, 140);
    pol.verts = [(0,0)];
    pol.verts.append((0,1));
    pol.pos = star;
    pol.thickness = 2;
    verts = maincam.renderPoly(pol);
    itr += 1;

def main():
  '''main entry point of the gameloop'''
  while(True):
    loop();

init();
#raise Exception();
main();
