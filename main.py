from pdf2text import process_pdf
from parcing_text import parcing
from text2excel import to_excel

def main():
    output_text_path = input('Введите название для промежуточного файла:\n')
    pdf_path = input('Укажите путь к .pdf-файду:\n')
    excel_path = input('Введите название для excel файла:\n')
    text_path = process_pdf(pdf_path, output_text_path)
    data = parcing(pdf_path, text_path)
    to_excel(data, excel_path)
    print("Парсинг данных завершен!")



if __name__ == '__main__':
    main()