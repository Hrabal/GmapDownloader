# !/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
from PIL import Image
import StringIO
from math import pi, log, tan, atan, exp, ceil
import datetime


class WorldMap(object):
    """docstring for WorldMap"""
    EARTH_RADIUS = 6378137
    EQUATOR_CIRCUMFERENCE = 2 * pi * EARTH_RADIUS
    INITIAL_RESOLUTION = EQUATOR_CIRCUMFERENCE / 256.0
    ORIGIN_SHIFT = EQUATOR_CIRCUMFERENCE / 2.0

    apikey = 'AIzaSyAoUzwHreNPC6pjDGqiHdF25d2q4QwV7M0'

    def __init__(self):
        super(WorldMap, self).__init__()
        self.params = [('zoom', '6'),
                       ('maptype', 'terrain'),
                       ('style', 'element:labels|visibility:off'),
                       ('style', 'feature:administrative.country|element:labels|visibility:on'),
                       ('style', 'element:geometry.stroke|visibility:off'),
                       ('style', 'feature:landscape|element:geometry|saturation:-100'),
                       ('style', 'feature:water|saturation:-100|invert_lightness:true'),
                       ('key', self.apikey)]
        self.zoom = 6
        self.zones = [('74, -180', '0, -120'),
                      ('74, -120', '0, -70'),
                      ('74, -70', '0, -20'),
                      ('74, -20', '0, 30'),
                      ('74, 30', '0, 80'),
                      ('74, 80', '0, 130'),
                      ('74, 130', '0, 180'),
                      ('0, -180', '60, -120'),
                      ('0, -120', '60, -70'),
                      ('0, -70', '60, -20'),
                      ('0, -20', '60, 30'),
                      ('0, 30', '60, 80'),
                      ('0, 80', '60, 130'),
                      ('0, 130', '60, 180')]
        self.scale = 2

    def get(self):
        zonecount = 0
        start = datetime.datetime.now()
        for zone in self.zones:
            zonecount += 1
            print 'Processing Zone %d - from %s to %s' % (zonecount, zone[0], zone[1])
            upperleft, lowerright = zone[0], zone[1]
            ullat, ullon = map(float, upperleft.split(','))
            lrlat, lrlon = map(float, lowerright.split(','))
            ulx, uly = self.latlontopixels(ullat, ullon, self.zoom)
            lrx, lry = self.latlontopixels(lrlat, lrlon, self.zoom)
            dx, dy = lrx - ulx, uly - lry
            cols, rows = int(ceil(dx/640)), int(ceil(dy/400))
            bottom = 120
            largura = int(ceil(dx/cols))
            altura = int(ceil(dy/rows))
            alturaplus = altura + bottom
            final = Image.new("RGB", (int(dx)*self.scale, int(dy)*self.scale))
            p = 0
            for x in range(cols):
                for y in range(rows):
                    p += 1
                    dxn = largura * (0.5 + x)
                    dyn = altura * (0.5 + y)
                    latn, lonn = self.pixelstolatlon(ulx + dxn, uly - dyn - bottom/2, self.zoom)
                    center = ('center', ','.join((str(latn), str(lonn))))
                    size = ('size', '%dx%d' % (largura, alturaplus))
                    sc = ('scale', str(self.scale))
                    pars = [center, size, sc]
                    url = 'http://maps.googleapis.com/maps/api/staticmap?' + '&'.join(['='.join(par) for par in pars + self.params])
                    googleresp = urllib.urlopen(url)
                    print googleresp.url
                    imag = googleresp.read()
                    im = Image.open(StringIO.StringIO(imag))
                    final.paste(im, (int(x*largura*self.scale), int(y*altura*self.scale)))
            zonename = 'zone_'+str(zonecount)
            final.save(zonename+'.bmp')
            del final
            print '\n'

    def latlontopixels(self, lat, lon, zoom):
        mx = (lon * self.ORIGIN_SHIFT) / 180.0
        my = log(tan((90 + lat) * pi/360.0))/(pi/180.0)
        my = (my * self.ORIGIN_SHIFT) / 180.0
        res = self.INITIAL_RESOLUTION / (2**zoom)
        px = (mx + self.ORIGIN_SHIFT) / res
        py = (my + self.ORIGIN_SHIFT) / res
        return px, py

    def pixelstolatlon(self, px, py, zoom):
        res = self.INITIAL_RESOLUTION / (2**zoom)
        mx = px * res - self.ORIGIN_SHIFT
        my = py * res - self.ORIGIN_SHIFT
        lat = (my / self.ORIGIN_SHIFT) * 180.0
        lat = 180 / pi * (2*atan(exp(lat*pi/180.0)) - pi/2.0)
        lon = (mx / self.ORIGIN_SHIFT) * 180.0
        return lat, lon

if __name__ == "__main__":
    worldmap = WorldMap()
    worldmap.get()
    print 'Done'
