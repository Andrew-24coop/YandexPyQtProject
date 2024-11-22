import sys
import datetime
import numpy as np
import sqlite3
import pyqtgraph as pg
from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt6.QtWidgets import (QApplication, QDialog, QGridLayout, QLabel,
                             QProgressBar, QCheckBox, QPushButton,
                             QComboBox, QGroupBox, QHBoxLayout, QMessageBox, QVBoxLayout, QTextEdit)
from PyQt6.QtCore import Qt, QIODevice
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QTimer


class ArduinoProject(QDialog):
    def __init__(self):
        super().__init__()
        self.readSDButton = None
        self.cursor = None
        self.conn = None
        self.setGeometry(380, 200, 729, 407)
        self.setWindowTitle("WeatherHUB")

        # Initialize Database
        self.init_db()

        # Create layout
        self.gridLayout = QGridLayout(self)

        # Labels for Temperature, Humidity, Pressure
        self.label_temp = QLabel("Temp")
        self.label_humidity = QLabel("Hmdt")
        self.label_pressure = QLabel("Prs")
        self.tempL = QLabel("0.0")
        self.hmdtL = QLabel("0")
        self.prsL = QLabel("0")

        # Progress Bars
        self.tempBar = QProgressBar(orientation=Qt.Orientation.Vertical)
        self.tempBar.setRange(-30, 40)

        self.humidityBar = QProgressBar(orientation=Qt.Orientation.Vertical)
        self.humidityBar.setRange(0, 100)

        self.pressureBar = QProgressBar(orientation=Qt.Orientation.Vertical)
        self.pressureBar.setRange(720, 800)

        # Control Group Box with CheckBox and Buttons
        self.controlGroupBox = QGroupBox("Управление")
        self.controlLayout = QGridLayout(self.controlGroupBox)
        self.led = QCheckBox("LED")
        self.comfortButton = QPushButton("Таблица комфорта")
        self.instructionsButton = QPushButton("Инструкция")
        self.startRecButton = QPushButton("Начать запись")
        self.stopRecButton = QPushButton("Завершить запись")
        self.statsLabel = QLabel("Отключено")
        self.statusLabel = QLabel("Статус:")

        self.setupControlLayout()

        # Connection Group Box
        self.connectionGroupBox = QGroupBox("Подключение")
        self.connectionLayout = QHBoxLayout(self.connectionGroupBox)
        self.portlist = QComboBox()
        self.conB = QPushButton("Подключить")
        self.disconnectB = QPushButton("Отключить")
        self.connectionLayout.addWidget(self.portlist)
        self.connectionLayout.addWidget(self.conB)
        self.connectionLayout.addWidget(self.disconnectB)

        self.serial = QSerialPort()
        self.serial.setBaudRate(115200)
        p_list = []
        ports = QSerialPortInfo().availablePorts()
        for port in ports:
            p_list.append(port.portName())
        self.portlist.addItems(p_list)

        # Adding all widgets to the main grid layout
        self.setupMainLayout()

        # Timer for recording data at 10Hz
        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.record_data)

        # Connect signals and slots
        self.startRecButton.clicked.connect(self.startRecording)

        self.stopRecButton.clicked.connect(self.stopRecording)
        self.instructionsButton.clicked.connect(self.showInstructions)
        self.comfortButton.clicked.connect(self.show_comfort_image)
        self.conB.clicked.connect(self.open_port)
        self.disconnectB.clicked.connect(self.close_port)
        self.led.stateChanged.connect(lambda state: self.led_control(state))

        self.serial.readyRead.connect(self.read_serial_port)

        self.personalizationButton = QPushButton("Персонализация")
        self.controlLayout.addWidget(self.personalizationButton, 5, 2)
        self.personalizationButton.clicked.connect(self.show_personalization_dialog)

        # Initialized states
        self.recording = False

    def init_db(self):
        """Initialize the SQLite database and create a table for recording data."""
        self.conn = sqlite3.connect('records.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                temperature REAL,
                humidity REAL,
                pressure REAL
            )
        ''')
        self.conn.commit()

    def setupControlLayout(self):
        self.controlLayout.addWidget(self.led, 1, 0)
        self.controlLayout.addWidget(self.comfortButton, 1, 1)
        self.controlLayout.addWidget(self.instructionsButton, 1, 2)
        self.controlLayout.addWidget(self.startRecButton, 2, 0, 1, 3)
        self.controlLayout.addWidget(self.stopRecButton, 3, 0, 1, 3)
        self.readSDButton = QPushButton("Прочитать запись")
        self.controlLayout.addWidget(self.readSDButton, 4, 0, 1, 3)
        self.controlLayout.addWidget(self.statusLabel, 5, 0)
        self.controlLayout.addWidget(self.statsLabel, 5, 1)

        # Connect read SD button
        self.readSDButton.clicked.connect(self.readSD)

    def setupMainLayout(self):
        self.gridLayout.addWidget(self.label_temp, 0, 1)
        self.gridLayout.addWidget(self.tempBar, 1, 1)
        self.gridLayout.addWidget(self.tempL, 0, 2)
        self.gridLayout.addWidget(self.label_humidity, 0, 3)
        self.gridLayout.addWidget(self.humidityBar, 1, 3)
        self.gridLayout.addWidget(self.hmdtL, 0, 4)
        self.gridLayout.addWidget(self.label_pressure, 0, 5)
        self.gridLayout.addWidget(self.pressureBar, 1, 5)
        self.gridLayout.addWidget(self.prsL, 0, 6)
        self.gridLayout.addWidget(self.controlGroupBox, 0, 0, 6, 1)
        self.gridLayout.addWidget(self.connectionGroupBox, 6, 0, 1, 4)

    def startRecording(self):
        print("Starting recording...")
        self.recording = True
        self.stopRecButton.setEnabled(True)
        self.startRecButton.setEnabled(False)
        self.serial_send([1, 1])
        # Start the recording timer
        self.recording_timer.start(100)  # 100 ms for 10Hz frequency

    def stopRecording(self):
        print("Stopping recording...")
        self.recording = False
        self.stopRecButton.setEnabled(False)
        self.startRecButton.setEnabled(True)
        self.serial_send([1, 0])
        # Stop the recording timer
        self.recording_timer.stop()

    def record_data(self):
        """Record data to the database at 10Hz."""
        if self.recording:
            # Simulate data reading (replace this with actual data)
            temperature = float(self.tempL.text().strip(' *С'))
            humidity = float(self.hmdtL.text().strip('%'))
            pressure = float(self.prsL.text().strip(' ммРтСт'))

            # Insert data into the database
            self.cursor.execute('''

            INSERT INTO record (temperature, humidity, pressure)
            VALUES (?, ?, ?)
        ''', (temperature, humidity, pressure))
        self.conn.commit()
        # print("Inserted:", temperature, humidity, pressure)  # Debug print

    def readSD(self):
        print("Чтение из базы данных...")  # Updated print statement for reading
        self.cursor.execute("SELECT * FROM record ORDER BY timestamp ASC")  # Changed to ascending order
        records = self.cursor.fetchall()

        if not records:  # Check if records are empty
            print("Записи не найдены.")  # Updated message for no records found
            QMessageBox.information(self, "Нет записей", "Данные не найдены в базе данных.")
            return

        # No need to reverse here since we are now reading in ascending order
        print("Записанные записи:", records)  # Debugging output to see the fetched records

        # Create a new dialog for plotting the data
        plot_dialog = QDialog(self)
        plot_dialog.setWindowTitle("Записи")  # Window title
        layout = QVBoxLayout(plot_dialog)

        # Create the plotting area
        plot_widget = pg.PlotWidget(title="Данные температуры, влажности и давления")  # Updated title
        layout.addWidget(plot_widget)

        # Extract data
        timestamps = [record[1] for record in records]  # No more reversal
        timestamps_float = [
            (datetime.datetime.strptime(record[1], "%Y-%m-%d %H:%M:%S") - datetime.datetime(1970, 1, 1)).total_seconds()
            for record in records]

        # Get the initial timestamp for calculating elapsed time
        initial_time = min(timestamps_float)

        # Calculate elapsed time in seconds
        elapsed_time = [t - initial_time for t in timestamps_float]

        # Convert humidity, pressure, and temperature to floats
        temperatures = [float(record[2]) for record in records]
        humidities = [float(record[3]) for record in records]
        pressures = [float(record[4]) * 0.7500616827 for record in records]  # Convert hPa to mmHg

        # Plot temperature and humidity
        plot_widget.plot(x=elapsed_time, y=temperatures, pen='r', name='Температура')  # Red line for temperature
        plot_widget.plot(x=elapsed_time, y=humidities, pen='g', name='Влажность')  # Green line for humidity

        # Set limits for the left Y-axis (Temperature and Humidity)
        plot_widget.setYRange(0, 100)

        # Create a second Y-axis for pressure
        pressure_axis = pg.AxisItem('right')  # Create a new axis item for the right
        plot_widget.setAxisItems({'right': pressure_axis})  # Set the new axis in the plot widget

        # Plot pressure using a different axis
        pressure_plot = plot_widget.plot(x=elapsed_time, y=pressures, pen='b', name='Давление',
                                         axis='right')  # Blue line for pressure

        # Set limits for the right Y-axis (Pressure)

        pressure_axis.setRange(780, max(pressures) + 10)  # Set limits for the right axis

        # Set labels for Y-axes
        plot_widget.setLabel('left', 'Температура/Влажность (%)')  # Updated label for left Y-axis
        pressure_axis.setLabel('Давление (мм рт. ст.)')  # Updated label for right Y-axis

        # Add legends
        plot_widget.addLegend()

        # Show the plot dialog
        plot_dialog.setLayout(layout)
        plot_dialog.resize(800, 600)
        plot_dialog.exec()

    def showInstructions(self):
        msg_box = QMessageBox()
        msg_box.setWindowIcon(QIcon('icon.png'))
        msg_box.setWindowTitle("Инструкция")
        msg_box.setText("Инструкция по эксплуатации")

        msg_box.setInformativeText("""
            1. Подключите метеостанцию
            2. Выберите появившийся порт в поле подключения
            3. Нажмите Подключить""")
        msg_box.exec()

    def open_port(self):
        self.serial.setPortName(self.portlist.currentText())
        if self.serial.open(QIODevice.OpenModeFlag.ReadWrite):
            print(f"Connected to {self.portlist.currentText()}")
        else:
            print("Connection failed")

    def close_port(self):
        self.serial.close()

    def led_control(self, state):
        led_state = 1 if state == Qt.CheckState.Checked else 0
        self.serial_send([0, led_state])

    def serial_send(self, data):
        txs = ','.join(map(str, data)) + ';'
        self.serial.write(txs.encode())

    def read_serial_port(self):
        while self.serial.canReadLine():
            rx = self.serial.readLine()
            rxs = str(rx, 'utf-8').strip()
            data = rxs.split(',')
            if data[0] == '1':
                self.tempBar.setValue(int(float(data[1])))
                self.tempL.setText(str(data[1]) + "*С")
                self.pressureBar.setValue(int(float(data[3])))
                self.prsL.setText(str(data[3]) + "ммРтСт")
                self.humidityBar.setValue(int(float(data[2])))
                self.hmdtL.setText(str(data[2]) + "%")
                if self.recording:
                    self.statsLabel.setText("Идет запись")
                else:
                    self.statsLabel.setText("Подключено")
            elif data[0] == '2':
                self.statsLabel.setText("Датчик не подключен")
            elif data[0] == '3':
                if data[1] == '1':
                    self.statsLabel.setText("Отсутствует SD карта")
                elif data[1] == '2':
                    self.statsLabel.setText("Ошибка открытия файла")

    def show_personalization_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Персонализация")
        layout = QVBoxLayout(dialog)

        label = QLabel("Выберите тему:")
        layout.addWidget(label)

        theme_combo = QComboBox()
        theme_combo.addItems(["Default", "Тёмная", "Светлая"])
        layout.addWidget(theme_combo)

        apply_button = QPushButton("Применить")
        apply_button.clicked.connect(lambda: self.change_theme(theme_combo.currentText()))
        layout.addWidget(apply_button)

        dialog.exec()

    def change_theme(self, selected_theme):
        if selected_theme == "Default":
            QApplication.setStyle("Fusion")

            self.setStyleSheet("")
        elif selected_theme == "Тёмная":
            QApplication.setStyle("Fusion")
            self.setStyleSheet("QWidget { background-color: #2b2b2b; color: white; }")
        elif selected_theme == "Светлая":
            QApplication.setStyle("Fusion")
            self.setStyleSheet("QWidget { background-color: white; color: black; }")

    def show_comfort_image(self):
        dialog = QDialog()
        dialog.setWindowTitle("Комфортный диапазон температуры и относительной влажности")
        layout = QVBoxLayout()

        label = QLabel()
        pixmap = QPixmap("img/table.jpg")
        scaled_pixmap = pixmap.scaled(834, 818)
        label.setPixmap(scaled_pixmap)
        label.setScaledContents(True)
        layout.addWidget(label)

        dialog.setLayout(layout)
        dialog.setFixedSize(834, 818)
        dialog.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ArduinoProject()
    window.show()
    sys.exit(app.exec())
