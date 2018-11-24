# `kokopelli` is back
`kokopelli reloaded` is a personal effort to prevent the end of something good. In 2013 [I took Fab Academy](http://fabacademy.org/archives/2013/students/sanchez.francisco/index.html) in Fab Lab Barcelona and discovered `kokopelli`. I was amazed by the versaltility of the tool (2D and 3D mechanical design, circuit boards, physical simulations, CAM, machine control...) and the fact that you could do all of these cool things with just a text editor.

Over the years I felt that, even though new tools were appearing, we were going backwards. Back to to graphical interfaces (very cool and visual actually), but still you still needed to manually point and click. So I felt I wanted kokopelli back. And since Matt Keeter abandoned the project, I thought I would give it a try while learning Python. Say hello to `kokopelli reloaded`.

## Compile and run
`kokopelli reloaded` has been tested on Linux (Arch). Clone or download the repository and then install it by typing in a terminal:
```bash
make clean
make
sudo make install
```
To run kokopelli just type `python2 kokopelli`

## What's new

### Aliases: PCB components, humanized
Now components classes are easier to remember and recall. No more looking at the pcb library to remember some weird names, no more combinations of upper case, lower case and underscores. For example, to add a commonly used SMD resistor (1206 size) just type **any** of the following:
```python
R1 = R_1206 (x, y, angle, 'label')
R1 = resistor (x, y, angle, 'label')
R1 = Resistor (x, y, angle, 'label')
```
This way components are  easier to remember for people who are not used to electronics:
```python
B1 = button (x, y, angle, 'label')
XTAL1 = resonator (x, y, angle, 'label')
C1 = capacitor (x, y, angle, 'label')
J1 = headerisp (x, y, angle, 'label')
U1 = usb (x, y, angle, 'label')
```
It works by adding a new class at the beginning of the library:
```python
class AKA(type):
    """ 'Also Known As' metaclass to create aliases for a class. """
    def __new__(cls, classname, bases, attrs):
        print('in AKA.__new__')
        class_ = type(classname, bases, attrs)
        globals().update({alias: class_ for alias in attrs.get('aliases', [])})
        return class_
```
In every class where we want to add aliases, we just list them:
```python
class R_1206(Component):
    ''' 1206 Resistor
    '''
    __metaclass__ = AKA                 # Add this for aliases
    aliases = 'resistor', 'Resistor'    # List here the aliases
    pins = [Pin(-0.06, 0, _pad_1206), Pin(0.06, 0, _pad_1206)]
    prefix = 'R'
```

### Sam Calish's pcb.lib additions merged
(WIP) While hyperjumping the web I came across [Sam's additions](https://gitlab.cba.mit.edu/pub/libraries/tree/master/kokopelli) to the pcb.lib. I am merging part of his code so Kudos for him!

### Free cutout shapes
WIP

## Warning
`kokopelli` stores designs as Python scripts and executes them.  This means that you can do cool things like using `numpy` to process arrays, load and process images with `PIL`, or even scrape web data and use it to inform designs.

However, it also means that bad actors can write malicious scripts.

As such, **do not open a .ko file from an untrusted source** without first examining it in a text editor to confirm that it is not malicious.

## About
`kokopelli` is an open-source tool for computer-aided design and manufacturing (CAD/CAM).

It uses Python as a hardware description language for solid models.  A set of core libraries define common shapes and transforms, but users are free to extend their designs with their own definitions.

![CAD](http://i.imgur.com/L1RQUxA.png)

The CAM tools enable path planning for two, three, and five-axis machines.  At the moment, paths can be exported to Universal and Epilog laser cutters, the Roland Modela mini-mill, three and five-axis Shopbot machines, and plain G-code.  A modular workflow system makes adding new machines easy.

![CAM](http://i.imgur.com/sb0uQq5.png)

In addition, models can be saved as `.svg` and water-tight `.stl` files.

`kokopelli` grew out of the MIT course ["How to Make Something that Makes (Almost) Anything"](http://fab.cba.mit.edu/classes/S62.12/index.html).
In that course, I worked on [fast geometry solvers](http://fab.cba.mit.edu/classes/S62.12/people/keeter.matt/solver/index.html) and developed a [fairly basic UI](http://fab.cba.mit.edu/classes/S62.12/people/keeter.matt/gui/index.html).  My work expanded on the [fab modules](http://kokompe.cba.mit.edu/) project, which allows [fab lab](http://fab.cba.mit.edu/about/faq/) users to make physical artifacts on a variety of machines.

This work grew into my [Master's thesis](http://cba.mit.edu/docs/theses/13.05.Keeter.pdf) at the MIT [Center for Bits and Atoms](http://cba.mit.edu).  This thesis focused on volumetric CAD/CAM workflows.  Now that it is complete, I'm releasing this tool for others to use and develop.  It has already been used by folks in [How to Make (Almost) Anything](http://fab.cba.mit.edu/classes/863.12/) and [Fab Academy](http://www.fabacademy.org/), but Matt Keeter was excited to offer it to a larger community.

## Copyright
* (c) 2012-2013 Massachusetts Institute of Technology
* (c) 2013 Matt Keeter
* (c) 2017 Sam Calisch
* (c) 2018 Francisco Sanchez
