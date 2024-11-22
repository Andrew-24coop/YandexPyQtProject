from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import QIODevice

app = QtWidgets.QApplication([])
ui = uic.loadUi("desktop.ui")
ui.setWindowTitle("Arduino Project")

serial = QSerialPort()
serial.setBaudRate(115200)
pList = []
ports = QSerialPortInfo().availablePorts()
for port in ports:
    pList.append(port.portName())
ui.portlist.addItems(pList)


def open_port():
    serial.setPortName(ui.portlist.currentText())
    serial.open(QIODevice.ReadWrite)


def close_port():
    serial.close()


def serial_send(data):  # int list
    txs = ""
    for val in data:
        txs += str(val)
        txs += ','
    txs = txs[:-1]
    txs += ';'
    serial.write(txs.encode())


def led_control(led_state):
    if led_state == 2: led_state = 1
    serial_send([0, led_state])


def read_serial_port():
    rx = serial.readLine()
    rxs = str(rx, 'utf-8').strip()
    data = rxs.split(',')
    if data[0] == '1':
        ui.tempBar.setValue(int(float(data[1])))
        ui.tempL.setText(str(data[1]) + "*С")
        ui.pressureBar.setValue(int(float(data[3])))
        ui.prsL.setText(str(data[3]) + "ммРтСт")
        ui.humidityBar.setValue(int(float(data[2])))
        ui.hmdtL.setText(str(data[2]) + "%")
    if data[0] == '2':
        ui.stats.setText("Датчик не подключен")
    if data[0] == '3':
        ui.stats.setText("Отсутствует SD карта")


def show_comfort_table():
    return


def show_instructions():
    msg_box = QtWidgets.QMessageBox()
    msg_box.setWindowIcon(QtGui.QIcon('icon.png'))
    msg_box.setWindowTitle("Инструкция")
    msg_box.setText("Инструкция по эксплуатации")
    msg_box.setStyleSheet("QLabel{font-size: 18px;}")
    msg_box.setInformativeText("""
    1. Подключите метеостанцию
    2. Выберите появившийся порт в поле подключения
    3. Нажмите Подключить""")
    msg_box.exec_()


def show_comfort_image():
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Комфортный диапазон температуры и относительной влажности")
    layout = QtWidgets.QVBoxLayout()

    label = QtWidgets.QLabel()
    pixmap = QtGui.QPixmap("img/table.jpg")
    scaled_pixmap = pixmap.scaled(834, 818, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
    label.setPixmap(scaled_pixmap)
    label.setScaledContents(True)
    layout.addWidget(label)

    dialog.setLayout(layout)
    dialog.setFixedSize(834, 818)
    dialog.exec_()


def show_personalization_dialog():
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Персонализация")

    layout = QtWidgets.QVBoxLayout()

    label = QtWidgets.QLabel("Выберите тему:")
    layout.addWidget(label)

    theme_combo = QtWidgets.QComboBox()
    theme_combo.addItems(["Default", "Тёмная", "Светлая"])
    layout.addWidget(theme_combo)

    apply_button = QtWidgets.QPushButton("Применить")
    layout.addWidget(apply_button)

    apply_button.clicked.connect(lambda: change_theme(theme_combo.currentText()))

    dialog.setLayout(layout)
    dialog.exec_()


def change_theme(selected_theme):
    if selected_theme == "Default":
        app.setStyle("Fusion")
    elif selected_theme == "Тёмная":
        app.setStyle("Fusion")
        app.setStyleSheet("QWidget { background-color: #2b2b2b; color: white; }")
    elif selected_theme == "Светлая":
        app.setStyle("Fusion")
        app.setStyleSheet("QWidget { background-color: white; color: black; }")


serial.readyRead.connect(read_serial_port)

ui.conB.clicked.connect(open_port)
ui.disconnectB.clicked.connect(close_port)
ui.comfort.clicked.connect(show_comfort_table)
ui.led.stateChanged.connect(led_control)
ui.instructions.clicked.connect(show_instructions)
ui.comfort.clicked.connect(show_comfort_image)
ui.personalization.clicked.connect(show_personalization_dialog)

ui.show()
app.exec()
