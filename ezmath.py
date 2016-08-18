#Isaiah smith
#cs140a
#6/6/2016
#ezmath.py

import math;
import random;

def distance(a, b = (0,0)):
  '''takes two points and returns the distance between them'''
  return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2);

def normal(a,b = (0,0)):
  '''returns the normalized vector from b to a'''
  dif = subtractPoints(b,a);
  return xyComponent(direction(dif));

def direction(vec):
  '''returns the angle the vector is pointing in'''
  return math.atan2(vec[1], vec[0]);

def xyComponent(ang):
  '''gets the rectangular components of an angle'''
  return (math.cos(ang), math.sin(ang));

def transform(point, translation, rotation = 0, origin = (0,0)):
  '''returns the point with the transformations given applied to it'''
  x,y = addPoints(point, translation);
  mag = distance(point);
  ang = direction(point);
  ang += rotation;
  xy = multPoint(xyComponent(ang), mag);
  xy = addPoints(xy, translation);
  return (addPoints((xy), origin));

def roundPoint(a):
  '''rounds a point to the nearest whole'''
  x = round(a[0],0);
  y = round(a[1],0);
  return(int(x),int(y));

def addPoints(a, b):
  '''takes two vector tuples and adds them together'''
  x = a[0] + b[0];
  y = a[1] + b[1];
  return(x,y);

def subtractPoints(a, b):
  '''subtracts point b from point a'''
  x = a[0] - b[0];
  y = a[1] - b[1];
  return(x,y);

def multPoint(point, factor):
  '''multiplies a point by a factor'''
  x = point[0] * factor;
  y = point[1] * factor;
  return(x,y);

def randPoint(maxdist = 1):
  '''a random point with even distribution within the given radius'''
  mag = random.random() * maxdist;
  ang = random.random() * math.pi * 2;
  return(math.cos(ang) * mag, math.sin(ang) * mag);

def randCirc(dist):
  '''returns a random point on the outer edge of a circle with a radius of 'dist' '''
  return multPoint(xyComponent(random.random() * math.pi * 2), dist);

def randChance(percent):
  '''randomly returns true 'percent' of the time'''
  return random.random() < percent / 100;

def randRange(end, start = 0):
  '''returns a float between start and end'''
  dif = end - start;
  return random.random() * dif + start;

def baseIs(item, base):
  '''returns true if item's type derives from base'''
  if(type(item) is base):
    return True;
  for typ in item.__class__.__bases__:
    if(typ is base):
      return True;
  return False;

def collision(obj1, obj2):
  '''tests collision between obj1 and obj2'''
  difpos = subtractPoints(obj1.pos, obj2.pos);
  colrad = obj1.radius + obj2.radius;
  return distance(difpos) <= colrad;
