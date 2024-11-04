from zipfile import ZipFile

import pandas as pd

with ZipFile("kinmac\check_report\Детализация_еженедельного_отчета_№269464144.zip", "r") as myzip:
    for item in myzip.namelist():
        content = myzip.read(item)

        excel_data_common = pd.read_excel(content)
        column_list = excel_data_common.columns.tolist()
