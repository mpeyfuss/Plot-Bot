#!/usr/bin/python

'''
General plotting application where you can import csv files, plot data in many different ways
(line, scatter, histogram, logarithmic), generate calculated variables, save plotting options,
and export csv file with calculated variables.
'''

# import packages
import sys
import os
import webbrowser
import pandas as pd
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
import plotly.offline
from plotly.subplots import make_subplots
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QUrl, QFileInfo
from PyQt5.QtWebEngineWidgets import QWebEngineView

# settings
np.seterr(divide="ignore")

# define application class
class Plot_Bot(QMainWindow):
    def __init__(self):
        # init
        super().__init__()

        # class variables
        self.filename = ""
        self.path = ""
        self.data = pd.DataFrame
        self.version = 1.0

        # base window creation
        self.resize(800, 800)
        self.center()
        self.setWindowTitle("Plot Bot")
        self.setWindowIcon(QIcon("Icons" + os.path.sep + "plot_bot.ico"))

        # create menu & toolbar actions
        save_prof_action = QAction(QIcon("Icons" + os.path.sep + "save_icon.ico"), "&Save Profile", self)
        save_prof_action.setShortcut("Ctrl+S")
        save_prof_action.setIconVisibleInMenu(False)
        save_prof_action.triggered.connect(self.save_prof)

        load_prof_action = QAction("&Load Profile", self)
        load_prof_action.setShortcut("Ctrl+L")
        load_prof_action.triggered.connect(self.load_prof)

        open_file_action = QAction(QIcon("Icons" + os.path.sep + "open_icon.ico"), "&Open CSV File", self)
        open_file_action.setShortcut("Ctrl+O")
        open_file_action.setIconVisibleInMenu(False)
        open_file_action.triggered.connect(self.open_file)

        plot_action = QAction(QIcon("Icons" + os.path.sep + "run_icon.ico"), "&Update Plot", self)
        plot_action.setShortcut("Ctrl+R")
        plot_action.setIconVisibleInMenu(False)
        plot_action.triggered.connect(self.update_plot)

        user_manual_action = QAction("&User Manual", self)
        user_manual_action.setShortcut("Ctrl+U")
        user_manual_action.triggered.connect(self.open_user_manual)

        open_issue_action = QAction("&Report Issue", self)
        open_issue_action.setShortcut("Ctrl+Shift+R")
        open_issue_action.triggered.connect(self.open_issue)

        get_version_action = QAction("&Version", self)
        get_version_action.setShortcut("Ctrl+Shift+V")
        get_version_action.triggered.connect(self.get_version)

        # create menu
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(save_prof_action)
        file_menu.addAction(load_prof_action)

        data_menu = menu_bar.addMenu("&Data")
        data_menu.addAction(open_file_action)
        data_menu.addAction(plot_action)

        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction(user_manual_action)
        help_menu.addAction(open_issue_action)
        help_menu.addAction(get_version_action)

        # create toolbar
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.addAction(save_prof_action)
        self.toolbar.addAction(open_file_action)
        self.toolbar.addAction(plot_action)

        # central widget
        wid = QWidget(self)
        self.setCentralWidget(wid)

        # create left side splitter (vertical splitter)
        top_left_frame = QFrame(wid)
        top_left_frame.setFrameShape(QFrame.StyledPanel)
        bottom_left_frame = QFrame(wid)
        bottom_left_frame.setFrameShape(QFrame.StyledPanel)
        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.addWidget(top_left_frame)
        v_splitter.addWidget(bottom_left_frame)
        v_splitter.setSizes([30, 70])

        # create overall horizontal splitter
        hbox = QHBoxLayout(wid)
        right_frame = QFrame(wid)
        right_frame.setFrameShape(QFrame.StyledPanel)
        h_splitter = QSplitter(Qt.Horizontal)
        h_splitter.addWidget(v_splitter)
        h_splitter.addWidget(right_frame)
        h_splitter.setSizes([30, 70])
        hbox.addWidget(h_splitter)

        # create top left grid layout in left frame
        upper_grid = QGridLayout()
        upper_grid.setHorizontalSpacing(5)
        upper_grid.setVerticalSpacing(10)
        top_left_frame.setLayout(upper_grid)

        # create file name display
        file_disp_label = QLabel("Current File")
        file_disp_label.setAlignment(Qt.AlignRight)
        self.file_disp = QLineEdit()
        self.file_disp.setAlignment(Qt.AlignLeft)
        self.file_disp.setReadOnly(True)

        # create variable list display
        var_list_label = QLabel("Variables")
        var_list_label.setAlignment(Qt.AlignRight)
        self.var_list = QListWidget()
        self.var_list.setItemAlignment(Qt.AlignLeft)
        self.var_list.setDragEnabled(True)
        self.var_list.setAcceptDrops(False)
        self.var_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        upper_grid.addWidget(file_disp_label, 0, 0, 1, 1, Qt.AlignTop)
        upper_grid.addWidget(self.file_disp, 0, 1, 1, 3)

        upper_grid.addWidget(var_list_label, 2, 0, 1, 1, Qt.AlignTop)
        upper_grid.addWidget(self.var_list, 2, 1, 4, 3)

        # create lower tab panel for plot setup
        self.setup_panel = QTabWidget()
        ts_tab = QWidget()
        xy_tab = QWidget()
        hist_tab = QWidget()
        three_dim_tab = QWidget()
        pair_tab = QWidget()
        self.setup_panel.addTab(ts_tab, "&Time Series")
        self.setup_panel.addTab(xy_tab, "&X-Y")
        self.setup_panel.addTab(three_dim_tab, "&3D")
        self.setup_panel.addTab(hist_tab, "&Histogram")
        self.setup_panel.addTab(pair_tab, "&Pair Plot")

        # add setup panel to lower left frame
        setup_layout = QGridLayout()
        bottom_left_frame.setLayout(setup_layout)
        setup_layout.addWidget(self.setup_panel)

        # time series setup tab
        self.setup_panel.currentWidget().setStyleSheet("QCheckBox{font-size: 12px;} QLineEdit{font-size: 12px;}")

        # create widgets for time series setup tab
        ts_num_subplots_label = QLabel("Plots")
        self.ts_num_subplots_disp = QSpinBox()
        self.ts_num_subplots_disp.setValue(1)
        self.ts_num_subplots_disp.valueChanged.connect(self.ts_subplots_changed)

        ts_t_label = QLabel("Time")
        self.ts_t_disp = QComboBox()
        self.ts_t_disp.addItem("")

        y1_left_label = QLabel("Y1 Left")
        self.y1_left_disp = QListWidget()
        self.y1_left_disp.setAcceptDrops(True)
        self.y1_left_disp.itemDoubleClicked.connect(self.remove_list_item)

        self.y1_left_log = QCheckBox()
        self.y1_left_log.setText("Log Scale")
        self.y1_left_log.setLayoutDirection(Qt.RightToLeft)

        self.y1_left_ax_label = QLineEdit()
        self.y1_left_ax_label.setAlignment(Qt.AlignLeft)

        y1_right_label = QLabel("Y1 Right")
        self.y1_right_disp = QListWidget()
        self.y1_right_disp.setAcceptDrops(True)
        self.y1_right_disp.itemDoubleClicked.connect(self.remove_list_item)

        self.y1_right_log = QCheckBox()
        self.y1_right_log.setText("Log Scale")
        self.y1_right_log.setLayoutDirection(Qt.RightToLeft)

        self.y1_right_ax_label = QLineEdit()
        self.y1_right_ax_label.setAlignment(Qt.AlignLeft)

        y2_left_label = QLabel("Y2 Left")
        self.y2_left_disp = QListWidget()
        self.y2_left_disp.setAcceptDrops(True)
        self.y2_left_disp.itemDoubleClicked.connect(self.remove_list_item)
        self.y2_left_disp.setEnabled(False)

        self.y2_left_log = QCheckBox()
        self.y2_left_log.setText("Log Scale")
        self.y2_left_log.setLayoutDirection(Qt.RightToLeft)
        self.y2_left_log.setEnabled(False)

        self.y2_left_ax_label = QLineEdit()
        self.y2_left_ax_label.setAlignment(Qt.AlignLeft)
        self.y2_left_ax_label.setEnabled(False)

        y2_right_label = QLabel("Y2 Right")
        self.y2_right_disp = QListWidget()
        self.y2_right_disp.setAcceptDrops(True)
        self.y2_right_disp.itemDoubleClicked.connect(self.remove_list_item)
        self.y2_right_disp.setEnabled(False)

        self.y2_right_log = QCheckBox()
        self.y2_right_log.setText("Log Scale")
        self.y2_right_log.setLayoutDirection(Qt.RightToLeft)
        self.y2_right_log.setEnabled(False)

        self.y2_right_ax_label = QLineEdit()
        self.y2_right_ax_label.setAlignment(Qt.AlignLeft)
        self.y2_right_ax_label.setEnabled(False)

        y3_left_label = QLabel("Y3 Left")
        self.y3_left_disp = QListWidget()
        self.y3_left_disp.setAcceptDrops(True)
        self.y3_left_disp.itemDoubleClicked.connect(self.remove_list_item)
        self.y3_left_disp.setEnabled(False)

        self.y3_left_ax_label = QLineEdit()
        self.y3_left_ax_label.setAlignment(Qt.AlignLeft)
        self.y3_left_ax_label.setEnabled(False)

        self.y3_left_log = QCheckBox()
        self.y3_left_log.setText("Log Scale")
        self.y3_left_log.setLayoutDirection(Qt.RightToLeft)
        self.y3_left_log.setEnabled(False)

        y3_right_label = QLabel("Y3 Right")
        self.y3_right_disp = QListWidget()
        self.y3_right_disp.setAcceptDrops(True)
        self.y3_right_disp.itemDoubleClicked.connect(self.remove_list_item)
        self.y3_right_disp.setEnabled(False)

        self.y3_right_log = QCheckBox()
        self.y3_right_log.setText("Log Scale")
        self.y3_right_log.setLayoutDirection(Qt.RightToLeft)
        self.y3_right_log.setEnabled(False)

        self.y3_right_ax_label = QLineEdit()
        self.y3_right_ax_label.setAlignment(Qt.AlignLeft)
        self.y3_right_ax_label.setEnabled(False)

        y4_left_label = QLabel("Y4 Left")
        self.y4_left_disp = QListWidget()
        self.y4_left_disp.setAcceptDrops(True)
        self.y4_left_disp.itemDoubleClicked.connect(self.remove_list_item)
        self.y4_left_disp.setEnabled(False)

        self.y4_left_log = QCheckBox()
        self.y4_left_log.setText("Log Scale")
        self.y4_left_log.setLayoutDirection(Qt.RightToLeft)
        self.y4_left_log.setEnabled(False)

        self.y4_left_ax_label = QLineEdit()
        self.y4_left_ax_label.setAlignment(Qt.AlignLeft)
        self.y4_left_ax_label.setEnabled(False)

        y4_right_label = QLabel("Y4 Right")
        self.y4_right_disp = QListWidget()
        self.y4_right_disp.setAcceptDrops(True)
        self.y4_right_disp.itemDoubleClicked.connect(self.remove_list_item)
        self.y4_right_disp.setEnabled(False)

        self.y4_right_log = QCheckBox()
        self.y4_right_log.setText("Log Scale")
        self.y4_right_log.setLayoutDirection(Qt.RightToLeft)
        self.y4_right_log.setEnabled(False)

        self.y4_right_ax_label = QLineEdit()
        self.y4_right_ax_label.setAlignment(Qt.AlignLeft)
        self.y4_right_ax_label.setEnabled(False)

        self.clear_ts_button = QPushButton("Clear Variables")
        self.clear_ts_button.pressed.connect(self.clear_ts_var)

        # add grid to time series tab and add widgets
        ts_grid = QGridLayout()
        self.setup_panel.setCurrentIndex(0)
        self.setup_panel.currentWidget().setLayout(ts_grid)
        ts_grid.addWidget(ts_num_subplots_label, 0, 0, 1, 1, Qt.AlignRight)
        ts_grid.addWidget(self.ts_num_subplots_disp, 0, 1, 1, 1, Qt.AlignVCenter)
        ts_grid.addWidget(ts_t_label, 1, 0, 1, 1, Qt.AlignRight)
        ts_grid.addWidget(self.ts_t_disp, 1, 1, 1, 2, Qt.AlignVCenter)
        ts_grid.addWidget(self.clear_ts_button, 0, 4, 1, 2, Qt.AlignCenter)
        ts_grid.addWidget(y1_left_label, 2, 0, 2, 1, Qt.AlignTop | Qt.AlignRight)
        ts_grid.addWidget(self.y1_left_log, 2, 0, 2, 1, Qt.AlignVCenter | Qt.AlignRight)
        ts_grid.addWidget(self.y1_left_ax_label, 2, 0, 2, 1, Qt.AlignBottom)
        ts_grid.addWidget(self.y1_left_disp, 2, 1, 2, 2)
        ts_grid.addWidget(y1_right_label, 2, 3, 2, 1, Qt.AlignTop | Qt.AlignRight)
        ts_grid.addWidget(self.y1_right_log, 2, 3, 2, 1, Qt.AlignVCenter | Qt.AlignRight)
        ts_grid.addWidget(self.y1_right_ax_label, 2, 3, 2, 1, Qt.AlignBottom)
        ts_grid.addWidget(self.y1_right_disp, 2, 4, 2, 2)
        ts_grid.addWidget(y2_left_label, 4, 0, 2, 1, Qt.AlignTop | Qt.AlignRight)
        ts_grid.addWidget(self.y2_left_log, 4, 0, 2, 1, Qt.AlignVCenter | Qt.AlignRight)
        ts_grid.addWidget(self.y2_left_ax_label, 4, 0, 2, 1, Qt.AlignBottom)
        ts_grid.addWidget(self.y2_left_disp, 4, 1, 2, 2)
        ts_grid.addWidget(y2_right_label, 4, 3, 2, 1, Qt.AlignTop | Qt.AlignRight)
        ts_grid.addWidget(self.y2_right_log, 4, 3, 2, 1, Qt.AlignVCenter | Qt.AlignRight)
        ts_grid.addWidget(self.y2_right_ax_label, 4, 3, 2, 1, Qt.AlignBottom)
        ts_grid.addWidget(self.y2_right_disp, 4, 4, 2, 2)
        ts_grid.addWidget(y3_left_label, 6, 0, 2, 1, Qt.AlignTop | Qt.AlignRight)
        ts_grid.addWidget(self.y3_left_log, 6, 0, 2, 1, Qt.AlignVCenter | Qt.AlignRight)
        ts_grid.addWidget(self.y3_left_ax_label, 6, 0, 2, 1, Qt.AlignBottom)
        ts_grid.addWidget(self.y3_left_disp, 6, 1, 2, 2)
        ts_grid.addWidget(y3_right_label, 6, 3, 2, 1, Qt.AlignTop | Qt.AlignRight)
        ts_grid.addWidget(self.y3_right_log, 6, 3, 2, 1, Qt.AlignVCenter | Qt.AlignRight)
        ts_grid.addWidget(self.y3_right_ax_label, 6, 3, 2, 1, Qt.AlignBottom)
        ts_grid.addWidget(self.y3_right_disp, 6, 4, 2, 2)
        ts_grid.addWidget(y4_left_label, 8, 0, 2, 1, Qt.AlignTop | Qt.AlignRight)
        ts_grid.addWidget(self.y4_left_log, 8, 0, 2, 1, Qt.AlignVCenter | Qt.AlignRight)
        ts_grid.addWidget(self.y4_left_ax_label, 8, 0, 2, 1, Qt.AlignBottom)
        ts_grid.addWidget(self.y4_left_disp, 8, 1, 2, 2)
        ts_grid.addWidget(y4_right_label, 8, 3, 2, 1, Qt.AlignTop | Qt.AlignRight)
        ts_grid.addWidget(self.y4_right_log, 8, 3, 2, 1, Qt.AlignVCenter | Qt.AlignRight)
        ts_grid.addWidget(self.y4_right_ax_label, 8, 3, 2, 1, Qt.AlignBottom)
        ts_grid.addWidget(self.y4_right_disp, 8, 4, 2, 2)

        # X-Y setup tab
        xy_style_label = QLabel("Line Style")
        self.xy_style_disp = QComboBox()
        self.xy_style_disp.addItem("Scatter")
        self.xy_style_disp.addItem("Line")

        xy_x_label = QLabel("X Variable")
        self.xy_x_disp = QComboBox()
        self.xy_x_disp.addItem("")

        xy_x_title_label = QLabel("X Axis Title")
        self.xy_x_title = QLineEdit()
        self.xy_x_title.setAlignment(Qt.AlignLeft)

        self.xy_x_log = QCheckBox()
        self.xy_x_log.setText("Log Scale X")
        self.xy_x_log.setLayoutDirection(Qt.RightToLeft)

        xy_y_label = QLabel("Y Variable")
        self.xy_y_disp = QComboBox()
        self.xy_y_disp.addItem("")

        xy_y_title_label = QLabel("Y Axis Title")
        self.xy_y_title = QLineEdit()
        self.xy_y_title.setAlignment(Qt.AlignLeft)

        self.xy_y_log = QCheckBox()
        self.xy_y_log.setText("Log Scale Y")
        self.xy_y_log.setLayoutDirection(Qt.RightToLeft)

        xy_color_label = QLabel("Color Variable")
        self.xy_color_disp = QComboBox()
        self.xy_color_disp.addItem("None")

        xy_trendline_label = QLabel("Trendline")
        self.xy_trendline_disp = QComboBox()
        self.xy_trendline_disp.addItem("None")
        self.xy_trendline_disp.addItem("Least Sqaures")
        self.xy_trendline_disp.addItem("LOWESS")

        # add X-Y widgets to grid
        xy_grid = QGridLayout()
        self.setup_panel.setCurrentIndex(1)
        self.setup_panel.currentWidget().setLayout(xy_grid)
        xy_grid.addWidget(xy_style_label, 0, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        xy_grid.addWidget(self.xy_style_disp, 0, 1, 1, 2)
        xy_grid.addWidget(xy_x_label, 1, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        xy_grid.addWidget(self.xy_x_disp, 1, 1, 1, 2)
        xy_grid.addWidget(xy_x_title_label, 2, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        xy_grid.addWidget(self.xy_x_title, 2, 1, 1, 2)
        xy_grid.addWidget(self.xy_x_log, 3, 2, 1, 1, Qt.AlignRight)
        xy_grid.addWidget(xy_y_label, 4, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        xy_grid.addWidget(self.xy_y_disp, 4, 1, 1, 2)
        xy_grid.addWidget(xy_y_title_label, 5, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        xy_grid.addWidget(self.xy_y_title, 5, 1, 1, 2)
        xy_grid.addWidget(self.xy_y_log, 6, 2, 1, 1, Qt.AlignRight)
        xy_grid.addWidget(xy_color_label, 7, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        xy_grid.addWidget(self.xy_color_disp, 7, 1, 1, 2)
        xy_grid.addWidget(xy_trendline_label, 8, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        xy_grid.addWidget(self.xy_trendline_disp, 8, 1, 1, 2)

        # create widgets for 3D tab
        three_dim_x_label = QLabel("X Variable")
        self.three_dim_x_disp = QComboBox()
        self.three_dim_x_disp.addItem("")

        three_dim_x_title_label = QLabel("X Axis Title")
        self.three_dim_x_title = QLineEdit()
        self.three_dim_x_title.setAlignment(Qt.AlignLeft)

        three_dim_y_label = QLabel("Y Variable")
        self.three_dim_y_disp = QComboBox()
        self.three_dim_y_disp.addItem("")

        three_dim_y_title_label = QLabel("Y Axis Title")
        self.three_dim_y_title = QLineEdit()
        self.three_dim_y_title.setAlignment(Qt.AlignLeft)

        three_dim_z_label = QLabel("Z Variable")
        self.three_dim_z_disp = QComboBox()
        self.three_dim_z_disp.addItem("")

        three_dim_z_title_label = QLabel("Z Axis Title")
        self.three_dim_z_title = QLineEdit()
        self.three_dim_z_title.setAlignment(Qt.AlignLeft)

        three_dim_color_label = QLabel("Color Variable")
        self.three_dim_color_disp = QComboBox()
        self.three_dim_color_disp.addItem("None")

        # put in grid container
        three_dim_grid = QGridLayout()
        self.setup_panel.setCurrentIndex(2)
        self.setup_panel.currentWidget().setLayout(three_dim_grid)
        three_dim_grid.addWidget(three_dim_x_label, 0, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        three_dim_grid.addWidget(self.three_dim_x_disp, 0, 1, 1, 2)
        three_dim_grid.addWidget(three_dim_x_title_label, 1, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        three_dim_grid.addWidget(self.three_dim_x_title, 1, 1, 1, 2)
        three_dim_grid.addWidget(three_dim_y_label, 2, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        three_dim_grid.addWidget(self.three_dim_y_disp, 2, 1, 1, 2)
        three_dim_grid.addWidget(three_dim_y_title_label, 3, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        three_dim_grid.addWidget(self.three_dim_y_title, 3, 1, 1, 2)
        three_dim_grid.addWidget(three_dim_z_label, 4, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        three_dim_grid.addWidget(self.three_dim_z_disp, 4, 1, 1, 2)
        three_dim_grid.addWidget(three_dim_z_title_label, 5, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        three_dim_grid.addWidget(self.three_dim_z_title, 5, 1, 1, 2)
        three_dim_grid.addWidget(three_dim_color_label, 6, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        three_dim_grid.addWidget(self.three_dim_color_disp, 6, 1, 1, 2)

        # create widgets for histogram
        hist_x_label = QLabel("X Variable")
        self.hist_x_disp = QComboBox()
        self.hist_x_disp.addItem("")

        hist_x_title_label = QLabel("X Axis Title")
        self.hist_x_title = QLineEdit()
        self.hist_x_title.setAlignment(Qt.AlignLeft)

        hist_num_bins_label = QLabel("Number of Bins")
        self.hist_num_bins_disp = QSpinBox()
        self.hist_num_bins_disp.setValue(0)
        self.hist_num_bins_disp.setSingleStep(5)

        hist_normal_label = QLabel("Normalization")
        self.hist_normal_disp = QComboBox()
        self.hist_normal_disp.addItem("None")
        self.hist_normal_disp.addItem("Percent")
        self.hist_normal_disp.addItem("Density")
        self.hist_normal_disp.addItem("Probability Density")

        hist_color_label = QLabel("Color Variable")
        self.hist_color_disp = QComboBox()
        self.hist_color_disp.addItem("None")

        hist_func_label = QLabel("Bin Function")
        self.hist_func_disp = QComboBox()
        self.hist_func_disp.addItem("Count")
        self.hist_func_disp.addItem("Sum")
        self.hist_func_disp.addItem("Avg")
        self.hist_func_disp.addItem("Min")
        self.hist_func_disp.addItem("Max")
        self.hist_func_disp.currentTextChanged.connect(self.hist_func_change)

        hist_y_label = QLabel("Y Variable")
        self.hist_y_disp = QComboBox()
        self.hist_y_disp.addItem("None")
        self.hist_y_disp.setEnabled(False)

        # add hist widgets to the grid
        hist_grid = QGridLayout()
        self.setup_panel.setCurrentIndex(3)
        self.setup_panel.currentWidget().setLayout(hist_grid)
        hist_grid.addWidget(hist_x_label, 0, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        hist_grid.addWidget(self.hist_x_disp, 0, 1, 1, 2)
        hist_grid.addWidget(hist_x_title_label, 1, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        hist_grid.addWidget(self.hist_x_title, 1, 1, 1, 2)
        hist_grid.addWidget(hist_num_bins_label, 2, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        hist_grid.addWidget(self.hist_num_bins_disp, 2, 1, 1, 2)
        hist_grid.addWidget(hist_normal_label, 3, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        hist_grid.addWidget(self.hist_normal_disp, 3, 1, 1, 2)
        hist_grid.addWidget(hist_color_label, 4, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        hist_grid.addWidget(self.hist_color_disp, 4, 1, 1, 2)
        hist_grid.addWidget(hist_func_label, 5, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        hist_grid.addWidget(self.hist_func_disp, 5, 1, 1, 2)
        hist_grid.addWidget(hist_y_label, 6, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        hist_grid.addWidget(self.hist_y_disp, 6, 1, 1, 2)

        # create widgets for pair plot
        pp_var_label = QLabel("Variables")
        self.pp_var_disp = QListWidget()
        self.pp_var_disp.setAcceptDrops(True)
        self.pp_var_disp.itemDoubleClicked.connect(self.remove_list_item)

        pp_color_label = QLabel("Color Variable")
        self.pp_color_disp = QComboBox()
        self.pp_color_disp.addItem("None")

        pp_clear_button = QPushButton("Clear")
        pp_clear_button.clicked.connect(self.clear_pp_var)

        # add to pair plot tab
        pp_grid = QGridLayout()
        self.setup_panel.setCurrentIndex(4)
        self.setup_panel.currentWidget().setLayout(pp_grid)
        pp_grid.addWidget(pp_var_label, 0, 0, 1, 1, Qt.AlignBottom | Qt.AlignHCenter)
        pp_grid.addWidget(self.pp_var_disp, 1, 0, 1, 1)
        pp_grid.addWidget(pp_color_label, 0, 2, 1, 1, Qt.AlignHCenter | Qt.AlignBottom)
        pp_grid.addWidget(self.pp_color_disp, 1, 2, 1, 1, Qt.AlignTop)
        pp_grid.addWidget(pp_clear_button, 1, 2, 1, 1, Qt.AlignBottom)

        # set tab to time series
        self.setup_panel.setCurrentIndex(0)

        # create plot tabs
        self.plot_panel = QTabWidget()
        ts_tab = QWidget()
        xy_tab = QWidget()
        hist_tab = QWidget()
        three_dim_tab = QWidget()
        pair_tab = QWidget()
        self.plot_panel.addTab(ts_tab, "&Time Series")
        self.plot_panel.addTab(xy_tab, "&X-Y")
        self.plot_panel.addTab(three_dim_tab, "&3D")
        self.plot_panel.addTab(hist_tab, "&Histogram")
        self.plot_panel.addTab(pair_tab, "&Pair Plot")

        # add plot panel to right frame
        plot_layout = QGridLayout()
        right_frame.setLayout(plot_layout)
        plot_layout.addWidget(self.plot_panel)

        # add html containers to each plot tab
        self.ts_plot = QWebEngineView()
        ts_plot_grid = QGridLayout()
        self.plot_panel.setCurrentIndex(0)
        self.plot_panel.currentWidget().setLayout(ts_plot_grid)
        ts_plot_grid.addWidget(self.ts_plot)

        self.xy_plot = QWebEngineView()
        xy_plot_grid = QGridLayout()
        self.plot_panel.setCurrentIndex(1)
        self.plot_panel.currentWidget().setLayout(xy_plot_grid)
        xy_plot_grid.addWidget(self.xy_plot)

        self.three_dim_plot = QWebEngineView()
        three_dim_plot_grid = QGridLayout()
        self.plot_panel.setCurrentIndex(2)
        self.plot_panel.currentWidget().setLayout(three_dim_plot_grid)
        three_dim_plot_grid.addWidget(self.three_dim_plot)

        self.hist_plot = QWebEngineView()
        hist_plot_grid = QGridLayout()
        self.plot_panel.setCurrentIndex(3)
        self.plot_panel.currentWidget().setLayout(hist_plot_grid)
        hist_plot_grid.addWidget(self.hist_plot)

        self.pp_plot = QWebEngineView()
        pp_plot_grid = QGridLayout()
        self.plot_panel.setCurrentIndex(4)
        self.plot_panel.currentWidget().setLayout(pp_plot_grid)
        pp_plot_grid.addWidget(self.pp_plot)

        # set plot panel back to time series
        self.plot_panel.setCurrentIndex(0)

        # add in setup and plot panel callbacks
        self.setup_panel.currentChanged.connect(self.setup_panel_changed)
        self.plot_panel.currentChanged.connect(self.plot_panel_changed)

        # show UI
        self.showMaximized()

    def center(self):
        # centers window geometry
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def save_prof(self):
        try:
            # ask user for name of the file
            name, ok = QInputDialog.getText(self, "Input Profile name", "Enter a profile name")
            if not ok:
                return

            # open file
            f = open("Profiles" + os.path.sep + name + ".json", "w")

            # create lists for timeseries subplots
            y1_l = []
            for i in range(self.y1_left_disp.count()):
                y1_l.append(self.y1_left_disp.item(i).text())

            y1_r = []
            for i in range(self.y1_right_disp.count()):
                y1_r.append(self.y1_right_disp.item(i).text())

            y2_l = []
            for i in range(self.y2_left_disp.count()):
                y2_l.append(self.y2_left_disp.item(i).text())

            y2_r = []
            for i in range(self.y2_right_disp.count()):
                y2_r.append(self.y2_right_disp.item(i).text())

            y3_l = []
            for i in range(self.y3_left_disp.count()):
                y3_l.append(self.y3_left_disp.item(i).text())

            y3_r = []
            for i in range(self.y3_right_disp.count()):
                y3_r.append(self.y3_right_disp.item(i).text())

            y4_l = []
            for i in range(self.y4_left_disp.count()):
                y4_l.append(self.y4_left_disp.item(i).text())

            y4_r = []
            for i in range(self.y4_right_disp.count()):
                y4_r.append(self.y4_right_disp.item(i).text())

            # create list for pair plot
            pp = []
            for i in range(self.pp_var_disp.count()):
                pp.append(self.pp_var_disp.item(i).text())

            # create dictionary of all items needed
            d = {"n_sub":self.ts_num_subplots_disp.value(), "ts_time":self.ts_t_disp.currentText(),
                 "y1_l":y1_l, "y1_l_log":self.y1_left_log.isChecked(), "y1_l_title":self.y1_left_ax_label.text(),
                 "y1_r":y1_r, "y1_r_log":self.y1_right_log.isChecked(), "y1_r_title":self.y1_right_ax_label.text(),
                 "y2_l": y2_l, "y2_l_log": self.y2_left_log.isChecked(), "y2_l_title": self.y2_left_ax_label.text(),
                 "y2_r": y2_r, "y2_r_log": self.y2_right_log.isChecked(), "y2_r_title": self.y2_right_ax_label.text(),
                 "y3_l": y3_l, "y3_l_log": self.y3_left_log.isChecked(), "y3_l_title": self.y3_left_ax_label.text(),
                 "y3_r": y3_r, "y3_r_log": self.y3_right_log.isChecked(), "y3_r_title": self.y3_right_ax_label.text(),
                 "y4_l": y4_l, "y4_l_log": self.y4_left_log.isChecked(), "y4_l_title": self.y4_left_ax_label.text(),
                 "y4_r": y4_r, "y4_r_log": self.y4_right_log.isChecked(), "y4_r_title": self.y4_right_ax_label.text(),
                 "xy_style":self.xy_style_disp.currentText(), "xy_x_var":self.xy_x_disp.currentText(),
                 "xy_x_title":self.xy_x_title.text(), "xy_x_log":self.xy_x_log.isChecked(),
                 "xy_y_var":self.xy_y_disp.currentText(), "xy_y_title":self.xy_y_title.text(),
                 "xy_y_log":self.xy_y_log.isChecked(), "xy_color":self.xy_color_disp.currentText(),
                 "xy_trend":self.xy_trendline_disp.currentText(),
                 "3d_x_var":self.three_dim_x_disp.currentText(), "3d_x_title":self.three_dim_x_title.text(),
                 "3d_y_var":self.three_dim_y_disp.currentText(), "3d_y_title":self.three_dim_y_title.text(),
                 "3d_z_var":self.three_dim_z_disp.currentText(), "3d_z_title":self.three_dim_z_title.text(),
                 "3d_color":self.three_dim_color_disp.currentText(),
                 "hist_x_var":self.hist_x_disp.currentText(), "hist_x_title":self.hist_x_title.text(),
                 "hist_bins":self.hist_num_bins_disp.value(), "hist_normal":self.hist_normal_disp.currentText(),
                 "hist_color":self.hist_color_disp.currentText(), "hist_bin_func":self.hist_func_disp.currentText(),
                 "hist_y_var":self.hist_y_disp.currentText(),
                 "pp_var":pp, "pp_color":self.pp_color_disp.currentText()}

            # write dictionary to file
            json.dump(d, f, ensure_ascii=False)

            # close file
            f.close()

        except Exception as e:
            f = open("Logs" + os.path.sep + "error.log", "w")
            f.write(str(e))
            f.close()
            msg = QMessageBox()
            msg.setWindowTitle("Something Went Wrong")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Uh oh!")
            msg.setInformativeText("Looks like something went wrong. Please check error.log in the Logs folder!")
            msg.exec()

    def load_prof(self):
        try:
            # ask user for file
            (file, _) = QFileDialog.getOpenFileName(filter="*.json", caption="Select File", directory="Profiles")
            # cancel handling
            if file == "":
                return

            # open file
            f = open(file, "r")

            # load json file to dictionary

            d = json.load(f)

            # write values to timeseries data
            self.ts_num_subplots_disp.setValue(d["n_sub"])
            self.ts_t_disp.setCurrentText(d["ts_time"])
            self.y1_left_disp.clear()
            self.y1_left_disp.addItems(d["y1_l"])
            self.y1_left_ax_label.setText(d["y1_l_title"])
            self.y1_left_log.setChecked(d["y1_l_log"])
            self.y1_right_disp.clear()
            self.y1_right_disp.addItems(d["y1_r"])
            self.y1_right_ax_label.setText(d["y1_r_title"])
            self.y1_right_log.setChecked(d["y1_r_log"])
            self.y2_left_disp.clear()
            self.y2_left_disp.addItems(d["y2_l"])
            self.y2_left_ax_label.setText(d["y2_l_title"])
            self.y2_left_log.setChecked(d["y2_l_log"])
            self.y2_right_disp.clear()
            self.y2_right_disp.addItems(d["y2_r"])
            self.y2_right_ax_label.setText(d["y2_r_title"])
            self.y2_right_log.setChecked(d["y2_r_log"])
            self.y3_left_disp.clear()
            self.y3_left_disp.addItems(d["y3_l"])
            self.y3_left_ax_label.setText(d["y3_l_title"])
            self.y3_left_log.setChecked(d["y3_l_log"])
            self.y3_right_disp.clear()
            self.y3_right_disp.addItems(d["y3_r"])
            self.y3_right_ax_label.setText(d["y3_r_title"])
            self.y3_right_log.setChecked(d["y3_r_log"])
            self.y4_left_disp.clear()
            self.y4_left_disp.addItems(d["y4_l"])
            self.y4_left_ax_label.setText(d["y4_l_title"])
            self.y4_left_log.setChecked(d["y4_l_log"])
            self.y4_right_disp.clear()
            self.y4_right_disp.addItems(d["y4_r"])
            self.y4_right_ax_label.setText(d["y4_r_title"])
            self.y4_right_log.setChecked(d["y4_r_log"])

            # write xy items
            self.xy_style_disp.setCurrentText(d["xy_style"])
            self.xy_x_disp.setCurrentText(d["xy_x_var"])
            self.xy_x_title.setText(d["xy_x_title"])
            self.xy_x_log.setChecked(d["xy_x_log"])
            self.xy_y_disp.setCurrentText(d["xy_y_var"])
            self.xy_y_title.setText(d["xy_y_title"])
            self.xy_y_log.setChecked(d["xy_y_log"])
            self.xy_color_disp.setCurrentText(d["xy_color"])
            self.xy_trendline_disp.setCurrentText(d["xy_trend"])

            # set 3d tab values
            self.three_dim_x_disp.setCurrentText(d["3d_x_var"])
            self.three_dim_x_title.setText(d["3d_x_title"])
            self.three_dim_y_disp.setCurrentText(d["3d_y_var"])
            self.three_dim_y_title.setText(d["3d_y_title"])
            self.three_dim_z_disp.setCurrentText(d["3d_z_var"])
            self.three_dim_z_title.setText(d["3d_z_title"])
            self.three_dim_color_disp.setCurrentText(d["3d_color"])

            # set histogram values
            self.hist_x_disp.setCurrentText(d["hist_x_var"])
            self.hist_x_title.setText(d["hist_x_title"])
            self.hist_num_bins_disp.setValue(d["hist_bins"])
            self.hist_normal_disp.setCurrentText(d["hist_normal"])
            self.hist_color_disp.setCurrentText(d["hist_color"])
            self.hist_func_disp.setCurrentText(d["hist_bin_func"])
            self.hist_y_disp.setCurrentText(d["hist_y_var"])

            # set pair plot values
            self.pp_var_disp.clear()
            self.pp_var_disp.addItems(d["pp_var"])
            self.pp_color_disp.setCurrentText(d["pp_color"])

            # close the file
            f.close()

        except Exception as e:
            f = open("Logs" + os.path.sep + "error.log", "w")
            f.write(str(e))
            f.close()
            msg = QMessageBox()
            msg.setWindowTitle("Something Went Wrong")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Uh oh!")
            msg.setInformativeText("Looks like something went wrong. Please check error.log in the Logs folder!")
            msg.exec()

    def open_file(self):
        # ask user for file
        (file, _) = QFileDialog.getOpenFileName(filter="*.csv", caption="Select File", directory=os.path.abspath(os.sep))

        # cancel handling
        if file == "":
            return

        # ask user for header and data start rows
        d = Csv_Import_Settings()
        d.exec()

        # create list of rows between header and data start
        if d.data_start - d.header <= 1:
            skip_rows = None
        else:
            skip_rows = np.arange(d.header+1, d.data_start, 1)

        # determine path and filename variables
        i = file.rfind(os.path.sep)
        self.path = file[0:i+1]
        self.filename = file[i+1:]

        # show filename in the proper field
        self.file_disp.setText(self.filename)

        # load in file, with error handling
        try:
            self.data = pd.read_csv(file, header=d.header-1, skiprows=skip_rows, delimiter=d.delim,
                                    skip_blank_lines=False, infer_datetime_format=True)
        except Exception as e:
            f = open("Logs" + os.path.sep + "error.log" , "w")
            f.write(str(e))
            f.close()
            msg = QMessageBox()
            msg.setWindowTitle("Something Went Wrong")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Uh oh!")
            msg.setInformativeText("Looks like something went wrong. Please check error.log in the Logs folder!")
            msg.exec()

        # update combo & list boxes
        if not self.data.empty:
            # var list widget
            self.var_list.clear()
            self.var_list.addItems(self.data.columns)
            # time series time box
            self.ts_t_disp.clear()
            self.ts_t_disp.addItem("")
            self.ts_t_disp.addItems(self.data.columns)
            # xy items
            self.xy_x_disp.clear()
            self.xy_x_disp.addItem("")
            self.xy_x_disp.addItems(self.data.columns)
            self.xy_y_disp.clear()
            self.xy_y_disp.addItem("")
            self.xy_y_disp.addItems(self.data.columns)
            self.xy_color_disp.clear()
            self.xy_color_disp.addItem("None")
            self.xy_color_disp.addItems(self.data.columns)
            # 3D
            self.three_dim_x_disp.clear()
            self.three_dim_x_disp.addItem("")
            self.three_dim_x_disp.addItems(self.data.columns)
            self.three_dim_y_disp.clear()
            self.three_dim_y_disp.addItem("")
            self.three_dim_y_disp.addItems(self.data.columns)
            self.three_dim_z_disp.clear()
            self.three_dim_z_disp.addItem("")
            self.three_dim_z_disp.addItems(self.data.columns)
            self.three_dim_color_disp.clear()
            self.three_dim_color_disp.addItem("None")
            self.three_dim_color_disp.addItems(self.data.columns)
            # hist
            self.hist_x_disp.clear()
            self.hist_x_disp.addItem("")
            self.hist_x_disp.addItems(self.data.columns)
            self.hist_y_disp.clear()
            self.hist_y_disp.addItem("")
            self.hist_y_disp.addItems(self.data.columns)
            self.hist_color_disp.clear()
            self.hist_color_disp.addItem("None")
            self.hist_color_disp.addItems(self.data.columns)
            # pair plot
            self.pp_color_disp.addItems(self.data.columns)

    def update_plot(self):
        try:
            # determine what plot is active
            if self.plot_panel.tabText(self.plot_panel.currentIndex()) == "&Time Series":
                # check that time and at least y1 are populated with variables
                if not self.ts_t_disp.currentText() == "" and self.y1_left_disp.count() > 0:
                    # create time variable
                    t_var = self.ts_t_disp.currentText()

                    # determine number of subplots
                    n_sub = self.ts_num_subplots_disp.value()

                    # create specs for subplots
                    spec = []
                    for i in range(0,n_sub):
                        spec.append([{"secondary_y":True}])

                    # create subplots
                    fig = make_subplots(rows=n_sub, cols=1, shared_xaxes=True, x_title="Time", specs=spec)

                    # populate the first
                    if n_sub >= 1:
                        # populate left axis
                        if self.y1_left_disp.count() > 0:
                            for i in range(0, self.y1_left_disp.count()):
                                y_var = self.y1_left_disp.item(i).text()
                                fig.add_trace(go.Scatter(x=self.data[t_var], y=self.data[y_var],
                                                         mode='lines', name=y_var), secondary_y=False, row=1, col=1)

                        # populate right axis
                        if self.y1_right_disp.count() > 0:
                            for i in range(0, self.y1_right_disp.count()):
                                y_var = self.y1_right_disp.item(i).text()
                                fig.add_trace(go.Scatter(x=self.data[t_var], y=self.data[y_var],
                                                        mode='lines', name=y_var), secondary_y=True, row=1, col=1)

                        # update layout
                        fig.update_layout(template='simple_white')

                        # update y axis log format and text
                        if self.y1_left_log.isChecked():
                            y_left_log = "log"
                        else:
                            y_left_log = "linear"
                        if self.y1_right_log.isChecked():
                            y_right_log = "log"
                        else:
                            y_right_log = "linear"
                        if self.y1_left_disp.count() > 0:
                            if self.y1_left_ax_label.text() == "":
                                y_left_title = self.y1_left_disp.item(0).text()
                            else:
                                y_left_title = self.y1_left_ax_label.text()
                            fig.update_yaxes(row=1, col=1, secondary_y=False, type=y_left_log,
                                             title_text=y_left_title, showgrid=True, gridcolor="LightGray")
                        if self.y1_right_disp.count() > 0:
                            if self.y1_right_ax_label.text() == "":
                                y_right_title = self.y1_right_disp.item(0).text()
                            else:
                                y_right_title = self.y1_right_ax_label.text()
                            fig.update_yaxes(row=1, col=1, secondary_y=True, type=y_right_log,
                                            title_text=y_right_title, showgrid=True, gridcolor="LightGray")
                        fig.update_xaxes(row=1, col=1, showgrid=True, gridcolor="LightGray")

                    # populate the second
                    if n_sub >= 2:
                        # populate left axis
                        if self.y2_left_disp.count() > 0:
                            for i in range(0, self.y2_left_disp.count()):
                                y_var = self.y2_left_disp.item(i).text()
                                fig.add_trace(go.Scatter(x=self.data[t_var], y=self.data[y_var],
                                                         mode='lines', name=y_var), secondary_y=False, row=2, col=1)

                        # populate right axis
                        if self.y2_right_disp.count() > 0:
                            for i in range(0, self.y2_right_disp.count()):
                                y_var = self.y2_right_disp.item(i).text()
                                fig.add_trace(go.Scatter(x=self.data[t_var], y=self.data[y_var],
                                                         mode='lines', name=y_var), secondary_y=True, row=2, col=1)

                        # update layout
                        fig.update_layout(template='simple_white')

                        # update y axis log format and text
                        if self.y2_left_log.isChecked():
                            y_left_log = "log"
                        else:
                            y_left_log = "linear"
                        if self.y2_right_log.isChecked():
                            y_right_log = "log"
                        else:
                            y_right_log = "linear"
                        if self.y2_left_disp.count() > 0:
                            if self.y2_left_ax_label.text() == "":
                                y_left_title = self.y2_left_disp.item(0).text()
                            else:
                                y_left_title = self.y2_left_ax_label.text()
                            fig.update_yaxes(row=2, col=1, secondary_y=False, type=y_left_log,
                                             title_text=y_left_title, showgrid=True, gridcolor="LightGray")
                        if self.y2_right_disp.count() > 0:
                            if self.y2_right_ax_label.text() == "":
                                y_right_title = self.y2_right_disp.item(0).text()
                            else:
                                y_right_title = self.y2_right_ax_label.text()
                            fig.update_yaxes(row=2, col=1, secondary_y=True, type=y_right_log,
                                             title_text=y_right_title, showgrid=True, gridcolor="LightGray")
                        fig.update_xaxes(row=2, col=1, showgrid=True, gridcolor="LightGray")

                    # populate the third
                    if n_sub >= 3:
                        # populate left axis
                        if self.y3_left_disp.count() > 0:
                            for i in range(0, self.y3_left_disp.count()):
                                y_var = self.y3_left_disp.item(i).text()
                                fig.add_trace(go.Scatter(x=self.data[t_var], y=self.data[y_var],
                                                         mode='lines', name=y_var), secondary_y=False, row=3, col=1)

                        # populate right axis
                        if self.y3_right_disp.count() > 0:
                            for i in range(0, self.y3_right_disp.count()):
                                y_var = self.y3_right_disp.item(i).text()
                                fig.add_trace(go.Scatter(x=self.data[t_var], y=self.data[y_var],
                                                         mode='lines', name=y_var), secondary_y=True, row=3, col=1)

                        # update layout
                        fig.update_layout(template='simple_white')

                        # update y axis log format and text
                        if self.y3_left_log.isChecked():
                            y_left_log = "log"
                        else:
                            y_left_log = "linear"
                        if self.y3_right_log.isChecked():
                            y_right_log = "log"
                        else:
                            y_right_log = "linear"
                        if self.y3_left_disp.count() > 0:
                            if self.y3_left_ax_label.text() == "":
                                y_left_title = self.y3_left_disp.item(0).text()
                            else:
                                y_left_title = self.y3_left_ax_label.text()
                            fig.update_yaxes(row=3, col=1, secondary_y=False, type=y_left_log,
                                             title_text=y_left_title, showgrid=True, gridcolor="LightGray")
                        if self.y3_right_disp.count() > 0:
                            if self.y3_right_ax_label.text() == "":
                                y_right_title = self.y3_right_disp.item(0).text()
                            else:
                                y_right_title = self.y3_right_ax_label.text()
                            fig.update_yaxes(row=3, col=1, secondary_y=True, type=y_right_log,
                                            title_text=y_right_title, showgrid=True, gridcolor="LightGray")
                        fig.update_xaxes(row=3, col=1, showgrid=True, gridcolor="LightGray")

                    # populate the fourth
                    if n_sub >= 4:
                        # populate left axis
                        if self.y4_left_disp.count() > 0:
                            for i in range(0, self.y4_left_disp.count()):
                                y_var = self.y4_left_disp.item(i).text()
                                fig.add_trace(go.Scatter(x=self.data[t_var], y=self.data[y_var],
                                                         mode='lines', name=y_var), secondary_y=False, row=4, col=1)

                        # populate right axis
                        if self.y4_right_disp.count() > 0:
                            for i in range(0, self.y4_right_disp.count()):
                                y_var = self.y4_right_disp.item(i).text()
                                fig.add_trace(go.Scatter(x=self.data[t_var], y=self.data[y_var],
                                                         mode='lines', name=y_var), secondary_y=True, row=4, col=1)

                        # update layout
                        fig.update_layout(template='simple_white')

                        # update y axis log format and text
                        if self.y4_left_log.isChecked():
                            y_left_log = "log"
                        else:
                            y_left_log = "linear"
                        if self.y4_right_log.isChecked():
                            y_right_log = "log"
                        else:
                            y_right_log = "linear"
                        if self.y4_left_disp.count() > 0:
                            if self.y4_left_ax_label.text() == "":
                                y_left_title = self.y4_left_disp.item(0).text()
                            else:
                                y_left_title = self.y4_left_ax_label.text()
                            fig.update_yaxes(row=4, col=1, secondary_y=False, type=y_left_log,
                                             title_text=y_left_title, showgrid=True, gridcolor="LightGray")
                        if self.y4_right_disp.count() > 0:
                            if self.y4_right_ax_label.text() == "":
                                y_right_title = self.y4_right_disp.item(0).text()
                            else:
                                y_right_title = self.y4_right_ax_label.text()
                            fig.update_yaxes(row=4, col=1, secondary_y=True, type=y_right_log,
                                            title_text=y_right_title, showgrid=True, gridcolor="LightGray")
                        fig.update_xaxes(row=4, col=1, showgrid=True, gridcolor="LightGray")

                    # put into html code
                    plotly.offline.plot(fig, filename="Temp Plots" + os.path.sep + "ts_temp.html",
                                        include_plotlyjs=True, auto_open=False)

                    # add to pair plot tab
                    self.ts_plot.load(QUrl.fromLocalFile(QFileInfo("Temp Plots" + os.path.sep + "ts_temp.html").absoluteFilePath()))

                else:
                    msg = QMessageBox()
                    msg.setWindowTitle("Missing Variables")
                    msg.setIcon(QMessageBox.Critical)
                    msg.setText("Uh oh!")
                    msg.setInformativeText("Looks like you are missing some variables!")
                    msg.exec()
            elif self.plot_panel.tabText(self.plot_panel.currentIndex()) == "&X-Y":
                # check that x and y are included
                if not self.xy_x_disp.currentText() == "" and not self.xy_y_disp.currentText() == "":
                    # x variable
                    x_var = self.xy_x_disp.currentText()

                    # x title
                    if self.xy_x_title.text() == "":
                        x_title = x_var
                    else:
                        x_title = self.xy_x_title.text()

                    # log scale x
                    if self.xy_x_log.isChecked():
                        log_x = True
                    else:
                        log_x = False

                    # y variable
                    y_var = self.xy_y_disp.currentText()

                    # y title
                    if self.xy_y_title.text() == "":
                        y_title = y_var
                    else:
                        y_title = self.xy_y_title.text()

                    # log scale y
                    if self.xy_y_log.isChecked():
                        log_y = True
                    else:
                        log_y = False

                    # color variable
                    if self.xy_color_disp.currentText() == "None":
                        color = None
                    else:
                        color = self.xy_color_disp.currentText()

                    # trendline
                    if self.xy_trendline_disp.currentText() == "None":
                        trend = None
                    elif self.xy_trendline_disp.currentText() == "Least Sqaures":
                        trend = "ols"
                    else:
                        trend = "lowess"

                    # build figure depending on scatter vs line
                    if self.xy_style_disp.currentText() == "Scatter":
                        fig = px.scatter(self.data, x=x_var, y=y_var, trendline=trend,
                                            color=color, log_x=log_x, log_y=log_y, template="simple_white",
                                            labels={x_var: x_title, y_var: y_title})

                    else:
                        fig = px.line(self.data, x=x_var, y=y_var, color=color, template="simple_white",
                                      log_x=log_x, log_y=log_y,
                                      labels={x_var: x_title, y_var: y_title})

                    # update grid lines
                    fig.update_xaxes(showgrid=True, gridcolor="LightGray")
                    fig.update_yaxes(showgrid=True, gridcolor="LightGray")

                    # put into html code
                    plotly.offline.plot(fig, filename="Temp Plots" + os.path.sep + "xy_temp.html",
                                        include_plotlyjs=True, auto_open=False)

                    # add to pair plot tab
                    self.xy_plot.load(
                        QUrl.fromLocalFile(QFileInfo("Temp Plots" + os.path.sep + "xy_temp.html").absoluteFilePath()))


                else:
                    msg = QMessageBox()
                    msg.setWindowTitle("Missing Variables")
                    msg.setIcon(QMessageBox.Critical)
                    msg.setText("Uh oh!")
                    msg.setInformativeText("Looks like you are missing some variables!")
                    msg.exec()
            elif self.plot_panel.tabText(self.plot_panel.currentIndex()) == "&3D":
                # make sure all variables are filled out
                if not self.three_dim_x_disp.currentText() == "" and not self.three_dim_y_disp.currentText() == "" and not self.three_dim_z_disp.currentText() == "":
                    # x variable
                    x_var = self.three_dim_x_disp.currentText()

                    # x title
                    if self.three_dim_x_title.text() == "":
                        x_title = x_var
                    else:
                        x_title = self.three_dim_x_title.text()

                    # y variable
                    y_var = self.three_dim_y_disp.currentText()

                    # y title
                    if self.three_dim_y_title.text() == "":
                        y_title = y_var
                    else:
                        y_title = self.three_dim_y_title.text()

                    # z variable
                    z_var = self.three_dim_z_disp.currentText()

                    # z title
                    if self.three_dim_z_title.text() == "":
                        z_title = z_var
                    else:
                        z_title = self.three_dim_z_title.text()

                    # color variable
                    if self.three_dim_color_disp.currentText() == "None":
                        color = None
                    else:
                        color = self.three_dim_color_disp.currentText()

                    # build figure
                    fig = px.scatter_3d(self.data, x=x_var, y=y_var, z=z_var,
                                        color=color, template="none",
                                       labels={x_var: x_title, y_var:y_title, z_var:z_title})
                    fig.update_traces(marker_size=2.5, selector=dict(type='scatter3d'))

                    # put into html code
                    plotly.offline.plot(fig, filename="Temp Plots" + os.path.sep + "3d_temp.html",
                                        include_plotlyjs=True, auto_open=False)

                    # add to pair plot tab
                    self.three_dim_plot.load(
                        QUrl.fromLocalFile(QFileInfo("Temp Plots" + os.path.sep + "3d_temp.html").absoluteFilePath()))

                else:
                    msg = QMessageBox()
                    msg.setWindowTitle("Missing Variables")
                    msg.setIcon(QMessageBox.Critical)
                    msg.setText("Uh oh!")
                    msg.setInformativeText("Looks like you are missing some variables!")
                    msg.exec()

            elif self.plot_panel.tabText(self.plot_panel.currentIndex()) == "&Histogram":
                # make sure an x variable is picked
                if not self.hist_x_disp.currentText() == "":
                    # get x variable
                    x_var = self.hist_x_disp.currentText()

                    # x title
                    if self.hist_x_title.text() == "":
                        x_title = x_var
                    else:
                        x_title = self.hist_x_title.text()

                    # number of bins
                    if self.hist_num_bins_disp.value() == 0:
                        n = None
                    else:
                        n = self.hist_num_bins_disp.value()

                    # normalization
                    if self.hist_normal_disp.currentText() == "None":
                        norm = None
                    else:
                        norm = self.hist_normal_disp.currentText().lower()

                    # color variable
                    if self.hist_color_disp.currentText() == "None":
                        color = None
                    else:
                        color = self.hist_color_disp.currentText()

                    # bin function
                    bin_func = self.hist_func_disp.currentText().lower()

                    # y value
                    if self.hist_y_disp.isEnabled == False or self.hist_y_disp.currentText() == "":
                        y_var = None
                    else:
                        y_var = self.hist_y_disp.currentText()

                    # build figure
                    fig = px.histogram(self.data, x=x_var, y=y_var, nbins=n, histnorm=norm,
                                       histfunc=bin_func, color=color, template="simple_white",
                                       labels={x_var:x_title})
                    fig.update_xaxes(showgrid=True, gridcolor="LightGray")
                    fig.update_yaxes(showgrid=True, gridcolor="LightGray")

                    # put into html code
                    plotly.offline.plot(fig, filename="Temp Plots" + os.path.sep + "hist_temp.html",
                                        include_plotlyjs=True, auto_open=False)

                    # add to pair plot tab
                    self.hist_plot.load(
                        QUrl.fromLocalFile(QFileInfo("Temp Plots" + os.path.sep + "hist_temp.html").absoluteFilePath()))

                else:
                    msg = QMessageBox()
                    msg.setWindowTitle("Missing Variables")
                    msg.setIcon(QMessageBox.Critical)
                    msg.setText("Uh oh!")
                    msg.setInformativeText("Looks like you are missing some variables!")
                    msg.exec()

            else:
                # check that at least two items are selected for the pair plot
                if self.pp_var_disp.count() > 1:
                    # generate list of variables
                    var = []
                    for i in range(self.pp_var_disp.count()):
                        var.append(self.pp_var_disp.item(i).text())

                    # see if the color should be based on a variable
                    if self.pp_color_disp.currentText() == "None":
                        color_data = None
                    else:
                        color_data = self.pp_color_disp.currentText()

                    # build figure
                    fig = px.scatter_matrix(self.data, dimensions=var, color=color_data, template="none")

                    # put into html code
                    plotly.offline.plot(fig, filename="Temp Plots" + os.path.sep + "pp_temp.html",
                                        include_plotlyjs=True, auto_open=False)

                    # add to pair plot tab
                    self.pp_plot.load(
                        QUrl.fromLocalFile(QFileInfo("Temp Plots" + os.path.sep + "pp_temp.html").absoluteFilePath()))
                else:
                    msg = QMessageBox()
                    msg.setWindowTitle("Missing Variables")
                    msg.setIcon(QMessageBox.Critical)
                    msg.setText("Uh oh!")
                    msg.setInformativeText("Looks like you are missing some variables!")
                    msg.exec()
        except Exception as e:
            f = open("Logs" + os.path.sep + "error.log", "w")
            f.write(str(e))
            f.close()
            msg = QMessageBox()
            msg.setWindowTitle("Something Went Wrong")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Uh oh!")
            msg.setInformativeText("Looks like something went wrong. Make sure all variables are correct, especially when using a profile. See error.log in the Logs folder for more details.")
            msg.exec()

    def open_user_manual(self):
        webbrowser.open("Documents" + os.path.sep + "Plot_Bot_User_Manual.pdf")

    def open_issue(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Open Issue")
        msg.setTextFormat(Qt.RichText)
        msg.setText("Please open an issue with as much information as you can supply. Thank you and sorry for any trouble!")
        msg.setInformativeText("<a href=https://github.com/mpeyfuss/Plot-Bot/issues>Open Issue</a>")
        msg.exec()

    def get_version(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Version")
        msg.setText("Version: %.2f" % self.version)
        msg.exec()

    def setup_panel_changed(self):
        # make sure plot panel matches setup tab
        self.plot_panel.setCurrentIndex(self.setup_panel.currentIndex())

    def plot_panel_changed(self):
        # make sure setup panel matches the tab you changed to
        self.setup_panel.setCurrentIndex(self.plot_panel.currentIndex())

    def ts_subplots_changed(self):
        # check max
        if self.ts_num_subplots_disp.value() > 4:
            self.ts_num_subplots_disp.setValue(4)
        # check min
        if self.ts_num_subplots_disp.value() < 1:
            self.ts_num_subplots_disp.setValue(1)

        # based on value, enable appropriate boxes
        if self.ts_num_subplots_disp.value() == 1:
            self.y2_left_disp.setEnabled(False)
            self.y2_left_log.setEnabled(False)
            self.y2_left_ax_label.setEnabled(False)
            self.y2_right_disp.setEnabled(False)
            self.y2_right_log.setEnabled(False)
            self.y2_right_ax_label.setEnabled(False)
            self.y3_left_disp.setEnabled(False)
            self.y3_left_log.setEnabled(False)
            self.y3_left_ax_label.setEnabled(False)
            self.y3_right_disp.setEnabled(False)
            self.y3_right_log.setEnabled(False)
            self.y3_right_ax_label.setEnabled(False)
            self.y4_left_disp.setEnabled(False)
            self.y4_left_log.setEnabled(False)
            self.y4_left_ax_label.setEnabled(False)
            self.y4_right_disp.setEnabled(False)
            self.y4_right_log.setEnabled(False)
            self.y4_right_ax_label.setEnabled(False)
        elif self.ts_num_subplots_disp.value() == 2:
            self.y2_left_disp.setEnabled(True)
            self.y2_left_log.setEnabled(True)
            self.y2_left_ax_label.setEnabled(True)
            self.y2_right_disp.setEnabled(True)
            self.y2_right_log.setEnabled(True)
            self.y2_right_ax_label.setEnabled(True)
            self.y3_left_disp.setEnabled(False)
            self.y3_left_log.setEnabled(False)
            self.y3_left_ax_label.setEnabled(False)
            self.y3_right_disp.setEnabled(False)
            self.y3_right_log.setEnabled(False)
            self.y3_right_ax_label.setEnabled(False)
            self.y4_left_disp.setEnabled(False)
            self.y4_left_log.setEnabled(False)
            self.y4_left_ax_label.setEnabled(False)
            self.y4_right_disp.setEnabled(False)
            self.y4_right_log.setEnabled(False)
            self.y4_right_ax_label.setEnabled(False)
        elif self.ts_num_subplots_disp.value() == 3:
            self.y2_left_disp.setEnabled(True)
            self.y2_left_log.setEnabled(True)
            self.y2_left_ax_label.setEnabled(True)
            self.y2_right_disp.setEnabled(True)
            self.y2_right_log.setEnabled(True)
            self.y2_right_ax_label.setEnabled(True)
            self.y3_left_disp.setEnabled(True)
            self.y3_left_log.setEnabled(True)
            self.y3_left_ax_label.setEnabled(True)
            self.y3_right_disp.setEnabled(True)
            self.y3_right_log.setEnabled(True)
            self.y3_right_ax_label.setEnabled(True)
            self.y4_left_disp.setEnabled(False)
            self.y4_left_log.setEnabled(False)
            self.y4_left_ax_label.setEnabled(False)
            self.y4_right_disp.setEnabled(False)
            self.y4_right_log.setEnabled(False)
            self.y4_right_ax_label.setEnabled(False)
        elif self.ts_num_subplots_disp.value() == 4:
            self.y2_left_disp.setEnabled(True)
            self.y2_left_log.setEnabled(True)
            self.y2_left_ax_label.setEnabled(True)
            self.y2_right_disp.setEnabled(True)
            self.y2_right_log.setEnabled(True)
            self.y2_right_ax_label.setEnabled(True)
            self.y3_left_disp.setEnabled(True)
            self.y3_left_log.setEnabled(True)
            self.y3_left_ax_label.setEnabled(True)
            self.y3_right_disp.setEnabled(True)
            self.y3_right_log.setEnabled(True)
            self.y3_right_ax_label.setEnabled(True)
            self.y4_left_disp.setEnabled(True)
            self.y4_left_log.setEnabled(True)
            self.y4_left_ax_label.setEnabled(True)
            self.y4_right_disp.setEnabled(True)
            self.y4_right_log.setEnabled(True)
            self.y4_right_ax_label.setEnabled(True)

    def remove_list_item(self, item: QListWidgetItem):
        wid = item.listWidget()
        wid.takeItem(wid.row(item))

    def clear_ts_var(self):
        self.y1_left_disp.clear()
        self.y1_right_disp.clear()
        self.y2_left_disp.clear()
        self.y2_right_disp.clear()
        self.y3_left_disp.clear()
        self.y3_right_disp.clear()
        self.y4_left_disp.clear()
        self.y4_right_disp.clear()

    def hist_func_change(self):
        if not self.hist_func_disp.currentText() == "Count":
            self.hist_y_disp.setEnabled(True)
        else:
            self.hist_y_disp.setEnabled(False)

    def clear_pp_var(self):
        self.pp_var_disp.clear()

class Csv_Import_Settings(QDialog):
    def __init__(self):
        QDialog.__init__(self)

        # create window
        self.resize(50, 50)

        # create variables
        self.header = 1
        self.data_start = 2
        self.delim = ","

        # add list view of items in CSV Import folder
        label = QLabel("CSV Import Method")
        self.l = QListWidget()
        self.l.addItems(os.listdir("CSV Import"))
        self.l.setSelectionMode(QAbstractItemView.SingleSelection)

        # add load button - close when clicked
        b = QPushButton()
        b.setText("Load")
        b.clicked.connect(self.load_prof)

        # add create prof button
        c = QPushButton()
        c.setText("Create")
        c.clicked.connect(self.create_prof)

        # add a layout
        layout = QGridLayout()
        self.setLayout(layout)

        # add widgets to layout
        layout.addWidget(label, 0, 0, 1, 2, Qt.AlignCenter)
        layout.addWidget(self.l, 1, 0, 2, 2)
        layout.addWidget(b, 3, 0, 1, 1)
        layout.addWidget(c, 3, 1, 1, 1)

        # show
        self.show()

    def load_prof(self):
        # read csv profile
        if self.l.currentItem() == None:
            # tell the user to select or create a profile
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Import Method Needed")
            msg.setText("Uh oh!")
            msg.setInformativeText("No CSV import method selected. Please select an option"
                                   " or create a new method.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
            return
        else:
            f = open("CSV Import" + os.path.sep + self.l.currentItem().text(), "r")
            for i in f:
                str = i.split(":")
                if str[0] == "header":
                    self.header = int(str[1])
                elif str[0] == "data start":
                    self.data_start = int(str[1])
                elif str[0] == "delimiter":
                    self.delim = str[1]

        # close out
        self.close()

    def create_prof(self):
        # ask user for method details
        str, ok = QInputDialog.getMultiLineText(self, "CSV Import Method Details",
                                                "Enter 4 lines... Method Name (1), Header (2), Data Start (3), Delimiter (4)",
                                                text="Name\n1\n2\n,")
        if ok:
            # open file
            str = str.split("\n")
            f = open("CSV Import" + os.path.sep + str[0] + ".cm", "w")

            # write to file
            f.write("header:" + str[1] + "\n")
            f.write("data start:" + str[2] + "\n")
            f.write("delimiter:" + str[3])

            # close file
            f.close()

        # update list view
        self.l.clear()
        self.l.addItems(os.listdir("CSV Import"))

if __name__ == '__main__':
    # create application container
    app = QApplication(sys.argv)

    # instantiate GUI
    gui = Plot_Bot()

    # run application
    sys.exit(app.exec())