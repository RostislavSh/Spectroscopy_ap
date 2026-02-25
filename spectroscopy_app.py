import sys
import os
import numpy as np
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QTextEdit, QWidget, 
                           QFileDialog, QMessageBox, QComboBox, QGroupBox,
                           QTabWidget, QProgressBar, QSplitter, QInputDialog,
                           QCheckBox, QDialog, QScrollArea)
from PyQt5.QtCore import Qt

class InstructionDialog(QDialog):
    def __init__(self, language='ru', parent=None):
        super().__init__(parent)
        self.language = language
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.tr("Инструкция по использованию") if self.language == 'ru' else "User Manual")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        # Область с прокруткой
        scroll = QScrollArea()
        content = QWidget()
        content_layout = QVBoxLayout()
        
        # Текст инструкции
        instruction_text = QTextEdit()
        instruction_text.setReadOnly(True)
        
        if self.language == 'ru':
            text = """
            <h2>Инструкция по использованию Spectroscopy Analyzer</h2>
            
            <h3>1. Загрузка данных</h3>
            <p><b>Формат файлов:</b></p>
            <ul>
            <li><b>.tit файлы</b> - спектры эмиссии (разделитель - точка с запятой)</li>
            <li><b>.txt файлы</b> - спектры абсорбции (разделитель - запятая)</li>
            </ul>
            
            <p><b>Важно:</b> Имена файлов эмиссии и абсорбции должны совпадать (например: sample1.tit и sample1.txt)</p>
            
            <h3>2. Настройка параметров</h3>
            <ul>
            <li><b>Длина волны возбуждения:</b> Укажите длину волны, используемую для возбуждения образца</li>
            <li><b>Метод интегрирования:</b> Выберите между методом Симпсона и методом трапеций </li>
            <li><b>Обрезка данных:</b> При необходимости укажите диапазон длин волн для интегрирования</li>
            </ul>
            
            <h3>3. Расчет и результаты</h3>
            <p>После загрузки данных нажмите "Выполнить расчет". Программа:</p>
            <ul>
            <li>Рассчитает интегралы спектров эмиссии</li>
            <li>Построит калибровочные кривые</li>
            <li>Рассчитает квантовый выход (если загружен стандарт)</li>
            </ul>
            
            <h3>4. Интерпретация результатов</h3>
            <p><b>Квантовый выход (QY):</b> Показывает показывает соотношение излученных фотонов к поглощенным,
            то есть соотношение процессов конкурирующих с эмиссией.</p>
            
            <h3>5. Сохранение результатов</h3>
            <p>Скопируйте текст результатов из поля "Результаты" для дальнейшего использования.</p>
            
            <hr>
            Шулепов Ростислав Русланович - разработчик<br>
            
            <p><i>Кафедра общей и неорганической химии<br>
            Санкт-Петербургский государственный университет</i></p>
            """
        else:
            text = """
            <h2>Spectroscopy Analyzer User Manual</h2>
            
            <h3>1. Data Loading</h3>
            <p><b>File formats:</b></p>
            <ul>
            <li><b>.tit files</b> - emission spectra (semicolon separated)</li>
            <li><b>.txt files</b> - absorption spectra (comma separated)</li>
            </ul>
            
            <p><b>Important:</b> Emission and absorption filenames must match (e.g.: sample1.tit and sample1.txt)</p>
            
            <h3>2. Parameter Setup</h3>
            <ul>
            <li><b>Excitation wavelength:</b> Specify the wavelength used for sample excitation</li>
            <li><b>Integration method:</b> Choose between Simpson's method and trapezoidal method </li>
            <li><b>Data trimming:</b> If needed, specify wavelength range for integration</li>
            </ul>
            
            <h3>3. Calculation and Results</h3>
            <p>After loading data, click "Perform Calculation". The program will:</p>
            <ul>
            <li>Calculate emission spectrum integrals</li>
            <li>Build calibration curves</li>
            <li>Calculate quantum yield (if standard is loaded)</li>
            </ul>
            
            <h3>4. Results Interpretation</h3>
            <p><b>Quantum Yield (QY):</b> It shows the ratio of emitted photons to absorbed ones, that is, 
            the ratio of processes competing with emission.</p>
            
            <h3>5. Saving Results</h3>
            <p>Copy the results text from the "Results" field for further use.</p>
            
            <hr>
            Shulepov Rostislav Ruslanovich - developer<br>
            
            <p><i>Department of General and Inorganic Chemistry<br>
            Saint Petersburg State University</i></p>
            """
        
        instruction_text.setHtml(text)
        content_layout.addWidget(instruction_text)
        
        content.setLayout(content_layout)
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        
        layout.addWidget(scroll)
        
        # Кнопка закрытия
        close_btn = QPushButton(self.tr("Закрыть") if self.language == 'ru' else "Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class SpectroscopyApp(QMainWindow):
    def __init__(self):
        super().__init__() #наследование из родительских классов
        self.language = 'ru'  # ru / en
        self.data = {
            'sample': {'emission_x': [], 'emission_y': [], 'absorption_x': [], 
                      'absorption_y': [], 'ex_pic': [], 'integrals_simpson': [], 
                      'integrals_trapezoid': []},
            'standard': {'emission_x': [], 'emission_y': [], 'absorption_x': [], 
                        'absorption_y': [], 'ex_pic': [], 'integrals_simpson': [], 
                        'integrals_trapezoid': []}
        }
        self.current_method = 'simpson'
        self.trim_data = False
        self.trim_min = 0
        self.trim_max = 1000
        
        # Создаем ссылки на элементы для удобного доступа при переводе
        self.ui_elements = {}
        
        self.initUI()
        self.apply_language()  # Применяем язык по умолчанию
    
    def initUI(self):
        self.setWindowTitle('Spectroscopy Data Analyzer')
        self.setGeometry(100, 50, 1400, 900)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Создаем разделитель
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель - управление
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Правая панель - графики
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # === ЛЕВАЯ ПАНЕЛЬ ===
        
        # Кнопка переключения языка
        lang_layout = QHBoxLayout()
        self.lang_btn = QPushButton("EN/RU")
        self.lang_btn.clicked.connect(self.toggle_language)
        lang_layout.addWidget(self.lang_btn)
        self.ui_elements['lang_btn'] = self.lang_btn
        
        # Кнопка инструкции
        self.help_btn = QPushButton("📖 Инструкция")
        self.help_btn.clicked.connect(self.show_instructions)
        lang_layout.addWidget(self.help_btn)
        self.ui_elements['help_btn'] = self.help_btn
        
        left_layout.addLayout(lang_layout)
        
        # Группа параметров
        self.params_group = QGroupBox("Параметры эксперимента")
        params_layout = QVBoxLayout()
        
        # Длина волны возбуждения
        wavelength_layout = QHBoxLayout()
        self.wavelength_label = QLabel("Длина волны возбуждения (нм):")
        wavelength_layout.addWidget(self.wavelength_label)
        self.ui_elements['wavelength_label'] = self.wavelength_label
        
        self.wavelength_input = QLineEdit()
        self.wavelength_input.setText("365")
        wavelength_layout.addWidget(self.wavelength_input)
        params_layout.addLayout(wavelength_layout)
        
        # Метод интегрирования
        method_layout = QHBoxLayout()
        self.method_label = QLabel("Метод интегрирования:")
        method_layout.addWidget(self.method_label)
        self.ui_elements['method_label'] = self.method_label
        
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Метод Симпсона", "Метод трапеций"])
        method_layout.addWidget(self.method_combo)
        self.ui_elements['method_combo'] = self.method_combo
        params_layout.addLayout(method_layout)
        
        # Обрезка данных
        trim_layout = QHBoxLayout()
        self.trim_checkbox = QCheckBox("Обрезка данных для интегрирования")
        self.trim_checkbox.stateChanged.connect(self.toggle_trimming)
        trim_layout.addWidget(self.trim_checkbox)
        self.ui_elements['trim_checkbox'] = self.trim_checkbox
        params_layout.addLayout(trim_layout)
        
        # Кнопка обновления графиков
        update_layout = QHBoxLayout()
        self.update_btn = QPushButton("Обновить графики спектров")
        self.update_btn.clicked.connect(self.update_spectra_plots)
        self.update_btn.setEnabled(False)  # Изначально отключена, пока нет данных
        update_layout.addWidget(self.update_btn)
        self.ui_elements['update_btn'] = self.update_btn
        
        params_layout.addLayout(update_layout)
        
        self.params_group.setLayout(params_layout)
        left_layout.addWidget(self.params_group)
        self.ui_elements['params_group'] = self.params_group        
        
        # Диапазон обрезки
        trim_range_layout = QHBoxLayout()
        self.trim_min_label = QLabel("От:")
        trim_range_layout.addWidget(self.trim_min_label)
        self.ui_elements['trim_min_label'] = self.trim_min_label
        
        self.trim_min_input = QLineEdit()
        self.trim_min_input.setText("0")
        self.trim_min_input.setEnabled(False)
        trim_range_layout.addWidget(self.trim_min_input)
        
        self.trim_max_label = QLabel("До:")
        trim_range_layout.addWidget(self.trim_max_label)
        self.ui_elements['trim_max_label'] = self.trim_max_label
        
        self.trim_max_input = QLineEdit()
        self.trim_max_input.setText("1000")
        self.trim_max_input.setEnabled(False)
        trim_range_layout.addWidget(self.trim_max_input)
        params_layout.addLayout(trim_range_layout)
        
        self.params_group.setLayout(params_layout)
        left_layout.addWidget(self.params_group)
        self.ui_elements['params_group'] = self.params_group
        
        # Группа загрузки данных
        self.data_group = QGroupBox("Загрузка данных")
        data_layout = QVBoxLayout()
        
        # Загрузка образца
        sample_layout = QHBoxLayout()
        self.sample_btn = QPushButton("Загрузить данные ОБРАЗЦА")
        self.sample_btn.clicked.connect(self.load_sample_data)
        sample_layout.addWidget(self.sample_btn)
        self.ui_elements['sample_btn'] = self.sample_btn
        
        self.sample_label = QLabel("Не загружено" if self.language == 'ru' else "Not uploaded")
        sample_layout.addWidget(self.sample_label)
        data_layout.addLayout(sample_layout)
        
        # Загрузка стандарта
        standard_layout = QHBoxLayout()
        self.standard_btn = QPushButton("Загрузить данные СТАНДАРТА")
        self.standard_btn.clicked.connect(self.load_standard_data)
        standard_layout.addWidget(self.standard_btn)
        self.ui_elements['standard_btn'] = self.standard_btn
        
        self.standard_label = QLabel("Не загружено" if self.language == 'ru' else "Not uploaded")
        standard_layout.addWidget(self.standard_label)
        data_layout.addLayout(standard_layout)
        
        self.data_group.setLayout(data_layout)
        left_layout.addWidget(self.data_group)
        self.ui_elements['data_group'] = self.data_group
        
        # Группа расчета
        self.calc_group = QGroupBox("Расчет")
        calc_layout = QVBoxLayout()
        
        self.calculate_btn = QPushButton("Выполнить расчет")
        self.calculate_btn.clicked.connect(self.perform_calculation)
        calc_layout.addWidget(self.calculate_btn)
        self.ui_elements['calculate_btn'] = self.calculate_btn
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        calc_layout.addWidget(self.progress_bar)
        
        self.calc_group.setLayout(calc_layout)
        left_layout.addWidget(self.calc_group)
        self.ui_elements['calc_group'] = self.calc_group
        
        # Группа результатов
        self.results_group = QGroupBox("Результаты")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(200)
        results_layout.addWidget(self.results_text)
        
        self.results_group.setLayout(results_layout)
        left_layout.addWidget(self.results_group)
        self.ui_elements['results_group'] = self.results_group
        
        # Информация об авторах
        self.authors_label = QLabel("Разработчик: Шулепов Р.Р.")
        self.authors_label.setStyleSheet("color: gray; font-size: 10px;")
        left_layout.addWidget(self.authors_label)
        self.ui_elements['authors_label'] = self.authors_label
        
        # Растягивающий элемент
        left_layout.addStretch()
        
        # === ПРАВАЯ ПАНЕЛЬ ===
        
        # Создаем вкладки для графиков
        self.tabs = QTabWidget()
        
        # Вкладка 1: Исходные спектры
        self.spectra_tab = QWidget()
        spectra_layout = QVBoxLayout()
        self.spectra_figure = Figure(figsize=(10, 6))
        self.spectra_canvas = FigureCanvas(self.spectra_figure)
        spectra_layout.addWidget(self.spectra_canvas)
        self.spectra_tab.setLayout(spectra_layout)
        
        # Вкладка 2: Интегралы
        self.integrals_tab = QWidget()
        integrals_layout = QVBoxLayout()
        self.integrals_figure = Figure(figsize=(10, 6))
        self.integrals_canvas = FigureCanvas(self.integrals_figure)
        integrals_layout.addWidget(self.integrals_canvas)
        self.integrals_tab.setLayout(integrals_layout)
        
        # Вкладка 3: Калибровочные кривые
        self.calibration_tab = QWidget()
        calibration_layout = QVBoxLayout()
        self.calibration_figure = Figure(figsize=(10, 6))
        self.calibration_canvas = FigureCanvas(self.calibration_figure)
        calibration_layout.addWidget(self.calibration_canvas)
        self.calibration_tab.setLayout(calibration_layout)
        
        self.tabs.addTab(self.spectra_tab, "Спектры")
        self.tabs.addTab(self.integrals_tab, "Интегралы")
        self.tabs.addTab(self.calibration_tab, "Калибровка")
        
        right_layout.addWidget(self.tabs)
        
        # Добавляем панели в разделитель
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 1000])
        
        main_layout.addWidget(splitter)
    
    def apply_language(self):
        """Применяет текущий язык ко всем элементам интерфейса"""
        if self.language == 'ru':
            self.apply_russian_translation()
        else:
            self.apply_english_translation()
        self.update_plot_labels()
    
    def apply_russian_translation(self):
        """Применяет русские тексты ко всем элементам интерфейса"""
        self.setWindowTitle("Анализатор спектроскопических данных")
        self.lang_btn.setText("RU")
        self.help_btn.setText("📖 Инструкция")
        
        # Параметры эксперимента
        self.params_group.setTitle("Параметры эксперимента")
        self.wavelength_label.setText("Длина волны возбуждения (нм):")
        self.method_label.setText("Метод интегрирования:")
        self.method_combo.setItemText(0, "Метод Симпсона")
        self.method_combo.setItemText(1, "Метод трапеций")
        self.trim_checkbox.setText("Обрезка данных для интегрирования")
        self.trim_min_label.setText("От:")
        self.trim_max_label.setText("До:")
        self.update_btn.setText("Обновить графики")
        
        # Загрузка данных
        self.data_group.setTitle("Загрузка данных")
        self.sample_btn.setText("Загрузить данные ОБРАЗЦА")
        self.standard_btn.setText("Загрузить данные СТАНДАРТА")
        if self.sample_label.text() in ["Not uploaded", "Не загружено"]:
            self.sample_label.setText("Не загружено")
        if self.standard_label.text() in ["Not uploaded", "Не загружено"]:
            self.standard_label.setText("Не загружено")
        
        # Расчет
        self.calc_group.setTitle("Расчет")
        self.calculate_btn.setText("Выполнить расчет")
        
        # Результаты
        self.results_group.setTitle("Результаты")
        
        # Вкладки
        self.tabs.setTabText(0, "Спектры")
        self.tabs.setTabText(1, "Интегралы")
        self.tabs.setTabText(2, "Калибровка")
        
        # Авторы
        self.authors_label.setText("Разработчик: Шулепов Р.Р.")
    
    def apply_english_translation(self):
        """Применяет английские тексты ко всем элементам интерфейса"""
        self.setWindowTitle("Spectroscopy Data Analyzer")
        self.lang_btn.setText("EN")
        self.help_btn.setText("📖 Manual")
        
        # Experiment parameters
        self.params_group.setTitle("Experiment Parameters")
        self.wavelength_label.setText("Excitation wavelength (nm):")
        self.method_label.setText("Integration method:")
        self.method_combo.setItemText(0, "Simpson's Method")
        self.method_combo.setItemText(1, "Trapezoidal Method")
        self.trim_checkbox.setText("Trim data for integration")
        self.trim_min_label.setText("From:")
        self.trim_max_label.setText("To:")
        self.update_btn.setText("Update spectra")
        
        
        # Data loading
        self.data_group.setTitle("Data Loading")
        self.sample_btn.setText("Load SAMPLE data")
        self.standard_btn.setText("Load STANDARD data")
        if self.sample_label.text() in ["Not uploaded", "Не загружено"]:
            self.sample_label.setText("Not uploaded")
        if self.standard_label.text() in ["Not uploaded", "Не загружено"]:
            self.standard_label.setText("Not uploaded")        
        
        # Calculation
        self.calc_group.setTitle("Calculation")
        self.calculate_btn.setText("Perform Calculation")
        
        # Results
        self.results_group.setTitle("Results")
        
        # Tabs
        self.tabs.setTabText(0, "Spectra")
        self.tabs.setTabText(1, "Integrals")
        self.tabs.setTabText(2, "Calibration")
        
        # Authors
        self.authors_label.setText("Developer: Shulepov R.R.")
    
    def toggle_language(self):
        """Переключение языка интерфейса"""
        if self.language == 'ru':
            self.language = 'en'
        else:
            self.language = 'ru'
        
        self.apply_language()
    
    def show_instructions(self):
        """Показать инструкцию"""
        dialog = InstructionDialog(self.language, self)
        dialog.exec_()
    
    def toggle_trimming(self, state):
        """Включение/выключение обрезки данных"""
        self.trim_data = (state == Qt.Checked)
        self.trim_min_input.setEnabled(self.trim_data)
        self.trim_max_input.setEnabled(self.trim_data)
    
    def update_spectra_plots(self):
        """Обновление графиков спектров с учетом текущего диапазона обрезки"""
        try:
            # Проверяем, есть ли данные для отображения
            if (self.data['sample']['emission_x'] or 
                self.data['standard']['emission_x']):
                
                # Обновляем графики для образца
                if self.data['sample']['emission_x']:
                    self.plot_spectra('sample')
                
                # Обновляем графики для стандарта
                if self.data['standard']['emission_x']:
                    self.plot_spectra('standard')
                
                # Показываем сообщение об успехе
                success_msg = ("Графики спектров успешно обновлены с учетом нового диапазона обрезки!" 
                              if self.language == 'ru' else 
                              "Spectra graphs successfully updated with new trimming range!")
                QMessageBox.information(self, "Успех" if self.language == 'ru' else "Success", success_msg)
            else:
                error_msg = ("Нет данных для отображения. Сначала загрузите данные." 
                            if self.language == 'ru' else 
                            "No data to display. Please load data first.")
                QMessageBox.warning(self, "Предупреждение" if self.language == 'ru' else "Warning", error_msg)
                
        except Exception as e:
            error_msg = (f"Ошибка при обновлении графиков: {str(e)}" 
                        if self.language == 'ru' else 
                        f"Error updating graphs: {str(e)}")
            QMessageBox.warning(self, "Ошибка" if self.language == 'ru' else "Error", error_msg)
        
    
    def trim_spectrum(self, x, y):
        """Обрезка спектра по заданному диапазону"""
        if not self.trim_data:
            return x, y
        
        try:
            min_val = float(self.trim_min_input.text())
            max_val = float(self.trim_max_input.text())
            
            trimmed_x = []
            trimmed_y = []
            
            for i, wavelength in enumerate(x):
                if min_val <= wavelength <= max_val:
                    trimmed_x.append(wavelength)
                    trimmed_y.append(y[i])
            
            return trimmed_x, trimmed_y
        except ValueError:
            return x, y
    
    def calculate_ex_pic(self, absorption_x, absorption_y, hv):
        """ВЫЧИСЛЯЕТ интенсивность при заданной длине волны ВОЗБУЖДЕНИЯ"""
        ex_pic = []
        for i in range(len(absorption_x)):
            spectrum_x = absorption_x[i]
            spectrum_y = absorption_y[i]
            ex_value = 0
            # Ищем ближайшее значение к hv в спектре
            min_diff = float('inf')
            best_value = 0
            for j, wavelength in enumerate(spectrum_x):
                diff = abs(wavelength - hv)
                if diff < min_diff:
                    min_diff = diff
                    best_value = spectrum_y[j]
            ex_pic.append(best_value)
        return ex_pic
    
    def robust_float_conversion(self, value):
        """Безопасное преобразование в float"""
        try:
            # Убираем возможные пробелы и нечисловые символы
            cleaned_value = ''.join(c for c in str(value) if c.isdigit() or c in '.-eE')
            return float(cleaned_value)
        except (ValueError, TypeError):
            return None
    
    def load_sample_data(self):
        folder = QFileDialog.getExistingDirectory(self, 
            "Выберите папку с данными ОБРАЗЦА" if self.language == 'ru' else "Select folder with SAMPLE data")
        if folder:
            self.sample_label.setText(os.path.basename(folder))
            self.process_folder_data(folder, 'sample')
        self.update_btn.setEnabled(True)
            
    def load_standard_data(self):
        folder = QFileDialog.getExistingDirectory(self,
            "Выберите папку с данными СТАНДАРТА" if self.language == 'ru' else "Select folder with STANDARD data")
        if folder:
            self.standard_label.setText(os.path.basename(folder))
            self.process_folder_data(folder, 'standard')
        self.update_btn.setEnabled(True)
    
    def process_folder_data(self, folder, data_type):
        """Обработка данных из папки БЕЗ сохранения ex_pic"""
        emission_x = []
        emission_y = []
        absorption_x = []
        absorption_y = []
        
        try:
            for root, dirs, files in os.walk(folder):
                emission_files = [f for f in files if f.endswith('.tit')]
                absorption_files = [f for f in files if f.endswith('.txt')]
                
                # Обрабатываем файлы эмиссии
                for file in emission_files:
                    file_path = os.path.join(root, file)
                    x, y = self.read_emission_file(file_path)
                    if x and y:
                        emission_x.append(x)
                        emission_y.append(y)
                
                # Обрабатываем файлы абсорбции
                for file in absorption_files:
                    file_path = os.path.join(root, file)
                    x_a, y_a = self.read_absorption_file(file_path)  # УБРАЛИ параметр hv
                    if x_a and y_a:
                        absorption_x.append(x_a)
                        absorption_y.append(y_a)
            
            self.data[data_type]['emission_x'] = emission_x
            self.data[data_type]['emission_y'] = emission_y
            self.data[data_type]['absorption_x'] = absorption_x
            self.data[data_type]['absorption_y'] = absorption_y
            # НЕ сохраняем ex_pic здесь - он будет вычисляться при каждом расчете
            
            self.plot_spectra(data_type)
            
            success_msg = (f"Данные {data_type} успешно загружены!" if self.language == 'ru' 
                          else f"{data_type.capitalize()} data successfully loaded!")
            QMessageBox.information(self, "Успех" if self.language == 'ru' else "Success", success_msg)
            
        except Exception as e:
            error_msg = (f"Ошибка при загрузке данных: {str(e)}" if self.language == 'ru'
                        else f"Error loading data: {str(e)}")
            QMessageBox.warning(self, "Ошибка" if self.language == 'ru' else "Error", error_msg)
    
    def read_emission_file(self, filepath):
        """Чтение .tit файлов с улучшенной обработкой ошибок"""
        x, y = [], []
        lines_processed = 0
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Пробуем разные разделители
                    for separator in [';', ',', '\t', ' ']:
                        if separator in line:
                            parts = [part.strip() for part in line.split(separator) if part.strip()]
                            if len(parts) >= 6:  # Нужно как минимум 6 колонок
                                try:
                                    x_val = self.robust_float_conversion(parts[0])
                                    y_val = self.robust_float_conversion(parts[5])
                                    
                                    if x_val is not None and y_val is not None:
                                        x.append(x_val)
                                        y.append(y_val)
                                        lines_processed += 1
                                        break  # Успешно обработали строку
                                except (ValueError, IndexError):
                                    continue
            
            if lines_processed == 0:
                warning_msg = (f"Файл {os.path.basename(filepath)} не содержит числовых данных в ожидаемом формате"
                              if self.language == 'ru' else
                              f"File {os.path.basename(filepath)} contains no numeric data in expected format")
                QMessageBox.warning(self, "Предупреждение" if self.language == 'ru' else "Warning", warning_msg)
                return [], []
                
            return x, y
            
        except Exception as e:
            error_msg = (f"Ошибка чтения файла {filepath}: {str(e)}" if self.language == 'ru'
                        else f"Error reading file {filepath}: {str(e)}")
            QMessageBox.warning(self, "Ошибка" if self.language == 'ru' else "Error", error_msg)
            return [], []
    
    def read_absorption_file(self, filepath):
        """Чтение .txt файлов абсорбции с улучшенной обработкой ошибок"""
        x, y = [], []
        lines_processed = 0
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                for line in file:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Пробуем разные разделители
                    for separator in [',', ';', '\t', ' ']:
                        if separator in line:
                            parts = [part.strip() for part in line.split(separator) if part.strip()]
                            if len(parts) >= 2:
                                try:
                                    x_val = self.robust_float_conversion(parts[0])
                                    y_val = self.robust_float_conversion(parts[1])
                                    
                                    if x_val is not None and y_val is not None:
                                        x.append(x_val)
                                        y.append(y_val)
                                        lines_processed += 1
                                        break
                                except (ValueError, IndexError):
                                    continue
            
            if lines_processed == 0:
                warning_msg = (f"Файл {os.path.basename(filepath)} не содержит числовых данных в ожидаемом формате"
                              if self.language == 'ru' else
                              f"File {os.path.basename(filepath)} contains no numeric data in expected format")
                QMessageBox.warning(self, "Предупреждение" if self.language == 'ru' else "Warning", warning_msg)
                return [], []
                
            return x, y
            
        except Exception as e:
            error_msg = (f"Ошибка чтения файла {filepath}: {str(e)}" if self.language == 'ru'
                        else f"Error reading file {filepath}: {str(e)}")
            QMessageBox.warning(self, "Ошибка" if self.language == 'ru' else "Error", error_msg)
            return [], []

    def simpson_nonuniform(self, x, f):
        """Метод Симпсона для неравномерной сетки"""
        if len(x) < 2:
            return 0.0
            
        N = len(x) - 1
        h = [x[i + 1] - x[i] for i in range(N)]
        assert N > 0
        result = 0.0
        for i in range(1, N, 2):
            h0, h1 = h[i - 1], h[i]
            hph, hdh, hmh = h1 + h0, h1 / h0, h1 * h0
            result += (hph / 6) * ((2 - hdh) * f[i - 1] + (hph**2 / hmh) * f[i] + (2 - 1 / hdh) * f[i + 1])
        if N % 2 == 1:
            h0, h1 = h[N - 2], h[N - 1]
            result += f[N] * (2 * h1 ** 2 + 3 * h0 * h1) / (6 * (h0 + h1))
            result += f[N - 1] * (h1 ** 2 + 3 * h1 * h0) / (6 * h0)
            result -= f[N - 2] * h1 ** 3 / (6 * h0 * (h0 + h1))
        return result
    
    def trapezoid_rule(self, x, f):
        """Метод трапеций"""
        if len(x) < 2:
            return 0.0
            
        N = len(x) - 1
        dx = [x[i+1] - x[i] for i in range(N)]
        result = 0.0
        for i in range(N):
            result += dx[i] * (f[i+1] + f[i]) / 2
        return result
    
    def calculate_integrals(self, data_type):
        """Расчет интегралов с возможностью обрезки"""
        emission_x = self.data[data_type]['emission_x']
        emission_y = self.data[data_type]['emission_y']
        
        integrals_simpson = []
        integrals_trapezoid = []
        
        for i in range(len(emission_x)):
            if len(emission_x[i]) > 1:
                # Применяем обрезку если включена
                x_trimmed, y_trimmed = self.trim_spectrum(emission_x[i], emission_y[i])
                
                if len(x_trimmed) > 1:
                    integral_s = self.simpson_nonuniform(x_trimmed, y_trimmed)
                    integral_t = self.trapezoid_rule(x_trimmed, y_trimmed)
                    integrals_simpson.append(integral_s)
                    integrals_trapezoid.append(integral_t)
        
        self.data[data_type]['integrals_simpson'] = integrals_simpson
        self.data[data_type]['integrals_trapezoid'] = integrals_trapezoid       
        
        return integrals_simpson, integrals_trapezoid
    
    def linear_regression(self, x, y):
        """Линейная регрессия МНК"""
        if len(x) < 2:
            return 0, 0
            
        n = len(x)
        sum_xy = sum(x_i * y_i for x_i, y_i in zip(x, y))
        sum_x = sum(x)
        sum_y = sum(y)
        sum_x2 = sum(x_i**2 for x_i in x)
        
        denominator = n * sum_x2 - sum_x**2
        if denominator == 0:
            return 0, 0
            
        a = (n * sum_xy - sum_x * sum_y) / denominator
        b = (sum_y - a * sum_x) / n
        
        return a, b
    
    def plot_spectra(self, data_type):
        """Построение спектров с учетом обрезки"""
        self.spectra_figure.clear()
        
        emission_x = self.data[data_type]['emission_x']
        emission_y = self.data[data_type]['emission_y']
        absorption_x = self.data[data_type]['absorption_x']
        absorption_y = self.data[data_type]['absorption_y']
        
        if emission_x and absorption_x:
            ax1 = self.spectra_figure.add_subplot(121)
            for i, (x, y) in enumerate(zip(emission_x, emission_y)):
                # Применяем обрезку если включена
                x_trimmed, y_trimmed = self.trim_spectrum(x, y)
                ax1.plot(x_trimmed, y_trimmed, label=f'Эмиссия {i+1}' if self.language == 'ru' else f'Emission {i+1}')
            ax1.set_xlabel('Длина волны (нм)' if self.language == 'ru' else "Wavelength (nm)")
            ax1.set_ylabel('Абсолютная интенсивность' if self.language == 'ru' else "Absolute intensity")
            ax1.set_title(f'Спектры эмиссии ({data_type})' if self.language == 'ru' else f'Emission spectra ({data_type})')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            ax2 = self.spectra_figure.add_subplot(122)
            for i, (x, y) in enumerate(zip(absorption_x, absorption_y)):
                ax2.plot(x, y, label=f'Абсорбция {i+1}' if self.language == 'ru' else f"Absorption {i+1}")
            ax2.set_xlabel('Длина волны (нм)' if self.language == 'ru' else "Wavelength (nm)")
            ax2.set_ylabel('Оптическая плотность' if self.language == 'ru' else "Optical density")
            ax2.set_title(f'Спектры абсорбции ({data_type})' if self.language == 'ru' else f"Absorption spectra ({data_type})")
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            self.spectra_figure.tight_layout()
            self.spectra_canvas.draw()        
    
    def update_plot_labels(self):
        """Обновляет подписи на графиках без перерасчета данных"""
        # Обновляем вкладки
        if self.language == 'ru':
            self.tabs.setTabText(0, "Спектры")
            self.tabs.setTabText(1, "Интегралы")
            self.tabs.setTabText(2, "Калибровка")
        else:
            self.tabs.setTabText(0, "Spectra")
            self.tabs.setTabText(1, "Integrals")
            self.tabs.setTabText(2, "Calibration")
        
        # Перерисовываем графики с новыми подписями
        self.redraw_all_plots()
    
    def redraw_all_plots(self):
        """Перерисовывает все графики с текущими данными и языком"""
        # Перерисовываем спектры если есть данные
        if self.data['sample']['emission_x']:
            self.plot_spectra('sample')
        elif self.data['standard']['emission_x']:
            self.plot_spectra('standard')
        
        # Перерисовываем интегралы если есть данные
        if (self.data['sample']['ex_pic'] and self.data['sample']['integrals_simpson']):
            self.plot_integrals()
        
        # Перерисовываем калибровку если есть данные
        if (self.data['sample']['ex_pic'] and self.data['sample']['integrals_simpson']):
            # Временно рассчитываем регрессию для перерисовки
            x_ob = self.data['sample']['ex_pic']
            y_ob = (self.data['sample']['integrals_simpson'] if self.current_method == 'simpson' 
                   else self.data['sample']['integrals_trapezoid'])
            
            if len(x_ob) >= 2:
                a_ob, b_ob = self.linear_regression(x_ob, y_ob)
                a_st, b_st = 0, 0
                
                if self.data['standard']['ex_pic'] and self.data['standard']['integrals_simpson']:
                    x_st = self.data['standard']['ex_pic']
                    y_st = (self.data['standard']['integrals_simpson'] if self.current_method == 'simpson' 
                           else self.data['standard']['integrals_trapezoid'])
                    
                    if len(x_st) >= 2:
                        a_st, b_st = self.linear_regression(x_st, y_st)
                
                self.plot_calibration(a_ob, b_ob, a_st, b_st)    
    
    def plot_integrals(self):
        """Построение графиков интегралов"""
        self.integrals_figure.clear()
        
        # Образец
        if self.data['sample']['ex_pic'] and self.data['sample']['integrals_simpson']:
            ax1 = self.integrals_figure.add_subplot(121)
            ex_pic = self.data['sample']['ex_pic']
            integrals_s = self.data['sample']['integrals_simpson']
            integrals_t = self.data['sample']['integrals_trapezoid']
            
            ax1.plot(ex_pic, integrals_s, 'ro-', label='Метод Симпсона')
            ax1.plot(ex_pic, integrals_t, 'bo-', label='Метод трапеций')
            ax1.set_xlabel('Интенсивность поглощения' if self.language == 'ru' else "Absorbtion intensity")
            ax1.set_ylabel('Интегральная интенсивность эмиссии' if self.language == 'ru' else "Integral emission intensity")
            ax1.set_title('Образец' if self.language == 'ru' else "Sample")
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        
        # Стандарт
        if self.data['standard']['ex_pic'] and self.data['standard']['integrals_simpson']:
            ax2 = self.integrals_figure.add_subplot(122)
            ex_pic = self.data['standard']['ex_pic']
            integrals_s = self.data['standard']['integrals_simpson']
            integrals_t = self.data['standard']['integrals_trapezoid']
            
            ax2.plot(ex_pic, integrals_s, 'ro-', label='Метод Симпсона')
            ax2.plot(ex_pic, integrals_t, 'bo-', label='Метод трапеций')
            ax2.set_xlabel('Интенсивность поглощения' if self.language == 'ru' else "Absorbtion intensity")
            ax2.set_ylabel('Интегральная интенсивность эмиссии' if self.language == 'ru' else "Integral emission intensity")
            ax2.set_title('Стандарт' if self.language == 'ru' else "Standard")
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        self.integrals_figure.tight_layout()
        self.integrals_canvas.draw()
    
    def plot_calibration(self, a_ob, b_ob, a_st, b_st):
        """Построение калибровочных кривых"""
        self.calibration_figure.clear()
        
        # Образец
        if self.data['sample']['ex_pic'] and self.data['sample']['integrals_simpson']:
            ax1 = self.calibration_figure.add_subplot(121)
            x_ob = self.data['sample']['ex_pic']
            y_ob = self.data['sample']['integrals_simpson'] if self.current_method == 'simpson' else self.data['sample']['integrals_trapezoid']
            
            ax1.plot(x_ob, y_ob, 'ro', label='Экспериментальные точки' if self.language == 'ru' else "Experimental points")
            
            # Линия регрессии
            x_line = np.array([0, max(x_ob)])
            y_line = a_ob * x_line + b_ob
            ax1.plot(x_line, y_line, 'b-', label=f'y = {a_ob:.4f}x + {b_ob:.4f}')
            
            ax1.set_xlabel('Интенсивность поглощения' if self.language == 'ru' else "Absorbtion intensity")
            ax1.set_ylabel('Интегральная интенсивность эмиссии' if self.language == 'ru' else "Integral emission intensity")
            ax1.set_title('Калибровка: Образец' if self.language == 'ru' else "Calibration: Sample")
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        
        # Стандарт
        if self.data['standard']['ex_pic'] and self.data['standard']['integrals_simpson']:
            ax2 = self.calibration_figure.add_subplot(122)
            x_st = self.data['standard']['ex_pic']
            y_st = self.data['standard']['integrals_simpson'] if self.current_method == 'simpson' else self.data['standard']['integrals_trapezoid']
            
            ax2.plot(x_st, y_st, 'ro', label='Экспериментальные точки' if self.language == 'ru' else "Experimental points")
            
            # Линия регрессии
            x_line = np.array([0, max(x_st)])
            y_line = a_st * x_line + b_st
            ax2.plot(x_line, y_line, 'b-', label=f'y = {a_st:.4f}x + {b_st:.4f}')
            
            ax2.set_xlabel('Интенсивность поглощения' if self.language == 'ru' else "Absorbtion intensity")
            ax2.set_ylabel('Интегральная интенсивность эмиссии' if self.language == 'ru' else "Integral emission intensity")
            ax2.set_title('Калибровка: Стандарт' if self.language == 'ru' else "Calibration: Standard")
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        self.calibration_figure.tight_layout()
        self.calibration_canvas.draw()
    
    def calculate_quantum_yield(self, a_ob, a_st):
        """Расчет квантового выхода"""
        # Диалог для ввода параметров
        title = "Квантовый выход стандарта" if self.language == 'ru' else "Standard quantum yield"
        label = "Введите квантовый выход стандарта (%):" if self.language == 'ru' else "Enter standard quantum yield (%):"
        
        qy_st, ok = QInputDialog.getDouble(self, title, label, 4.2, 0, 100, 2)
        if not ok:
            return None
        
        question = "Образец и стандарт в одном растворителе?" if self.language == 'ru' else "Sample and standard in the same solvent?"
        solvent_same = QMessageBox.question(self, "Растворитель" if self.language == 'ru' else "Solvent", 
                                          question, QMessageBox.Yes | QMessageBox.No)
        
        if solvent_same == QMessageBox.Yes:
            n_o, n_s = 1, 1
        else:
            if self.language == 'ru':
                solvents = {"Вода": 1.348, "Этанол": 1.3688, "Метанол": 1.3284, "Дихлорметан": 1.439, "Другой": "a"}
                
                solvent_ob, ok = QInputDialog.getItem(self, "Растворитель образца", 
                                                    "Выберите растворитель для образца:", list(solvents.keys()), 0, False)
                if ok:
                    n_o = solvents[solvent_ob]
                    if n_o == "a":
                        n_o, ok = QInputDialog.getDouble(self, "Показатель преломления образца", 
                                             "Введите показатель преломления образца (%):", 1.3333, 0, 20, 4)
                    if not ok:
                        return None
                
                solvent_st, ok = QInputDialog.getItem(self, "Растворитель стандарта", 
                                                    "Выберите растворитель для стандарта:", list(solvents.keys()), 0, False)
                if ok:
                    n_s = solvents[solvent_st]
                    if n_s == "a":
                        n_s, ok = QInputDialog.getDouble(self, "Показатель преломления образца", 
                                             "Введите показатель преломления образца:", 1.3333, 0, 20, 4)                 
            else:
                solvents = {"Water": 1.348, "Ethanol": 1.3688, "Methanol": 1.3284, "Dichloromethane": 1.439, "Another": "a"}
                
                solvent_ob, ok = QInputDialog.getItem(self, "Sample Solvent", 
                                                    "Enter the refractive index of the sample:", list(solvents.keys()), 0, False)
                if ok:
                    n_o = solvents[solvent_ob]
                    if n_o == "a":
                        n_o, ok = QInputDialog.getDouble(self, "Refractive index of the sample", 
                                             "Enter the refractive index of the sample:", 1.3333, 0, 20, 4)
                    if not ok:
                        return None
                
                solvent_st, ok = QInputDialog.getItem(self, "Solvent of the standard", 
                                                    "Choose a solvent for the standard:", list(solvents.keys()), 0, False)
                if ok:
                    n_s = solvents[solvent_st]
                    if n_s == "a":
                        n_s, ok = QInputDialog.getDouble(self, "Refractive index of the standard", 
                                             "Enter the refractive index of the standard:", 1.3333, 0, 20, 4)                 
        
        # Расчет квантового выхода
        if a_st != 0:
            QY = qy_st * (a_ob / a_st) * (n_o / n_s) ** 2
        else:
            QY = 0
        
        return QY
    
    def perform_calculation(self):
        """Основная процедура расчета"""
        try:
            self.progress_bar.setValue(10)
            
            # Проверка данных
            if not self.data['sample']['emission_x']:
                error_msg = "Сначала загрузите данные образца!" if self.language == 'ru' else "Please load sample data first!"
                QMessageBox.warning(self, "Ошибка" if self.language == 'ru' else "Error", error_msg)
                return
            
            # ПОЛУЧАЕМ ТЕКУЩУЮ длину волны возбуждения
            try:
                hv = float(self.wavelength_input.text())
            except ValueError:
                error_msg = "Некорректное значение длины волны возбуждения!" if self.language == 'ru' else "Invalid excitation wavelength value!"
                QMessageBox.warning(self, "Ошибка" if self.language == 'ru' else "Error", error_msg)
                return
            
            self.progress_bar.setValue(20)
            
            # ВЫЧИСЛЯЕМ ex_pic для образца с ТЕКУЩЕЙ длиной волны
            if self.data['sample']['absorption_x']:
                self.data['sample']['ex_pic'] = self.calculate_ex_pic(
                    self.data['sample']['absorption_x'], 
                    self.data['sample']['absorption_y'], 
                    hv
                )
            
            # ВЫЧИСЛЯЕМ ex_pic для стандарта с ТЕКУЩЕЙ длиной волны
            if self.data['standard']['absorption_x']:
                self.data['standard']['ex_pic'] = self.calculate_ex_pic(
                    self.data['standard']['absorption_x'],
                    self.data['standard']['absorption_y'],
                    hv
                )
            
            self.progress_bar.setValue(30)
            
            # Определение метода
            self.current_method = 'simpson' if self.method_combo.currentText() == "Метод Симпсона" else 'trapezoid'
            
            # Расчет интегралов
            self.calculate_integrals('sample')
            if self.data['standard']['emission_x']:
                self.calculate_integrals('standard')
            
            self.progress_bar.setValue(50)
            
            # Построение графиков
            self.plot_integrals()
            
            self.progress_bar.setValue(70)
            
            # Линейная регрессия для образца
            x_ob = self.data['sample']['ex_pic']
            y_ob = (self.data['sample']['integrals_simpson'] if self.current_method == 'simpson' 
                   else self.data['sample']['integrals_trapezoid'])
            
            if len(x_ob) != len(y_ob) or len(x_ob) < 2:
                error_msg = "Недостаточно данных для регрессии образца!" if self.language == 'ru' else "Not enough data for sample regression!"
                QMessageBox.warning(self, "Ошибка" if self.language == 'ru' else "Error", error_msg)
                return
            
            a_ob, b_ob = self.linear_regression(x_ob, y_ob)
            
            # Линейная регрессия для стандарта
            a_st, b_st = 0, 0
            if self.data['standard']['ex_pic'] and self.data['standard']['integrals_simpson']:
                x_st = self.data['standard']['ex_pic']
                y_st = (self.data['standard']['integrals_simpson'] if self.current_method == 'simpson' 
                       else self.data['standard']['integrals_trapezoid'])
                
                if len(x_st) == len(y_st) and len(x_st) >= 2:
                    a_st, b_st = self.linear_regression(x_st, y_st)
            
            self.progress_bar.setValue(90)
            
            # Построение калибровочных кривых
            self.plot_calibration(a_ob, b_ob, a_st, b_st)
            
            # Расчет квантового выхода (если есть стандарт)
            if self.language == 'ru':
                results_text = f"=== РЕЗУЛЬТАТЫ РАСЧЕТА ===\n\n"
                results_text += f"Длина волны возбуждения: {hv} нм\n"
                results_text += f"Метод интегрирования: {self.method_combo.currentText()}\n"
                
                if self.trim_data:
                    results_text += f"Обрезка данных: {self.trim_min_input.text()} - {self.trim_max_input.text()} нм\n"
                
                results_text += f"\nОБРАЗЕЦ:\n"
                results_text += f"Уравнение регрессии: y = {a_ob:.6f}x + {b_ob:.6f}\n"
                results_text += f"Коэффициент наклона: {a_ob:.6f}\n\n"
                
                if a_st != 0:
                    results_text += f"СТАНДАРТ:\n"
                    results_text += f"Уравнение регрессии: y = {a_st:.6f}x + {b_st:.6f}\n"
                    results_text += f"Коэффициент наклона: {a_st:.6f}\n\n"
                    
                    # Расчет квантового выхода
                    QY = self.calculate_quantum_yield(a_ob, a_st)
                    if QY is not None:
                        results_text += f"КВАНТОВЫЙ ВЫХОД:\n"
                        results_text += f"QY = {QY:.2f} %\n\n"
                
                results_text += "Разработчики: Шулепов Ростислав Русланович\n"
                results_text += "Кафедра общей и неорганической химии СПбГУ"
            else:
                results_text = f"=== CALCULATION RESULTS ===\n\n"
                results_text += f"Excitation wavelength: {hv} nm\n"
                results_text += f"Integration method: {self.method_combo.currentText()}\n"
                
                if self.trim_data:
                    results_text += f"Data trimming: {self.trim_min_input.text()} - {self.trim_max_input.text()} nm\n"
                
                results_text += f"\nSAMPLE:\n"
                results_text += f"Regression equation: y = {a_ob:.6f}x + {b_ob:.6f}\n"
                results_text += f"Slope coefficient: {a_ob:.6f}\n\n"
                
                if a_st != 0:
                    results_text += f"STANDARD:\n"
                    results_text += f"Regression equation: y = {a_st:.6f}x + {b_st:.6f}\n"
                    results_text += f"Slope coefficient: {a_st:.6f}\n\n"
                    
                    # Расчет квантового выхода
                    QY = self.calculate_quantum_yield(a_ob, a_st)
                    if QY is not None:
                        results_text += f"QUANTUM YIELD:\n"
                        results_text += f"QY = {QY:.2f} %\n\n"
                
                results_text += "Developers: Shulepov Rostislav Ruslanovich\n"
                results_text += "Department of General and Inorganic Chemistry SPbSU"
            
            self.results_text.setText(results_text)
            self.progress_bar.setValue(100)
            
            success_msg = "Все расчеты успешно выполнены!" if self.language == 'ru' else "All calculations completed successfully!"
            QMessageBox.information(self, "Расчет завершен" if self.language == 'ru' else "Calculation Complete", success_msg)
            
        except Exception as e:
            error_msg = f"Произошла ошибка: {str(e)}" if self.language == 'ru' else f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Ошибка расчета" if self.language == 'ru' else "Calculation Error", error_msg)
            self.progress_bar.setValue(0)

def main():
    app = QApplication(sys.argv)
    window = SpectroscopyApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()