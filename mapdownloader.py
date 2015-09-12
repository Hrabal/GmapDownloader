# !/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
from PIL import Image
import StringIO
from math import pi, log, tan, atan, exp, ceil
from progressbar import ProgressBar, Bar, ETA, ReverseBar
import datetime

EARTH_RADIUS = 6378137
EQUATOR_CIRCUMFERENCE = 2 * pi * EARTH_RADIUS
INITIAL_RESOLUTION = EQUATOR_CIRCUMFERENCE / 256.0
ORIGIN_SHIFT = EQUATOR_CIRCUMFERENCE / 2.0


def latlontopixels(lat, lon, zoom):
    mx = (lon * ORIGIN_SHIFT) / 180.0
    my = log(tan((90 + lat) * pi/360.0))/(pi/180.0)
    my = (my * ORIGIN_SHIFT) / 180.0
    res = INITIAL_RESOLUTION / (2**zoom)
    px = (mx + ORIGIN_SHIFT) / res
    py = (my + ORIGIN_SHIFT) / res
    return px, py


def pixelstolatlon(px, py, zoom):
    res = INITIAL_RESOLUTION / (2**zoom)
    mx = px * res - ORIGIN_SHIFT
    my = py * res - ORIGIN_SHIFT
    lat = (my / ORIGIN_SHIFT) * 180.0
    lat = 180 / pi * (2*atan(exp(lat*pi/180.0)) - pi/2.0)
    lon = (mx / ORIGIN_SHIFT) * 180.0
    return lat, lon

apikey = 'AIzaSyAoUzwHreNPC6pjDGqiHdF25d2q4QwV7M0'
params = [
          ('zoom', '6'),
          ('maptype', 'terrain'),
          ('style', 'element:labels|visibility:off'),
          ('style', 'feature:administrative.country|element:labels|visibility:on'),
          ('style', 'element:geometry.stroke|visibility:off'),
          ('style', 'feature:landscape|element:geometry|saturation:-100'),
          ('style', 'feature:water|saturation:-100|invert_lightness:true'),
          ('key', apikey)]

zoom = 6
# max zoom = 6
zones = [('83.473288, -180', '-72.426566, -120'),
         ('83.473288, -120', '-72.426566, -70'),
         ('83.473288, -70', '-72.426566, -20'),
         ('83.473288, -20', '-72.426566, 30'),
         ('83.473288, 30', '-72.426566, 80'),
         ('83.473288, 80', '-72.426566, 130'),
         ('83.473288, 130', '-72.426566, 180')]

scale = 2
# max scale = 2
zonecount = 0
start = datetime.datetime.now()
for zone in zones:
    zonecount += 1
    print 'Processing Zone %d' % (zonecount)
    upperleft, lowerright = zone[0], zone[1]
    ullat, ullon = map(float, upperleft.split(','))
    lrlat, lrlon = map(float, lowerright.split(','))
    ulx, uly = latlontopixels(ullat, ullon, zoom)
    lrx, lry = latlontopixels(lrlat, lrlon, zoom)
    dx, dy = lrx - ulx, uly - lry
    cols, rows = int(ceil(dx/640)), int(ceil(dy/400))
    bottom = 120
    largura = int(ceil(dx/cols))
    altura = int(ceil(dy/rows))
    alturaplus = altura + bottom
    final = Image.new("RGB", (int(dx)*scale, int(dy)*scale))  
    p = 0
    widgets = [Bar('>'), ' ', ETA(), ' ', ReverseBar('<')]
    pbar = ProgressBar(widgets=widgets, maxval=cols*rows).start()
    for x in range(cols):
        for y in range(rows):
            p += 1
            dxn = largura * (0.5 + x)
            dyn = altura * (0.5 + y)
            latn, lonn = pixelstolatlon(ulx + dxn, uly - dyn - bottom/2, zoom)
            center = ('center', ','.join((str(latn), str(lonn))))
            size = ('size', '%dx%d' % (largura, alturaplus))
            sc = ('scale', str(scale))
            pars = [center, size, sc]
            url = 'http://maps.googleapis.com/maps/api/staticmap?' + '&'.join(['='.join(par) for par in pars + params])
            googleresp = urllib.urlopen(url)
            imag = googleresp.read()
            im = Image.open(StringIO.StringIO(imag))
            final.paste(im, (int(x*largura*scale), int(y*altura*scale)))
            pbar.update(p)
    pbar.finish()
    zonename = 'zone_'+str(zonecount)
    final.save(zonename+'.bmp')
    del final
    print '\n'

stop = datetime.datetime.now()
print stop - start
