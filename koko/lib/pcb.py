import operator
from math import cos, sin, atan2, radians, degrees, sqrt

import koko.lib.shapes2d as s2d
from koko.lib.text import text

class PCB(object):
    def __init__(self, x0, y0, width, height):
        self.x0 = x0
        self.y0 = y0
        self.width = width
        self.height = height

        self.components  = []
        self.connections = []

        self._cutout = None

    @property
    def traces(self):
        L = [c.pads for c in self.components] + [c.traces for c in self.connections]
        shape = reduce(operator.add, L) if L else None
        shape.bounds = self.cutout.bounds
        return shape

    @property
    def part_labels(self):
        L = [c.label for c in self.components if c.label is not None]
        shape = reduce(operator.add, L) if L else None
        shape.bounds = self.cutout.bounds
        return shape

    @property
    def pin_labels(self):
        L = [c.pin_labels for c in self.components if c.pin_labels is not None]
        shape = reduce(operator.add, L) if L else None
        shape.bounds = self.cutout.bounds
        return shape

    @property
    def layout(self):
        T = []
        if self.part_labels:
            T.append(s2d.color(self.part_labels, (125, 200, 60)))
        if self.pin_labels:
            T.append(s2d.color(self.pin_labels, (255, 90, 60)))
        if self.traces:
            T.append(s2d.color(self.traces, (125, 90, 60)))
        return T

    @property
    def cutout(self):
        if self._cutout is not None:    return self._cutout
        return s2d.rectangle(self.x0, self.x0 + self.width,
                             self.y0, self.y0 + self.height)

    def __iadd__(self, rhs):
        if isinstance(rhs, Component):
            self.components.append(rhs)
        elif isinstance(rhs, Connection):
            self.connections.append(rhs)
        else:
            raise TypeError("Invalid type for PCB addition (%s)" % type(rhs))
        return self

    def connectH(self, *args, **kwargs):
        ''' Connects a set of pins or points, traveling first
            horizontally then vertically
        '''
        width = kwargs['width'] if 'width' in kwargs else 0.016
        points = []
        for A, B in zip(args[:-1], args[1:]):
            if not isinstance(A, BoundPin):     A = Point(*A)
            if not isinstance(B, BoundPin):     B = Point(*B)
            points.append(A)
            if (A.x != B.x):
                points.append(Point(B.x, A.y))
        if A.y != B.y:  points.append(B)
        self.connections.append(Connection(width, *points))

    def connectV(self, *args, **kwargs):
        ''' Connects a set of pins or points, travelling first
            vertically then horizontally.
        '''
        width = kwargs['width'] if 'width' in kwargs else 0.016
        points = []
        for A, B in zip(args[:-1], args[1:]):
            if not isinstance(A, BoundPin):     A = Point(*A)
            if not isinstance(B, BoundPin):     B = Point(*B)
            points.append(A)
            if (A.y != B.y):
                points.append(Point(A.x, B.y))
        if A.x != B.x:  points.append(B)
        self.connections.append(Connection(width, *points))

################################################################################

class Component(object):
    ''' Generic PCB component.
    '''
    def __init__(self, x, y, rot=0, name=''):
        ''' Constructs a Component object
                x           X position
                y           Y position
                rotation    angle (degrees)
                name        String
        '''
        self.x = x
        self.y = y
        self.rot   = rot

        self.name = name

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
    def pin_labels(self):
        L = []
        for p in self.pins:
            p = BoundPin(p, self)
            if p.pin.name:
                L.append(text(p.pin.name, p.x, p.y, 0.03))
        return reduce(operator.add, L) if L else None

    @property
    def label(self):
        return text(self.name, self.x, self.y, 0.03)

################################################################################

class Pin(object):
    ''' PCB pin, with name, shape, and position
    '''
    def __init__(self, x, y, shape, name=''):
        self.x      = x
        self.y      = y
        self.shape  = shape
        self.name   = name

    @property
    def pad(self):
        return s2d.move(self.shape, self.x, self.y)

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

################################################################################

class Point(object):
    ''' Object with x and y member variables
    '''
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __iter__(self):
        return iter([self.x, self.y])

################################################################################

class Connection(object):
    ''' Connects two pins via a series of intermediate points
    '''
    def __init__(self, width, *args):
        self.width = width
        self.points = [
            a if isinstance(a, BoundPin) else Point(*a) for a in args
        ]

    @property
    def traces(self):
        t = []
        for p1, p2 in zip(self.points[:-1], self.points[1:]):
            d = sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
            if p2 != self.points[-1]:
                d += self.width/2
            a = atan2(p2.y - p1.y, p2.x - p1.x)
            r = s2d.rectangle(0, d, -self.width/2, self.width/2)
            t.append(s2d.move(s2d.rotate(r, degrees(a)), p1.x, p1.y))
        return reduce(operator.add, t)

################################################################################
# Pad definitions
################################################################################

_pad_1206 = s2d.rectangle(-0.032, 0.032, -0.034, 0.034)
_pad_1210 = s2d.rectangle(-0.032, 0.032, -0.048, 0.048)
_pad_choke = s2d.rectangle(-0.06, 0.06, -0.06, 0.06)
_pad_0402 = s2d.rectangle(-0.175, 0.175, -0.014, 0.014)
_pad_SJ = s2d.rectangle(-0.02, 0.02, -0.03, 0.03)
_pad_SOD_123 = s2d.rectangle(-0.02, 0.02, -0.024, 0.024)
_pad_USB_trace = s2d.rectangle(-0.0075, 0.0075, -0.04, 0.04)
_pad_USB_foot  = s2d.rectangle(-0.049, 0.049, -0.043, 0.043)
_pad_header  = s2d.rectangle(-0.06, 0.06, -0.025, 0.025)
_pad_SOT23 = s2d.rectangle(-.02,.02,-.012,.012)
_pad_SOT23_5 = s2d.rectangle(-.01,.01,-.02,.02)
_pad_SOT223 = s2d.rectangle(-.02,.02,-.03,.03)
_pad_SOT223_ground = s2d.rectangle(-.065,.065,-.03,.03)
_pad_XTAL_NX5032GA = s2d.rectangle(-.039,.039,-.047,.047)
_pad_XTAL_EFOBM = s2d.rectangle(-.016,.016,-.085,.085)
_pad_XTAL_CSM_7 = s2d.rectangle(-.108,.108,-.039,.039)
_pad_SOIC = s2d.rectangle(-0.041, 0.041, -0.015, 0.015)
_pad_SOICN = s2d.rectangle(-0.035, 0.035, -0.015, 0.015)
_pad_TQFP_h = s2d.rectangle(-0.025, 0.025, -0.008, 0.008)
_pad_TQFP_v = s2d.rectangle(-0.008, 0.008, -0.025, 0.025)
_pad_ESP8266 = s2d.rectangle(-0.0493, 0.0493, -0.0197, 0.0197)
_pad_ESP8266_bot = s2d.rectangle(-0.0197, 0.0197, -0.0415, 0.0415)
_pad_MTA = s2d.rectangle(-0.021, 0.021, -0.041, 0.041)
_pad_MTA_solder = s2d.rectangle(-0.071, 0.071, -0.041, 0.041)
_pad_screw_terminal = s2d.circle(0, 0, 0.047)
_pad_hole_screw_terminal = s2d.circle(0, 0, 0.025)
_pad_stereo_2_5mm = s2d.rectangle(-0.03, 0.03, -0.05, 0.05)
_pad_Molex = s2d.rectangle(-0.0155, 0.0155, -0.0265, 0.0265)
_pad_Molex_solder = s2d.rectangle(-0.055, 0.055, -0.065, 0.065)
_pad_button_6mm = s2d.rectangle(-0.04, 0.04, -0.03, 0.03)
_pad_RGB = s2d.rectangle(-0.02, 0.02, -0.029, 0.029)
_pad_PLCC2 = s2d.rectangle(-0.029, 0.029, -0.059, 0.059)
_pad_SM8 = s2d.rectangle(-0.035, 0.035, -0.016, 0.016)
_pad_mic = s2d.circle(0, 0, 0.02)
_pad_accel = s2d.rectangle(-0.03, 0.03, -0.0125, 0.0125)
_pad_accel90 = s2d.rectangle(-0.0125, 0.0125, -0.03, 0.03)
_pad_cc_14_1 = s2d.rectangle(-0.014, 0.014, -0.0075, 0.0075)
_pad_cc_14_1_90 = s2d.rectangle(-0.0075, 0.0075, -0.014, 0.014)
_pad_TQFP_h = s2d.rectangle(-0.025, 0.025, -0.007, 0.007)
_pad_TQFP_v = s2d.rectangle(-0.007, 0.007, -0.025, 0.025)

TSSOP_pad_width = 0.040
TSSOP_pad_height = 0.011
TSSOP_pad_dy = 0.026
TSSOP_pad_dx = 0.120
_pad_TSSOP = s2d.rectangle(-TSSOP_pad_width/2.0,TSSOP_pad_width/2.0,-TSSOP_pad_height/2.0,TSSOP_pad_height/2.0)


################################################################################
# Discrete passive components
################################################################################

class R_0402(Component):
   ''' 0402 resistor
   '''

class R_1206(Component):
    ''' 1206 Resistor
    '''
    pins = [Pin(-0.06, 0, _pad_1206), Pin(0.06, 0, _pad_1206)]
    prefix = 'R'

class C_1206(Component):
    ''' 1206 Capacitor
    '''
    pins = [Pin(-0.06, 0, _pad_1206), Pin(0.06, 0, _pad_1206)]
    prefix = 'C'

class SJ(Component):
    ''' Solder jumper
    '''
    pins = [Pin(-0.029, 0, _pad_SJ), Pin(0.029, 0, _pad_SJ)]
    prefix = 'SJ'

class D_SOD_123(Component):
    ''' Diode
    '''
    pins = [Pin(-0.07, 0, _pad_SOD_123, 'A'),
            Pin(0.07, 0, _pad_SOD_123, 'C')]
    prefix = 'D'

class R_0402(Component):
   ''' 0402 resistor
   '''

class L_1210(Component):
   ''' 1210 inductor
   '''

class choke(Component):
   ''' Panasonic ELLCTV
   '''

################################################################################
# Connectors
################################################################################

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

class Header_signal(Component):
    ''' signal header
        FCI 95278-101A04LF Bergstik 2x2x0.1"
    '''

class Header_power(Component):
    ''' power header
        FCI 95278-101A04LF Bergstik 2x2x0.1"
    '''

class Header_i0(Component):
    ''' i0 header
        FCI 95278-101A04LF Bergstik 2x2x0.1"
    '''

class Header_serial(Component):
    ''' serial comm header
        FCI 95278-101A04LF Bergstik 2x2x0.1"
    '''

class Header_bus(Component):
    ''' bus header
        FCI 95278-101A04LF Bergstik 2x2x0.1"
    '''

class Header_I2C(Component):
    ''' i2c header
        FCI 95278-101A04LF Bergstik 2x2x0.1"
    '''

class Header_APA(Component):
    ''' APA header
        FCI 95278-101A04LF Bergstik 2x2x0.1"
    '''

class Header_6(Component):
    ''' 6-pin header
        FCI 95278-101A06LF Bergstik 2x3x0.1"
    '''

class Header_PDI(Component):
    ''' in-circuit PDI programming header
        FCI 95278-101A06LF Bergstik 2x3x0.1"
    '''

class Header_servo(Component):
    ''' servo motor header
        FCI 95278-101A06LF Bergstik 2x3x0.1"
    '''

class Header_unipolar_stepper(Component):
    ''' unipolar stepper header
        FCI 95278-101A06LF Bergstik 2x3x0.1"
    '''

class Header_LCD(Component):
    ''' LCD interface header
        FCI 95278-101A10LF Bergstik 2x5x0.1"
    '''

class HCSR4(Component):
    ''' HC-SR04 sonar header
    '''

class HCSR501(Component):
    ''' HC-SR0501 motion-detector header
    '''

class ESP8266_12E(Component):
    ''' ESP8266 12E
    '''

class MTA_2(Component):
    ''' AMP 1445121-2
        MTA .050 SMT 2-pin vertical
    '''

class MTA_power(Component):
    ''' AMP 1445121-2
        MTA .050 SMT 2-pin vertical
    '''

class MTA_3(Component):
    ''' AMP 1445121-3
        MTA .050 SMT 3-pin vertical
    '''

class MTA_i0(Component):
    ''' AMP 1445121-3
        MTA .050 SMT 3-pin vertical
    '''

class MTA_4(Component):
    ''' AMP 1445121-4
        MTA .050 SMT 4-pin vertical
    '''

class MTA_serial(Component):
    ''' AMP 1445121-4
        MTA .050 SMT 4-pin vertical
    '''

class MTA_PS2(Component):
    ''' AMP 1445121-4
        MTA .050 SMT 4-pin vertical
    '''

class MTA_5(Component):
    ''' AMP 1445121-5
        MTA .050 SMT 5-pin vertical
    '''

class MTA_ICP(Component):
    ''' AMP 1445121-5
        MTA .050 SMT 5-pin vertical
    '''

class screw_terminal_2(Component):
    ''' On Shore ED555/2DS
        two position screw terminal
    '''

class screw_terminal_power(Component):
    ''' On Shore ED555/2DS
        power screw terminal
    '''

class screw_terminal_i0(Component):
    ''' On Shore ED555/2DS
        i0 screw terminal
    '''

class power_65mm(Component):
    ''' CUI PJ1-023-SMT
    '''

class stereo_2_5mm(Component):
    ''' CUI SJ1-2533-SMT
    '''

class Molex_serial(Component):
    ''' Molex 53261-0471
    '''

################################################################################
# Switches
################################################################################

class button_6mm(Component):
    ''' Omron 6mm pushbutton
        B3SN-3112P
    '''

################################################################################
#   Clock crystals and resonators
################################################################################

class XTAL_NX5032GA(Component):
    pins = [Pin(-0.079, 0, _pad_XTAL_NX5032GA),
            Pin(0.079, 0, _pad_XTAL_NX5032GA)]
    prefix = 'X'

################################################################################
# Diodes, transistors and regulators
################################################################################

class NMOS_SOT23(Component):
    ''' NMOS transistor in SOT23 package
        Fairchild NDS355AN
    '''
    pins = [
        Pin(0.045, -0.0375, _pad_SOT23, 'G'),
        Pin(0.045,  0.0375, _pad_SOT23, 'S'),
        Pin(-0.045, 0, _pad_SOT23, 'D')
    ]
    prefix = 'Q'

class PMOS_SOT23(Component):
    ''' PMOS transistor in SOT23 package
        Fairchild NDS356AP
    '''
    pins = [
        Pin(-0.045, -0.0375, _pad_SOT23, 'G'),
        Pin(-0.045,  0.0375, _pad_SOT23, 'S'),
        Pin(0.045, 0, _pad_SOT23, 'D')
    ]
    prefix = 'Q'

class Regulator_SOT23(Component):
    '''  SOT23 voltage regulator
    '''
    pins = [
        Pin(-0.045, -0.0375, _pad_SOT23, 'Out'),
        Pin(-0.045,  0.0375, _pad_SOT23, 'In'),
        Pin(0.045, 0, _pad_SOT23, 'GND')
    ]
    prefix = 'U'


################################################################################
# ICs Atmel microcontrollers
################################################################################

class ATtiny45_SOIC(Component):
    pins = []
    y = 0.075
    for t in ['RST', 'PB3', 'PB4', 'GND']:
        pins.append(Pin(-0.14, y, _pad_SOIC, t))
        y -= 0.05
    for p in ['PB0', 'PB1', 'PB2', 'VCC']:
        y += 0.05
        pins.append(Pin(0.14, y, _pad_SOIC, t))
    del y
    prefix = 'U'

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

################################################################################
#   CBA logo and other graphics
################################################################################
_pin_circle_CBA = s2d.circle(0, 0, 0.02)
_pin_square_CBA = s2d.rectangle(-0.02, 0.02, -0.02, 0.02)
class CBA(Component):
    pins = []
    for i in range(3):
        for j in range(3):
            pin = _pin_circle_CBA if i == 2-j and j >= 1 else _pin_square_CBA
            pins.append(Pin(0.06*(i-1), 0.06*(j-1), pin))
