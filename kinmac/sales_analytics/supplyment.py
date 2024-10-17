from datetime import datetime
import time
import gspread
import pandas as pd


from gspread_formatting import *
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from celery_tasks.tasks import sales_report_statistic
from database.models import (Articles, CodingMarketplaces, CostPrice,
                             SalesReportOnSales)
from django.db.models import Case, Count, IntegerField, Q, Sum, When
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Side

from api_requests.wb_requests import get_check_storage_cost_report_status, get_create_storage_cost_report, get_storage_cost_report_data
from kinmac.constants_file import wb_headers, BRAND_LIST
from .models import (ArticleSaleAnalytic, CommonSaleAnalytic,
                     ReportForCommonSaleAnalytic)


def template_for_article_costprice(costprice_data):
    """Создает и скачивает excel файл с шаблоном для себестоимости"""
    # Создаем DataFrame из данных
    wb = Workbook()
    # Получаем активный лист
    ws = wb.active

    # Заполняем лист данными
    row = 2
    for article in costprice_data:
        ws.cell(row=row, column=1, value=article.article.common_article)
        ws.cell(row=row, column=2, value=article.article.name)
        if article.costprice:
            ws.cell(row=row, column=3, value=article.costprice)
        else:
            ws.cell(row=row, column=3, value='')
        row += 1
    # Устанавливаем заголовки столбцов
    ws.cell(row=1, column=1, value='Артикул')
    ws.cell(row=1, column=2, value='Название')
    ws.cell(row=1, column=3, value='Себестоимость')

    al = Alignment(horizontal="center",
                   vertical="center")
    al_left = Alignment(horizontal="left",
                        vertical="center")
    thin = Side(border_style="thin", color="000000")

    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 18

    for i in range(len(costprice_data)+1):
        for c in ws[f'A{i+1}:C{i+1}']:
            for i in range(3):
                c[i].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[i].alignment = al_left

    # Сохраняем книгу Excel в память
    response = HttpResponse(content_type='application/xlsx')
    name = f'Article_Costprice_Template_{datetime.now().strftime("%Y.%m.%d")}.xlsx'
    file_data = 'attachment; filename=' + name
    response['Content-Disposition'] = file_data
    wb.save(response)

    return response


def costprice_article_timport_from_excel(xlsx_file):
    """Импортирует данные о группе артикула из Excel"""
    excel_data_common = pd.read_excel(xlsx_file)
    column_list = excel_data_common.columns.tolist()
    if 'Артикул' in column_list and 'Название' in column_list and 'Себестоимость' in column_list:
        excel_data = pd.DataFrame(excel_data_common, columns=[
                                  'Артикул', 'Название', 'Себестоимость'])
        article_list = excel_data['Артикул'].to_list()
        designer_type_list = excel_data['Название'].to_list()
        costprice_list = excel_data['Себестоимость'].to_list()

        for i in range(len(article_list)):

            if Articles.objects.filter(common_article=article_list[i]).exists():
                if CostPrice.objects.filter(article__common_article=article_list[i]).exists():
                    if not CostPrice.objects.filter(article__common_article=article_list[i], costprice=costprice_list[i]).exists():
                        CostPrice.objects.filter(article__common_article=article_list[i]).update(
                            costprice=costprice_list[i],
                            costprice_date=datetime.now()
                        )
                else:
                    CostPrice(article__common_article=article_list[i],
                        costprice=costprice_list[i],
                        costprice_date=datetime.now()

                    )
            else:
                return f'В базе данных нет артикула {article_list[i]}.'

        
    else:
        return f'Вы пытались загрузить ошибочный файл {xlsx_file}.'
