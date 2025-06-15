import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image, ImageOps
import io
import os

from image2text import abbyy_cloud_ocr

# Инициализация EasyOCR (указываем языки: русский + английский)

def normalize_page(img_pil):
    """Нормализация страницы с обрезкой шапки"""
    # 1. Обрезаем верхнюю часть
    cropped = img_pil.crop((0, 155, img_pil.width, img_pil.height))
    
    # 2. Обрезка полей (как в предыдущем решении)
    img_cv = cv2.cvtColor(np.array(cropped), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = cv2.findNonZero(binary)
    x, y, w, h = cv2.boundingRect(coords)
    
    # 3. Финализируем обрезку
    final_crop = cropped.crop((x-10, y-10, x+w+10, y+h+10))
    return ImageOps.pad(final_crop, (1240, 1754), color='white')


def split_page(img_pil):
    """Делит страницу на 2 вертикальные части"""
    width, height = img_pil.size
    left = img_pil.crop((0, 0, width // 2, height))
    right = img_pil.crop((width // 2, 0, width, height))
    return left, right

def enhance_image(img_pil):
    # Загрузка изображения в градациях серого
    image = cv2.cvtColor(np.array(img_pil), cv2.COLOR_BGR2GRAY)

    kernel = np.array([[0, -1, 0],
                       [-1, 5.5, -1],
                       [0, -1, 0]])
    sharpened = cv2.filter2D(image, -1, kernel)

    # Контраст с CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(sharpened)

    # Мягкий гауссов фильтр
    blurred = cv2.GaussianBlur(contrast, (3, 3), 0)

    # Порог Оцу вместо адаптивного
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Проверка на инверсию
    white_ratio = np.sum(binary == 255) / binary.size
    if white_ratio < 0.5:
        binary = cv2.bitwise_not(binary)
    _, img_encoded = cv2.imencode(".jpg", binary)


    return img_encoded.tobytes()
    

def process_pdf(pdf_path, output_txt_path):
    """Основная функция обработки PDF файла.
    
    Выполняет:
    1. Поиск страниц с содержанием
    2. Обработку каждой страницы:
       - Рендеринг в изображение с высоким DPI
       - Нормализацию страницы
       - Разделение на две части
       - Улучшение качества каждой части
       - Распознавание текста через ABBYY Cloud OCR
    3. Сохранение результатов в текстовый файл
    
    Args:
        pdf_path (str): Путь к исходному PDF файлу
        output_txt_path (str): Путь для сохранения результата
        
    Returns:
        str: Абсолютный путь к созданному текстовому файлу
        
    Note:
        Пропускает страницы до "Содержания" (оглавления)
        Обрабатывает только страницы после оглавления
    """
    doc = fitz.open(pdf_path)
    full_text = []
    num_page_list = None

    for outline in doc.get_toc():
        if outline[1].lower() == 'содержание':
            num_page_list = range(outline[2] - 1 , len(doc) - 1)
    
    for page_num in num_page_list:
        page = doc.load_page(page_num)
    
        # Рендеринг с высоким DPI
        pix = page.get_pixmap(dpi=155)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        img = normalize_page(img)
        
        # Разделение страницы на 2 части
        left, right = split_page(img)
        
        # Обработка каждой половины
        for half in [left, right]:
            enhanced = enhance_image(half)
            response = abbyy_cloud_ocr(enhanced)
            response.encoding = 'utf-8'

            full_text.append(response.text)

    with open(output_txt_path, 'wb+') as output_file:
            for item in full_text:
                output_file.write(item.encode())
            
    return os.path.abspath(output_txt_path)

