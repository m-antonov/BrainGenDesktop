# Configurations and parameters
from library import config

# System-specific parameters and functions
from sys import argv
# Double-ended queue
from collections import deque
# Combination of a date and a time for logging
from datetime import datetime
# Binary data from the hex string
from binascii import unhexlify
# Serial communication with generator and TGAM
# noinspection PyPackageRequirements
from serial import Serial
# noinspection PyPackageRequirements
from serial.tools import list_ports
# Configuration parser
from configparser import ConfigParser
# Converting a string to a floating point number
from locale import setlocale, LC_NUMERIC, atof
# Plotting charts modules
from pyqtgraph import setConfigOption, PlotWidget, LegendItem, mkPen
# PyQt5 modules
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QMenu, QAction, QApplication
# Async threading interface
from asyncio import sleep, all_tasks, ProactorEventLoop, set_event_loop, CancelledError


# ============================================================================ #
# SYNC FUNCTIONS
# ============================================================================ #

# Software configuration parser
def config_parser():
    ini = ConfigParser()
    ini.read('config.ini')
    return ini


# ============================================================================ #
# ASYNC FUNCTIONS
# ============================================================================ #

# Main processing events loop
async def async_process_subprocess(qapp):
    while True:
        await sleep(0)
        qapp.processEvents()


# ============================================================================ #
# GUI
# ============================================================================ #

class ProgramUI(QMainWindow):
    # Setting locale for formatting numbers
    setlocale(LC_NUMERIC, '')

    def __init__(self, main_loop):
        # noinspection PyArgumentList
        super(ProgramUI, self).__init__()
        uic.loadUi('ui/BrainGenDesktop.ui', self)
        # Setting application icon
        self.setWindowIcon(QIcon('icon/logo.png'))
        # Application main loop
        self.main_loop = main_loop
        # Getting software configuration from config.ini
        self.config = config_parser()
        self.config_com = self.config['COM_PORT']
        self.config_signal = self.config['SIGNAL']

        # Switch case for returned value from the generator
        self.response_switch = {'': config.gen_, 'aa': config.gen_aa}

        # Connect / disconnect button actions
        self.connection_btn.clicked.connect(self.gen_tgam_conn)
        # Set generator parameters button action
        self.signal_btn.clicked.connect(self.gen_signal_define)

        # Setting default values for signal amplitude and frequency from config.ini
        for signal in config.signal_input:
            getattr(self, signal).setValue(float(self.config_signal[signal]))

        # Activity plot style
        setConfigOption('background', '#FF000000')

        # Generating and displaying plots for EEG and Attention / Meditation rhythms
        for graph in config.graph_types:
            # Defining activity plot
            setattr(self, graph + '_drawing', PlotWidget())
            drawing = getattr(self, graph + '_drawing')
            drawing.setMenuEnabled(enableMenu=False)
            drawing.setMouseEnabled(x=False, y=False)
            drawing.showGrid(x=True, y=True)
            drawing.hideButtons()
            # Defining legend and applying it to the plot
            setattr(self, graph + '_legend', LegendItem(offset=(70, 30)))
            legend = getattr(self, graph + '_legend')
            legend.setParentItem(drawing.getPlotItem())

            for signal in getattr(config, graph + '_output'):
                # Defining activity curves and applying them to legend
                setattr(self, signal + '_curve', drawing.getPlotItem().plot())
                curve = getattr(self, signal + '_curve')
                legend.addItem(curve, ' '.join(signal.split('_')).title())
                # Curve checkbox view options
                getattr(self, signal + '_checkbox').clicked.connect(
                    lambda show, name=signal: self.graph_view_options(show, name))

            # Setting activity box layout and adding activity plot to the program window
            setattr(self, graph + '_layout', QGridLayout())
            layout = getattr(self, graph + '_layout')
            graph_box = getattr(self, graph + '_graph')
            graph_box.setLayout(layout)
            layout.addWidget(drawing)
            # Setting the right-click context menu
            graph_box.setContextMenuPolicy(Qt.CustomContextMenu)
            graph_box.customContextMenuRequested.connect(
                lambda event, box=graph_box: self.graph_context_menu(event, box))

        # Getting COM ports and filling interface with default values
        self.main_loop.create_task(self.async_get_ports())
        # Checking TGAM process
        self.tgam_checking = None

        # Initializing generator and TGAM serial connections in non-blocking mode
        self.serial_generator = Serial()
        self.serial_generator.timeout = 0
        self.serial_tgam = Serial()
        self.serial_tgam.timeout = 0

    # ============================================================================ #
    # SYNC FUNCTIONS
    # ============================================================================ #

    # Preparing output the message to the event log
    def write_log(self, param):
        log_type, message = param
        curr_time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + ' : '
        return {
            'success': lambda: self.log.append(curr_time + '<font color=\'green\'>Success: </font>' + message),
            'warning': lambda: self.log.append(curr_time + '<font color=\'orange\'>Warning: </font>' + message),
            'error': lambda: self.log.append(curr_time + '<font color=\'red\'>An error has occurred: </font>' + message)
        }.get(log_type, lambda: self.log.append(curr_time + message))

    # Setting serial ports parameters and creating a task with getting data from TGAM
    def gen_tgam_conn(self):
        self.serial_generator.baudrate = self.generator_baud.currentText()
        self.serial_generator.port = self.generator_port.currentText()
        self.serial_tgam.baudrate = self.tgam_baud.currentText()
        self.serial_tgam.port = self.tgam_port.currentText()
        self.main_loop.create_task(self.async_gen_tgam_conn())

    # Setting signal generator parameters based on user input
    def gen_signal_define(self):
        # Preparing the request
        query = list()
        for idx, signal in enumerate(config.signal_input):
            value, suffix = getattr(self, signal).text().split(' ')
            raw_input = atof(value)
            if idx % 2:
                query.append(int(raw_input * 10).to_bytes(2, 'little').hex())
            else:
                query.append(int(raw_input).to_bytes(1, 'little').hex())

        # Sending the request to the generator
        self.serial_generator.write(unhexlify(''.join(query)))
        # Reading response and output the message to the event log
        response = self.serial_generator.read().hex()
        self.write_log(self.response_switch.get(response, config.gen_err)())()

    # Signal view options checkboxes actions
    def graph_view_options(self, show, signal):
        # Getting the signal curve and its parameters
        curve = getattr(self, signal + '_curve')
        amplitude = getattr(self, signal + '_amplitude', None)
        frequency = getattr(self, signal + '_frequency', None)

        # Actions for checking and unchecking states
        if show:
            curve.show()
            if amplitude and frequency:
                amplitude.setEnabled(True)
                frequency.setEnabled(True)
        else:
            curve.hide()
            if amplitude and frequency:
                amplitude.setEnabled(False)
                frequency.setEnabled(False)

    # Graph box right click context menu
    def graph_context_menu(self, event, graph_box):
        menu = QMenu()
        reset_action = QAction(QIcon('icon/reset.png'), 'Reset signals', self)
        reset_action.triggered.connect(self.reset_activity)
        menu.addAction(reset_action)
        menu.exec_(graph_box.mapToGlobal(event))

    # Resetting signal graph data and restarting checking TGAM process
    def reset_activity(self):
        if self.serial_generator.is_open and self.serial_tgam.is_open:
            self.tgam_checking.cancel()
            self.tgam_checking = self.main_loop.create_task(self.async_get_signal())

    # Actions during the program window closed
    def closeEvent(self, event):
        for queue in all_tasks(self.main_loop):
            queue.cancel()

    # ============================================================================ #
    # ASYNC FUNCTIONS
    # ============================================================================ #

    # Setting interface default values
    async def async_get_ports(self):
        # Adding available COM ports
        port_list = list()
        for port, _, _ in sorted(list_ports.comports()):
            self.generator_port.addItem(port)
            self.tgam_port.addItem(port)
            port_list.append(port)

        # Adding available bauds
        for baud in config.device_baud:
            self.generator_baud.addItem(baud)
            self.tgam_baud.addItem(baud)

        # Setting default baud and COM values if presented in the system
        try:
            self.generator_port.setCurrentIndex(port_list.index(self.config_com['GENERATOR_PORT']))
            self.generator_baud.setCurrentIndex(config.device_baud.index(self.config_com['GENERATOR_BAUD']))
        except ValueError:
            pass

        try:
            self.tgam_port.setCurrentIndex(port_list.index(self.config_com['TGAM_PORT']))
            self.tgam_baud.setCurrentIndex(config.device_baud.index(self.config_com['TGAM_BAUD']))
        except ValueError:
            pass

    # Serial port connect / disconnect procedures
    async def async_gen_tgam_conn(self):
        # Connect procedure
        if self.connection_btn.text() == 'CONNECT':
            # Disabling / enabling interfaces and renaming button
            self.generator_port.setEnabled(False)
            self.generator_baud.setEnabled(False)
            self.tgam_port.setEnabled(False)
            self.tgam_baud.setEnabled(False)
            self.signal_box.setEnabled(True)
            self.connection_btn.setText('DISCONNECT')
            # Opening generator and TGAM ports
            self.serial_generator.open()
            self.serial_tgam.open()
            # Creating a task with getting data from TGAM and drawing curves
            self.tgam_checking = self.main_loop.create_task(self.async_get_signal())
        # Disconnect procedure
        elif self.connection_btn.text() == 'DISCONNECT':
            # Disabling / enabling interfaces and renaming button
            self.generator_port.setEnabled(True)
            self.generator_baud.setEnabled(True)
            self.tgam_port.setEnabled(True)
            self.tgam_baud.setEnabled(True)
            self.signal_box.setEnabled(False)
            self.connection_btn.setText('CONNECT')
            # Closing generator and TGAM ports
            self.serial_generator.close()
            self.serial_tgam.close()
            # Cancelling a getting data task
            self.tgam_checking.cancel()

    # Getting data from TGAM and drawing curves
    async def async_get_signal(self):
        # Default empty deque list with 31 items
        for graph in config.graph_types:
            for signal in getattr(config, graph + '_output'):
                setattr(self, signal + '_data', deque([0] * 31, maxlen=31))

        while True:
            raw_data = list()
            clear_data = dict()

            # TODO More stable TGAM1 receiving packet analysis based on MindSet Communications Protocol
            for byte in range(36):
                data = self.serial_tgam.read().hex()
                if data:
                    raw_data.append(data)

            if raw_data:
                # Associating received data with packet structure
                raw_data.reverse()
                for param in config.signal_protocol:
                    clear_data[param] = list()
                    for byte in range(config.signal_protocol[param]):
                        clear_data[param].append(raw_data.pop())

                # Updating curves values
                for graph in config.graph_types:
                    for idx, signal in enumerate(getattr(config, graph + '_output')):
                        signal_curve = getattr(self, signal + '_curve')
                        signal_data = getattr(self, signal + '_data')
                        signal_color = getattr(config, graph + '_color')
                        signal_data.append(int(''.join(clear_data[signal]), 16))
                        signal_curve.setData(signal_data, pen=mkPen(width=1.5, color=signal_color[idx]))

            await sleep(1)


if __name__ == '__main__':
    app = QApplication(argv)

    # Preparing the main loop
    loop = ProactorEventLoop()
    set_event_loop(loop)

    # Preparing and displaying the GUI
    gui = ProgramUI(loop)
    gui.show()
    try:
        loop.run_until_complete(async_process_subprocess(app))
    except CancelledError:
        pass
