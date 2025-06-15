import os
import base64
import requests
import time
from dotenv import load_dotenv
import json


# Загружаем ключи из .env
load_dotenv()
APP_ID = os.getenv("ABBYY_APP_ID")
APP_PASSWORD = os.getenv("ABBYY_APP_PASSWORD")
auth = base64.b64encode(f"{APP_ID}:{APP_PASSWORD}".encode()).decode()
URL_PATTERN = 'https://cloud-eu.ocrsdk.com/v2/'

class Task:
	"""Класс для представления задачи OCR в ABBYY Cloud.
    
    Attributes:
        Status (str): Текущий статус задачи ('Unknown', 'Queued', 'InProgress', 'Completed').
        Id (str): Уникальный идентификатор задачи.
        DownloadUrl (str): URL для скачивания результатов после завершения задачи.
    """
    
	Status = "Unknown"
	Id = None
	DownloadUrl = None

	def is_active(self):
		"""Проверяет, активна ли задача (в процессе выполнения или в очереди).
        
        Returns:
            bool: True если задача еще выполняется, False если завершена или не начата.
        """

		if self.Status == "InProgress" or self.Status == "Queued":
			return True
		else:
			return False

def get_request_url(url):
      return URL_PATTERN.strip('/') + '/' + url.strip('/')
    

def get_task_status(task):
    """Получает текущий статус задачи от сервера ABBYY Cloud OCR.
    
    Args:
        task (Task): Объект задачи, для которой нужно проверить статус.
        
    Returns:
        Task: Обновленный объект задачи с текущим статусом.
        
    Note:
        Если передан неверный ID задачи, выводит предупреждение в консоль.
    """
	
    if task.Id.find('00000000-0') != -1:
        print("Null task id passed")
        return None

    url_params = {"taskId": task.Id}
    status_url = get_request_url("getTaskStatus")

    response = requests.get(status_url, params=url_params,
                            auth=(APP_ID, APP_PASSWORD))
    task = decode_response(response.text)
    return task

def decode_response(json_response):
		"""Парсит JSON-ответ от сервера ABBYY Cloud OCR.
        
        Args:
            json_response (str): JSON-строка с ответом сервера.
            
        Returns:
            Task: Объект задачи с заполненными полями из ответа сервера.
        """
		
		dom = json.loads(json_response)
		task = Task()
		task.Id = dom.get("taskId")
		task.Status = dom.get("status")
		if task.Status == "Completed":
			task.DownloadUrl = dom.get("resultUrls")
		return task

def abbyy_cloud_ocr(file_data):
    """
    Отправляет файл в ABBYY Cloud OCR и возвращает текст.
    Поддерживает: PDF, JPEG, PNG, TIFF, BMP.
    """
    # if not os.path.isfile(file_path):
    #     raise FileNotFoundError(f"Файл \"{file_path}\" не найден")

    # Читаем и кодируем файл
    # with open(file_path, "rb") as file:
    #     file_data = file.read()

    # URL для новой версии API (v2)
    url = get_request_url('processImage')

    url_params = {
			"language": "Russian",
			"exportFormat": 'txt'
		}

    # Отправляем файл
    response = requests.post(url, params=url_params, data=file_data,
                             auth=(APP_ID, APP_PASSWORD))
    
    response.raise_for_status()  # Проверка других ошибок
    task = decode_response(response.text)
    print('uploaded')


    while task.is_active():
        time.sleep(3)
        print('...')
        task = get_task_status(task)
    
    print(f"Status = {task.Status}")

    if task.Status == "Completed":
	    if task.DownloadUrl is not None:
                file_response = requests.get(task.DownloadUrl[0], stream=True,)
                return file_response