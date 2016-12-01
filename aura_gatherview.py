#!/usr/bin/env pythonw

# ****************************************************************************
#
#   Aura SEG-Y View
#   
#   An application for viewing seismic data stored in SEG-Y format.
#   
#       Written by: Wes Hamlyn
#       Last Mod:   28-Jan-2016
#   Copyright 2016 Wes Hamlyn
#   
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#   
#       http://www.apache.org/licenses/LICENSE-2.0

#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ****************************************************************************


import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2Wx

import matplotlib.cm as cm

from matplotlib.ticker import FormatStrFormatter
majorFormatter = FormatStrFormatter('%i')

import numpy as np
import os

import auralib as aura

try:
    import wx
except ImportError:
    print("Oops!! Cannot import wxPython, please verify that it is installed")


class AuraSEGYView(wx.Frame):
    """
    Main class for gather viewer
    """
    
    def __init__(self):
        """
        constructor method
        """
        wx.Frame.__init__(self, None, -1, 'Aura SEG-Y View', size=(600, 700), 
                          style=wx.DEFAULT_FRAME_STYLE|wx.MAXIMIZE)
        self.doSetIcon(self)
        
        self.cur_trace = 1
        self.num_disp_traces = 500
        self.num_traces = 1000000
        self.gather_file = ''
        
        self.head1_pos = 29
        self.head1_fmt = 'h'
        self.head2_pos = 37
        self.head2_fmt = 'l'
        
        
        self.amp_min = -5000
        self.amp_max = 5000
        
        self.DoCreateMenus()
        #self.SetBackgroundColour([100,100,100])
        self.doLayout()
        self.set_def_thead()
        self.formatAxes()
        
    
    def doLayout(self):
        """
        Method to build the figure window layout.
        """
        
        #  wxPython and Matplotlib use different RGB ranges (0-255 and 0-1 
        #  respectively).  The following lines convert the matplotlib 
        #  foreground colour to the equivalent wxPython colour
        app_fg_color_mpl = [0.94, 0.94, 0.94]
        app_fg_color_wx = np.array(app_fg_color_mpl)*255
        app_fg_color_wx = app_fg_color_wx.tolist()
        
        #  Create the matplotlib figure, canvas, and axes to handle the
        #  graphical displays
        self.fig = Figure((5,5), dpi=72, facecolor=app_fg_color_mpl)
        self.canvas = FigCanvas(self, -1, self.fig)
        
        # axes to handle seismic data displays
        self.ax1 = self.fig.add_axes([0.05, 0.05, 0.90, 0.80])
        
        # twinned axes to handle graphing of trace header values
        self.ax2 = self.fig.add_axes([0.05, 0.88, 0.90, 0.10], sharex=self.ax1)
        self.ax2t= matplotlib.pyplot.twinx(self.ax2)
        
        #  Create a panel to hold all of the various widgets that will be used
        #  to edit the seismic display properties
        panControls = wx.Panel(self, size=(-1, 110))
        panControls.SetBackgroundColour(app_fg_color_wx)
        
        #  Build slider bar
        self.sl1 = wx.Slider(panControls, -1, 1, 1, self.num_traces, wx.DefaultPosition, 
                        (-1, -1), style=wx.SL_AUTOTICKS|wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.sl1.SetTickFreq(0) # turn off the slider bar ticks
        
        #  Create text labels for parameter text boxes
        st1 = wx.StaticText(panControls, -1, 'Displayed Traces:', size=(-1, -1))
        stCurTrc = wx.StaticText(panControls, -1, 'Current Trace:', size=(-1, -1))
        stAmpMin = wx.StaticText(panControls, -1, 'Min Amp:', size=(-1, -1))
        stAmpMax = wx.StaticText(panControls, -1, 'Max Amp:', size=(-1, -1))
        stH1Pos = wx.StaticText(panControls, -1, 'Trace Head 1:  Pos', size=(-1, -1))
        stH2Pos = wx.StaticText(panControls, -1, 'Trace Head 2:  Pos', size=(-1, -1))
        stH1Fmt = wx.StaticText(panControls, -1, 'Format Code', size=(-1, -1))
        stH2Fmt = wx.StaticText(panControls, -1, 'Format Code', size=(-1, -1))       
        
        #  Create parameter text boxes
        self.tc1 = wx.TextCtrl(panControls, -1, str(self.num_disp_traces), 
                               size=(70, -1), style=wx.TE_PROCESS_ENTER)
        self.tcCurTrc = wx.TextCtrl(panControls, -1, str(self.cur_trace), 
                               size=(70, -1), style=wx.TE_PROCESS_ENTER)
        self.tcAmpMin = wx.TextCtrl(panControls, -1, str(self.amp_min),
                                    size=(70, -1), style=wx.TE_PROCESS_ENTER)
        self.tcAmpMax = wx.TextCtrl(panControls, -1, str(self.amp_max),
                                    size=(70, -1), style=wx.TE_PROCESS_ENTER)
        self.tcH1Pos = wx.TextCtrl(panControls, -1, str(self.head1_pos),
                                    size=(70, -1), style=wx.TE_PROCESS_ENTER)
        self.tcH2Pos = wx.TextCtrl(panControls, -1, str(self.head2_pos),
                                    size=(70, -1), style=wx.TE_PROCESS_ENTER)
        self.tcH1Fmt = wx.TextCtrl(panControls, -1, self.head1_fmt,
                                    size=(70, -1), style=wx.TE_PROCESS_ENTER)
        self.tcH2Fmt = wx.TextCtrl(panControls, -1, self.head2_fmt,
                                    size=(70, -1), style=wx.TE_PROCESS_ENTER)

        #  Use a grid sizer to build a 3x2 array of labels and parameter boxes
        gs = wx.GridSizer(4, 4, 5, 5)
        gs.AddMany([(st1, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL),
                    (self.tc1, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
                    (stCurTrc, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL),
                    (self.tcCurTrc, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
                    (stAmpMin, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL),
                    (self.tcAmpMin, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
                    (stAmpMax, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL),
                    (self.tcAmpMax, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
                    (stH1Pos, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL),
                    (self.tcH1Pos, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
                    (stH1Fmt, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL),
                    (self.tcH1Fmt, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
                    (stH2Pos, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL),
                    (self.tcH2Pos, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
                    (stH2Fmt, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL),
                    (self.tcH2Fmt, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)])
        
        
        #  Add the slider and parameter boxes to the parameter controls panel
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.sl1, 1, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 30)
        hbox1.Add(gs, 0, wx.RIGHT, 30)
        panControls.SetSizer(hbox1)
        
        #  Create a matplotlib toolbar for zooming and panning
        self.toolbar = NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()        
        
        #  User a vertical box sizer to set the final interface layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.toolbar, 0, wx.EXPAND|wx.ALL, 0)
        vbox.Add(self.canvas, 1, wx.EXPAND|wx.ALL, 0) # only the graphic area will resize
        vbox.Add(panControls, 0, wx.EXPAND|wx.ALL, 0)
        self.SetSizer(vbox)
        
        # Add a status bar
        self.StatBar = self.CreateStatusBar()
       
        # Controls event bindings
        self.Bind(wx.EVT_SCROLL_CHANGED, self.onScroll, self.sl1)
        self.Bind(wx.EVT_TEXT_ENTER, self.onEnter, self.tc1)
        self.Bind(wx.EVT_TEXT_ENTER, self.onEnter, self.tcAmpMin)
        self.Bind(wx.EVT_TEXT_ENTER, self.onEnter, self.tcAmpMax)
        self.Bind(wx.EVT_TEXT_ENTER, self.onEnter, self.tcH1Pos)
        self.Bind(wx.EVT_TEXT_ENTER, self.onEnter, self.tcH1Fmt)
        self.Bind(wx.EVT_TEXT_ENTER, self.onEnter, self.tcH2Pos)
        self.Bind(wx.EVT_TEXT_ENTER, self.onEnter, self.tcH2Fmt)

        

    def DoCreateMenus(self):
        """
        Method to create menus and menu bar.
        """
        menuBar = wx.MenuBar()
        
        
        # Build File Menu
        menuFile = wx.Menu()
        menuOpenGather = menuFile.Append(-1, '&Open SEG-Y File...', 
                                         'Open a SEG-Y File Containg Seismic Traces')
        menuFile.AppendSeparator()
        menuExit = menuFile.Append(wx.ID_EXIT, 'E&xit', 'Exit application')            
        menuBar.Append(menuFile, '&File')
        
        # Build View Menu
        menuView = wx.Menu()
        menuViewEBCDIC = menuView.Append(-1, '&View EBCDIC...', 
                                     'View contents of EBCDIC header')
        menuFormat = menuView.Append(-1, '&Define Header Format...', 
                                     'Define trace and binary header info') 
        menuBar.Append(menuView, '&View')
        
       # Build Help Menu
        menuHelp = wx.Menu()
        menuAbout = menuHelp.Append(wx.ID_ABOUT, '&About', 
                                    'Display information about application')
        menuBar.Append(menuHelp, '&Help')
        
        # Finalize the menu bar
        self.SetMenuBar(menuBar)
        
        # Event Handler Bindings
        self.Bind(wx.EVT_MENU, self.OnOpenSEGY, menuOpenGather)
        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
        self.Bind(wx.EVT_MENU, self.OnViewEBCDIC, menuViewEBCDIC)
    
    
    def doSetIcon(self, frame):
        """"
        Set icon for main application windows
        """
        
        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(wx.Image('./icons/aura-waves_24x24.gif').ConvertToBitmap())
        frame.SetIcon(icon)
        
        
    def formatAxes(self):
        
        self.ax1.set_aspect('auto')
        self.ax1.grid()
        self.ax1.set_xlabel('Trace')
        self.ax1.set_ylabel('Time (ms)')
        self.ax1.xaxis.set_major_formatter(majorFormatter)
        self.ax1.yaxis.set_major_formatter(majorFormatter)  
        self.canvas.draw()
    
        self.ax2.grid()
        self.ax2.set_ylabel('Trace Head 1', color='b')
        self.ax2.tick_params(axis='y', colors='b')
        self.ax2.xaxis.set_major_formatter(majorFormatter)
        self.ax2.yaxis.set_major_formatter(majorFormatter)
        
        self.ax2t.set_ylabel('Trace Head 2', color='r')
        self.ax2t.tick_params(axis='y', colors='r')
        self.ax2t.xaxis.set_major_formatter(majorFormatter)
        self.ax2t.yaxis.set_major_formatter(majorFormatter)  
        self.canvas.draw()
    
    
    def onScroll(self, event):
        self.cur_trace = int(self.sl1.GetValue())
        self.tcCurTrc.SetValue(str(int(self.cur_trace)))
        self.num_disp_traces = int(self.tc1.GetValue())
        self.set_def_thead()
        del(self.segybuf)
        self.segybuf = aura.segy.Segy(self.gather_file, def_thead=self.def_thead)
        self.getSegyHeaders()
        self.getSegyTraces()
    
    
    def onEnter(self, event):
        self.cur_trace = int(self.tcCurTrc.GetValue())
        self.sl1.SetValue(self.cur_trace)
        self.num_disp_traces = int(self.tc1.GetValue())
        self.amp_min = float(self.tcAmpMin.GetValue())
        self.amp_max = float(self.tcAmpMax.GetValue())
        self.set_def_thead()
        del(self.segybuf)
        self.segybuf = aura.segy.Segy(self.gather_file, def_thead=self.def_thead)
        self.set_def_thead()
        self.getSegyHeaders()
        self.getSegyTraces()


    def getSegyTraces(self):
        t0 = self.cur_trace - 1
        t1 = self.cur_trace + self.num_disp_traces - 1

        self.StatBar.SetStatusText('Reading Traces %i to %i...' % 
                                   (self.cur_trace, t1))
        
        if t1 > self.num_traces:
            t1 = self.num_traces
            t0 = t1 - self.num_disp_traces
            self.sl1.SetValue(t0+1)
        
        tdata = self.segybuf.read_multi_trace_data_new(t0, t1)
        
        self.tdata = np.array(tdata)
                
        self.StatBar.SetStatusText('Reading Traces %i to %i... DONE!' % 
                                   (self.cur_trace, t1))
        
        self.plotSegyHeaders()
        self.plotSegyTraces()
        
        
    def plotSegyTraces(self):
        xmin = self.cur_trace
        xmax = self.cur_trace + self.num_disp_traces
        tmin = 0
        tmax = self.segybuf.bhead['num_samp']*self.segybuf.bhead['samp_rate']*0.001
        bounds = [xmin, xmax, tmax, tmin]
        self.ax1.cla()
        self.ax1.imshow(self.tdata.T, cmap=cm.bwr_r, vmin=self.amp_min, vmax=self.amp_max, extent=bounds)

        self.formatAxes()
        
        
    def getSegyHeaders(self):
        self.StatBar.SetStatusText('Reading Headers...')

        t0 = self.cur_trace - 1
        t1 = self.cur_trace + self.num_disp_traces - 1
        
        if t1 > self.num_traces:
            t1 = self.num_traces
            t0 = t1 - self.num_disp_traces
            self.sl1.SetValue(t0+1)
            
        self.segybuf.read_thead2(t0, t1)
        self.StatBar.SetStatusText('Reading Headers...Done!')
    
    
    def plotSegyHeaders(self):
        t0 = self.cur_trace
        t1 = self.cur_trace + self.num_disp_traces
        
        x = np.arange(t0, t1, 1)
        h1 = self.segybuf.thead['head1']
        h2 = self.segybuf.thead['head2']
        
        self.ax2.cla()
        self.ax2t.cla()
        
        self.ax2.plot(x, h1, 'b')
        self.ax2.set_ylim([min(h1), max(h1)])
        
        self.ax2t.plot(x, h2, 'r')
        self.ax2t.set_ylim([min(h2), max(h2)])
    
    
    def set_def_thead(self):
        
        self.head1_fmt = str(self.tcH1Fmt.GetValue())
        self.head2_fmt = str(self.tcH2Fmt.GetValue())
        
        self.head1_pos = int(self.tcH1Pos.GetValue())
        self.head2_pos = int(self.tcH2Pos.GetValue())
        
        # Set number of bytes for Header 1
        if self.head1_fmt in ['l', 'f', 'ibm']:
            h1_nbyte = 4
        elif self.head1_fmt == 'h':
            h1_nbyte = 2
        elif self.head1_fmt == 's':
            h1_nbyte = 1
        
        # Set number of bytes for Header 2
        if self.head2_fmt in ['l', 'f', 'ibm']:
            h2_nbyte = 4
        elif self.head2_fmt == 'h':
            h2_nbyte = 2
        elif self.head2_fmt == 's':
            h2_nbyte = 1
        
        # Build structure for format definition
        def_thead = {'head1':{'bpos':self.head1_pos,  'fmt':self.head1_fmt, 'nbyte':h1_nbyte},
                     'head2':{'bpos':self.head2_pos,  'fmt':self.head2_fmt, 'nbyte':h2_nbyte}
                     }
        self.def_thead = def_thead
    
    
    
    ########################################
    #
    #  File Menu Event Handlers
    
    def OnOpenSEGY(self, event):
        """
        Event handler for opening a SEG-Y file containing gathers
        """
        
        dlg = wx.FileDialog(self, "Select the SEG-Y Gather File...",
                            style=wx.FD_OPEN)
        
        if dlg.ShowModal() == wx.ID_OK:
            self.gather_file = dlg.GetPath()

        dlg.Destroy()
        
        self.SetTitle('Aura - GatherView: %s' % self.gather_file)
        
        self.set_def_thead()
        
        self.segybuf = aura.segy.Segy(self.gather_file, def_thead=self.def_thead)
        self.num_traces = self.segybuf.num_traces
        
        self.sl1.SetRange(1, self.num_traces)
        self.sl1.SetValue(1)
        self.cur_trace = int(self.sl1.GetValue())
        
        self.getSegyHeaders()
        self.getSegyTraces()
        
        
    def OnExit(self, event):
        """
        Event handler for exiting the application
        """
        
        self.Close()


    ########################################
    #
    #  View Menu Event Handlers
    
    def OnViewEBCDIC(self, event):
        """
        Event handler for launched the EBCDIC header viewer
        """
        
        filename = os.path.basename(self.gather_file)
        frame_title = 'EBCDIC Header Viewer: %s' % filename
        frEBCDIC = wx.Frame(None, -1, frame_title, size=(600, 700))
        self.doSetIcon(frEBCDIC)
        
        tcEBCDIC = wx.TextCtrl(frEBCDIC, -1, '', 
                               style=wx.TE_MULTILINE|wx.TE_READONLY, size=(-1, -1))

        for line in self.segybuf.ebcdic:
            tcEBCDIC.AppendText(line)
                    
        frEBCDIC.Show()


    ########################################
    #
    #  Help Menu Event Handlers
    
    def OnAbout(self, event):
        """
        Event handler for displaying the About screen
        """
        
        description = """
        Aura GatherView is a software package for viewing and analysing prestack 
        seismic gather data stored in SEG-Y format.
        """
        
        licence = """None."""
        
        info = wx.AboutDialogInfo()
        
        info.SetIcon(wx.Icon('./icons/aura-qi.png', wx.BITMAP_TYPE_PNG))
        info.SetName('Aura - GatherView')
        info.SetVersion('0.1')
        info.SetDescription(description)
        info.SetCopyright('(C) 2016 Wes Hamlyn')
        info.SetLicence(licence)
        info.AddDeveloper('Wes Hamlyn')
        #info.AddDocWriter('Wes Hamlyn')
        #info.AddArtist('Wes Hamlyn')
        #info.AddTranslator('Wes Hamlyn')
        
        wx.AboutBox(info)

        
        
    

if __name__ == '__main__':
    app = wx.App(redirect=False)
    frame = AuraSEGYView()
    frame.Show()
    app.MainLoop()
    
