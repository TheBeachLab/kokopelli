import ctypes
import queue
import shutil
import subprocess
import tempfile
import threading
import time
import os

import wx

import  koko
import  koko.dialogs as dialogs
from    koko.c.region     import Region

from    koko.fab.asdf     import ASDF
from    koko.fab.path     import Path
from    koko.fab.image    import Image
from    koko.fab.mesh     import Mesh

class ExportProgress(wx.Frame):
    ''' Frame with a progress bar and a cancel button.
        When the cancel button is pressed, events are set.
    '''
    def __init__(self, title, event1, event2):
        self.events = event1, event2

        wx.Frame.__init__(self, parent=koko.FRAME, title=title)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.gauge = wx.Gauge(self, wx.ID_ANY, size=(200, 20))
        hbox.Add(self.gauge, flag=wx.ALL, border=10)

        cancel = wx.Button(self, label='Cancel')
        self.Bind(wx.EVT_BUTTON, self.cancel)
        hbox.Add(cancel, flag=wx.ALL, border=10)

        self.SetSizerAndFit(hbox)
        self.Show()

    @property
    def progress(self): return self.gauge.GetValue()
    @progress.setter
    def progress(self, v):  wx.CallAfter(self.gauge.SetValue, v)

    def cancel(self, event):
        for e in self.events:   e.set()

################################################################################

class ExportTaskCad(object):
    ''' A class representing a FabVars export task.

        Requires a filename and cad structure,
        plus optional supporting arguments.
    '''

    def __init__(self, filename, cad, **kwargs):

        self.filename   = filename
        self.extension  = self.filename.split('.')[-1]
        self.cad        = cad
        for k in kwargs:    setattr(self, k, kwargs[k])

        self.event   = threading.Event()
        self.c_event = threading.Event()

        self.window = ExportProgress(
            'Exporting to %s' % self.extension, self.event, self.c_event
        )

        # Create a new thread to run the export in the background
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()


    def export_png(self):
        ''' Exports a png using libtree.
        '''

        if self.make_heightmap:
            out = self.make_image(self.cad.shape)
        else:
            i = 0
            imgs = []
            for e in self.cad.shapes:
                if self.event.is_set(): return
                img = self.make_image(e)
                if img is not None: imgs.append(img)
                i += 1
                self.window.progress = i*90/len(self.cad.shapes)
            out = Image.merge(imgs)

        if self.event.is_set(): return

        self.window.progress = 90
        out.save(self.filename)
        self.window.progress = 100



    def make_image(self, expr):
        ''' Renders a single expression, returning the image
        '''
        zmin = self.cad.zmin if self.cad.zmin else 0
        zmax = self.cad.zmax if self.cad.zmax else 0

        region = Region(
            (self.cad.xmin, self.cad.ymin, zmin),
            (self.cad.xmax, self.cad.ymax, zmax),
            self.resolution*self.cad.mm_per_unit
        )

        img = expr.render(
            region, mm_per_unit=self.cad.mm_per_unit, interrupt=self.c_event
        )

        img.color = expr.color
        return img


    def export_asdf(self):
        ''' Exports an ASDF file.
        '''
        asdf = self.make_asdf(self.cad.shape)
        self.window.progress = 50
        if self.event.is_set(): return
        asdf.save(self.filename)
        self.window.progress = 100


    def export_svg(self):
        ''' Exports an svg file at 90 DPI with per-object colors.
        '''
        xmin = self.cad.xmin*self.cad.mm_per_unit
        dx = (self.cad.xmax - self.cad.xmin)*self.cad.mm_per_unit
        ymax = self.cad.ymax*self.cad.mm_per_unit
        dy = (self.cad.ymax - self.cad.ymin)*self.cad.mm_per_unit
        stroke = max(dx, dy)/100.


        Path.write_svg_header(self.filename, dx, dy)

        i = 0
        for expr in self.cad.shapes:
            # Generate an ASDF
            if self.event.is_set(): return
            asdf = self.make_asdf(expr, flat=True)
            i += 1
            self.window.progress = i*33/len(self.cad.shapes)

            # Find the contours of the ASDF
            if self.event.is_set(): return
            contours = self.make_contour(asdf)
            i += 2
            self.window.progress = i*33/len(self.cad.shapes)

            # Write them out to the SVG file
            for c in contours:
                c.write_svg_contour(
                    self.filename, xmin, ymax, stroke=stroke,
                    color=expr.color if expr.color else (0,0,0)
                )

        Path.write_svg_footer(self.filename)


    def export_stl(self):
        ''' Exports an stl, using an asdf as intermediary.
        '''
        i = 0
        meshes = []
        for expr in self.cad.shapes:

            if self.event.is_set(): return
            asdf = self.make_asdf(expr)
            i += 1
            self.window.progress = i*33/len(self.cad.shapes)

            if self.event.is_set(): return
            mesh = self.make_mesh(asdf)
            i += 2
            self.window.progress = i*33/len(self.cad.shapes)

            if mesh is not None:    meshes.append(mesh)

        if self.event.is_set(): return
        total = Mesh.merge(meshes)
        total.save_stl(self.filename)

    def make_asdf(self, expr, flat=False):
        ''' Renders an expression to an ASDF '''
        if flat:
            region = Region(
                (expr.xmin - self.cad.border*expr.dx,
                 expr.ymin - self.cad.border*expr.dy,
                 0),
                (expr.xmax + self.cad.border*expr.dx,
                 expr.ymax + self.cad.border*expr.dy,
                 0),
                 self.resolution * self.cad.mm_per_unit
            )
        else:
            region = Region(
                (expr.xmin - self.cad.border*expr.dx,
                 expr.ymin - self.cad.border*expr.dy,
                 expr.zmin - self.cad.border*expr.dz),
                (expr.xmax + self.cad.border*expr.dx,
                 expr.ymax + self.cad.border*expr.dy,
                 expr.zmax + self.cad.border*expr.dz),
                 self.resolution * self.cad.mm_per_unit
            )
        asdf = expr.asdf(
            region=region, mm_per_unit=self.cad.mm_per_unit,
            interrupt=self.c_event
        )
        return asdf


    def make_contour(self, asdf):
        contour = asdf.contour(interrupt=self.c_event)
        return contour


    def make_mesh(self, asdf):
        ''' Renders an ASDF to a mesh '''
        if self.use_cms:
            return asdf.triangulate_cms()
        else:
            return asdf.triangulate(interrupt=self.c_event)


    def export_dot(self):
        ''' Saves a math tree as a .dot file. '''

        # Make the cad function and C data structure
        expr = self.cad.shape
        expr.ptr
        self.window.progress = 25

        # Save as a dot file
        expr.save_dot(self.filename, self.dot_arrays)
        self.window.progress = 100


    def run(self):
        getattr(self, 'export_%s' % self.extension)()
        wx.CallAfter(self.window.Destroy)

################################################################################

class ExportTaskASDF(object):
    ''' A class representing an ASDF export task.
    '''

    def __init__(self, filename, asdf, **kwargs):
        self.filename = filename
        self.extension = self.filename.split('.')[-1]
        self.asdf = asdf

        for k in kwargs:    setattr(self, k, kwargs[k])

        self.event = threading.Event()
        self.c_event = threading.Event()

        self.progress = ExportProgress(
            'Exporting to %s' % self.extension, self.event, self.c_event
        )

        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def export_png(self):
        img = self.asdf.render(
            alpha=self.alpha, beta=self.beta, resolution=self.resolution
        )
        self.progress.progress = 90
        img.save(self.filename)
        self.progress.progress = 100

    def export_stl(self):
        mesh = self.asdf.triangulate_cms()
        self.progress.progress = 60
        mesh.save_stl(self.filename)
        self.progress.progress = 100

    def export_asdf(self):
        self.asdf.save(self.filename)
        koko.APP.savepoint(True)
        self.progress.progress = 100

    def run(self):
        getattr(self, 'export_%s' % self.extension)()
        wx.CallAfter(self.progress.Destroy)
