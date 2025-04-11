from PySide6.QtCore import QSettings, QTimer
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QLabel, QGridLayout, QMessageBox, QListWidget, \
    QListWidgetItem
import requests


from city_list_item import CityListItem
from settings_dialog import SettingsDialog


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Weather')
        self.city_edit = QLineEdit('Lublin', self)
        get_cities_button = QPushButton("Get cities", self)
        self.weather_label = QLabel(self)
        self.city_list = QListWidget(self)
        settings_button = QPushButton("Settings", self)
        self.favourite_city_list = QListWidget(self)
        self.timer = QTimer()

        get_cities_button.clicked.connect(self.get_cities)
        settings_button.clicked.connect(self.show_settings)
        #self.city_list.itemClicked.connect(self.get_weather)
        self.city_list.itemDoubleClicked.connect(self.add_item_to_favourites)
        self.timer.timeout.connect(self.get_weather)
        self.timer.start(30000)


        layout = QGridLayout(self)
        layout.addWidget(self.city_edit, 0, 0)
        layout.addWidget(get_cities_button, 0, 1)
        layout.addWidget(self.city_list, 1, 0, 1, 1)
        layout.addWidget(self.weather_label, 2, 0, 1, 2)
        layout.addWidget(settings_button, 3, 0, 1, 2)
        layout.addWidget(self.favourite_city_list, 1, 1, 1, 1)

        self.load_persistent_cities()
        self.get_weather()

        # self.weather_params = {"temperature_2m": True}

    def get_cities(self):
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={self.city_edit.text()}"
        response = requests.get(url)
        json = response.json()
        if 'results' not in json.keys():
            QMessageBox.critical(self, "Error!!!", "No such city")
            return
        results = json['results']
        for city in results:
            latitude = city['latitude']
            longitude = city['longitude']
            name = city['name']
            country = city['country']
            item = CityListItem(f"{name}, {country}", latitude, longitude)
            self.city_list.addItem(item)

    def get_weather(self):
        # print(self.city_list.currentItem().data(Qt.UserRole))
        latitude = []
        longitude =[]
        if self.favourite_city_list.count() == 0:
            return
        for row in range(self.favourite_city_list.count()):
            item = self.favourite_city_list.item(row)
            latitude.append(str(item.latitude))
            longitude.append(str(item.longitude))
        latitude = ','.join(latitude)
        longitude = ','.join(longitude)

        keys = ''
        settings = QSettings()
        settings.beginGroup('parameters')
        for key in settings.childKeys():
            if settings.value(key, type=bool) == True:
                keys += key + ','
        url=f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current={keys}"
        #print(url)
        response = requests.get(url)
        json = response.json()
        weather_text = []
        for city in json:
            print(city)
            weather_text.append(str(city["current"]))
        self.weather_label.setText('\n'.join(weather_text))
        #print(json)

    def show_settings(self):
        settings_dialog = SettingsDialog()

        settings_dialog.exec()
        if settings_dialog.result() == 1:
            # self.weather_params = settings_dialog.result_data()
            settings = QSettings()
            for key, value in settings_dialog.result_data().items():
                settings.setValue(f'parameters/{key}', value)

    def add_item_to_favourites(self):
        checked_item = self.city_list.item(self.city_list.currentRow())
        for row in range(self.favourite_city_list.count()):
            item = self.favourite_city_list.item(row)
            if item==checked_item:
                QMessageBox.critical(self, "Error!!!", "To miasto już zostało dodane")
                return

        taken_item = self.city_list.takeItem(self.city_list.currentRow())

        self.favourite_city_list.addItem(taken_item)

        self.update_persistent_cities()

    def delete_item(self):
        taken_item = self.favourite_city_list.takeItem(self.favourite_city_list.currentRow())
        self.city_list.addItem(taken_item)
        self.update_persistent_cities()


    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete and self.favourite_city_list.hasFocus():
            self.delete_item()


    def update_persistent_cities(self):
        result = []
        settings = QSettings()
        for row in range(self.favourite_city_list.count()):
            item = self.favourite_city_list.item(row)
            data = item.dump()
            result.append(data.decode('utf-8'))

        settings.setValue('cities/cities', ';'.join(result))

    def load_persistent_cities(self):
        settings = QSettings()
        coded_cities = settings.value('cities/cities', type=str)
        if len(coded_cities) == 0:
            return
        for coded_city in coded_cities.split(';'):
            city = CityListItem.from_dump(coded_city)
            self.favourite_city_list.addItem(city)