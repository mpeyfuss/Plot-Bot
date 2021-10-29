#!/usr/bin/python

'''
General plotting application where you can import txt, csv, and xlsx files, plot data in many different ways
(line, scatter, histogram, 3D, pair plot), save plotting profiles, exports png and html files, and interact 
with data in ways you can't with excel!
'''

# import packages
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
import dateutil
import webbrowser
import pandas as pd
import numexpr as ne
import math
import hjson
import plotly.express as px
import plotly.graph_objects as go
import plotly.offline
from plotly.subplots import make_subplots
from PyQt5.QtWidgets import QMainWindow, QCheckBox, QAction, QWidget, QGroupBox, QLabel, QSplitter, QHBoxLayout, QGridLayout, QLineEdit, QListWidget, QTabWidget, QComboBox, QSpinBox, QPushButton, QInputDialog, QApplication, QMessageBox, QFileDialog, QDialog, QListWidgetItem, QDesktopWidget, QAbstractItemView
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QUrl, QFileInfo, pyqtSlot
from PyQt5.QtWebEngineWidgets import QWebEngineView

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    #print('running in a PyInstaller bundle')
    try:
        ICON = sys._MEIPASS + os.path.sep + "Icons" + os.path.sep + "plot_bot.ico"
        SAVE_ICON = sys._MEIPASS + os.path.sep + "Icons" + os.path.sep + "save_icon.ico"
        OPEN_ICON = sys._MEIPASS + os.path.sep + "Icons" + os.path.sep + "open_icon.ico"
        PLOT_ICON = sys._MEIPASS + os.path.sep + "Icons" + os.path.sep + "run_icon.ico"
        EXPORT_ICON = sys._MEIPASS + os.path.sep + "Icons" + os.path.sep + "export_html.ico"
        DOC_PATH = sys._MEIPASS + os.path.sep + "Documents"
    except IOError:
        VERSION = "ERROR"
else:
    #print('running in a normal Python process')
    VERSION = "DEVELOPMENT VERSION"
    ICON = "Icons" + os.path.sep + "plot_bot.ico"
    SAVE_ICON = "Icons" + os.path.sep + "save_icon.ico"
    OPEN_ICON = "Icons" + os.path.sep + "open_icon.ico"
    PLOT_ICON = "Icons" + os.path.sep + "run_icon.ico"
    EXPORT_ICON = "Icons" + os.path.sep + "export_html.ico"
    DOC_PATH = "Documents"


# define application class
class Plot_Bot(QMainWindow):
    def __init__(self):
        # init
        super().__init__()

        # verify that the temp plot folder exists in this directory --> make directory if doesn't exist
        if not os.path.exists("Temp Plots"):
            os.mkdir("Temp Plots")

        # import app config file -- this stores locations for log files, default profiles, and file import methods
        with open("Plot_Bot.config", "r") as file:
            app_config = hjson.load(file)
            # create some object variables, making them if they don't exist
            self.log_path = app_config["Log_Path"]
            if not os.path.exists(self.log_path):
                os.makedirs(self.log_path)
            self.file_imports_path = app_config["File_Import_Methods_Path"]
            if not os.path.exists(self.file_imports_path):
                os.makedirs(self.file_imports_path)
            self.profiles_path = app_config["Profiles_Path"]
            if not os.path.exists(self.profiles_path):
                os.makedirs(self.profiles_path)

        # create logger
        self.log_file = self.log_path + os.path.sep + datetime.now().strftime("%Y-%m-%d %H.%M.%S") + ".log"
        logging.basicConfig(filename=self.log_file, filemode="w", level=logging.DEBUG)

        # more object variables
        self.filenames = []
        self.path = ""
        self.data = pd.DataFrame()
        self.version = "2.0"

        # base window creation
        self.resize(800, 800)
        self.center()
        self.setWindowTitle("Plot Bot")
        self.setWindowIcon(QIcon(ICON))

        # create menu & toolbar actions
        save_prof_action = QAction(QIcon(SAVE_ICON), "&Save Profile", self)
        save_prof_action.setShortcut("Ctrl+S")
        save_prof_action.setIconVisibleInMenu(False)
        save_prof_action.triggered.connect(self.save_prof)

        load_prof_action = QAction("&Load Profile", self)
        load_prof_action.setShortcut("Ctrl+L")
        load_prof_action.triggered.connect(self.load_prof)

        open_file_action = QAction(QIcon(OPEN_ICON), "&Open Data File", self)
        open_file_action.setShortcut("Ctrl+O")
        open_file_action.setIconVisibleInMenu(False)
        open_file_action.triggered.connect(self.open_file)

        plot_action = QAction(QIcon(PLOT_ICON), "&Update Plot", self)
        plot_action.setShortcut("Ctrl+R")
        plot_action.setIconVisibleInMenu(False)
        plot_action.triggered.connect(self.update_plot)

        export_csv_action = QAction("&Export Data to CSV", self)
        export_csv_action.setShortcut("Ctrl+E")
        export_csv_action.triggered.connect(self.export_csv)

        export_html_action = QAction(QIcon(EXPORT_ICON), "&Export HTML", self)
        export_html_action.setShortcut("Ctrl+H")
        export_html_action.setIconVisibleInMenu(False)
        export_html_action.triggered.connect(self.export_html)

        unit_conversion_action = QAction("&Unit Conversion", self)
        unit_conversion_action.setShortcut("Ctrl+U")
        unit_conversion_action.triggered.connect(self.add_unit_conversion)

        math_action = QAction("&Add Math Channel", self)
        math_action.setShortcut("Ctrl+M")
        math_action.triggered.connect(self.add_math_channel)

        user_manual_action = QAction("&User Manual", self)
        user_manual_action.setShortcut("Ctrl+Shift+U")
        user_manual_action.triggered.connect(self.open_user_manual)

        #open_issue_action = QAction("&Report Issue", self)
        #open_issue_action.setShortcut("Ctrl+Shift+R")
        #open_issue_action.triggered.connect(self.open_issue)

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
        data_menu.addAction(export_csv_action)
        data_menu.addAction(plot_action)
        data_menu.addAction(export_html_action)

        math_menu = menu_bar.addMenu("&Math")
        math_menu.addAction(unit_conversion_action)
        math_menu.addAction(math_action)

        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction(user_manual_action)
        #help_menu.addAction(open_issue_action)
        help_menu.addAction(get_version_action)

        # create toolbar
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.addAction(save_prof_action)
        self.toolbar.addAction(open_file_action)
        self.toolbar.addAction(plot_action)
        self.toolbar.addAction(export_html_action)

        # central widget
        wid = QWidget(self)
        self.setCentralWidget(wid)

        # create left side splitter (vertical splitter)
        top_left_frame = QGroupBox("File Information")
        top_left_frame.setMinimumWidth(400)
        top_left_frame.setMaximumWidth(500)
        #top_left_frame.setFrameShape(QFrame.StyledPanel)
        bottom_left_frame = QGroupBox("Chart Settings")
        bottom_left_frame.setMinimumWidth(400)
        bottom_left_frame.setMaximumWidth(500)
        #bottom_left_frame.setFrameShape(QFrame.StyledPanel)
        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.addWidget(top_left_frame)
        v_splitter.addWidget(bottom_left_frame)
        v_splitter.setSizes([30, 70])

        # create overall horizontal splitter
        hbox = QHBoxLayout(wid)
        right_frame = QGroupBox("Chart Display")
        #right_frame.setFrameShape(QFrame.StyledPanel)
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

        # create path display widgets
        path_disp_label = QLabel("Current Path")
        path_disp_label.setAlignment(Qt.AlignRight)
        self.path_disp = QLineEdit()
        self.path_disp.setAlignment(Qt.AlignLeft)
        self.path_disp.setReadOnly(True)

        # create file names dislay
        filenames_disp_label = QLabel("Current Files")
        filenames_disp_label.setAlignment(Qt.AlignRight)
        self.files_disp = QListWidget()
        self.files_disp.setItemAlignment(Qt.AlignLeft)
        self.files_disp.setDragEnabled(False)
        self.files_disp.setAcceptDrops(False)
        self.files_disp.setMaximumHeight(100)

        # create variable list display
        var_list_label = QLabel("Variables")
        var_list_label.setAlignment(Qt.AlignRight)
        self.var_list = QListWidget()
        self.var_list.setItemAlignment(Qt.AlignLeft)
        self.var_list.setDragEnabled(True)
        self.var_list.setAcceptDrops(False)
        self.var_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        upper_grid.addWidget(path_disp_label, 0, 0, 1, 1, Qt.AlignTop)
        upper_grid.addWidget(self.path_disp, 0, 1, 1, 1)

        upper_grid.addWidget(filenames_disp_label, 1, 0, 1, 1, Qt.AlignTop)
        upper_grid.addWidget(self.files_disp, 1, 1, 1, 1)

        upper_grid.addWidget(var_list_label, 2, 0, 1, 1, Qt.AlignTop)
        upper_grid.addWidget(self.var_list, 2, 1, 4, 1)

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

        ts_chart_title_label = QLabel("Chart Title")
        self.ts_chart_title = QLineEdit()
        self.ts_chart_title.setAlignment(Qt.AlignLeft)

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
        ts_grid.addWidget(self.clear_ts_button, 0, 4, 1, 2, Qt.AlignRight)
        ts_grid.addWidget(ts_t_label, 1, 0, 1, 1, Qt.AlignRight)
        ts_grid.addWidget(self.ts_t_disp, 1, 1, 1, 2, Qt.AlignVCenter)
        ts_grid.addWidget(ts_chart_title_label, 1, 3, 1, 1, Qt.AlignRight)
        ts_grid.addWidget(self.ts_chart_title, 1, 4, 1, 2)
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

        xy_chart_title_label = QLabel("Chart Title")
        self.xy_chart_title = QLineEdit()
        self.xy_chart_title.setAlignment(Qt.AlignLeft)

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

        # add X-Y widgets to grid
        xy_grid = QGridLayout()
        self.setup_panel.setCurrentIndex(1)
        self.setup_panel.currentWidget().setLayout(xy_grid)
        xy_grid.addWidget(xy_style_label, 0, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        xy_grid.addWidget(self.xy_style_disp, 0, 1, 1, 2)
        xy_grid.addWidget(xy_chart_title_label, 1, 0 , 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        xy_grid.addWidget(self.xy_chart_title, 1, 1, 1, 2)
        xy_grid.addWidget(xy_x_label, 2, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        xy_grid.addWidget(self.xy_x_disp, 2, 1, 1, 2)
        xy_grid.addWidget(xy_x_title_label, 3, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        xy_grid.addWidget(self.xy_x_title, 3, 1, 1, 2)
        xy_grid.addWidget(self.xy_x_log, 4, 0, 1, 1, Qt.AlignLeft)
        xy_grid.addWidget(xy_y_label, 5, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        xy_grid.addWidget(self.xy_y_disp, 5, 1, 1, 2)
        xy_grid.addWidget(xy_y_title_label, 6, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        xy_grid.addWidget(self.xy_y_title, 6, 1, 1, 2)
        xy_grid.addWidget(self.xy_y_log, 7, 0, 1, 1, Qt.AlignLeft)
        xy_grid.addWidget(xy_color_label, 8, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        xy_grid.addWidget(self.xy_color_disp, 8, 1, 1, 2)
        xy_grid.addWidget(xy_trendline_label, 9, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        xy_grid.addWidget(self.xy_trendline_disp, 9, 1, 1, 2)
        

        # create widgets for 3D tab
        three_dim_chart_title_label = QLabel("Chart Title")
        self.three_dim_chart_title = QLineEdit()
        self.three_dim_chart_title.setAlignment(Qt.AlignLeft)

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
        three_dim_grid.addWidget(three_dim_chart_title_label, 0, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        three_dim_grid.addWidget(self.three_dim_chart_title, 0, 1, 1, 2)
        three_dim_grid.addWidget(three_dim_x_label, 1, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        three_dim_grid.addWidget(self.three_dim_x_disp, 1, 1, 1, 2)
        three_dim_grid.addWidget(three_dim_x_title_label, 2, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        three_dim_grid.addWidget(self.three_dim_x_title, 2, 1, 1, 2)
        three_dim_grid.addWidget(three_dim_y_label, 3, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        three_dim_grid.addWidget(self.three_dim_y_disp, 3, 1, 1, 2)
        three_dim_grid.addWidget(three_dim_y_title_label, 4, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        three_dim_grid.addWidget(self.three_dim_y_title, 4, 1, 1, 2)
        three_dim_grid.addWidget(three_dim_z_label, 5, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        three_dim_grid.addWidget(self.three_dim_z_disp, 5, 1, 1, 2)
        three_dim_grid.addWidget(three_dim_z_title_label, 6, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        three_dim_grid.addWidget(self.three_dim_z_title, 6, 1, 1, 2)
        three_dim_grid.addWidget(three_dim_color_label, 7, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        three_dim_grid.addWidget(self.three_dim_color_disp, 7, 1, 1, 2)

        # create widgets for histogram
        hist_chart_title_label = QLabel("Chart Title")
        self.hist_chart_title = QLineEdit()
        self.hist_chart_title.setAlignment(Qt.AlignLeft)

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
        hist_grid.addWidget(hist_chart_title_label, 0, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        hist_grid.addWidget(self.hist_chart_title, 0, 1, 1, 2)
        hist_grid.addWidget(hist_x_label, 1, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        hist_grid.addWidget(self.hist_x_disp, 1, 1, 1, 2)
        hist_grid.addWidget(hist_x_title_label, 2, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        hist_grid.addWidget(self.hist_x_title, 2, 1, 1, 2)
        hist_grid.addWidget(hist_num_bins_label, 3, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        hist_grid.addWidget(self.hist_num_bins_disp, 3, 1, 1, 2)
        hist_grid.addWidget(hist_normal_label, 4, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        hist_grid.addWidget(self.hist_normal_disp, 4, 1, 1, 2)
        hist_grid.addWidget(hist_color_label, 5, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        hist_grid.addWidget(self.hist_color_disp, 5, 1, 1, 2)
        hist_grid.addWidget(hist_func_label, 6, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        hist_grid.addWidget(self.hist_func_disp, 6, 1, 1, 2)
        hist_grid.addWidget(hist_y_label, 7, 0, 1, 1, Qt.AlignVCenter | Qt.AlignRight)
        hist_grid.addWidget(self.hist_y_disp, 7, 1, 1, 2)

        # create widgets for pair plot
        pp_chart_title_label = QLabel("Chart Title")
        self.pp_chart_title = QLineEdit()
        self.pp_chart_title.setAlignment(Qt.AlignLeft)

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
        pp_grid.addWidget(pp_chart_title_label, 0, 0, 1, 1, Qt.AlignHCenter | Qt.AlignBottom)
        pp_grid.addWidget(self.pp_chart_title, 1, 0, 1, 1, Qt.AlignTop)
        pp_grid.addWidget(pp_var_label, 2, 0, 1, 1, Qt.AlignBottom | Qt.AlignHCenter)
        pp_grid.addWidget(self.pp_var_disp, 3, 0, 1, 1)
        pp_grid.addWidget(pp_color_label, 0, 1, 1, 1, Qt.AlignHCenter | Qt.AlignBottom)
        pp_grid.addWidget(self.pp_color_disp, 1, 1, 1, 1, Qt.AlignTop)
        pp_grid.addWidget(pp_clear_button, 3, 1, 1, 1, Qt.AlignBottom)

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
        self.ts_plot.page().profile().downloadRequested.connect(self.download_requested)
        ts_plot_grid = QGridLayout()
        self.plot_panel.setCurrentIndex(0)
        self.plot_panel.currentWidget().setLayout(ts_plot_grid)
        ts_plot_grid.addWidget(self.ts_plot)

        self.xy_plot = QWebEngineView()
        self.xy_plot.page().profile().downloadRequested.connect(self.download_requested)
        xy_plot_grid = QGridLayout()
        self.plot_panel.setCurrentIndex(1)
        self.plot_panel.currentWidget().setLayout(xy_plot_grid)
        xy_plot_grid.addWidget(self.xy_plot)

        self.three_dim_plot = QWebEngineView()
        self.three_dim_plot.page().profile().downloadRequested.connect(self.download_requested)
        three_dim_plot_grid = QGridLayout()
        self.plot_panel.setCurrentIndex(2)
        self.plot_panel.currentWidget().setLayout(three_dim_plot_grid)
        three_dim_plot_grid.addWidget(self.three_dim_plot)

        self.hist_plot = QWebEngineView()
        self.hist_plot.page().profile().downloadRequested.connect(self.download_requested)
        hist_plot_grid = QGridLayout()
        self.plot_panel.setCurrentIndex(3)
        self.plot_panel.currentWidget().setLayout(hist_plot_grid)
        hist_plot_grid.addWidget(self.hist_plot)

        self.pp_plot = QWebEngineView()
        self.pp_plot.page().profile().downloadRequested.connect(self.download_requested)
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
            with open(self.profiles_path + os.path.sep + name + ".pbprof", "w") as f:

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

                # create dictionary for time series plotting
                ts_d = {"Number of Subplots":self.ts_num_subplots_disp.value(),
                        "Chart Title":self.ts_chart_title.text(),
                        "Time Variable":self.ts_t_disp.currentText(),
                        "Y1 Left Variables":y1_l, "Y1 Left Log Plot":self.y1_left_log.isChecked(), "Y1 Left Axis Title":self.y1_left_ax_label.text(),
                        "Y1 Right Variables":y1_r, "Y1 Right Log Plot":self.y1_right_log.isChecked(), "Y1 Right Axis Title":self.y1_right_ax_label.text(),
                        "Y2 Left Variables":y2_l, "Y2 Left Log Plot":self.y2_left_log.isChecked(), "Y2 Left Axis Title":self.y2_left_ax_label.text(),
                        "Y2 Right Variables":y2_r, "Y2 Right Log Plot":self.y2_right_log.isChecked(), "Y2 Right Axis Title":self.y2_right_ax_label.text(),
                        "Y3 Left Variables":y3_l, "Y3 Left Log Plot":self.y3_left_log.isChecked(), "Y3 Left Axis Title":self.y3_left_ax_label.text(),
                        "Y3 Right Variables":y3_r, "Y3 Right Log Plot":self.y3_right_log.isChecked(), "Y3 Right Axis Title":self.y3_right_ax_label.text(),
                        "Y4 Left Variables":y4_l, "Y4 Left Log Plot":self.y4_left_log.isChecked(), "Y4 Left Axis Title":self.y4_left_ax_label.text(),
                        "Y4 Right Variables":y4_r, "Y4 Right Log Plot":self.y4_right_log.isChecked(), "Y4 Right Axis Title":self.y4_right_ax_label.text()}

                # create dictionary for x-y plotting
                xy_d = {"Chart Title":self.xy_chart_title.text(),
                        "Line Style":self.xy_style_disp.currentText(),
                        "X Variable":self.xy_x_disp.currentText(),
                        "X Axis Title":self.xy_x_title.text(),
                        "X Axis Log Plot":self.xy_x_log.isChecked(),
                        "Y Variable":self.xy_y_disp.currentText(),
                        "Y Axis Title":self.xy_y_title.text(),
                        "Y Axis Log Plot":self.xy_y_log.isChecked(),
                        "Color Variable":self.xy_color_disp.currentText(),
                        "Trendline":self.xy_trendline_disp.currentText()
                        }

                # create dict for three d plotting
                three_d = {"Chart Title":self.three_dim_chart_title.text(),
                        "X Variable":self.three_dim_x_disp.currentText(),
                        "X Axis Title":self.three_dim_x_title.text(),
                        "Y Variable":self.three_dim_y_disp.currentText(),
                        "Y Axis Title":self.three_dim_y_title.text(),
                        "Z Variable":self.three_dim_z_disp.currentText(),
                        "Z Axis Title":self.three_dim_z_title.text(),
                        "Color Variable":self.three_dim_color_disp.currentText()}

                # create dict for histogram
                hist_d = {"Chart Title":self.hist_chart_title.text(),
                        "X Variable":self.hist_x_disp.currentText(),
                        "X Axis Title":self.hist_x_title.text(),
                        "Number of Bins":self.hist_num_bins_disp.value(),
                        "Normalization":self.hist_normal_disp.currentText(),
                        "Color Variable":self.hist_color_disp.currentText(),
                        "Bin Function":self.hist_func_disp.currentText(),
                        "Y Variable":self.hist_y_disp.currentText()}

                # create dict for pair plot
                pp_d = {"Chart Title":self.pp_chart_title.text(),
                        "Variables":pp,
                        "Color Variable":self.pp_color_disp.currentText()}

                # create dictionary of all items needed
                d = {"Time Series":ts_d,
                    "X-Y":xy_d,
                    "3D":three_d,
                    "Histogram":hist_d,
                    "Pair Plot":pp_d}

                # write dictionary to file
                hjson.dump(d, f)

        except Exception:
            logging.exception("Exception thrown while saving profile!")
            msg = QMessageBox()
            msg.setWindowTitle("Something Went Wrong")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Uh oh!")
            msg.setInformativeText("Looks like something went wrong. Please check %s" % self.log_file)
            msg.exec()

    def load_prof(self):
        try:
            # ask user for file
            (file, _) = QFileDialog.getOpenFileName(filter="*.pbprof", caption="Select File", directory=self.profiles_path)

            # cancel handling
            if file == "":
                return

            # open file
            with open(file, "r") as f:
                main_d = hjson.load(f)

            # write values to timeseries data
            d = main_d["Time Series"]
            self.ts_chart_title.setText(d["Chart Title"])
            self.ts_num_subplots_disp.setValue(d["Number of Subplots"])
            self.ts_t_disp.setCurrentText(d["Time Variable"])
            self.y1_left_disp.clear()
            self.y1_left_disp.addItems(d["Y1 Left Variables"])
            self.y1_left_ax_label.setText(d["Y1 Left Axis Title"])
            self.y1_left_log.setChecked(d["Y1 Left Log Plot"])
            self.y1_right_disp.clear()
            self.y1_right_disp.addItems(d["Y1 Right Variables"])
            self.y1_right_ax_label.setText(d["Y1 Right Axis Title"])
            self.y1_right_log.setChecked(d["Y1 Right Log Plot"])
            self.y2_left_disp.clear()
            self.y2_left_disp.addItems(d["Y2 Left Variables"])
            self.y2_left_ax_label.setText(d["Y2 Left Axis Title"])
            self.y2_left_log.setChecked(d["Y2 Left Log Plot"])
            self.y2_right_disp.clear()
            self.y2_right_disp.addItems(d["Y2 Right Variables"])
            self.y2_right_ax_label.setText(d["Y2 Right Axis Title"])
            self.y2_right_log.setChecked(d["Y2 Right Log Plot"])
            self.y3_left_disp.clear()
            self.y3_left_disp.addItems(d["Y3 Left Variables"])
            self.y3_left_ax_label.setText(d["Y3 Left Axis Title"])
            self.y3_left_log.setChecked(d["Y3 Left Log Plot"])
            self.y3_right_disp.clear()
            self.y3_right_disp.addItems(d["Y3 Right Variables"])
            self.y3_right_ax_label.setText(d["Y3 Right Axis Title"])
            self.y3_right_log.setChecked(d["Y3 Right Log Plot"])
            self.y4_left_disp.clear()
            self.y4_left_disp.addItems(d["Y4 Left Variables"])
            self.y4_left_ax_label.setText(d["Y4 Left Axis Title"])
            self.y4_left_log.setChecked(d["Y4 Left Log Plot"])
            self.y4_right_disp.clear()
            self.y4_right_disp.addItems(d["Y4 Right Variables"])
            self.y4_right_ax_label.setText(d["Y4 Right Axis Title"])
            self.y4_right_log.setChecked(d["Y4 Right Log Plot"])

            # write xy items
            d = main_d["X-Y"]
            self.xy_chart_title.setText(d["Chart Title"])
            self.xy_style_disp.setCurrentText(d["Line Style"])
            self.xy_x_disp.setCurrentText(d["X Variable"])
            self.xy_x_title.setText(d["X Axis Title"])
            self.xy_x_log.setChecked(d["X Axis Log Plot"])
            self.xy_y_disp.setCurrentText(d["Y Variable"])
            self.xy_y_title.setText(d["Y Axis Title"])
            self.xy_y_log.setChecked(d["Y Axis Log Plot"])
            self.xy_color_disp.setCurrentText(d["Color Variable"])
            self.xy_trendline_disp.setCurrentText(d["Trendline"])

            # set 3d tab values
            d = main_d["3D"]
            self.three_dim_chart_title.setText(d["Chart Title"])
            self.three_dim_x_disp.setCurrentText(d["X Variable"])
            self.three_dim_x_title.setText(d["X Axis Title"])
            self.three_dim_y_disp.setCurrentText(d["Y Variable"])
            self.three_dim_y_title.setText(d["Y Axis Title"])
            self.three_dim_z_disp.setCurrentText(d["Z Variable"])
            self.three_dim_z_title.setText(d["Z Axis Title"])
            self.three_dim_color_disp.setCurrentText(d["Color Variable"])

            # set histogram values
            d = main_d["Histogram"]
            self.hist_chart_title.setText(d["Chart Title"])
            self.hist_x_disp.setCurrentText(d["X Variable"])
            self.hist_x_title.setText(d["X Axis Title"])
            self.hist_num_bins_disp.setValue(d["Number of Bins"])
            self.hist_normal_disp.setCurrentText(d["Normalization"])
            self.hist_color_disp.setCurrentText(d["Color Variable"])
            self.hist_func_disp.setCurrentText(d["Bin Function"])
            self.hist_y_disp.setCurrentText(d["Y Variable"])

            # set pair plot values
            d = main_d["Pair Plot"]
            self.pp_chart_title.setText(d["Chart Title"])
            self.pp_var_disp.clear()
            self.pp_var_disp.addItems(d["Variables"])
            self.pp_color_disp.setCurrentText(d["Color Variable"])

        except Exception:
            logging.exception("Exception thrown while saving profile!")
            msg = QMessageBox()
            msg.setWindowTitle("Something Went Wrong")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Uh oh!")
            msg.setInformativeText("Looks like something went wrong. Please check %s" % self.log_file)
            msg.exec()

    def open_file(self):
        # ask user for file
        (files, _) = QFileDialog.getOpenFileNames(filter="Text (*.csv *.txt);; Workbook (*.xls *.xlsx)", caption="Select File", directory=os.path.abspath(os.sep))

        # cancel handling
        if not files:
            return

        # sort files by date
        files.sort(key=os.path.getctime)

        #print(files)

        # get header and data start rows
        d = File_Import_Settings(self.file_imports_path)
        d.exec()

        # make sure the usre actually loaded in settings
        if not d.loaded:
            return

        # create list of rows between header and data start
        if d.data_start - d.header <= 1:
            head = d.header - 1
        else:
            head = range(start=d.header-1, stop=d.data_start-2)

        # determine path
        i = files[0].rfind("/")
        self.path = files[0][0:i+1]

        # get filenames
        self.filenames = []
        for file in files:
            i = file.rfind("/")
            self.filenames.append(file[i+1:])

        # show path
        self.path_disp.setText(self.path)

        # show filenames in the proper field
        self.files_disp.clear()
        self.files_disp.addItems(self.filenames)

        # set date/time parser for loading data
        if d.datetime_format.lower() == "iso":
            date_format = True
            date_parser = dateutil.parser.isoparse
        else: # unix epoch
            date_format = False
            date_parser = None

        # concatenate dataframes
        self.data = pd.DataFrame()
        import_success = True
        for file in files:
            # load in file, with error handling
            try:
                # determine whether it is a txt file or speadsheet
                if d.file_type.lower() == "text":
                    data = pd.read_csv(file, header=head, sep=d.delim, skip_blank_lines=False, infer_datetime_format=date_format, date_parser=date_parser)
                elif d.file_type.lower() == "spreadsheet":
                    data = pd.read_excel(file, sheet_name=d.sheet, header=head)
                # concat data
                self.data = pd.concat([self.data, data])
            except Exception:
                logging.exception("Exception thrown while loading in file(s)!")
                import_success = False
        
        if not import_success:
            msg = QMessageBox()
            msg.setWindowTitle("Something Went Wrong")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Uh oh!")
            msg.setInformativeText("Looks like something went wrong loading the files. Please check %s" % self.log_file)
            msg.exec()

        # update combo & list boxes
        if not self.data.empty:
            self.update_variable_holders()

    def update_variable_holders(self):
        # var list widget
        self.var_list.clear()
        self.var_list.addItems(self.data.columns)
        # time series time box, trying to save what was last in there
        str = self.ts_t_disp.currentText()
        self.ts_t_disp.clear()
        self.ts_t_disp.addItem("")
        self.ts_t_disp.addItems(self.data.columns)
        loc = self.ts_t_disp.findText(str)
        if not loc == -1:
            self.ts_t_disp.setCurrentIndex(loc)
        # xy items, trying to keep values from before
        str = self.xy_x_disp.currentText()
        self.xy_x_disp.clear()
        self.xy_x_disp.addItem("")
        self.xy_x_disp.addItems(self.data.columns)
        loc = self.xy_x_disp.findText(str)
        if not loc == -1:
            self.xy_x_disp.setCurrentIndex(loc)
        
        str = self.xy_y_disp.currentText()
        self.xy_y_disp.clear()
        self.xy_y_disp.addItem("")
        self.xy_y_disp.addItems(self.data.columns)
        loc = self.xy_y_disp.findText(str)
        if not loc == -1:
            self.xy_y_disp.setCurrentIndex(loc)
        
        str = self.xy_color_disp.currentText()
        self.xy_color_disp.clear()
        self.xy_color_disp.addItem("None")
        self.xy_color_disp.addItems(self.data.columns)
        loc = self.xy_color_disp.findText(str)
        if not loc == -1:
            self.xy_color_disp.setCurrentIndex(loc)

        # 3D
        str = self.three_dim_x_disp.currentText()
        self.three_dim_x_disp.clear()
        self.three_dim_x_disp.addItem("")
        self.three_dim_x_disp.addItems(self.data.columns)
        loc = self.three_dim_x_disp.findText(str)
        if not loc == -1:
            self.three_dim_x_disp.setCurrentIndex(loc)

        str = self.three_dim_y_disp.currentText()
        self.three_dim_y_disp.clear()
        self.three_dim_y_disp.addItem("")
        self.three_dim_y_disp.addItems(self.data.columns)
        loc = self.three_dim_y_disp.findText(str)
        if not loc == -1:
            self.three_dim_y_disp.setCurrentIndex(loc)

        str = self.three_dim_z_disp.currentText()
        self.three_dim_z_disp.clear()
        self.three_dim_z_disp.addItem("")
        self.three_dim_z_disp.addItems(self.data.columns)
        loc = self.three_dim_z_disp.findText(str)
        if not loc == -1:
            self.three_dim_z_disp.setCurrentIndex(loc)

        str = self.three_dim_color_disp.currentText()
        self.three_dim_color_disp.clear()
        self.three_dim_color_disp.addItem("None")
        self.three_dim_color_disp.addItems(self.data.columns)
        loc = self.three_dim_color_disp.findText(str)
        if not loc == -1:
            self.three_dim_color_disp.setCurrentIndex(loc)

        # hist
        str = self.hist_x_disp.currentText()
        self.hist_x_disp.clear()
        self.hist_x_disp.addItem("")
        self.hist_x_disp.addItems(self.data.columns)
        loc = self.hist_x_disp.findText(str)
        if not loc == -1:
            self.hist_x_disp.setCurrentIndex(loc)

        str = self.hist_y_disp.currentText() 
        self.hist_y_disp.clear()
        self.hist_y_disp.addItem("")
        self.hist_y_disp.addItems(self.data.columns)
        loc = self.hist_y_disp.findText(str)
        if not loc == -1:
            self.hist_y_disp.setCurrentIndex(loc)

        str = self.hist_color_disp.currentText()
        self.hist_color_disp.clear()
        self.hist_color_disp.addItem("None")
        self.hist_color_disp.addItems(self.data.columns)
        loc = self.hist_color_disp.findText(str)
        if not loc == -1:
            self.hist_color_disp.setCurrentIndex(loc)

        # pair plot
        str = self.pp_color_disp.currentText()
        self.pp_color_disp.clear()
        self.pp_color_disp.addItem("None")
        self.pp_color_disp.addItems(self.data.columns)
        loc = self.pp_color_disp.findText(str)
        if not loc == -1:
            self.pp_color_disp.setCurrentIndex(loc)

    def update_plot(self):
        try:
            # determine what plot is active
            if self.plot_panel.tabText(self.plot_panel.currentIndex()) == "&Time Series":
                # check that time and at least y1 are populated with variables
                if not self.ts_t_disp.currentText() == "" and self.y1_left_disp.count() > 0:
                    # create time variable
                    t_var = self.ts_t_disp.currentText()

                    # get title
                    if self.ts_chart_title.text() == "":
                        chart_title = None
                    else:
                        chart_title = self.ts_chart_title.text()

                    # determine number of subplots
                    n_sub = self.ts_num_subplots_disp.value()

                    # create specs for subplots
                    spec = []
                    for i in range(0,n_sub):
                        spec.append([{"secondary_y":True}])

                    # create subplots
                    fig = make_subplots(rows=n_sub, cols=1, shared_xaxes=True, specs=spec)

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

                    # update x axis
                    fig.update_xaxes(title="Time", nticks=30, tickmode="auto")

                    # update title
                    fig.update_layout(title_text=chart_title, title_x=0.5)

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
                    # get title
                    if self.xy_chart_title.text() == "":
                        chart_title = None
                    else:
                        chart_title = self.xy_chart_title.text()
                    
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
                        trend = None
                    
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

                    # update title
                    fig.update_layout(title_text=chart_title, title_x=0.5)

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
                    # get title
                    if self.three_dim_chart_title.text() == "":
                        chart_title = None
                    else:
                        chart_title = self.three_dim_chart_title.text()
                    
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
                    fig.update_layout(title_text=chart_title, title_x=0.5, title_y=0.92)

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
                    # get title
                    if self.hist_chart_title.text() == "":
                        chart_title = None
                    else:
                        chart_title = self.hist_chart_title.text()
                    
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
                    fig.update_layout(title_text=chart_title, title_x=0.5)

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
                    # get title
                    if self.pp_chart_title.text() == "":
                        chart_title = None
                    else:
                        chart_title = self.pp_chart_title.text()
                    
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

                    fig.update_layout(title_text=chart_title, title_x=0.5)

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
            logging.error(e)
            msg = QMessageBox()
            msg.setWindowTitle("Something Went Wrong")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Uh oh!")
            msg.setInformativeText("Looks like something went wrong. Make sure you have all the right variables when using a profile. For more help, check %s" % self.log_file)
            msg.exec()

    def open_user_manual(self):
        webbrowser.open(DOC_PATH + os.path.sep + "Plot_Bot_User_Manual.pdf")

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
        msg.setText("%s" % self.version)
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

    def export_csv(self):
        try:
            # ask user for save location
            file, _ = QFileDialog.getSaveFileName(directory=os.path.join(Path.home(), ""), caption="Export File To", filter="*.csv")
            
            # handle cancel
            if file == "":
                return

            # check that data field is not empty
            if self.data.empty:
                return
            
            # export dataframe to csv file
            self.data.to_csv(file)

            # print message saying success
            msg = QMessageBox()
            msg.setWindowTitle("Success!")
            msg.setIcon(QMessageBox.Information)
            msg.setText("Export was successful!")
            msg.exec()
        except Exception as e:
            logging.error(e)
            msg = QMessageBox()
            msg.setWindowTitle("Something Went Wrong")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Uh oh!")
            msg.setInformativeText("Looks like something went wrong exporting the data. Please check %s" % self.log_file)
            msg.exec()

    def export_html(self):
        try:
            # ask user for save location
            file, _ = QFileDialog.getSaveFileName(directory=os.path.join(Path.home(), ""), caption="Save File As", filter="*.html")
            
            # handle cancel
            if file == "":
                return
            
            # move current plot to file
            if self.plot_panel.tabText(self.plot_panel.currentIndex()) == "&Time Series":
                base_file = "ts_temp.html"
            elif self.plot_panel.tabText(self.plot_panel.currentIndex()) == "&X-Y":
                base_file = "xy_temp.html"
            elif self.plot_panel.tabText(self.plot_panel.currentIndex()) == "&3D":
                base_file = "3d_temp.html"
            elif self.plot_panel.tabText(self.plot_panel.currentIndex()) == "&Histogram":
                base_file = "hist_temp.html"
            elif self.plot_panel.tabText(self.plot_panel.currentIndex()) == "&Pair Plot":
                base_file = "pp_temp.html"
            else:
                return

            # move
            os.rename("Temp Plots" + os.path.sep + base_file, file)

            # print message saying success
            msg = QMessageBox()
            msg.setWindowTitle("Success!")
            msg.setIcon(QMessageBox.Information)
            msg.setText("Export was successful!")
            msg.exec()
        except Exception as e:
            logging.error(e)
            msg = QMessageBox()
            msg.setWindowTitle("Something Went Wrong")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Uh oh!")
            msg.setInformativeText("Looks like something went wrong exporting the plot. Please check %s" % self.log_file)
            msg.exec()

    def add_unit_conversion(self):
        # open the conversion GUI, passing in the data
        u_app = Add_Conversion(self.data)
        u_app.exec()

        # check to make sure data was changed
        if u_app.data_changed:
            # copy over data
            self.data = u_app.data
            # reload needed items
            self.update_variable_holders()

    def add_math_channel(self):
        # open math channel GUI, passing in the data
        m_app = Add_Math_Channel(self.data)
        m_app.exec()

        # check to make sure data was changed
        if m_app.data_changed:
            # copy over data
            self.data = m_app.data
            # reload needed items
            self.update_variable_holders()

    @pyqtSlot("QWebEngineDownloadItem*")
    def download_requested(self, download):
        # accept the download item
        download.accept()

        # if download is complete, call download finished function
        if download.isFinished():
            Plot_Bot.download_finished()

    @classmethod
    def download_finished():
        # delete any .tmp files created
        files = os.listdir(os.path.join(Path.home(), "Downloads"))
        for file in files:
            if file[-3:] == "tmp":
                os.remove(file)
        
        
class File_Import_Settings(QDialog):
    def __init__(self, folder="C:\\Data\\Plot_Bot\\File_Import"):
        QDialog.__init__(self)

        # create window
        self.resize(300, 250)

        # set window title
        self.setWindowTitle("Select File Import Method")

        # create variables
        self.folder = folder
        self.file_type = "text"
        self.datetime_format = "ISO"
        self.header = 1
        self.data_start = 2
        self.delim = ","
        self.sheet = None
        self.loaded = False

        # add list view of items in file import folder
        label = QLabel("File Import Method")
        self.l = QListWidget()
        self.l.addItems(os.listdir(self.folder))
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
            msg.setWindowTitle("File Import Method Needed")
            msg.setText("Uh oh!")
            msg.setInformativeText("No CSV import method selected. Please select an option"
                                   " or create a new method.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
            return
        else:
            with open(self.folder + os.path.sep + self.l.currentItem().text(), "r") as file:
                data = hjson.load(file)

            # enumerate delimiter
            delim_enum = {"Comma":",", "Semicolon":";", "Tab":"\t"}
            # assign variables
            self.file_type = data["File_Type"].lower()
            self.header = data["Header_Row"]
            self.data_start = data["Data_Row"]
            if (self.file_type == "text"):
                self.sheet = None
                self.delim = delim_enum[data["Delimiter"]]
            elif (self.file_type == "spreadsheet"):
                self.sheet = data["Sheet"]
                self.delim = None
            self.datetime_format = data["Datetime_Format"]

            self.loaded = True
                
        # close out
        self.close()

    def create_prof(self):
        # ask user for method details
        d = Create_File_Import_Method(self.folder)
        d.exec()

        if d.saved:
            # update list view
            self.l.clear()
            self.l.addItems(os.listdir(self.folder))

class Create_File_Import_Method(QDialog):
    def __init__(self, folder):
        QDialog.__init__(self)

        # create a window
        self.resize(200,200)

        # set window title
        self.setWindowTitle("Create File Import Method")

        # properties
        self.folder = folder
        self.saved = False

        # create inputs
        self.name = QLineEdit()
        self.file_type = QComboBox()
        self.file_type.addItem("Text")
        self.file_type.addItem("Spreadsheet")
        self.header_input = QSpinBox()
        self.header_input.setMinimum(1)
        self.header_input.valueChanged.connect(self.header_changed)
        self.data_input = QSpinBox()
        self.data_input.setMinimum(self.header_input.value() + 1)
        self.data_input.valueChanged.connect(self.data_changed)
        self.delimiter_input = QComboBox()
        self.delimiter_input.addItems(["Comma", "Semicolon", "Tab"])
        self.sheet_input = QLineEdit()
        self.datetime_input = QComboBox()
        self.datetime_input.addItems(["ISO", "Unix Epoch"])
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save)

        # set layout and add items
        self.setLayout(QGridLayout())
        self.layout().addWidget(QLabel("Method Name"), 0, 0, 1, 1, Qt.AlignRight)
        self.layout().addWidget(self.name, 0, 1, 1, 1)
        self.layout().addWidget(QLabel("File Type"), 0, 2, 1, 1, Qt.AlignRight)
        self.layout().addWidget(self.file_type, 0, 3, 1, 1)
        self.layout().addWidget(QLabel("Header Row"), 1, 0, 1, 1, Qt.AlignRight)
        self.layout().addWidget(self.header_input, 1, 1, 1, 1)
        self.layout().addWidget(QLabel("Data Row"), 1, 2, 1 ,1, Qt.AlignRight)
        self.layout().addWidget(self.data_input, 1, 3, 1, 1)
        self.layout().addWidget(QLabel("Delimiter Type"), 2, 0, 1, 1, Qt.AlignRight)
        self.layout().addWidget(self.delimiter_input, 2, 1, 1, 1)
        self.layout().addWidget(QLabel("Sheet"), 2, 2, 1, 1, Qt.AlignRight)
        self.layout().addWidget(self.sheet_input, 2, 3, 1, 1)
        self.layout().addWidget(QLabel("Datetime Format"), 3, 0, 1, 1, Qt.AlignRight)
        self.layout().addWidget(self.datetime_input, 3, 1, 1, 1)
        self.layout().addWidget(self.save_button, 3, 3, 1, 1)

        self.show()

    def header_changed(self):
        if self.data_input.value() <= self.header_input.value():
            self.data_input.setValue(self.header_input.value() + 1)

    def data_changed(self):
        if self.header_input.value() >= self.data_input.value():
            self.header_input.setValue(self.data_input.value() - 1)

    def save(self):
        # create dictionary with items
        d = {"File_Type": self.file_type.currentText(),
         "Header_Row":self.header_input.value(),
         "Data_Row":self.data_input.value(),
         "Delimiter":self.delimiter_input.currentText(),
         "Sheet":self.sheet_input.text(),
         "Datetime_Format":self.datetime_input.currentText()}
        with open(self.folder + os.path.sep + self.name.text() + ".fim", "w") as file:
            hjson.dump(d, file)

        # set saved proprety to true
        self.saved = True

        self.close()

class Add_Conversion(QDialog):
    def __init__(self, data):
        QDialog.__init__(self)

        # create a window
        self.resize(300,200)

        # set window title
        self.setWindowTitle("Unit Conversions")

        # load in data - make a copy
        self.data = data.copy()

        # make a flag for if a calc was performed
        self.data_changed = False

        # store channel to be converted
        self.conv_channel = ""

        # create conversions dictionary
        self.conv_dict = {"Celsius to Fahrenheit": self.c_to_f,
                     "Fahrenheit to Celsius": self.f_to_c,
                     "in-lb to Nm": self.inlb_to_nm,
                     "Nm to in-lb": self.nm_to_inlb,
                     "in-lb to in-oz": self.inlb_to_inoz,
                     "in-oz to in-lb": self.inoz_to_inlb,
                     "deg to rad": self.deg_to_rad,
                     "rad to deg": self.rad_to_deg}

        # create inputs
        self.channel_input = QComboBox()
        self.channel_input.addItems(self.data.columns)
        self.conversion_input = QComboBox()
        self.conversion_input.addItems(self.conv_dict.keys())
        self.new_channel_input = QLineEdit()
        self.calc_button = QPushButton("Calculate")
        self.calc_button.clicked.connect(self.calc)
        self.exit_button = QPushButton("Save and Exit")
        self.exit_button.clicked.connect(self.save_exit)

        # place in grid
        self.setLayout(QGridLayout())
        self.layout().addWidget(QLabel("Source"), 0, 0, 1, 1, Qt.AlignRight)
        self.layout().addWidget(self.channel_input, 0, 1, 1, 1)
        self.layout().addWidget(QLabel("Conversion"), 1, 0, 1, 1, Qt.AlignRight)
        self.layout().addWidget(self.conversion_input, 1, 1, 1, 1)
        self.layout().addWidget(QLabel("New Channel Name"), 2, 0, 1, 1, Qt.AlignRight)
        self.layout().addWidget(self.new_channel_input, 2, 1, 1, 1)
        self.layout().addWidget(self.calc_button, 3, 0, 1, 2, Qt.AlignHCenter)
        self.layout().addWidget(self.exit_button, 4, 0, 1, 2, Qt.AlignHCenter)

        self.show()

    def calc(self):
        try:
            # check that a new channel name was entered
            if self.new_channel_input.text() == "":
                msg = QMessageBox()
                msg.setWindowTitle("Enter New Channel Name")
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Uh oh!")
                msg.setInformativeText("Please enter a new channel name!")
                msg.exec()
                return

            # check that an input channel was selected
            if self.channel_input.currentText() == "":
                msg = QMessageBox()
                msg.setWindowTitle("Select Input Channel")
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Uh oh!")
                msg.setInformativeText("Please enter an input channel!")
                msg.exec()
                return

            # store variable to be converted
            self.conv_channel = self.channel_input.currentText()

            # make conversion
            new_data = self.conv_dict[self.conversion_input.currentText()]()

            # add that new data to dataframe
            self.data[self.new_channel_input.text()] = new_data
            
            # update data changed flag
            self.data_changed = True

            # print success
            msg = QMessageBox()
            msg.setWindowTitle("Success")
            msg.setIcon(QMessageBox.Information)
            msg.setText("Success!")
            msg.setInformativeText("Unit conversion channel added")
            msg.exec()
            
        except Exception as e:
            logging.error(e)
            msg = QMessageBox()
            msg.setWindowTitle("Something Went Wrong")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Uh oh!")
            msg.setInformativeText("Looks like something went wrong when calculating new channel.")
            msg.exec()

    def c_to_f(self):
        return self.data[self.conv_channel]*9/5+32

    def f_to_c(self):
        return 5/9*(self.data[self.conv_channel]-32)

    def inlb_to_nm(self):
        return self.data[self.conv_channel]*0.11298482933333

    def nm_to_inlb(self):
        return self.data[self.conv_channel]*8.85074576737892

    def inlb_to_inoz(self):
        return self.data[self.conv_channel]*16
    
    def inoz_to_inlb(self):
        return self.data[self.conv_channel]*0.0625

    def deg_to_rad(self):
        return self.data[self.conv_channel]*math.pi/180

    def rad_to_deg(self):
        return self.data[self.conv_channel]*180/math.pi

    def save_exit(self):
        self.close()

class Add_Math_Channel(QDialog):
    def __init__(self, data):
        QDialog.__init__(self)

        # create a window
        self.resize(500,500)

        # set window title
        self.setWindowTitle("Math Channels")

        # load in data - make a copy
        self.data = data.copy()

        # make a boolean property for checking
        self.data_changed = False

        # create inputs
        self.channel_list = QListWidget()
        self.channel_list.addItems(self.data.columns)
        self.channel_list.setItemAlignment(Qt.AlignLeft)
        self.channel_list.setDragEnabled(False)
        self.channel_list.setAcceptDrops(False)
        self.channel_list.itemDoubleClicked.connect(self.list_double_clicked)
        self.formula_input = QLineEdit()
        self.new_channel_input = QLineEdit()
        self.calc_button = QPushButton("Calculate")
        self.calc_button.clicked.connect(self.calc)
        self.exit_button = QPushButton("Save and Exit")
        self.exit_button.clicked.connect(self.save_exit)

        # place in grid
        self.setLayout(QGridLayout())
        self.layout().addWidget(QLabel("Channels"), 0, 0, 1, 1, Qt.AlignRight | Qt.AlignTop)
        self.layout().addWidget(self.channel_list, 0, 1, 1, 1)
        self.layout().addWidget(QLabel("Formula"), 1, 0, 1, 1, Qt.AlignRight)
        self.layout().addWidget(self.formula_input, 1, 1, 1, 1)
        self.layout().addWidget(QLabel("New Channel Name"), 2, 0, 1, 1, Qt.AlignRight)
        self.layout().addWidget(self.new_channel_input, 2, 1, 1, 1)
        self.layout().addWidget(self.calc_button, 3, 0, 1, 2, Qt.AlignHCenter)
        self.layout().addWidget(self.exit_button, 4, 0, 1, 2, Qt.AlignHCenter)

        self.show()

    def calc(self):
        try:
            # make sure there is something typed in the formula cell
            if self.formula_input.text() == "":
                return

            # take care of new channel name if there is no name specified
            if self.new_channel_input.text() == "":
                msg = QMessageBox()
                msg.setWindowTitle("Enter New Channel Name")
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Uh oh!")
                msg.setInformativeText("Please enter a new channel name!")
                msg.exec()
                return

            # parse for variable names, replacing spaces with underscores
            # get indices for @ symbols
            input_str = self.formula_input.text()
            ind = [pos for pos,char in enumerate(input_str) if char == "@"]
            # assign get rid of variable names with spaces
            for val in ind:
                start_ind = val + 2
                # find first occurrence of ' after start of variable name
                end_ind = input_str[start_ind:].find("'") + start_ind
                # replace variable name in string with a variable name without spaces
                input_str = input_str.replace(input_str[start_ind:end_ind], input_str[start_ind:end_ind].replace(" ", "_"))

            # remove @ and ' from input_str
            input_str = input_str.replace("@","")
            input_str = input_str.replace("'","")

            # store data frame column names and append new channel name to list
            cols = list(self.data.columns)
            cols.append(self.new_channel_input.text())

            # replace column name spaces with underscores
            l = list(self.data.columns)
            for i in range(len(l)):
                l[i] = l[i].replace(" ", "_")
            self.data.columns = l

            # evaluate formula
            temp_calc = ne.evaluate(input_str, local_dict=self.data)

            # add to dataframe
            self.data[cols[-1]] = temp_calc

            # revert data columns to original names
            self.data.columns = cols

            # set data changed to true
            self.data_changed = True

            # print success
            msg = QMessageBox()
            msg.setWindowTitle("Success")
            msg.setIcon(QMessageBox.Information)
            msg.setText("Success!")
            msg.setInformativeText("Math channel added")
            msg.exec()

        except Exception as e:
            logging.error(e)
            msg = QMessageBox()
            msg.setWindowTitle("Something Went Wrong")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Uh oh!")
            msg.setInformativeText("Looks like something went wrong when calculating new channel.")
            msg.exec()

    def list_double_clicked(self, item: QListWidgetItem):
        # add items text to the formula string
        str = self.formula_input.text()
        str = str + "@'" + item.text() + "'"
        self.formula_input.setText(str)

    def save_exit(self):
        # close
        self.close()

if __name__ == '__main__':

    # create application container
    app = QApplication([])
    app.setStyle("Fusion")

    # instantiate GUI
    gui = Plot_Bot()

    # run application
    app.exec()