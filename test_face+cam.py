import flet as ft
import cv2
import base64
import face_recognition
import numpy as np
from pathlib import Path
import os


class Cam:
    """Класс, который обрабатывает камеры"""
    
    def __init__(self):
        """Создание объекта камеры для OpenCV."""
        self.cap = cv2.VideoCapture(0)
        self._is_capture = True
        
    def get_image(self):
        """Получение изображения с камеры."""
        _, self.frame = self.cap.read()
        img = self._cv_to_base64(self.frame)
        return img

    def start_cam(self, e):
        """Обработка в начале получения изображения"""
        self._is_capture = True

    def end_cam(self, e):
        """Обработка в конце получения изображения"""
        self._is_capture = False

    @property
    def is_capture(self) -> bool:
        """Флаг, указывающий, следует ли выполнять получение изображения
        Returns:
            bool: При получении изображений True
        """
        return self._is_capture

    def _cv_to_base64(self, img):
        """Переводит изображение в base64 для flet."""
        _, encoded = cv2.imencode(".jpg", img)
        img_str = base64.b64encode(encoded).decode("ascii")
        return img_str

    def __del__(self):
        """Выходная камера."""
        self.cap.release()


def main(page: ft.Page):

    # Общая планировка.
    page.title = "Camera App"

    # Определение экземпляра, который обрабатывает глобальную камеру.
    camera = Cam()

    # Создание элементов на странице.
    image = ft.Image(
        width=480,
        height=320,
        fit=ft.ImageFit.CONTAIN,
    )
    start_button = ft.TextButton("start", on_click=camera.start_cam)
    stop_button = ft.TextButton("stop", on_click=camera.end_cam)
    row = ft.Row(spacing=0, controls=[start_button, stop_button])

    # Добавление эдементов на страницу.
    page.add(image)
    page.add(row)

    # Поиск картинок в папке pic.
    folder = Path("pic")
    folder_count = len([1 for file in folder.iterdir()])
    print(folder_count)

    # хз что.
    known_face_encodings = []
    known_face_names = []

    os.chdir("pic/")

    # Присвоение картинкам имён по их названию (название картинок пока 1, 2, 3....).
    for i in range(3):
        print(i)
        idk_image = cv2.imread(f'{i + 1}.jpg')
        idk_face_encoding = face_recognition.face_encodings(idk_image)[0]
        known_face_encodings.insert(i, idk_face_encoding)
        count = str(i)
        known_face_names.insert(i, count)

    known_face_names = ["Obama",
                        "Biden",
                        "Tsar"]

    # Тоже хз что.
    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    # Бесконечный цикл.
    while True:
        if camera.is_capture:
            _, frame = camera.cap.read()

            # Изменение размера кадра видео до 1/4 для более быстрой обработки распознавания лиц.
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            # Преобразование изображения из цвета BGR (который использует OpenCV) в цвет RGB (который использует face_recognition)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                
            # Нахождение всех лиц и их кодировки в текущем кадре видео.
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                # Просмотр соответствия лица известному лицу (лицам).
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"

                # Если совпадение найдено в «known_face_encodings», просто использует первое.
                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]

                # Или вместо этого использует известное лицо с наименьшим расстоянием до нового лица.
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

                face_names.append(name)
                
            process_this_frame = not process_this_frame


            # Отображение результатов.
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Масштабирует резервные копии лиц, поскольку кадр, который мы обнаружили, был уменьшен до 1/4 размера
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Рисует рамку вокруг лица.
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Нарисуйте метку с именем под лицом.
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
            image.src_base64 = camera._cv_to_base64(frame)
            page.update()


ft.app(target=main, view=ft.AppView.WEB_BROWSER)