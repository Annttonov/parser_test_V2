import pandas

from pdf2text import process_pdf
from parcing_text import parcing

def to_excel(data, output_path):
    columns_order = ['id', 'name', 'parent']


    # # Парсинг и сохранение в .xlsx
    df = pandas.DataFrame(data, columns=columns_order,)
    df.rename(columns={
        'name': 'название'
    }, inplace=True)
    df.to_excel(output_path, index=False, engine='openpyxl')