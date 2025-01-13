import flet as ft
import cv2
import base64


class Cam:
    """Класс, который обрабатывает камеры"""

    def __init__(self):
        # Создайте объект камеры для OpenCV.
        self.cap = cv2.VideoCapture(0)
        self._is_capture = True

    def get_image(self):
        # Получить изображение с камеры.
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
        _, encoded = cv2.imencode(".jpg", img)
        img_str = base64.b64encode(encoded).decode("ascii")
        return img_str

    def __del__(self):
        # Выходная камера.
        self.cap.release()


def main(page: ft.Page):
    #Общая планировка.
    page.title = "Camera App"
    # Определение экземпляра, который обрабатывает глобальную камеру.
    camera = Cam()
    # Макет внутри страницы.
    image = ft.Image(
        src_base64=camera.get_image(),
        width=480,
        height=320,
        fit=ft.ImageFit.CONTAIN,
    )
    start_button = ft.TextButton("start", on_click=camera.start_cam)
    stop_button = ft.TextButton("stop", on_click=camera.end_cam)
    row = ft.Row(spacing=0, controls=[start_button, stop_button])
    page.add(image)
    page.add(row)

    # Петля изображения.
    while True:
        if camera.is_capture:
            img = camera.get_image()
            image.src_base64 = img
            page.update()
ft.app(target=main, view=ft.AppView.WEB_BROWSER)