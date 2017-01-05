# !/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
from PIL import Image
import StringIO
from math import pi, log, tan, atan, exp, ceil
from operator import sub, div
from pprint import pprint


def factors(n):
    result = set()
    for i in range(1, int(n ** 0.5) + 1):
        div, mod = divmod(n, i)
        if mod == 0:
            result |= {i, div}
    return result


def closest(number, li):
    return min(li, key=lambda x: abs(x-number))


class WorldMap(object):
    """Styled GMap Object
    ::topleft: tuple of coordinates
    ::bottomright: tuple of coordinates
    ::name: name of the style
    ::params: Google Maps API style
    ::zoom: well.. the map zoom"""
    EARTH_RADIUS = 6378137
    EQUATOR_CIRCUMFERENCE = 2 * pi * EARTH_RADIUS
    INITIAL_RESOLUTION = EQUATOR_CIRCUMFERENCE / 256.0
    ORIGIN_SHIFT = EQUATOR_CIRCUMFERENCE / 2.0

    apikey = 'I am an API key'

    max_delta = 45

    def __init__(self, topleft, bottomright, name, params, zoom=6):
        super(WorldMap, self).__init__()
        self.topleft = topleft
        self.bottomright = bottomright
        self.name = name
        self.params = [('zoom', str(zoom)), ('key', self.apikey)] + params
        self.zoom = zoom
        bigzone_delta = tuple(map(abs, map(sub, bottomright, topleft)))
        if min(bigzone_delta) > self.max_delta:
            zone_sizes = tuple((closest(self.max_delta, facts) for facts in map(factors, bigzone_delta)))
            self.zone_n = map(div, bigzone_delta, zone_sizes)
            x_steps = [(zone_sizes[1] * z) + topleft[1] for z in range(0, self.zone_n[1]+1)]
            y_steps = [(zone_sizes[0] * z) + bottomright[0] for z in range(0, self.zone_n[0]+1)]
            self.zones = [[((y, x), (y-zone_sizes[0], x+zone_sizes[1])) for x in x_steps[:-1]] for y in reversed(y_steps[1:])]
        else:
            self.zones = [(topleft, bottomright)]
        self.scale = 2

    def get(self):
        print 'Starting image download'
        zonecount = 0
        tilescount = 0
        for zoney in range(self.zone_n[0]):
            for zonex in range(self.zone_n[1]):
                zone = self.zones[zoney][zonex]
                zonecount += 1
                print 'Processing Zone %d - from %s to %s' % (zonecount, zone[0], zone[1])
                upperleft, lowerright = zone[0], zone[1]
                ullat, ullon = map(float, upperleft)
                lrlat, lrlon = map(float, lowerright)
                ulx, uly = self.latlontopixels(ullat, ullon, self.zoom)
                lrx, lry = self.latlontopixels(lrlat, lrlon, self.zoom)
                dx, dy = lrx - ulx, uly - lry
                cols, rows = int(ceil(dx/640)), int(ceil(dy/400))
                bottom = 120
                largura = int(ceil(dx/cols))
                altura = int(ceil(dy/rows))
                alturaplus = altura + bottom
                if zonecount == 1:
                    dx_final, dy_final = int(dx)*self.zone_n[1], int(dy)*self.zone_n[0]
                    largura_final = int(dx_final/self.zone_n[1])
                    altura_final = int(dy_final/self.zone_n[0])
                    final_img = Image.new("RGB", (int(dx_final)*self.scale, int(dy_final)*self.scale))
                zone_img = Image.new("RGB", (int(dx)*self.scale, int(dy)*self.scale))
                p = 0
                for x in range(cols):
                    for y in range(rows):
                        tilescount += 1
                        p += 1
                        print '%d ' % (p),
                        dxn = largura * (0.5 + x)
                        dyn = altura * (0.5 + y)
                        latn, lonn = self.pixelstolatlon(ulx + dxn, uly - dyn - bottom/2, self.zoom)
                        center = ('center', ','.join((str(latn), str(lonn))))
                        size = ('size', '%dx%d' % (largura, alturaplus))
                        sc = ('scale', str(self.scale))
                        pars = [center, size, sc]
                        url = 'http://maps.googleapis.com/maps/api/staticmap?' + '&'.join(['='.join(par) for par in pars + self.params])
                        googleresp = urllib.urlopen(url)
                        print googleresp.code,
                        imag = googleresp.read()
                        im = Image.open(StringIO.StringIO(imag))
                        zone_img.paste(im, (int(x*largura*self.scale), int(y*altura*self.scale)))
                print '\n'
                final_img.paste(zone_img, (int(zonex*largura_final*self.scale), int(zoney*altura_final*self.scale)))
                del zone_img
                print '\n'
        print 'Saving big map...'
        final_img.save(self.name + '.png')
        print 'Saved'
        print '%d zones processed, %d tiles downloaded' % (zonecount, tilescount)

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

styles = {
          'borders': [('maptype', 'roadmap'),
                      ('style', 'feature:landscape|color:0xffffff'),
                      ('style', 'feature:water|color:0xffffff'),
                      ('style', 'feature:administrative|element:labels|visibility:off'),
                      ('style', 'feature:poi|visibility:off'),
                      ('style', 'feature:road|visibility:off')
                      ],
          'terrain': [('maptype', 'terrain'),
                      ('style', 'element:labels|visibility:off'),
                      ('style', 'feature:administrative|visibility:off'),
                      ('style', 'feature:water|color:#000000'),
                      ('style', 'feature:poi|visibility:off'),
                      ('style', 'feature:landscape|element:geometry.fill|color:#ffffff'),
                      ('style', 'feature:road|visibility:off')
                      ],
          'labels':  [('maptype', 'roadmap'),
                      ('style', 'feature:administrative|element:geometry|visibility:off'),
                      ('style', 'feature:landscape|color:0xffffff'),
                      ('style', 'feature:road|visibility:off'),
                      ('style', 'feature:poi|visibility:off'),
                      ('style', 'feature:water|color:0xffffff')
                      ],
          'water':   [('maptype', 'terrain'),
                      ('style', 'feature:administrative|element:geometry|visibility:off'),
                      ('style', 'feature:landscape|color:#000000'),
                      ('style', 'feature:road|visibility:off'),
                      ('style', 'feature:poi|visibility:off'),
                      ('style', 'feature:water|element:labels|visibility:off')
                      ],
          'contrast':[('style', 'color:#000000'),
                      ('style', 'element:labels|visibility:off'),
                      ('style', 'feature:water|color:0xffffff')
                      ]
        }


if __name__ == "__main__":
    for gmap, pars in styles.iteritems():
        worldmap = WorldMap((74, -180), (-60, 180), gmap, pars, 6)
        worldmap.get()
