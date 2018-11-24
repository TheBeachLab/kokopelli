import operator
from math import cos, sin, atan2, radians, degrees, sqrt

import koko.lib.shapes2d as s2d
from koko.lib.text import text
from numpy import *

class PCB(object):
    def __init__(self, x0, y0, width, height, chamfer_distance=0):
        self.x0 = x0
        self.y0 = y0
        self.width = width
        self.height = height

        self.components  = []
        self.connections = []
        self._cutout = None
        self.custom_cutout = None
        self.custom_layers = {}
        self.chamfer_distance = chamfer_distance

    @property
    def traces(self):
        L = [c.pads for c in self.components if c.side == 0] + [c.traces[0] for c in self.connections]
        if L:
            t = reduce(operator.add, L)
            #L = [c.holes for c in self.components if c.holes is not None]
            #L.extend([c.holes for c in self.connections if c.holes is not None])
            #if L:
            #    t = t - reduce(operator.add,L)
            return t
        else: return None
    @property
    def traces_other_side(self):
        L = [c.pads for c in self.components if c.side == 1] + [c.traces[1] for c in self.connections if c.traces[1] is not None]
        if L:
            t = reduce(operator.add, L)
            #L = [c.holes for c in self.components if c.holes is not None]
            #L.extend([c.holes for c in self.connections if c.holes is not None])
            #if L:
            #    t = t - reduce(operator.add,L)
            return t
        else: return None        
    @property
    def holes(self):
        L = [c.holes for c in self.components if c.holes is not None]
        L.extend([c.holes for c in self.connections if c.holes is not None])
        if L:
            t = reduce(operator.add,L)  
            return t
        else:
            return None

    @property
    def part_labels_top(self):
        L = [c.label for c in self.components if c.label is not None and c.side==0]
        return reduce(operator.add, L) if L else None
    @property
    def part_labels_bot(self):
        L = [c.label for c in self.components if c.label is not None and c.side==1]
        return reduce(operator.add, L) if L else None
    @property
    def part_shadows_top(self):
        L = [c.shadow_shape for c in self.components if c.shadow_shape is not None and c.side==0]
        return reduce(operator.add, L) if L else None 
    @property
    def part_shadows_bot(self):
        L = [c.shadow_shape for c in self.components if c.shadow_shape is not None and c.side==1]
        return reduce(operator.add, L) if L else None        
    @property
    def pin_labels_top(self):
        L = [c.pin_labels for c in self.components if c.pin_labels is not None and c.side==0]
        return reduce(operator.add, L) if L else None
    @property
    def pin_labels_bot(self):
        L = [c.pin_labels for c in self.components if c.pin_labels is not None and c.side==1]
        return reduce(operator.add, L) if L else None

    @property
    def cutout(self):
        if self.custom_cutout is not None:    
            if self.holes:
                return self.custom_cutout - self.holes
            else: 
                return self.custom_cutout 
        outer = s2d.rectangle(self.x0, self.x0 + self.width,
                             self.y0, self.y0 + self.height)
        if self.chamfer_distance:
            c = self.chamfer_distance
            c1 = s2d.triangle(self.x0,self.y0,self.x0,self.y0+c,self.x0+c,self.y0)
            c2 = s2d.triangle(self.x0+self.width,self.y0+self.height, self.x0+self.width, self.y0+self.height-c, self.x0+self.width-c, self.y0+self.height)
            c3 = s2d.triangle(self.x0,self.y0+self.height, self.x0+c, self.y0+self.height, self.x0, self.y0+self.height-c)
            c4 = s2d.triangle(self.x0+self.width,self.y0, self.x0+self.width-c, self.y0, self.x0+self.width, self.y0+c)
            outer -= c1+c2+c3+c4
        #L = [c.holes for c in self.components if c.holes is not None]
        #L.extend([c.holes for c in self.connections if c.holes is not None])
        return outer - self.holes if self.holes else outer

    #@property
    def layout(self,sides=[0,1]):
        T = []
        if 0 in sides:
            if self.part_labels_top:
                T.append(s2d.color(self.part_labels_top, (125, 200, 60)))
            if self.pin_labels_top:
                T.append(s2d.color(self.pin_labels_top, (255, 90, 60)))
            if self.traces:
                T.append(s2d.color(self.traces-self.holes, (125, 90, 60)))
            if self.part_shadows_top:
                T.append(s2d.color(self.part_shadows_top-self.holes,(55,55,60)))
        if 1 in sides:
            if self.part_labels_bot:
                T.append(s2d.color(self.part_labels_bot, (90, 60, 255)))
            if self.pin_labels_bot:
                T.append(s2d.color(self.pin_labels_bot, (175, 30, 175)))
            if self.traces_other_side:
                T.append(s2d.color(self.traces_other_side-self.holes, (90, 60, 125)))
            if self.part_shadows_bot:
               T.append(s2d.color(self.part_shadows_bot-self.holes,(45, 30, 62)))
        
        for v in sorted(self.custom_layers.values(),key=lambda v: -v['position']):
            if v['visible']: T.append(s2d.color(v['layer'],v['color']))
        T.append(s2d.color(self.cutout, (35,35,40)))
        return T


    def __iadd__(self, rhs):
        if isinstance(rhs, Component):
            self.components.append(rhs)
        elif isinstance(rhs, Connection):
            self.connections.append(rhs)
        else:
            raise TypeError("Invalid type for PCB addition (%s)" % type(rhs))
        return self

    def add_custom_layer(self,name,layer,color):
        self.custom_layers[name] = {'layer':layer,'color':color,'position':len(self.custom_layers),'visible':1}
    def hide_layer(self,name):
        self.custom_layers[name]['visible'] = 0

    def connectH(self, *args, **kwargs):
        ''' Connects a set of pins or points, traveling first
            horizontally then vertically
        '''
        width = kwargs['width'] if 'width' in kwargs else 0.016
        mode = kwargs['mode'] if 'mode' in kwargs else 'explicit'
        sides = kwargs['sides'] if 'sides' in kwargs else [0 for a in args[:-1]]
        new_sides = []
        points = []
        args = list(args)
        for i,p in enumerate(args):
            if not isinstance(p,BoundPin):
                if mode=='diff':
                    args[i] = Point(args[i-1].x+p[0],args[i-1].y+p[1])
                elif mode=='explicit':
                    args[i] = Point(*p)
                else:
                    raise NotImplementedError("Unknown mode type %s"%mode)
        for A, B, s in zip(args[:-1], args[1:], sides):
            points.append(A); new_sides.append(s)
            if (A.x != B.x):
                points.append(Point(B.x, A.y)); new_sides.append(s)
        if A.y != B.y:  points.append(B)
        c = Connection(width, *points, sides=new_sides)
        self.connections.append(c)
        return c

    def connectV(self, *args, **kwargs):
        ''' Connects a set of pins or points, travelling first
            vertically then horizontally.
        '''
        width = kwargs['width'] if 'width' in kwargs else 0.016
        mode = kwargs['mode'] if 'mode' in kwargs else 'explicit'
        sides = kwargs['sides'] if 'sides' in kwargs else [0 for a in args[:-1]]
        new_sides = []
        points = []
        args = list(args)
        for i,p in enumerate(args):
            if not isinstance(p,BoundPin):
                if mode=='diff':
                    args[i] = Point(args[i-1].x+p[0],args[i-1].y+p[1])
                elif mode=='explicit':
                    args[i] = Point(*p)
                else:
                    raise NotImplementedError("Unknown mode type %s"%mode)
        for A, B, s in zip(args[:-1], args[1:], sides):
            points.append(A); new_sides.append(s)
            if (A.y != B.y):
                points.append(Point(A.x, B.y)); new_sides.append(s)
        if A.x != B.x:  points.append(B)
        c = Connection(width, *points, sides=new_sides)
        self.connections.append(c)
        return c

    def connectD(self, *args, **kwargs):
        ''' Connects a set of pins or points, travelling first
            diagonally then horizontally or vertically, depending on geometry.
        '''
        width = kwargs['width'] if 'width' in kwargs else 0.016
        sides = kwargs['sides'] if 'sides' in kwargs else [0 for a in args[:-1]]
        new_sides = []
        points = []
        def sgn(x): 
            if x>=0: 
                return 1 
            else:
                return -1
        args = list(args)
        for i,p in enumerate(args):
            if not isinstance(p,BoundPin):
                args[i] = Point(*p)
        for A, B, s in zip(args[:-1], args[1:], sides):
            points.append(A); new_sides.append(s)
            if (B.y-A.y != B.x-A.x):
                if abs(B.y-A.y) > abs(B.x-A.x):
                    points.append(Point(B.x, A.y+sgn(B.y-A.y)*abs(B.x-A.x))); new_sides.append(s)
                else:
                    points.append(Point(A.x+sgn(B.x-A.x)*abs(B.y-A.y),B.y)); new_sides.append(s)                    
        if (A.x != B.x) or (A.y != B.y):  points.append(B)
        c = Connection(width, *points, sides=new_sides)
        self.connections.append(c)
        return c


################################################################################

class Component(object):
    ''' Generic PCB component.
    '''
    def __init__(self, x, y, rot=0, name='',label_size=0.05, side=0):
        ''' Constructs a Component object
                x           X position
                y           Y position
                rotation    angle (degrees)
                name        String
                side        which side of board 0 for top, 1 for bottom
        '''
        self.x = x
        self.y = y
        self.rot   = rot
        self.name = name
        self.label_size = label_size
        self.side = side
        if self.side == 1:
            self.pins = [p.mirror_x()  for p in self.pins]
            self.vias = [v.mirror_x()  for v in self.vias]

    def __getitem__(self, i):
        if isinstance(i, str):
            try:
                pin = [p for p in self.pins if p.name == i][0]
            except IndexError:
                raise IndexError("No pin with name %s" % i)
        elif isinstance(i, int):
            try:
                pin = self.pins[i-1]
            except IndexError:
                raise IndexError("Pin %i is not in array" %i)
        return BoundPin(pin, self)

    @property
    def pads(self):
        pads = reduce(operator.add, [p.pad for p in self.pins])
        return s2d.move(s2d.rotate(pads, self.rot), self.x, self.y)

    @property
    def holes(self):
        if self.vias:
            holes = reduce(operator.add,[v.hole for v in self.vias])
            return s2d.move(s2d.rotate(holes,self.rot), self.x, self.y)
        else: return None

    @property
    def pin_labels(self):
        L = []
        for p in self.pins:
            p = BoundPin(p, self)
            if p.pin.name:
                t = s2d.rotate(text(p.pin.name, 0, 0, p.pin.label_size),self.rot+p.pin.label_rot)
                L.append(s2d.move(t, p.x, p.y))
        return reduce(operator.add, L) if L else None

    @property
    def label(self):
        return text(self.name, self.x, self.y, self.label_size)
    @property
    def shadow_shape(self):
        try:
            return s2d.move(s2d.rotate(self.shadow, self.rot),self.x, self.y)
        except AttributeError:
            return None

################################################################################

class Pin(object):
    ''' PCB pin, with name, shape, and position
    '''
    def __init__(self, x, y, shape, name='', label_size=.03, label_rot=0):
        self.x      = x
        self.y      = y
        self.shape  = shape
        self.name   = name
        self.label_size   = label_size
        self.label_rot   = label_rot

    @property
    def pad(self):
        return s2d.move(self.shape, self.x, self.y)

    def mirror_x(self):
        return Pin( -self.x, self.y, self.shape, self.name, label_size=self.label_size, label_rot=self.label_rot )

################################################################################

class Via(object):
    ''' PCB via, with shape, and position
    '''
    def __init__(self, x, y, shape):
        self.x      = x
        self.y      = y
        self.shape  = shape

    @property
    def hole(self):
        return s2d.move(self.shape, self.x, self.y)

    def mirror_x(self):
        return Via( -self.x, self.y, self.shape )

################################################################################

class BoundPin(object):
    ''' PCB pin localized to a specific component
        (so that it has correct x and y positions)
    '''
    def __init__(self, pin, component):
        self.pin = pin
        self.component = component

    @property
    def x(self):
        return (cos(radians(self.component.rot)) * self.pin.x -
                sin(radians(self.component.rot)) * self.pin.y +
                self.component.x)

    @property
    def y(self):
        return (sin(radians(self.component.rot)) * self.pin.x +
                cos(radians(self.component.rot)) * self.pin.y +
                self.component.y)
    @property
    def point(self):
        return Point(self.x,self.y)
################################################################################

class Point(object):
    ''' Object with x and y member variables
    '''
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __iter__(self):
        return iter([self.x, self.y])
    def __add__(self, p):
        return Point(self.x+p.x,self.y+p.y)
    def __sub__(self, p):
        return Point(self.x-p.x,self.y-p.y)
    def __rmul__(self,a):
        return Point(a*self.x,a*self.y)
    def magnitude(self):
        return sqrt(self.x*self.x + self.y+self.y)
    def normalized(self):
        return Point(self.x/self.magnitude(), self.y/self.magnitude())
    @property
    def point(self):
        return self

################################################################################

class Connection(object):
    ''' Connects two pins via a series of intermediate points
    '''
    def __init__(self, width, *args, **kwargs):
        self.width = width
        self.points = [
            a if isinstance(a, BoundPin) else Point(*a) for a in args
        ]
        self.sides = kwargs['sides'] if 'sides' in kwargs else [0 for a in args[:-1]] #0 is base side, 1 is other side
        self.holes = None
        self.jumpers = []
    
    def add_jumper(self,p,rot=0,width=.12, height=.07,thick=.05):
        self.jumpers.append((p,rot,width,height,thick))
        return self

    def cut_corners(self,idx):
        for i in idx:
            i,v = i #unpack index and distance
            assert(i>0) #start corner numbering at 1
            assert(i<len(self.points)) #no corner to cut at end
            d = lambda p,q: sqrt( (p.x-q.x)**2 + (p.y-q.y)**2 )
            dm = d(self.points[i],self.points[i-1])
            dp = d(self.points[i],self.points[i+1])
            #if dm > dp:
            self.points = self.points[:i] + \
                [Point(self.points[i].x-v/dm*(self.points[i].x-self.points[i-1].x ), self.points[i].y-v/dm*(self.points[i].y-self.points[i-1].y )),
                 Point(self.points[i].x+v/dp*(self.points[i+1].x-self.points[i].x ), self.points[i].y+v/dp*(self.points[i+1].y-self.points[i].y ))
                ] + \
                self.points[i+1:]
            self.sides.insert(i,self.sides[i])
            #else:
            #    self.points[i] = self.points[i] - dm/dp*(self.points[i]-self.points[i+1])
        return self

    @property
    def traces(self):
        #_pad_1206 = s2d.rectangle(-0.025, 0.025, -0.034, 0.034)
        _pad_via = s2d.circle(0,0,.025) #s2d.rectangle(-0.025, 0.025, -0.025, 0.025)
        _hole_via = s2d.circle(0,0,.016)
        jumper_cuts = []
        jumper_pads = []
        for p,r,w,h,t in self.jumpers:
            _jumper_pad  = s2d.move(s2d.rectangle(-.5*t, .5*t, -.5*h, .5*h),-.5*w,0)
            _jumper_pad += s2d.move(s2d.rectangle(-.5*t, .5*t, -.5*h, .5*h), .5*w,0)
            _cut = s2d.rectangle(-.5*w,.5*w,-.5*h,.5*h)
            jumper_cuts.append(s2d.move(s2d.rotate(_cut,r),p[0],p[1]))
            jumper_pads.append(s2d.move(s2d.rotate(_jumper_pad,r),p[0],p[1]))
        t = [[],[]]
        for p1, p2, side in zip(self.points[:-1], self.points[1:], self.sides):
            d = sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
            if p2 != self.points[-1]:
                d += self.width/2
            a = atan2(p2.y - p1.y, p2.x - p1.x)
            r = s2d.rounded_rectangle(0, d, -self.width/2, self.width/2,1.)
            t[side].append(s2d.move(s2d.rotate(r, degrees(a)), p1.x, p1.y))
        try:
            result0 = reduce(operator.add, t[0])
        except TypeError:
            result0 = None
        try:
            result1 = reduce(operator.add, t[1])
        except TypeError:
            result1 = None
        #calculate locations for via holes and pads
        for s1,s2,p in zip(self.sides[:-1],self.sides[1:],self.points[1:-1]):
            if s1!=s2:
                result0 += s2d.move(_pad_via,p.x,p.y)
                result1 += s2d.move(_pad_via,p.x,p.y)
                self.holes += s2d.move(_hole_via,p.x,p.y)
        if len(self.jumpers)!=0:
            result0 -= reduce(operator.add,jumper_cuts)
            result0 += reduce(operator.add,jumper_pads)
        return result0, result1

################################################################################
# Discrete passive components
################################################################################

_pad_1206 = s2d.rectangle(-0.032, 0.032, -0.034, 0.034)

class R_1206(Component):
    ''' 1206 Resistor
    '''
    pins = [Pin(-0.06, 0, _pad_1206), Pin(0.06, 0, _pad_1206)]
    prefix = 'R'
    vias = []


class C_1206(Component):
    ''' 1206 Capacitor
    '''
    pins = [Pin(-0.06, 0, _pad_1206), Pin(0.06, 0, _pad_1206)]
    prefix = 'C'
    vias = []

_pad_0805 = s2d.rectangle(-.023,.023, -.027, .027)

class R_0805(Component):
    ''' 0805 Resistor
    '''
    pins = [Pin(-0.04, 0, _pad_0805), Pin(0.04, 0, _pad_0805)]
    prefix = 'R'
    vias = []


class C_0805(Component):
    ''' 0805 Capacitor
    '''
    pins = [Pin(-0.04, 0, _pad_0805), Pin(0.04, 0, _pad_0805)]
    prefix = 'C'
    vias = []


_pad_SJ = s2d.rectangle(-0.02, 0.02, -0.03, 0.03)
class SJ(Component):
    ''' Solder jumper
    '''
    pins = [Pin(-0.029, 0, _pad_SJ), Pin(0.029, 0, _pad_SJ)]
    prefix = 'SJ'
    vias = []

_pad_SOD_123 = s2d.rectangle(-0.02, 0.02, -0.024, 0.024)
class D_SOD_123(Component):
    ''' Diode
    '''
    pins = [Pin(-0.07, 0, _pad_SOD_123, 'A'),
            Pin(0.07, 0, _pad_SOD_123, 'C')]
    prefix = 'D'
    vias = []


################################################################################
# Connectors
################################################################################

_pad_USB_trace = s2d.rectangle(-0.0075, 0.0075, -0.04, 0.04)
_pad_USB_foot  = s2d.rectangle(-0.049, 0.049, -0.043, 0.043)
class USB_mini_B(Component):
    ''' USB mini B connector
        Hirose UX60-MB-5ST
    '''
    pins = [
        Pin(0.063,   0.24, _pad_USB_trace, 'G'),
        Pin(0.0315,  0.24, _pad_USB_trace),
        Pin(0,       0.24, _pad_USB_trace, '+'),
        Pin(-0.0315, 0.24, _pad_USB_trace, '-'),
        Pin(-0.063,  0.24, _pad_USB_trace, 'V'),

        Pin( 0.165, 0.21, _pad_USB_foot),
        Pin(-0.165, 0.21, _pad_USB_foot),
        Pin( 0.165, 0.0, _pad_USB_foot),
        Pin(-0.165, 0.0, _pad_USB_foot)
    ]
    prefix = 'J'
    vias = []

_pad_header  = s2d.rectangle(-0.06, 0.06, -0.025, 0.025)
_pad_header_skinny  = s2d.rectangle(-0.06, 0.06, -0.020, 0.020)
class Header_4(Component):
    ''' 4-pin header
        fci 95278-101a04lf bergstik 2x2x0.1
    '''
    pins = [
        Pin(-0.107,  0.05, _pad_header),
        Pin(-0.107, -0.05, _pad_header),
        Pin( 0.107, -0.05, _pad_header),
        Pin( 0.107,  0.05, _pad_header)
    ]
    prefix = 'J'
    vias = []

class Header_4_skinny(Component):
    ''' 4-pin header
        fci 95278-101a04lf bergstik 2x2x0.1
    '''
    pins = [
        Pin(-0.107,  0.05, _pad_header_skinny),
        Pin(-0.107, -0.05, _pad_header_skinny),
        Pin( 0.107, -0.05, _pad_header_skinny),
        Pin( 0.107,  0.05, _pad_header_skinny)
    ]
    prefix = 'J'
    vias = []

class Header_Power(Component):
    ''' 4-pin header
        fci 95278-101a04lf bergstik 2x2x0.1
    '''
    pins = [
        Pin(-0.107,  0.05, _pad_header,"V"),
        Pin(-0.107, -0.05, _pad_header,"GND"),
        Pin( 0.107, -0.05, _pad_header),
        Pin( 0.107,  0.05, _pad_header)
    ]
    prefix = 'J'
    vias = []

class Header_ISP(Component):
    ''' ISP programming header
        FCI 95278-101A06LF Bergstik 2x3x0.1
    '''
    pins = [
        Pin(-0.107, 0.1,  _pad_header, 'GND'),
        Pin(-0.107, 0,    _pad_header, 'MOSI'),
        Pin(-0.107, -0.1, _pad_header, 'V'),
        Pin( 0.107, -0.1, _pad_header, 'MISO'),
        Pin( 0.107, 0,    _pad_header, 'SCK'),
        Pin( 0.107, 0.1,  _pad_header, 'RST')
    ]
    prefix = 'J'
    vias = []

class Header_ISP_skinny(Component):
    ''' ISP programming header
        FCI 95278-101A06LF Bergstik 2x3x0.1
    '''
    pins = [
        Pin(-0.107, 0.1,  _pad_header_skinny, 'GND'),
        Pin(-0.107, 0,    _pad_header_skinny, 'MOSI'),
        Pin(-0.107, -0.1, _pad_header_skinny, 'V'),
        Pin( 0.107, -0.1, _pad_header_skinny, 'MISO'),
        Pin( 0.107, 0,    _pad_header_skinny, 'SCK'),
        Pin( 0.107, 0.1,  _pad_header_skinny, 'RST')
    ]
    prefix = 'J'
    vias = []
    #shadow = s2d.rectangle(-.06,8/25.4,-.325,.325)


class Header_FTDI(Component):
    ''' FTDI cable header
    '''
    pins = [
        Pin(0,  0.25, _pad_header, 'GND'),
        Pin(0,  0.15, _pad_header, 'CTS'),
        Pin(0,  0.05, _pad_header, 'VCC'),
        Pin(0, -0.05, _pad_header, 'TX'),
        Pin(0, -0.15, _pad_header, 'RX'),
        Pin(0, -0.25, _pad_header, 'RTS')
    ]
    prefix = 'J'
    vias = []
    shadow = s2d.rectangle(-.06,8/25.4,-.325,.325)

class Header_FTDI_skinny(Component):
    ''' FTDI cable header
    '''
    pins = [
        Pin(0,  0.25, _pad_header_skinny, 'GND'),
        Pin(0,  0.15, _pad_header_skinny, 'CTS'),
        Pin(0,  0.05, _pad_header_skinny, 'VCC'),
        Pin(0, -0.05, _pad_header_skinny, 'TX'),
        Pin(0, -0.15, _pad_header_skinny, 'RX'),
        Pin(0, -0.25, _pad_header_skinny, 'RTS')
    ]
    prefix = 'J'
    vias = []
    shadow = s2d.rectangle(-.06,8/25.4,-.325,.325)


class ScrewTerminal(Component):
    pitch = .131
    _pad = s2d.rectangle(-0.04, 0.04, -0.04, 0.04)
    _via = s2d.circle(0,0,.025)  
    pins = [Pin(-.5*pitch,0,_pad),Pin(.5*pitch,0,_pad)]
    vias = [Via(-.5*pitch,0,_via),Via(.5*pitch,0,_via)]
    shadow = s2d.rectangle(-3.5/25.4,3.5/25.4,-3/25.4,3/25.4)

class ScrewTerminal3(Component):
    pitch = .131
    _pad = s2d.rectangle(-0.04, 0.04, -0.04, 0.04)
    _via = s2d.circle(0,0,.025)  
    pins = [Pin(-pitch,0,_pad),Pin(0,0,_pad),Pin(pitch,0,_pad)]
    vias = [Via(-pitch,0,_via),Via(0,0,_via),Via(pitch,0,_via)]
    shadow = s2d.rectangle(-5.35/25.4,5.35/25.4,-3/25.4,3/25.4)

class JST_2(Component):
    pitch = 2./25.4
    _pad = s2d.rectangle(-0.5/25.4,0.5/25.4, -1.75/25.4, 1.75/25.4)
    _pad2 = s2d.rectangle(-.75/25.4,.75/25.4,-1.7/25.4,1.7/25.4)
    y2 = -4.55/25.4
    pins = [Pin(-.5*pitch,0,_pad,'VCC'),Pin(.5*pitch,0,_pad,'GND'),Pin(-.5*pitch-2.35/25.4,y2,_pad2),Pin(.5*pitch+2.35/25.4,y2,_pad2)]
    vias = []
    shadow = s2d.rectangle(-3.95/25.4,3.95/25.4,y2-1.7/25.4,1.75/25.4)

################################################################################
# SOT-23 components
################################################################################

_pad_SOT23 = s2d.rectangle(-.02,.02,-.012,.012)
class NMOS_SOT23(Component):
    ''' NMOS transistor in SOT23 package
        Fairchild NDS355AN
    '''
    pins = [
        Pin(0.045, -0.0375, _pad_SOT23,'G'),
        Pin(0.045,  0.0375, _pad_SOT23,'S'),
        Pin(-0.045, 0, _pad_SOT23,'D')
    ]
    prefix = 'Q'
    vias = []

class PMOS_SOT23(Component):
    ''' PMOS transistor in SOT23 package
        Fairchild NDS356AP
    '''
    pins = [
        Pin(-0.045, -0.0375, _pad_SOT23,'G'),
        Pin(-0.045,  0.0375, _pad_SOT23,'S'),
        Pin(0.045, 0, _pad_SOT23,'D')
    ]
    prefix = 'Q'
    vias = []

class Regulator_SOT23(Component):
    '''  SOT23 voltage regulator
    '''
    pins = [
        Pin(-0.045, -0.0375, _pad_SOT23,'Out'),
        Pin(-0.045,  0.0375, _pad_SOT23,'In'),
        Pin(0.045, 0, _pad_SOT23,'GND')
    ]
    prefix = 'U'
    vias = []

class Regulator_LM3480(Component):
    '''  SOT23 voltage regulator, LM3480
    '''
    pins = [
        Pin(-0.045, -0.0375, _pad_SOT23,'In'),
        Pin(-0.045,  0.0375, _pad_SOT23,'Out'),
        Pin(0.045, 0, _pad_SOT23,'GND')
    ]
    prefix = 'U'
    vias = []

###########
# H Bridge
############
_pad_SOIC = s2d.rectangle(-.041,.041,-.015,.015)
class A4953_SOICN(Component):
    pins = [
        Pin(-.11, .075,_pad_SOIC+s2d.circle(-.041,0,.015),"GND"),
        Pin(-.11, .025,_pad_SOIC,"IN2"),
        Pin(-.11,-.025,_pad_SOIC,"IN1"),
        Pin(-.11,-.075,_pad_SOIC,"VREF"),
        Pin( .11,-.075,_pad_SOIC,"VBB"),
        Pin( .11,-.025,_pad_SOIC,"OUT1"),
        Pin( .11, .025,_pad_SOIC,"LSS"),
        Pin( .11, .075,_pad_SOIC,"OUT2"),
        Pin( 0,0,s2d.rectangle(-.04,.04,-.075,.075),"")
    ]
    prefix = 'U'
    vias = []


################################################################################
#   Clock crystals
################################################################################
_pad_XTAL_NX5032GA = s2d.rectangle(-.039,.039,-.047,.047)

class XTAL_NX5032GA(Component):
    pins = [Pin(-0.079, 0, _pad_XTAL_NX5032GA),
            Pin(0.079, 0, _pad_XTAL_NX5032GA)]
    prefix = 'X'
    vias = []

################################################################################
# Atmel microcontrollers
################################################################################

_pad_SOIC = s2d.rectangle(-0.041, 0.041, -0.015, 0.015)
class ATtiny45_SOIC(Component):
    pins = []
    y = 0.075
    for t in ['NC', 'PB3', 'PB4', 'GND']:
        pins.append(Pin(-0.14, y, _pad_SOIC, t))
        y -= 0.05
    for p in ['PB0', 'PB1', 'PB2', 'VCC']:
        y += 0.05
        pins.append(Pin(0.14, y, _pad_SOIC, p))
    del y
    prefix = 'U'
    vias = []

class ATtiny44_SOIC(Component):
    pins = []
    y = 0.15
    for t in ['VCC', 'PB0', 'PB1', 'PB3', 'PB2', 'PA7', 'PA6']:
        pad = _pad_SOIC + s2d.circle(-0.041, 0, 0.015) if t == 'VCC' else _pad_SOIC
        pins.append(Pin(-0.12, y, pad, t))
        y -= 0.05
    for t in ['PA5', 'PA4', 'PA3', 'PA2', 'PA1', 'PA0', 'GND']:
        y += 0.05
        pins.append(Pin(0.12, y, _pad_SOIC, t))
    prefix = 'U'
    vias = []

_pad_TQFP_h = s2d.rectangle(-0.025, 0.025, -0.008, 0.008)
_pad_TQFP_v = s2d.rectangle(-0.008, 0.008, -0.025, 0.025)

class ATmega88_TQFP(Component):
    pins = []
    y = 0.1085
    for t in ['PD3', 'PD4', 'GND', 'VCC', 'GND', 'VCC', 'PB6', 'PB7']:
        pins.append(Pin(-0.18, y, _pad_TQFP_h, t))
        y -= 0.031
    x = -0.1085
    for t in ['PD5', 'PD6', 'PD7', 'PB0', 'PB1', 'PB2', 'PB3', 'PB4']:
        pins.append(Pin(x, -0.18, _pad_TQFP_v, t))
        x += 0.031
    y = -0.1085
    for t in ['PB5', 'AVCC', 'ADC6', 'AREF', 'GND', 'ADC7', 'PC0', 'PC1']:
        pins.append(Pin(0.18, y, _pad_TQFP_h, t))
        y += 0.031
    x = 0.1085
    for t in ['PC2', 'PC3', 'PC4', 'PC5', 'PC6', 'PD0', 'PD1', 'PD2']:
        pins.append(Pin(x, 0.18, _pad_TQFP_v, t))
        x -= 0.031
    del x, y
    prefix = 'U'
    vias = []


################################################################################
#   CBA logo
################################################################################
_pin_circle_CBA = s2d.circle(0, 0, 0.02)
_pin_square_CBA = s2d.rectangle(-0.02, 0.02, -0.02, 0.02)
class CBA(Component):
    pins = []
    for i in range(3):
        for j in range(3):
            pin = _pin_circle_CBA if i == 2-j and j >= 1 else _pin_square_CBA
            pins.append(Pin(0.06*(i-1), 0.06*(j-1), pin))
    vias = []



class ESP8266_03(Component):
    _pad = s2d.rectangle(-0.04, 0.04, -0.03, 0.03)
    _via = s2d.circle(0,0,.019)
    names = ['VCC','GPIO14','GPIO12','GPIO13','GPIO15','GPIO2','GPIO0',
        'WIFI_ANT','CH-PD','GPIO18','URXD','UTXD','NC','GND']
    w = 12.2/25.4
    l = 17.4/25.4
    wp = 12.2/25.4
    lp = .5
    dp = 2/25.4
    ys = arange(.5*lp-dp    ,-.5*lp-.001-dp,-dp)
    pts = vstack(( dstack((-.5*wp*ones_like(ys),ys))[0], dstack((.5*wp*ones_like(ys),ys))[0] ))
    pins = [Pin(p[0],p[1],_pad,n) for n,p in zip(names,pts)]
    vias = []#[Via(p[0],p[1],_via) for n,p in zip(names,pts)]
    shadow = s2d.rectangle(-.5*w,.5*w,-.5*l,.5*l)
    prefix = 'IC'  

class ZLDO1117(Component):
    '''3.3 V 1 A regulator, SOT223'''
    _pad1 = s2d.rectangle(-.6/25.4,.6/25.4,-.8/25.4,.8/25.4)
    _pad2 = s2d.rectangle(-1.65/25.4,1.65/25.4,-.6/25.4,.6/25.4)
    pins = [
        Pin(-2.3/25.4, -3.2/25.4, _pad1,'GND'),
        Pin(0, -3.2/25.4, _pad1,'Vout'),
        Pin(2.3/25.4, -3.2/25.4, _pad1,'Vin'),
        Pin(0, 3.2/25.4, _pad2,'Vout2'),
    ]
    prefix = 'U'
    vias = []

class AstarMicro(Component):
    ''' Polulo Astar micro
    '''
    _pad = s2d.rectangle(-0.04, 0.04, -0.025, 0.025)
    _via = s2d.circle(0,0,.019)
    #flip names since through hole
    names = [
        'VIN','GND','5V','3v3','RST','12/A11/PWM','11','10/A10/PWM','A1','A0',
        '9/A9/PWM','8/A8','7','6/A7/PWM','5/PWM','4/A6','3/PWM','2','1','0']
    w = .6
    l = 1.
    wp = .5
    lp = .9
    ys = arange(.5*lp,-.5*lp-.001,-.1)
    os = 0*.13*(arange(shape(ys)[0])%2-.5)
    pts = vstack(( dstack((-.5*wp*ones_like(ys)+os,ys[::-1]))[0], dstack((.5*wp*ones_like(ys)-os,ys))[0] ))
    pins = [Pin(p[0],p[1],_pad,n) for n,p in zip(names,pts)]
    vias = [Via(p[0],p[1],_via) for n,p in zip(names,pts)]
    shadow = s2d.rectangle(-.5*w,.5*w,-.5*l,.5*l)
    prefix = 'IC'

class Header_bldc_skinny(Component):
    ''' brushless motor logic
    '''
    _pad_header_skinny  = s2d.rectangle(-0.06, 0.06, -0.020, 0.020)
    pins = [
        Pin(0,  0.1, _pad_header_skinny, 'GND'),
        Pin(0, -0.0, _pad_header_skinny, 'VCC'),
        Pin(0, -0.1, _pad_header_skinny, 'RC')
    ]
    prefix = 'J'
    shadow = s2d.rectangle(-.06,8/25.4,-.325,.325)
    vias = []


class A4988_Carrier(Component):
    '''  Stepper driver carrier black from pololu
    '''
    _pad = s2d.rectangle(-0.04, 0.04, -0.028, 0.028)
    _via = s2d.circle(0,0,.019)
    names = ['VMOT','GMOT','2B','2A','1A','1B','VDD','GND','DIR','STEP','SLP','RST','MS3','MS2','MS1','EN']
    ys = arange(.4,-.4+.001,-.1)-.05    
    pts = vstack(( dstack((-.25*ones_like(ys),ys))[0], dstack((.25*ones_like(ys),ys[::-1]))[0] ))
    pins = [Pin(p[0],p[1],_pad,n) for n,p in zip(names,pts)]
    vias = [Via(p[0],p[1],_via) for n,p in zip(names,pts)]
    prefix = 'IC'
    shadow = s2d.rectangle(-.3,.3,-.45,.45)




class CDRH2D18(Component):
    '''Power Inductor'''
    def chamfered_rectangle(x0,x1,y0,y1,c):
        r = s2d.rectangle(x0,x1,y0,y1)
        c1 = s2d.triangle(x0,y0,x0,y0+c,x0+c,y0)
        c2 = s2d.triangle(x1,y1, x1, y1-c, x1-c, y1)
        c3 = s2d.triangle(x0,y1, x0+c, y1, x0, y1-c)
        c4 = s2d.triangle(x1,y0, x1-c, y0, x1, y0+c)
        return r-c1-c2-c3-c4
    _pad = s2d.rectangle(-.65/25.4,.65/25.4,-.65/25.4,.65/25.4)
    pins = [Pin(-1.5/25.5,0,_pad), Pin(1.5/25.5,0,_pad)]
    vias = []
    shadow = s2d.rotate(chamfered_rectangle(-1.5/25.4,1.5/25.4,-1.5/25.4, 1.5/25.4,1/25.5),45)
    prefix='I'

class LTC35881(Component):
    ''' Energy Scavenger '''
    _pad  = s2d.rectangle(-.889/2/25.4, .889/2/25.4,-.25/2/25.4, .25/2/25.4)
    p = .5/25.4
    pins = [
        Pin(0, 0, s2d.rectangle(-1.68/2/25.4,1.68/2/25.4,-1.88/2/25.4,1.88/2/25.4), 'GND'),
        Pin(-2.1/25.4, 2*p,_pad,'PZ1',label_size=.015,label_rot=0),
        Pin(-2.1/25.4, 1*p,_pad,'PZ2',label_size=.015,label_rot=0),
        Pin(-2.1/25.4,   0,_pad,'CAP',label_size=.015,label_rot=0),
        Pin(-2.1/25.4,-1*p,_pad,'VIN',label_size=.015,label_rot=0),
        Pin(-2.1/25.4,-2*p,_pad,'SW',label_size=.015,label_rot=0),
        Pin(2.1/25.4, -2*p,_pad,'VOUT',label_size=.015,label_rot=0),
        Pin(2.1/25.4, -1*p,_pad,'VIN2',label_size=.015,label_rot=0),
        Pin(2.1/25.4,    0,_pad,'D1',label_size=.015,label_rot=0),
        Pin(2.1/25.4,  1*p,_pad,'D0',label_size=.015,label_rot=0),
        Pin(2.1/25.4,  2*p,_pad,'PGOOD',label_size=.015,label_rot=0)
    ]
    prefix = 'J'
    h = 2.9/25.4; w = 2.8/25.4;
    shadow = s2d.rectangle(-.5*w,.5*w,-.5*h,.5*h)
    vias = []    

class DSK414(Component):
    '''Dynacap, ELNA, 220mF'''
    pins = [
        Pin(0,5.15/25.4, s2d.rectangle(-2.4/25.4,2.4/25.4,-1./25.4,1/25.4),'+'),
        Pin(0,-5/25.4, s2d.rectangle(-2/25.4,2/25.4,-.85/25.4,.81/25.4),'-')
    ]
    vias = []
    shadow = s2d.rectangle(-2.5/25.4,2.5/25.4,-5.85/25.4, 6.15/25.4)
    shadow += s2d.circle(0,0,3.4/25.4)
    prefix='C'   

class EECRG(Component):
    '''Panasonic 1F, 3.6 V'''
    _pad = s2d.rectangle(-.02,.02,-.035,.035)
    pins = [
        Pin(-10/25.4, 0, _pad),
        Pin(10/25.4, 0, _pad)
    ]
    _via = s2d.rectangle(-.1/25.4,.1/25.4,-.5/25.4,.5/25.4)
    vias = [Via(p.x,p.y,_via) for p in pins]
    shadow = s2d.rectangle(0,0,0,0)
    prefix='C'

class EEE1EA101XP(Component):
    '''Panasonic 100uF, 25V'''
    _pad = s2d.rectangle(-.6/25.4,.6/25.4,-1.35/25.4,1.35/25.4)
    pins = [
        Pin(0, 2.2/25.4, _pad),
        Pin(0, -2.2/25.4, _pad)
    ]
    #_via = s2d.rectangle(-.1/25.4,.1/25.4,-.5/25.4,.5/25.4)
    vias = []
    def half_chamfered_rectangle(x0,x1,y0,y1,c):
        r = s2d.rectangle(x0,x1,y0,y1)
        c1 = s2d.triangle(x0,y0,x0,y0+c,x0+c,y0)
        c2 = s2d.triangle(x1,y1, x1, y1-c, x1-c, y1)
        c3 = s2d.triangle(x0,y1, x0+c, y1, x0, y1-c)
        c4 = s2d.triangle(x1,y0, x1-c, y0, x1, y0+c)
        return r-c1-c4
    shadow = half_chamfered_rectangle(-3.3/25.4,3.3/25.4,-3.3/25.4,3.3/25.4,1/25.4)
    prefix='C'


def chamfered_rectangle(x0,x1,y0,y1,c):
    r = s2d.rectangle(x0,x1,y0,y1)
    c1 = s2d.triangle(x0,y0,x0,y0+c,x0+c,y0)
    c2 = s2d.triangle(x1,y1, x1, y1-c, x1-c, y1)
    c3 = s2d.triangle(x0,y1, x0+c, y1, x0, y1-c)
    c4 = s2d.triangle(x1,y0, x1-c, y0, x1, y0+c)
    return r-c1-c2-c3-c4

