import pandas


def to_excel(data, output_path):
    columns_order = ['id', 'name', 'parent']

    df = pandas.DataFrame(data, columns=columns_order,)
    df.rename(columns={
        'name': 'название'
    }, inplace=True)
    df.to_excel(output_path, index=False, engine='openpyxl')
