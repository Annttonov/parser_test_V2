import re

import fitz

def parcing(pdf_path, content_txt_path):
    """Парсит структуру учебника из PDF и текстового файла с содержанием.
    
    Функция анализирует:
    1. Оглавление PDF (через get_toc())
    2. Распознанный текст с номерами страниц
    3. Строит иерархическую структуру разделов и подразделов
    
    Args:
        pdf_path (str): Путь к PDF файлу учебника
        content_txt_path (str): Путь к текстовому файлу с распознанным содержанием
        
    Returns:
        list: Список словарей с элементами структуры, где каждый элемент содержит:
            - id: уникальный идентификатор
            - name: название раздела
            - parent: id родительского раздела (0 для корневых)
    """
    parent_id = 0
    next_id = 1
    result = []
    start_pos = 0
    
    content = fitz.open(pdf_path).get_toc()
    with open(content_txt_path, "r") as f:
        text = f.readlines()

    for i in range(len(content)):
        chapter = content[i]
        item = {
            'id': next_id,
            'name': chapter[1],
            'parent': parent_id if chapter[0] >= 2 else 0
        }
        result.append(item)
        next_id += 1
        parent_id = item['id'] if chapter[0] == 1 else parent_id

        if chapter[0] != 1:
            part_string = ''
            end_pos = content[i+1][2]
            for j in range(start_pos, len(text)):
                if text[j].startswith('\ufeff'):
                    text[j] = text[j].replace('\ufeff', '')
                string = text[j] if part_string == '' else part_string + text[j] 
                section_match = re.search(r"^(\d+)\.\s+(.*?)\s*\.+\s*(\d+)\s*$", string)
                if section_match:
                    num = int(section_match.group(3))
                    if num == end_pos:
                        start_pos = j if part_string == '' else j + 1
                        part_string = ''
                        break
                    elif num > end_pos:
                        part_string = ''
                        break
                    continue
                
                part_string = ''
                part_match = re.search(r"^([А-Яа-яёЁ\s,.\-]+?)\.+\s*(\d+)\s*$", string)
                if part_match:
                    num = int(part_match.group(2))
                    if num < chapter[2] or num >= end_pos:
                        continue
                    cleaned = re.sub(r'[\.\s]*\d*\s*$', '', string.strip())
                    cleaned = re.sub(r'\.{2,}', '.', cleaned)
                    cleaned = re.sub(r'\.$', '', cleaned)
                    jtem = {
                        'id': next_id,
                        'name': cleaned.strip(),
                        'parent': item['id']
                    }
                    next_id += 1
                    result.append(jtem)
                elif text[j].isupper():
                    continue
                else:
                    part_string = text[j].replace('\n', '').strip()
                    if part_string.endswith('-'):
                        part_string = part_string[:-1]
                    else:
                        part_string = part_string + ' '

    
    return result