import flet as ft
from flet_route import Params, Basket
import base64
import asyncio
import cv2
import face_recognition
import numpy as np
import os
from pathlib import Path


# Класс камеры.---------------------------------------------------------------------

class Cam:
    """Класс, который обрабатывает камеры"""

    def __init__(self):
        # Создайте объект камеры для OpenCV.
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Не удалось открыть камеру")
            self._is_capture = False
        else:
            self._is_capture = True

    def get_image(self):
        # Получить изображение с камеры.
        ret, self.frame = self.cap.read()
        if not ret:
            print("Ошибка захвата изображения")
            return None  # Возвращаем None, если кадр не был захвачен.
        
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
        if img is None or img.size == 0:
            print("Пустое изображение")
            return ""  # Возвращаем пустую строку или можно обработать ошибку как угодно.
        
        _, encoded = cv2.imencode(".jpg", img)
        img_str = base64.b64encode(encoded).decode("ascii")
        return img_str

    def __del__(self):
        # Выходная камера.
        self.cap.release()

#-----------------------------------------------------------------------------------
# Функция обновления кадра в реальном времени с распознаванием лиц.-----------------
async def update_frame(page: ft.Page, camera: Cam, image: ft.Image, known_face_encodings, known_face_names):
    """Функция обновления кадра в реальном времени с распознаванием лиц"""
    # Инициализация переменных для распознавания лиц
    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    while True:
        if camera.is_capture:
            img = camera.get_image()
            if img:
                # Захват одного кадра видео
                frame = camera.frame  # Получаем последний кадр с камеры

                # Обрабатываем только каждый второй кадр видео, чтобы сэкономить время
                if process_this_frame:
                    # Измените размер кадра видео до 1/4 для более быстрой обработки распознавания лиц.
                    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

                    # Преобразование изображения из цвета BGR (который использует OpenCV) в цвет RGB (который использует face_recognition)
                    rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])
                        
                    # Найдите все лица и кодировки лиц в текущем кадре видео.
                    face_locations = face_recognition.face_locations(rgb_small_frame)
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                    face_names = []
                    for face_encoding in face_encodings:
                        # Посмотрите, соответствует ли лицо известному лицу (лицам)
                        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                        name = "Unknown"

                        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = known_face_names[best_match_index]

                        face_names.append(name)

                process_this_frame = not process_this_frame

                # Отображение результатов
                for (top, right, bottom, left), name in zip(face_locations, face_names):
                    # Масштабируйте резервные копии лиц, поскольку кадр, который мы обнаружили, был уменьшен до 1/4 размера.
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4

                    # Рисование рамки вокруг лица
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                    # Рисование метки с именем под лицом
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                    font = cv2.FONT_HERSHEY_DUPLEX
                    cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

                # Обновляем изображение на странице Flet
                img = camera._cv_to_base64(frame)
                image.src_base64 = img
                page.update()

        await asyncio.sleep(0.1)  # Пауза, чтобы не блокировать интерфейс

#-----------------------------------------------------------------------------------
# Класс страницы.-------------------------------------------------------------------

class MainPage():
    async def view(page: ft.Page):
        # Считаем файлы в папке
        directory = "pic/"
        folder = Path(directory)
        folder_count = len([1 for file in folder.iterdir()])
        print(folder_count)

        # Инициализируем переменные
        known_face_encodings = []
        known_face_names = []

        # Меняем текущую директорию
        dirlist = os.listdir(directory)

        os.chdir(directory)

        # Записываем кодировки фото
        for i in range(folder_count):
            idk_image = cv2.imread(dirlist[i])
            idk_face_encoding = face_recognition.face_encodings(idk_image)[0]
            known_face_encodings.insert(i, idk_face_encoding)

            names = dirlist[i].split(".", -1)[0]
            known_face_names.insert(i, names)

        # Инициализация камеры
        camera = Cam()

        # Макет страницы
        page.title = "Camera App"
        image = ft.Image(
            src_base64=camera.get_image(),
            width=480,
            height=320,
            fit=ft.ImageFit.CONTAIN,
        )

        start_button = ft.TextButton("Start", on_click=camera.start_cam)
        stop_button = ft.TextButton("Stop", on_click=camera.end_cam)
        row = ft.Row(spacing=0, controls=[start_button, stop_button])

        # Запуск асинхронного цикла обновления кадра с распознаванием лиц
        await update_frame(page, camera, image, known_face_encodings, known_face_names)
        return ft.View(
            '/',
            controls=[image, row]
        )
