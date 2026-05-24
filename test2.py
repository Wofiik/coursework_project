import sys
import os
import math
import json
import shutil
from threading import Thread
from functools import partial
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QScrollArea, 
                             QFrame, QFileDialog, QMessageBox, QLineEdit,
                             QComboBox, QGroupBox, QCheckBox, QSlider,
                             QTabWidget, QDoubleSpinBox, QSplitter, QSizePolicy,
                             QColorDialog, QProgressBar)
from PyQt5.QtCore import Qt, QSize, QPoint, QRect, QPointF, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import (QFont, QPainter, QColor, QPen, QBrush, QPolygon, QPolygonF,
                         QPainterPath, QLinearGradient, QRadialGradient, 
                         QPixmap, QImage, QTransform)


class RectangularButton(QPushButton):
    """Стилизованная кнопка"""
    def __init__(self, text, command=None, width=200, height=40, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(width, height)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font: bold 10pt 'Segoe UI';
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        if command:
            self.clicked.connect(command)


class ScrollableWidget(QWidget):
    """Виджет с прокруткой"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)
    
    def clear(self):
        """Очищает содержимое"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class ShapeOverlayWidget(QWidget):
    """Виджет для наложения фигур с расширенными возможностями"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 500)
        self.setStyleSheet("background-color: white; border: 1px solid #cccccc; border-radius: 10px;")
        
        # Параметры фигур
        self.shape1_type = "Квадрат"
        self.shape2_type = "Круг"
        self.shape1_params = {'x_offset': -50, 'y_offset': 0, 'size': 120, 'rotation': 0, 'opacity': 200}
        self.shape2_params = {'x_offset': 50, 'y_offset': 0, 'size': 120, 'rotation': 0, 'opacity': 200}
        
        self.shape1_color = QColor(70, 130, 200)
        self.shape2_color = QColor(220, 80, 80)
        
        self.show_shape1 = True
        self.show_shape2 = True
        
        # Переменные для перетаскивания
        self.dragging_shape = None
        self.drag_start_pos = None
        self.shape1_drag_start = None
        self.shape2_drag_start = None
        
        # Масштаб
        self.zoom_level = 1.0
        
        self.setMouseTracking(True)
    
    def set_visibility(self, shape1_visible, shape2_visible):
        self.show_shape1 = shape1_visible
        self.show_shape2 = shape2_visible
        self.update()
    
    def set_zoom(self, zoom):
        self.zoom_level = zoom
        self.update()
    
    def paintEvent(self, event):
        """Рисует фигуры с наложением"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Рисуем фон
        painter.fillRect(self.rect(), QColor(240, 240, 245))
        
        # Сохраняем состояние painter'а перед масштабированием
        painter.save()
        
        # Применяем масштаб
        painter.scale(self.zoom_level, self.zoom_level)
        
        # Рисуем сетку
        self.draw_grid(painter)
        
        # Рисуем фигуры с прозрачностью
        self.draw_normal(painter)
        
        painter.restore()
    
    def draw_grid(self, painter):
        """Рисует координатную сетку"""
        scaled_width = self.width() / self.zoom_level
        scaled_height = self.height() / self.zoom_level
        
        painter.setPen(QPen(QColor(180, 180, 200), 1, Qt.SolidLine))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        
        # Вертикальные линии
        for x in range(0, int(scaled_width), 50):
            painter.drawLine(x, 0, x, int(scaled_height))
            x_coord = int(x - scaled_width // 2)
            painter.setPen(QPen(QColor(100, 100, 120), 1))
            painter.drawText(x + 2, 12, f"{x_coord}")
            painter.setPen(QPen(QColor(180, 180, 200), 1))
        
        # Горизонтальные линии
        for y in range(0, int(scaled_height), 50):
            painter.drawLine(0, y, int(scaled_width), y)
            y_coord = int(scaled_height // 2 - y)
            painter.setPen(QPen(QColor(100, 100, 120), 1))
            painter.drawText(2, y - 2, f"{y_coord}")
            painter.setPen(QPen(QColor(180, 180, 200), 1))
        
        # Оси координат - преобразуем float в int
        center_x = int(scaled_width // 2)
        center_y = int(scaled_height // 2)
        
        painter.setPen(QPen(QColor(0, 0, 0), 3))
        painter.drawLine(center_x, 0, center_x, int(scaled_height))
        painter.drawLine(0, center_y, int(scaled_width), center_y)
        
        # Подписи осей
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(center_x + 5, 15, "X")
        painter.drawText(int(scaled_width) - 15, center_y - 5, "Y")
        
        # Центр
        painter.setPen(QPen(QColor(0, 0, 0), 4))
        painter.drawPoint(center_x, center_y)
        painter.drawText(center_x + 3, center_y - 3, "0")
    
    def draw_shape_3d(self, painter, shape_type, params, color, label, is_dragging=False):
        """Рисует 3D фигуру с эффектом объема и поддержкой вращения"""
        center_x = self.width() / self.zoom_level / 2
        center_y = self.height() / self.zoom_level / 2
        
        x = params.get('x_offset', 0)
        y = params.get('y_offset', 0)
        size = params.get('size', 120)
        radius = size // 2
        rotation = params.get('rotation', 0)
        
        # Эффект подсветки при перетаскивании
        if is_dragging:
            painter.setOpacity(0.8)
            glow_color = QColor(color.red(), color.green(), color.blue(), 100)
            painter.setBrush(QBrush(glow_color))
        
        # Сохраняем состояние painter'а для вращения
        painter.save()
        
        # Применяем трансформацию: сначала перемещаем в центр фигуры, вращаем, потом возвращаем
        transform = QTransform()
        transform.translate(center_x + x, center_y + y)
        transform.rotate(rotation)
        transform.translate(-(center_x + x), -(center_y + y))
        painter.setTransform(transform, True)
        
        if shape_type == "Круг":
            # 2D окружность
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawEllipse(int(center_x - radius + x), int(center_y - radius + y), radius * 2, radius * 2)
            
        elif shape_type == "Квадрат":
            # 2D квадрат
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawRect(int(center_x - size//2 + x), int(center_y - size//2 + y), size, size)
            
        elif shape_type == "Треугольник":
            # 2D треугольник
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            points = [
                QPoint(int(center_x + x), int(center_y - size//2 + y)),
                QPoint(int(center_x - size//2 + x), int(center_y + size//2 + y)),
                QPoint(int(center_x + size//2 + x), int(center_y + size//2 + y))
            ]
            painter.drawPolygon(points)
            
        elif shape_type == "Куб":
            # 3D куб без теней - все грани одного цвета
            offset = size // 3
            
            # Передняя грань
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawRect(int(center_x - size//2 + x), int(center_y - size//2 + y), size, size)
            
            # Верхняя грань
            points = [
                QPoint(int(center_x - size//2 + x), int(center_y - size//2 + y)),
                QPoint(int(center_x - size//2 + offset + x), int(center_y - size//2 - offset + y)),
                QPoint(int(center_x + size//2 + offset + x), int(center_y - size//2 - offset + y)),
                QPoint(int(center_x + size//2 + x), int(center_y - size//2 + y))
            ]
            painter.drawPolygon(points)
            
            # Боковая грань
            points = [
                QPoint(int(center_x + size//2 + x), int(center_y - size//2 + y)),
                QPoint(int(center_x + size//2 + offset + x), int(center_y - size//2 - offset + y)),
                QPoint(int(center_x + size//2 + offset + x), int(center_y + size//2 - offset + y)),
                QPoint(int(center_x + size//2 + x), int(center_y + size//2 + y))
            ]
            painter.drawPolygon(points)
            
        elif shape_type == "Шар":
            # 3D шар с радиальным градиентом
            gradient = QRadialGradient(center_x + x - radius//3, center_y + y - radius//3, radius)
            gradient.setColorAt(0, QColor(color.red() + 50, color.green() + 50, color.blue() + 50))
            gradient.setColorAt(0.5, color)
            gradient.setColorAt(1, QColor(color.red()//2, color.green()//2, color.blue()//2))
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawEllipse(int(center_x - radius + x), int(center_y - radius + y), radius * 2, radius * 2)
            
            # Добавляем блик
            painter.setBrush(QBrush(QColor(255, 255, 255, 100)))
            painter.drawEllipse(int(center_x + x - radius//2), int(center_y + y - radius//2), radius//3, radius//3)
        
        painter.setOpacity(1.0)
        
        # Рисуем метку
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        font = painter.font()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(int(center_x + x - 35), int(center_y + y - size//2 - 10), label)
        
        # Координаты
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(QColor(255, 255, 200, 230)))
        font.setPointSize(8)
        font.setBold(False)
        painter.setFont(font)
        coord_text = f"X:{x:+d} Y:{y:+d} R:{rotation}°"
        painter.drawText(int(center_x + x - 55), int(center_y + y + size//2 + 15), coord_text)
        
        # Восстанавливаем состояние painter'а
        painter.restore()
    
    def draw_normal(self, painter):
        """Обычное наложение с прозрачностью"""
        if self.show_shape1:
            color1 = QColor(self.shape1_color)
            color1.setAlpha(self.shape1_params.get('opacity', 200))
            self.draw_shape_3d(painter, self.shape1_type, self.shape1_params, color1, "Фигура 1", 
                              self.dragging_shape == 'shape1')
        
        if self.show_shape2:
            color2 = QColor(self.shape2_color)
            color2.setAlpha(self.shape2_params.get('opacity', 200))
            self.draw_shape_3d(painter, self.shape2_type, self.shape2_params, color2, "Фигура 2",
                              self.dragging_shape == 'shape2')
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            scaled_x = int(pos.x() / self.zoom_level)
            scaled_y = int(pos.y() / self.zoom_level)
            scaled_pos = QPointF(scaled_x, scaled_y)
            
            center_x = self.width() / self.zoom_level / 2
            center_y = self.height() / self.zoom_level / 2
            
            if self.show_shape1 and self.shape1_type:
                path1 = self.get_shape_path(self.shape1_type, self.shape1_params, center_x, center_y, True)
                if path1.contains(scaled_pos):
                    self.dragging_shape = 'shape1'
                    self.drag_start_pos = scaled_pos
                    self.shape1_drag_start = QPoint(self.shape1_params.get('x_offset', 0), 
                                                    self.shape1_params.get('y_offset', 0))
                    self.setCursor(Qt.ClosedHandCursor)
                    self.update()
                    return
            
            if self.show_shape2 and self.shape2_type:
                path2 = self.get_shape_path(self.shape2_type, self.shape2_params, center_x, center_y, False)
                if path2.contains(scaled_pos):
                    self.dragging_shape = 'shape2'
                    self.drag_start_pos = scaled_pos
                    self.shape2_drag_start = QPoint(self.shape2_params.get('x_offset', 0),
                                                    self.shape2_params.get('y_offset', 0))
                    self.setCursor(Qt.ClosedHandCursor)
                    self.update()
                    return
    
    def mouseMoveEvent(self, event):
        if self.dragging_shape and self.drag_start_pos:
            pos = event.pos()
            scaled_x = int(pos.x() / self.zoom_level)
            scaled_y = int(pos.y() / self.zoom_level)
            scaled_pos = QPointF(scaled_x, scaled_y)
            
            delta_x = int(scaled_pos.x() - self.drag_start_pos.x())
            delta_y = int(scaled_pos.y() - self.drag_start_pos.y())
            
            if self.dragging_shape == 'shape1' and self.shape1_drag_start:
                new_x = self.shape1_drag_start.x() + delta_x
                new_y = self.shape1_drag_start.y() + delta_y
                self.shape1_params['x_offset'] = new_x
                self.shape1_params['y_offset'] = new_y
                self.update()
                
                if hasattr(self.parent(), 'update_controls'):
                    self.parent().update_controls()
            elif self.dragging_shape == 'shape2' and self.shape2_drag_start:
                new_x = self.shape2_drag_start.x() + delta_x
                new_y = self.shape2_drag_start.y() + delta_y
                self.shape2_params['x_offset'] = new_x
                self.shape2_params['y_offset'] = new_y
                self.update()
                
                if hasattr(self.parent(), 'update_controls'):
                    self.parent().update_controls()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging_shape = None
            self.drag_start_pos = None
            self.shape1_drag_start = None
            self.shape2_drag_start = None
            self.setCursor(Qt.ArrowCursor)
            self.update()
    
    def get_shape_path(self, shape_type, params, center_x, center_y, is_shape1=True):
        """Возвращает QPainterPath для фигуры (для определения клика) с учётом вращения"""
        path = QPainterPath()
        x = params.get('x_offset', 0)
        y = params.get('y_offset', 0)
        size = params.get('size', 120)
        radius = size // 2
        rotation = params.get('rotation', 0)
        
        shape_center_x = center_x + x
        shape_center_y = center_y + y
        
        if shape_type == "Круг":
            path.addEllipse(center_x - radius + x, center_y - radius + y, radius * 2, radius * 2)
        elif shape_type == "Квадрат":
            path.addRect(center_x - size//2 + x, center_y - size//2 + y, size, size)
        elif shape_type == "Треугольник":
            points = [
                QPointF(center_x + x, center_y - size//2 + y),
                QPointF(center_x - size//2 + x, center_y + size//2 + y),
                QPointF(center_x + size//2 + x, center_y + size//2 + y)
            ]
            path.addPolygon(QPolygonF(points))
        elif shape_type == "Куб":
            # Для куба используем переднюю грань для определения клика
            path.addRect(center_x - size//2 + x, center_y - size//2 + y, size, size)
        elif shape_type == "Шар":
            path.addEllipse(center_x - radius + x, center_y - radius + y, radius * 2, radius * 2)
        
        # Применяем вращение к пути
        if rotation != 0:
            transform = QTransform()
            transform.translate(shape_center_x, shape_center_y)
            transform.rotate(rotation)
            transform.translate(-shape_center_x, -shape_center_y)
            path = transform.map(path)
        
        return path
    
    def set_shape1(self, shape_type, params):
        self.shape1_type = shape_type
        self.shape1_params.update(params)
        self.update()
    
    def set_shape2(self, shape_type, params):
        self.shape2_type = shape_type
        self.shape2_params.update(params)
        self.update()
    
    def set_shape1_color(self, color):
        self.shape1_color = color
        self.update()
    
    def set_shape2_color(self, color):
        self.shape2_color = color
        self.update()
    
    def export_to_image(self, filename):
        """Экспортирует текущее состояние в изображение"""
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        pixmap.save(filename)


class InteractiveGeometryCalculator(QWidget):
    """Интерактивный калькулятор геометрических формул (с форматированием ответа)"""
    def __init__(self):
        super().__init__()
        self.params_inputs = {}
        self.current_shape = "Окружность"
        self.current_params = {}
        self.correct_answer = None
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Заголовок
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: transparent;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(5)
        
        title = QLabel("Калькулятор геометрических формул")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font: bold 18pt 'Segoe UI'; color: #2196F3; padding: 5px;")
        header_layout.addWidget(title)
        
        subtitle = QLabel("Выберите фигуру, введите параметры и решите задачу самостоятельно")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font: 9pt 'Segoe UI'; color: #757575; padding-bottom: 5px;")
        header_layout.addWidget(subtitle)
        
        main_layout.addWidget(header_widget)
        
        # Основное содержимое
        calculator_widget = QWidget()
        calculator_layout = QHBoxLayout(calculator_widget)
        calculator_layout.setSpacing(15)
        
        # Левая панель
        left_panel = QWidget()
        left_panel.setStyleSheet("background-color: #F5F5F5; border-radius: 10px;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(15, 15, 15, 15)
        
        # Выбор фигуры
        shape_group = QFrame()
        shape_group.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #E0E0E0;")
        shape_group_layout = QVBoxLayout(shape_group)
        shape_group_layout.setSpacing(10)
        shape_group_layout.setContentsMargins(15, 15, 15, 15)
        
        shape_label = QLabel("Тип фигуры")
        shape_label.setStyleSheet("font: bold 11pt 'Segoe UI'; color: #1976D2;")
        shape_group_layout.addWidget(shape_label)
        
        self.shape_combo = QComboBox()
        # Все фигуры без разделителей
        self.shape_combo.addItem("Окружность")
        self.shape_combo.addItem("Треугольник")
        self.shape_combo.addItem("Квадрат")
        self.shape_combo.addItem("Куб")
        self.shape_combo.addItem("Шар")
        self.shape_combo.addItem("Конус")
        
        self.shape_combo.setStyleSheet("""
            QComboBox {
                font: 10pt 'Segoe UI';
                padding: 8px;
                border: 1px solid #BDBDBD;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        self.shape_combo.currentTextChanged.connect(self.on_shape_changed)
        shape_group_layout.addWidget(self.shape_combo)
        left_layout.addWidget(shape_group)
        
        # Параметры
        params_group = QFrame()
        params_group.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #E0E0E0;")
        params_group_layout = QVBoxLayout(params_group)
        params_group_layout.setSpacing(10)
        params_group_layout.setContentsMargins(15, 15, 15, 15)
        
        params_label = QLabel("Параметры фигуры")
        params_label.setStyleSheet("font: bold 11pt 'Segoe UI'; color: #1976D2;")
        params_group_layout.addWidget(params_label)
        
        self.params_widget = QWidget()
        self.params_layout = QVBoxLayout(self.params_widget)
        self.params_layout.setSpacing(10)
        self.params_layout.setAlignment(Qt.AlignTop)
        
        params_group_layout.addWidget(self.params_widget)
        left_layout.addWidget(params_group)
        
        # Кнопка генерации
        self.generate_btn = QPushButton("Сгенерировать задачу")
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                font: bold 11pt 'Segoe UI';
                padding: 12px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.generate_btn.clicked.connect(self.generate_task)
        left_layout.addWidget(self.generate_btn)
        left_layout.addStretch()
        
        # Правая панель
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(15)
        
        # Задача
        task_group = QFrame()
        task_group.setStyleSheet("background-color: #E3F2FD; border-radius: 10px; border: 1px solid #BBDEFB;")
        task_group_layout = QVBoxLayout(task_group)
        task_group_layout.setSpacing(10)
        task_group_layout.setContentsMargins(20, 20, 20, 20)
        
        task_label = QLabel("Задание")
        task_label.setStyleSheet("font: bold 13pt 'Segoe UI'; color: #1565C0;")
        task_group_layout.addWidget(task_label)
        
        self.question_label = QLabel("Нажмите 'Сгенерировать задачу' для начала")
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("font: 12pt 'Segoe UI'; color: #333; padding: 10px; background-color: white; border-radius: 6px;")
        task_group_layout.addWidget(self.question_label)
        right_layout.addWidget(task_group)
        
        # Ответ
        answer_group = QFrame()
        answer_group.setStyleSheet("background-color: #E8EAF6; border-radius: 10px; border: 1px solid #C5CAE9;")
        answer_group_layout = QVBoxLayout(answer_group)
        answer_group_layout.setSpacing(10)
        answer_group_layout.setContentsMargins(20, 20, 20, 20)
        
        answer_label = QLabel("Ваше решение")
        answer_label.setStyleSheet("font: bold 13pt 'Segoe UI'; color: #3F51B5;")
        answer_group_layout.addWidget(answer_label)
        
        answer_input_widget = QWidget()
        answer_input_layout = QHBoxLayout(answer_input_widget)
        answer_input_layout.setSpacing(10)
        
        self.user_answer = QLineEdit()
        self.user_answer.setPlaceholderText("Введите число (формат: 0.00)...")
        self.user_answer.setStyleSheet("""
            QLineEdit {
                font: 12pt 'Segoe UI';
                padding: 12px;
                border: 2px solid #9FA8DA;
                border-radius: 6px;
            }
        """)
        # Подключаем обработчик форматирования при потере фокуса
        self.user_answer.editingFinished.connect(self.format_answer_input)
        answer_input_layout.addWidget(self.user_answer)
        
        self.check_btn = QPushButton("Проверить")
        self.check_btn.setCursor(Qt.PointingHandCursor)
        self.check_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 6px;
                font: bold 11pt 'Segoe UI';
                padding: 12px 25px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.check_btn.clicked.connect(self.check_answer)
        answer_input_layout.addWidget(self.check_btn)
        answer_group_layout.addWidget(answer_input_widget)
        right_layout.addWidget(answer_group)
        
        # Результат
        result_group = QFrame()
        result_group.setStyleSheet("background-color: #F5F5F5; border-radius: 10px; border: 1px solid #E0E0E0;")
        result_group_layout = QVBoxLayout(result_group)
        result_group_layout.setSpacing(10)
        result_group_layout.setContentsMargins(20, 20, 20, 20)
        
        result_label = QLabel("Результат проверки")
        result_label.setStyleSheet("font: bold 13pt 'Segoe UI'; color: #616161;")
        result_group_layout.addWidget(result_label)
        
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("font: 11pt 'Segoe UI'; padding: 12px; background-color: white; border-radius: 6px;")
        result_group_layout.addWidget(self.result_label)
        right_layout.addWidget(result_group)
        right_layout.addStretch()
        
        calculator_layout.addWidget(left_panel, 3)
        calculator_layout.addWidget(right_panel, 7)
        main_layout.addWidget(calculator_widget)
        
        self.on_shape_changed("Окружность")
    
    def format_answer_input(self):
        """Форматирует ввод пользователя: всегда два знака после точки (вызывается при потере фокуса)"""
        text = self.user_answer.text().strip()
        
        if not text:
            return
        
        # Заменяем запятую на точку
        text = text.replace(',', '.')
        
        # Проверяем, можно ли преобразовать в число
        try:
            value = float(text)
            # Форматируем с двумя знаками после точки
            formatted = f"{value:.2f}"
            
            # Обновляем текст
            if text != formatted:
                self.user_answer.setText(formatted)
        except ValueError:
            # Если не число, очищаем поле
            if text:
                self.user_answer.clear()
    
    def on_shape_changed(self, shape_name):
        """Обработчик изменения выбранной фигуры"""
        self.current_shape = shape_name
        self.correct_answer = None
        self.result_label.setText("")
        self.user_answer.clear()
        self.question_label.setText("Нажмите 'Сгенерировать задачу' для начала")
        
        # Очищаем старые параметры
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.params_inputs = {}
        
        # Добавляем параметры для выбранной фигуры
        if shape_name == "Окружность":
            self.add_param_input("Радиус (R)", "см", 5)
        elif shape_name == "Треугольник":
            self.add_param_input("Сторона a", "см", 3)
            self.add_param_input("Сторона b", "см", 4)
            self.add_param_input("Сторона c", "см", 5)
        elif shape_name == "Квадрат":
            self.add_param_input("Сторона a", "см", 5)
        elif shape_name == "Куб":
            self.add_param_input("Ребро a", "см", 5)
        elif shape_name == "Шар":
            self.add_param_input("Радиус R", "см", 5)
        elif shape_name == "Конус":
            self.add_param_input("Радиус основания R", "см", 3)
            self.add_param_input("Высота h", "см", 7)
    
    def add_param_input(self, label_text, unit, default_value):
        """Добавляет поле ввода параметра"""
        frame = QFrame()
        frame.setStyleSheet("background-color: #FAFAFA; border-radius: 6px;")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        
        label = QLabel(label_text)
        label.setMinimumWidth(130)
        label.setStyleSheet("font: 10pt 'Segoe UI'; color: #424242;")
        layout.addWidget(label)
        
        spinbox = QDoubleSpinBox()
        spinbox.setRange(0.1, 1000)
        spinbox.setValue(default_value)
        spinbox.setSingleStep(0.5)
        spinbox.setDecimals(2)
        spinbox.setStyleSheet("""
            QDoubleSpinBox {
                font: 10pt 'Segoe UI';
                padding: 5px;
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                min-width: 80px;
            }
        """)
        layout.addWidget(spinbox)
        
        unit_label = QLabel(unit)
        unit_label.setFixedWidth(35)
        unit_label.setStyleSheet("font: 10pt 'Segoe UI'; color: #757575;")
        layout.addWidget(unit_label)
        
        self.params_layout.addWidget(frame)
        key = label_text.replace(" ", "_").replace("(", "").replace(")", "")
        self.params_inputs[key] = spinbox
    
    def generate_task(self):
        """Генерирует задачу на основе выбранной фигуры и введённых параметров"""
        try:
            self.current_params = {}
            for key, spinbox in self.params_inputs.items():
                self.current_params[key] = spinbox.value()
            
            if self.current_shape == "Окружность":
                r = self.current_params.get("Радиус_R", 5)
                self.correct_answer = math.pi * r ** 2
                self.question_label.setText(f"Найдите площадь круга с радиусом R = {r:.2f} см")
            elif self.current_shape == "Треугольник":
                a = self.current_params.get("Сторона_a", 3)
                b = self.current_params.get("Сторона_b", 4)
                c = self.current_params.get("Сторона_c", 5)
                p = (a + b + c) / 2
                self.correct_answer = math.sqrt(p * (p - a) * (p - b) * (p - c))
                self.question_label.setText(f"Найдите площадь треугольника со сторонами a={a:.2f}, b={b:.2f}, c={c:.2f} см")
            elif self.current_shape == "Квадрат":
                a = self.current_params.get("Сторона_a", 5)
                self.correct_answer = a ** 2
                self.question_label.setText(f"Найдите площадь квадрата со стороной a = {a:.2f} см")
            elif self.current_shape == "Куб":
                a = self.current_params.get("Ребро_a", 5)
                self.correct_answer = a ** 3
                self.question_label.setText(f"Найдите объём куба с ребром {a:.2f} см³")
            elif self.current_shape == "Шар":
                r = self.current_params.get("Радиус_R", 5)
                self.correct_answer = 4/3 * math.pi * r ** 3
                self.question_label.setText(f"Найдите объём шара с радиусом R = {r:.2f} см³")
            elif self.current_shape == "Конус":
                r = self.current_params.get("Радиус_основания_R", 3)
                h = self.current_params.get("Высота_h", 7)
                self.correct_answer = 1/3 * math.pi * r ** 2 * h
                self.question_label.setText(f"Найдите объём конуса (R={r:.2f} см, h={h:.2f} см)")
            
            self.result_label.setText("")
            self.user_answer.clear()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка: {str(e)}")
    
    def check_answer(self):
        """Проверяет введённый пользователем ответ"""
        if self.correct_answer is None:
            QMessageBox.warning(self, "Внимание", "Сначала сгенерируйте задачу!")
            return
        try:
            # Получаем текст ответа и заменяем запятую на точку
            user_text = self.user_answer.text().strip().replace(',', '.')
            user_value = float(user_text)
            # Округляем до двух знаков для сравнения
            user_value_rounded = round(user_value, 2)
            correct_rounded = round(self.correct_answer, 2)
            
            if abs(user_value_rounded - correct_rounded) < 0.01:
                self.result_label.setStyleSheet("font: 11pt 'Segoe UI'; padding: 12px; background-color: #C8E6C9; border-radius: 6px; color: #2E7D32;")
                self.result_label.setText(f"ПРАВИЛЬНО!\nОтвет: {correct_rounded:.2f}")
            else:
                self.result_label.setStyleSheet("font: 11pt 'Segoe UI'; padding: 12px; background-color: #FFCDD2; border-radius: 6px; color: #C62828;")
                self.result_label.setText(f"НЕПРАВИЛЬНО\nВаш ответ: {user_value_rounded:.2f}\nПравильный: {correct_rounded:.2f}")
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите число в правильном формате (например, 13.42)")


class EnhancedOverlayInterface(QWidget):
    """Улучшенный интерфейс наложения фигур"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Наложение геометрических фигур")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font: bold 20pt 'Segoe UI'; color: #2196F3; margin: 10px;")
        layout.addWidget(title)
        
        subtitle = QLabel("Совмещайте фигуры, изменяйте их параметры и сохраняйте результаты")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font: 9pt 'Segoe UI'; color: #757575; margin-bottom: 15px;")
        layout.addWidget(subtitle)
        
        content_frame = QFrame()
        content_layout = QHBoxLayout(content_frame)
        
        # Левая панель управления
        left_panel = self.create_control_panel()
        content_layout.addWidget(left_panel)
        
        # Правая панель с виджетом отображения
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: white; border-radius: 10px;")
        right_layout = QVBoxLayout(right_panel)
        
        self.overlay_widget = ShapeOverlayWidget()
        right_layout.addWidget(self.overlay_widget)
        
        # Нижняя панель инструментов
        toolbar_frame = QFrame()
        toolbar_frame.setFixedHeight(50)
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setSpacing(10)
        
        export_btn = RectangularButton("Сохранить как PNG", self.export_image, 150, 35)
        toolbar_layout.addWidget(export_btn)
        
        save_btn = RectangularButton("Сохранить композицию", self.save_composition, 150, 35)
        toolbar_layout.addWidget(save_btn)
        
        load_btn = RectangularButton("Загрузить композицию", self.load_composition, 150, 35)
        toolbar_layout.addWidget(load_btn)
        
        toolbar_layout.addStretch()
        right_layout.addWidget(toolbar_frame)
        
        content_layout.addWidget(right_panel, 2)
        layout.addWidget(content_frame)
        
        self.update_overlay()
    
    def create_control_panel(self):
        panel = QFrame()
        panel.setStyleSheet("background-color: #FAFAFA; border-radius: 10px;")
        panel.setFixedWidth(380)
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(15)
        
        self.figures_tab = QTabWidget()
        self.figures_tab.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E0E0E0; background: white; border-radius: 5px; }
            QTabBar::tab { padding: 8px 20px; font: 9pt 'Segoe UI'; }
        """)
        
        tab1 = self.create_shape_tab(1)
        self.figures_tab.addTab(tab1, "Фигура 1")
        
        tab2 = self.create_shape_tab(2)
        self.figures_tab.addTab(tab2, "Фигура 2")
        
        tab3 = self.create_settings_tab()
        self.figures_tab.addTab(tab3, "Настройки")
        
        layout.addWidget(self.figures_tab)
        
        return panel
    
    def create_shape_tab(self, shape_num):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        show_cb = QCheckBox("Показать фигуру")
        show_cb.setChecked(True)
        show_cb.setStyleSheet("font: 10pt 'Segoe UI';")
        layout.addWidget(show_cb)
        
        layout.addWidget(QLabel("Тип фигуры:"))
        shape_combo = QComboBox()
        shapes_list = ["Круг", "Треугольник", "Квадрат", "Куб", "Шар"]
        for s in shapes_list:
            shape_combo.addItem(s)
        
        shape_combo.setStyleSheet("font: 10pt 'Segoe UI'; padding: 5px;")
        layout.addWidget(shape_combo)
        
        layout.addWidget(QLabel("Размер:"))
        size_slider = QSlider(Qt.Horizontal)
        size_slider.setRange(30, 250)
        size_slider.setValue(120)
        size_slider.setTickPosition(QSlider.TicksBelow)
        size_slider.setTickInterval(20)
        layout.addWidget(size_slider)
        
        size_label = QLabel("120 px")
        size_label.setAlignment(Qt.AlignCenter)
        size_label.setStyleSheet("font: 10pt 'Segoe UI'; color: #2196F3;")
        layout.addWidget(size_label)
        
        layout.addWidget(QLabel("Позиция X:"))
        x_slider = QSlider(Qt.Horizontal)
        x_slider.setRange(-250, 250)
        x_slider.setValue(-50 if shape_num == 1 else 50)
        x_slider.setTickPosition(QSlider.TicksBelow)
        x_slider.setTickInterval(25)
        layout.addWidget(x_slider)
        
        x_value = QLineEdit(str(-50 if shape_num == 1 else 50))
        x_value.setFixedWidth(60)
        x_value.setAlignment(Qt.AlignCenter)
        x_value.setStyleSheet("font: 10pt 'Segoe UI';")
        layout.addWidget(x_value, alignment=Qt.AlignCenter)
        
        layout.addWidget(QLabel("Позиция Y:"))
        y_slider = QSlider(Qt.Horizontal)
        y_slider.setRange(-250, 250)
        y_slider.setValue(0)
        y_slider.setTickPosition(QSlider.TicksBelow)
        y_slider.setTickInterval(25)
        layout.addWidget(y_slider)
        
        y_value = QLineEdit("0")
        y_value.setFixedWidth(60)
        y_value.setAlignment(Qt.AlignCenter)
        y_value.setStyleSheet("font: 10pt 'Segoe UI';")
        layout.addWidget(y_value, alignment=Qt.AlignCenter)
        
        layout.addWidget(QLabel("Вращение:"))
        rot_slider = QSlider(Qt.Horizontal)
        rot_slider.setRange(-180, 180)
        rot_slider.setValue(0)
        rot_slider.setTickPosition(QSlider.TicksBelow)
        rot_slider.setTickInterval(30)
        rot_slider.valueChanged.connect(lambda v: self.update_rotation(rot_value, v))
        layout.addWidget(rot_slider)
        
        rot_value = QLineEdit("0°")
        rot_value.setFixedWidth(60)
        rot_value.setAlignment(Qt.AlignCenter)
        rot_value.setStyleSheet("font: 10pt 'Segoe UI';")
        rot_value.textChanged.connect(lambda t: self.sync_rotation_slider(rot_slider, t))
        layout.addWidget(rot_value, alignment=Qt.AlignCenter)
        
        layout.addWidget(QLabel("Прозрачность:"))
        opacity_slider = QSlider(Qt.Horizontal)
        opacity_slider.setRange(50, 255)
        opacity_slider.setValue(200)
        opacity_slider.setTickPosition(QSlider.TicksBelow)
        opacity_slider.setTickInterval(25)
        layout.addWidget(opacity_slider)
        
        opacity_label = QLabel("200")
        opacity_label.setAlignment(Qt.AlignCenter)
        opacity_label.setStyleSheet("font: 10pt 'Segoe UI'; color: #2196F3;")
        layout.addWidget(opacity_label)
        
        layout.addWidget(QLabel("Цвет:"))
        color_btn = QPushButton("Выбрать цвет")
        color_btn.setCursor(Qt.PointingHandCursor)
        color_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font: 9pt 'Segoe UI';
            }
        """)
        layout.addWidget(color_btn)
        
        layout.addStretch()
        
        if shape_num == 1:
            self.shape1_show = show_cb
            self.shape1_combo = shape_combo
            self.shape1_size_slider = size_slider
            self.shape1_size_label = size_label
            self.shape1_x_slider = x_slider
            self.shape1_x_value = x_value
            self.shape1_y_slider = y_slider
            self.shape1_y_value = y_value
            self.shape1_rot_slider = rot_slider
            self.shape1_rot_value = rot_value
            self.shape1_opacity_slider = opacity_slider
            self.shape1_opacity_label = opacity_label
            self.shape1_color_btn = color_btn
            
            show_cb.stateChanged.connect(lambda state: self.toggle_shape(1, state))
            shape_combo.currentTextChanged.connect(self.on_shape_combo_changed)
            size_slider.valueChanged.connect(lambda v: self.update_size(1, v, size_label))
            x_slider.valueChanged.connect(lambda v: self.update_coordinate(x_value, v))
            y_slider.valueChanged.connect(lambda v: self.update_coordinate(y_value, v))
            rot_slider.valueChanged.connect(lambda v: self.update_rotation(rot_value, v))
            opacity_slider.valueChanged.connect(lambda v: self.update_opacity_label(opacity_label, v))
            color_btn.clicked.connect(lambda: self.choose_color(1))
            
            x_value.textChanged.connect(lambda t: self.sync_slider(x_slider, t))
            y_value.textChanged.connect(lambda t: self.sync_slider(y_slider, t))
        else:
            self.shape2_show = show_cb
            self.shape2_combo = shape_combo
            self.shape2_size_slider = size_slider
            self.shape2_size_label = size_label
            self.shape2_x_slider = x_slider
            self.shape2_x_value = x_value
            self.shape2_y_slider = y_slider
            self.shape2_y_value = y_value
            self.shape2_rot_slider = rot_slider
            self.shape2_rot_value = rot_value
            self.shape2_opacity_slider = opacity_slider
            self.shape2_opacity_label = opacity_label
            self.shape2_color_btn = color_btn
            
            show_cb.stateChanged.connect(lambda state: self.toggle_shape(2, state))
            shape_combo.currentTextChanged.connect(self.on_shape_combo_changed)
            size_slider.valueChanged.connect(lambda v: self.update_size(2, v, size_label))
            x_slider.valueChanged.connect(lambda v: self.update_coordinate(x_value, v))
            y_slider.valueChanged.connect(lambda v: self.update_coordinate(y_value, v))
            rot_slider.valueChanged.connect(lambda v: self.update_rotation(rot_value, v))
            opacity_slider.valueChanged.connect(lambda v: self.update_opacity_label(opacity_label, v))
            color_btn.clicked.connect(lambda: self.choose_color(2))
            
            x_value.textChanged.connect(lambda t: self.sync_slider(x_slider, t))
            y_value.textChanged.connect(lambda t: self.sync_slider(y_slider, t))
        
        return tab
    
    def on_shape_combo_changed(self, text):
        self.update_overlay()
    
    def create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        layout.addWidget(QLabel("Масштаб:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(50, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setTickPosition(QSlider.TicksBelow)
        self.zoom_slider.setTickInterval(25)
        self.zoom_slider.valueChanged.connect(self.change_zoom)
        layout.addWidget(self.zoom_slider)
        
        zoom_label = QLabel("100%")
        zoom_label.setAlignment(Qt.AlignCenter)
        zoom_label.setStyleSheet("font: 10pt 'Segoe UI'; color: #2196F3;")
        layout.addWidget(zoom_label)
        self.zoom_slider.valueChanged.connect(lambda v: zoom_label.setText(f"{v}%"))
        
        layout.addSpacing(20)
        
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setSpacing(10)
        
        reset_btn = RectangularButton("Сбросить все", self.reset_all, 150, 40)
        btn_layout.addWidget(reset_btn)
        
        center_btn = RectangularButton("Центрировать", self.center_all, 150, 40)
        btn_layout.addWidget(center_btn)
        
        layout.addWidget(btn_frame)
        layout.addStretch()
        
        return tab
    
    def toggle_shape(self, shape_num, state):
        visible = state == Qt.Checked
        if shape_num == 1:
            self.overlay_widget.set_visibility(visible, self.shape2_show.isChecked())
        else:
            self.overlay_widget.set_visibility(self.shape1_show.isChecked(), visible)
    
    def update_size(self, shape_num, value, label):
        label.setText(f"{value} px")
        self.update_overlay()
    
    def update_coordinate(self, value_widget, value):
        value_widget.setText(str(value))
        self.update_overlay()
    
    def update_rotation(self, value_widget, value):
        value_widget.setText(f"{value}°")
        self.update_overlay()
    
    def update_opacity_label(self, label, value):
        label.setText(str(value))
        self.update_overlay()
    
    def sync_slider(self, slider, text):
        try:
            slider.setValue(int(text))
        except:
            pass
    
    def sync_rotation_slider(self, slider, text):
        try:
            val = int(text.replace("°", ""))
            slider.setValue(val)
        except:
            pass
    
    def choose_color(self, shape_num):
        color = QColorDialog.getColor()
        if color.isValid():
            if shape_num == 1:
                self.overlay_widget.set_shape1_color(color)
                self.shape1_color_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color.name()};
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 8px;
                        font: 9pt 'Segoe UI';
                    }}
                """)
            else:
                self.overlay_widget.set_shape2_color(color)
                self.shape2_color_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color.name()};
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 8px;
                        font: 9pt 'Segoe UI';
                    }}
                """)
    
    def change_zoom(self, value):
        self.overlay_widget.set_zoom(value / 100.0)
    
    def update_overlay(self):
        try:
            shape1_type = self.shape1_combo.currentText()
            size1 = self.shape1_size_slider.value()
            x1 = self.shape1_x_slider.value()
            y1 = self.shape1_y_slider.value()
            rot1 = self.shape1_rot_slider.value()
            opacity1 = self.shape1_opacity_slider.value()
            
            shape2_type = self.shape2_combo.currentText()
            size2 = self.shape2_size_slider.value()
            x2 = self.shape2_x_slider.value()
            y2 = self.shape2_y_slider.value()
            rot2 = self.shape2_rot_slider.value()
            opacity2 = self.shape2_opacity_slider.value()
            
            self.overlay_widget.set_shape1(shape1_type, {
                'size': size1, 'x_offset': x1, 'y_offset': y1, 
                'rotation': rot1, 'opacity': opacity1
            })
            
            self.overlay_widget.set_shape2(shape2_type, {
                'size': size2, 'x_offset': x2, 'y_offset': y2,
                'rotation': rot2, 'opacity': opacity2
            })
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка: {str(e)}")
    
    def reset_all(self):
        self.shape1_combo.setCurrentText("Квадрат")
        self.shape1_size_slider.setValue(120)
        self.shape1_x_slider.setValue(-50)
        self.shape1_y_slider.setValue(0)
        self.shape1_rot_slider.setValue(0)
        self.shape1_opacity_slider.setValue(200)
        
        self.shape2_combo.setCurrentText("Круг")
        self.shape2_size_slider.setValue(120)
        self.shape2_x_slider.setValue(50)
        self.shape2_y_slider.setValue(0)
        self.shape2_rot_slider.setValue(0)
        self.shape2_opacity_slider.setValue(200)
        
        self.zoom_slider.setValue(100)
    
    def center_all(self):
        self.shape1_x_slider.setValue(0)
        self.shape1_y_slider.setValue(0)
        self.shape2_x_slider.setValue(0)
        self.shape2_y_slider.setValue(0)
    
    def export_image(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить изображение", 
            f"overlay_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "PNG Image (*.png)"
        )
        if filename:
            self.overlay_widget.export_to_image(filename)
            QMessageBox.information(self, "Успех", f"Изображение сохранено:\n{filename}")
    
    def save_composition(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить композицию",
            f"composition_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        if filename:
            try:
                composition = {
                    'shape1': {
                        'type': self.shape1_combo.currentText(),
                        'size': self.shape1_size_slider.value(),
                        'x': self.shape1_x_slider.value(),
                        'y': self.shape1_y_slider.value(),
                        'rotation': self.shape1_rot_slider.value(),
                        'opacity': self.shape1_opacity_slider.value(),
                        'visible': self.shape1_show.isChecked()
                    },
                    'shape2': {
                        'type': self.shape2_combo.currentText(),
                        'size': self.shape2_size_slider.value(),
                        'x': self.shape2_x_slider.value(),
                        'y': self.shape2_y_slider.value(),
                        'rotation': self.shape2_rot_slider.value(),
                        'opacity': self.shape2_opacity_slider.value(),
                        'visible': self.shape2_show.isChecked()
                    },
                    'zoom': self.zoom_slider.value()
                }
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(composition, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "Успех", f"Композиция сохранена:\n{filename}")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка сохранения: {str(e)}")
    
    def load_composition(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Загрузить композицию", "",
            "JSON Files (*.json)"
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    comp = json.load(f)
                
                self.shape1_combo.setCurrentText(comp['shape1']['type'])
                self.shape1_size_slider.setValue(comp['shape1']['size'])
                self.shape1_x_slider.setValue(comp['shape1']['x'])
                self.shape1_y_slider.setValue(comp['shape1']['y'])
                self.shape1_rot_slider.setValue(comp['shape1']['rotation'])
                self.shape1_opacity_slider.setValue(comp['shape1']['opacity'])
                self.shape1_show.setChecked(comp['shape1']['visible'])
                
                self.shape2_combo.setCurrentText(comp['shape2']['type'])
                self.shape2_size_slider.setValue(comp['shape2']['size'])
                self.shape2_x_slider.setValue(comp['shape2']['x'])
                self.shape2_y_slider.setValue(comp['shape2']['y'])
                self.shape2_rot_slider.setValue(comp['shape2']['rotation'])
                self.shape2_opacity_slider.setValue(comp['shape2']['opacity'])
                self.shape2_show.setChecked(comp['shape2']['visible'])
                
                self.zoom_slider.setValue(comp['zoom'])
                
                QMessageBox.information(self, "Успех", "Композиция загружена")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка загрузки: {str(e)}")
    
    def update_controls(self):
        if hasattr(self.overlay_widget, 'dragging_shape'):
            if self.overlay_widget.dragging_shape == 'shape1':
                x = self.overlay_widget.shape1_params.get('x_offset', 0)
                y = self.overlay_widget.shape1_params.get('y_offset', 0)
                self.shape1_x_slider.setValue(int(x))
                self.shape1_y_slider.setValue(int(y))
                self.shape1_x_value.setText(str(int(x)))
                self.shape1_y_value.setText(str(int(y)))
            elif self.overlay_widget.dragging_shape == 'shape2':
                x = self.overlay_widget.shape2_params.get('x_offset', 0)
                y = self.overlay_widget.shape2_params.get('y_offset', 0)
                self.shape2_x_slider.setValue(int(x))
                self.shape2_y_slider.setValue(int(y))
                self.shape2_x_value.setText(str(int(x)))
                self.shape2_y_value.setText(str(int(y)))


class GeometryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Модуль для работы с геометрическими фигурами")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 700)
        
        self.setStyleSheet("QMainWindow { border: none; }")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Верхняя панель
        self.toolbar = QWidget()
        self.toolbar.setFixedHeight(60)
        self.toolbar.setStyleSheet("background-color: #FAFAFA; border: none;")
        
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(15, 10, 15, 5)
        
        self.back_btn = RectangularButton("Назад", self.go_back, 100, 38)
        self.back_btn.setEnabled(False)
        toolbar_layout.addWidget(self.back_btn)
        
        toolbar_layout.addStretch()
        
        exit_btn = RectangularButton("Выход", self.close, 100, 38)
        toolbar_layout.addWidget(exit_btn)
        
        main_layout.addWidget(self.toolbar)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #E0E0E0; max-height: 1px;")
        main_layout.addWidget(separator)
        
        # Вкладки
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: none; background: white; }
            QTabBar::tab { 
                padding: 15px 30px; 
                font: 9pt 'Segoe UI'; 
                background-color: #E0E0E0; 
                color: #424242;
                min-width: 180px;
            }
            QTabBar::tab:selected { 
                background-color: #2196F3; 
                color: white; 
            }
        """)
        
        # Страница 1: Библиотека фигур
        self.main_page = ScrollableWidget()
        self.tab_widget.addTab(self.main_page, "БИБЛИОТЕКА ФИГУР")
        
        # Страница 2: Наложение фигур
        self.overlay_interface = EnhancedOverlayInterface(self)
        scroll_overlay = ScrollableWidget()
        scroll_overlay.content_layout.addWidget(self.overlay_interface)
        self.tab_widget.addTab(scroll_overlay, "НАЛОЖЕНИЕ ФИГУР")
        
        # Страница 3: Калькулятор формул
        self.calculator_page = InteractiveGeometryCalculator()
        self.tab_widget.addTab(self.calculator_page, "КАЛЬКУЛЯТОР ФОРМ")
        
        main_layout.addWidget(self.tab_widget)
        
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        self.navigation_history = []
        self.show_figure_selection()
    
    def on_tab_changed(self, index):
        self.navigation_history = []
        self.back_btn.setEnabled(False)
    
    def go_back(self):
        if self.navigation_history:
            previous_state = self.navigation_history.pop()
            if previous_state['type'] == 'figure_selection':
                self.show_figure_selection()
            elif previous_state['type'] == 'file_selection':
                self.show_file_selection(previous_state['figure_name'])
        self.back_btn.setEnabled(len(self.navigation_history) > 0)
    
    def show_figure_selection(self):
        self.main_page.clear()
        main_layout = self.main_page.content_layout
        
        title = QLabel("Выберите геометрическую фигуру")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font: bold 24pt 'Segoe UI'; color: #424242; margin: 20px;")
        main_layout.addWidget(title)
        
        central_container = QWidget()
        central_container.setStyleSheet("background-color: transparent;")
        central_layout = QVBoxLayout(central_container)
        central_layout.setAlignment(Qt.AlignCenter)
        central_layout.setSpacing(30)
        
        figures_2d = ["Треугольник", "Квадрат", "Окружность"]
        figures_3d = ["Куб", "Шар", "Конус"]
        
        # 2D фигуры
        section_2d = QFrame()
        section_2d.setStyleSheet("background-color: #E8F5E9; border-radius: 15px; border: 2px solid #4CAF50;")
        section_2d.setFixedWidth(400)
        section_2d.setMinimumHeight(300)
        section_layout = QVBoxLayout(section_2d)
        section_layout.setSpacing(15)
        section_layout.setContentsMargins(20, 20, 20, 20)
        
        title_2d = QLabel("Плоские фигуры (2D)")
        title_2d.setAlignment(Qt.AlignCenter)
        title_2d.setStyleSheet("font: bold 16pt 'Segoe UI'; color: #2E7D32; background-color: #C8E6C9; padding: 8px; border-radius: 10px;")
        section_layout.addWidget(title_2d)
        
        for figure_name in figures_2d:
            btn = RectangularButton(figure_name, 
                                   partial(self.show_file_selection, figure_name),
                                   280, 45)
            section_layout.addWidget(btn, alignment=Qt.AlignCenter)
        
        central_layout.addWidget(section_2d, alignment=Qt.AlignCenter)
        
        # 3D фигуры
        section_3d = QFrame()
        section_3d.setStyleSheet("background-color: #E3F2FD; border-radius: 15px; border: 2px solid #2196F3;")
        section_3d.setFixedWidth(400)
        section_3d.setMinimumHeight(300)
        section_layout_3d = QVBoxLayout(section_3d)
        section_layout_3d.setSpacing(15)
        section_layout_3d.setContentsMargins(20, 20, 20, 20)
        
        title_3d = QLabel("Объёмные фигуры (3D)")
        title_3d.setAlignment(Qt.AlignCenter)
        title_3d.setStyleSheet("font: bold 16pt 'Segoe UI'; color: #1565C0; background-color: #BBDEFB; padding: 8px; border-radius: 10px;")
        section_layout_3d.addWidget(title_3d)
        
        for figure_name in figures_3d:
            btn = RectangularButton(figure_name,
                                   partial(self.show_file_selection, figure_name),
                                   280, 45)
            section_layout_3d.addWidget(btn, alignment=Qt.AlignCenter)
        
        central_layout.addWidget(section_3d, alignment=Qt.AlignCenter)
        
        main_layout.addWidget(central_container, alignment=Qt.AlignCenter)
        main_layout.addStretch()
    
    def show_file_selection(self, figure_name):
        if not isinstance(figure_name, str):
            return
        
        self.navigation_history.append({'type': 'figure_selection'})
        self.back_btn.setEnabled(True)
        
        self.main_page.clear()
        main_layout = self.main_page.content_layout
        
        title = QLabel(figure_name)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font: bold 24pt 'Segoe UI'; color: #2196F3; margin: 15px;")
        main_layout.addWidget(title)
        
        files_list = FIGURES_DATA.get(figure_name, [])
        if not files_list:
            label = QLabel("Нет доступных файлов для этой фигуры.")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font: 12pt 'Segoe UI'; color: #757575; margin: 20px;")
            main_layout.addWidget(label)
            return
        
        buttons_container = QWidget()
        buttons_container.setStyleSheet("background-color: transparent;")
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setAlignment(Qt.AlignCenter)
        buttons_layout.setSpacing(10)
        
        for btn_text, file_path, local_filename in files_list:
            btn = RectangularButton(btn_text,
                                   partial(self.copy_file, file_path, local_filename, btn_text),
                                   500, 45)
            buttons_layout.addWidget(btn, alignment=Qt.AlignCenter)
        
        main_layout.addWidget(buttons_container, alignment=Qt.AlignCenter)
        main_layout.addStretch()
    
    def copy_file(self, source_path, local_filename, display_name):
        if not os.path.exists(source_path):
            QMessageBox.critical(self, "Ошибка", 
                f"Файл не найден:\n{source_path}\n\nФайл должен находиться в папке с программой")
            return
        
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить файл", local_filename,
            "All files (*.*)")
        
        if not save_path:
            return
        
        self.setCursor(Qt.WaitCursor)
        
        def copy_thread():
            try:
                shutil.copy2(source_path, save_path)
                QMessageBox.information(self, "Успех", 
                    f"Файл '{display_name}' успешно скопирован:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка копирования:\n{str(e)}")
            finally:
                self.unsetCursor()
        
        Thread(target=copy_thread, daemon=True).start()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FIGURES_DATA = {
    "Треугольник": [
        ("Теория о треугольнике", os.path.join(BASE_DIR, "треугольник", "Теория о треугольнике.doc"), "Теория о треугольнике.doc"),
        ("Площадь треугольника (формулы + задачи)", os.path.join(BASE_DIR, "треугольник", "Площадь треугольника (формулы + задачи).doc"), "Площадь треугольника (формулы + задачи).doc"),
        ("Периметр треугольника (формулы + задачи)", os.path.join(BASE_DIR, "треугольник", "Периметр треугольника(формулы + задачи).doc"), "Периметр треугольника(формулы + задачи).doc"),
        ("Свойства треугольника", os.path.join(BASE_DIR, "треугольник", "Свойства треугольника.doc"), "Свойства треугольника.doc"),
    ],
    "Квадрат": [
        ("Теория о квадрате", os.path.join(BASE_DIR, "квадрат", "Теория о квадрате.doc"), "Теория о квадрате.doc"),
        ("Площадь квадрата (формулы + задачи)", os.path.join(BASE_DIR, "квадрат", "Площадь квадрата (формулы + задачи).doc"), "Площадь квадрата (формулы + задачи).doc"),
        ("Периметр квадрата (формулы + задачи)", os.path.join(BASE_DIR, "квадрат", "Периметр квадрата (формулы + задачи).doc"), "Периметр квадрата (формулы + задачи).doc"),
        ("Свойства квадрата", os.path.join(BASE_DIR, "квадрат", "Свойства квадрата.doc"), "Свойства квадрата.doc")
    ],
    "Окружность": [
        ("Теория о окружности", os.path.join(BASE_DIR, "окружность", "Теория о окружности.doc"), "Теория о окружности.doc"),
        ("Площадь окружности (формулы + задачи)", os.path.join(BASE_DIR, "окружность", "Площадь окружности (формулы + задачи).doc"), "Площадь окружности (формулы + задачи).doc"),
        ("Периметр окружности (формулы + задачи)", os.path.join(BASE_DIR, "окружность", "Периметр окружности (формулы + задачи).doc"), "Периметр окружности (формулы + задачи).doc"),
        ("Свойства окружности", os.path.join(BASE_DIR, "окружность", "Свойства окружности.doc"), "Свойства окружности.doc")
    ],
    "Куб": [
        ("Теория о кубе", os.path.join(BASE_DIR, "куб", "Теория о кубе.doc"), "Теория о кубе.doc"),
        ("Площадь куба (формулы + задачи)", os.path.join(BASE_DIR, "куб", "Площадь куба (формулы + задачи).doc"), "Площадь куба (формулы + задачи).doc"),
        ("Периметр куба (формулы + задачи)", os.path.join(BASE_DIR, "куб", "Периметр куба (формулы + задачи).doc"), "Периметр куба (формулы + задачи).doc"),
        ("Объём куба (формулы + задачи)", os.path.join(BASE_DIR, "куб", "Объём куба (формулы + задачи).doc"), "Объём куба (формулы + задачи).doc"),
        ("Свойства куба", os.path.join(BASE_DIR, "куб", "Свойства куба.doc"), "Свойства куба.doc")
    ],
    "Шар": [
        ("Теория о шаре", os.path.join(BASE_DIR, "шар", "Теория о шаре.doc"), "Теория о шаре.doc"),
        ("Площадь шара (формулы + задачи)", os.path.join(BASE_DIR, "шар", "Площадь шара (формулы + задачи).doc"), "Площадь шара (формулы + задачи).doc"),
        ("Объём шара (формулы + задачи)", os.path.join(BASE_DIR, "шар", "Объём шара (формулы + задачи).doc"), "Объём шара (формулы + задачи).doc"),
        ("Свойства шара", os.path.join(BASE_DIR, "шар", "Свойства о шаре.doc"), "Свойства о шаре.doc")
    ],
    "Конус": [
        ("Теория о конусе", os.path.join(BASE_DIR, "конус", "Теория о конусе.doc"), "Теория о конусе.doc"),
        ("Площадь конуса (формулы + задачи)", os.path.join(BASE_DIR, "конус", "Площадь конуса (формулы + задачи).doc"), "Площадь конуса (формулы + задачи).doc"),
        ("Объём конуса (формулы + задачи)", os.path.join(BASE_DIR, "конус", "Объём конуса (формулы + задачи).doc"), "Объём конуса (формулы + задачи).doc"),
        ("Свойства конуса", os.path.join(BASE_DIR, "конус", "Свойства о конусе.doc"), "Свойства о конусе.doc")
    ]
}


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GeometryApp()
    window.show()
    sys.exit(app.exec_())