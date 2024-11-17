from api_requests.wb_requests import wb_article_data_from_api, wb_comissions, wb_logistic
from kinmac.constants_file import wb_headers
from database.models import Articles
from unit_economic.models import WbLogisticTariffs
from unit_economic.supplyment import add_marketplace_comission_to_db, add_marketplace_logistic_to_db


def wb_categories_list(TOKEN_WB):
    """Возвращает список категорий товаров текущего пользователя"""
    main_data = wb_article_data_from_api(wb_headers)
    categories_dict = {}
    for data in main_data:
        if data['subjectID'] not in categories_dict:
            categories_dict[data['subjectID']] = data['subjectName']
    return categories_dict


def wb_comission_add_to_db():
    """
    Записывает комиссии ВБ в базу данных

    Входящие переменные:
        TOKEN_WB - токен учетной записи
    """
    data_list = wb_comissions(wb_headers)
    wb_comission_dict = {}
    if data_list:
        for data in data_list:
            wb_comission_dict[data['subjectID']] = {
                'fbs_commission': data['kgvpMarketplace'],
                'fbo_commission': data['paidStorageKgvp'],
                'dbs_commission': data['kgvpSupplier'],
                'fbs_express_commission': data['kgvpSupplierExpress']
            }
        goods_list = Articles.objects.all()
        for good_data in goods_list:
            try:
                fbs_commission = wb_comission_dict[good_data.category.category_number]['fbs_commission']
                fbo_commission = wb_comission_dict[good_data.category.category_number]['fbo_commission']
                dbs_commission = wb_comission_dict[good_data.category.category_number]['dbs_commission']
                fbs_express_commission = wb_comission_dict[
                    good_data.category.category_number]['fbs_express_commission']
                add_marketplace_comission_to_db(
                    good_data,
                    fbs_commission,
                    fbo_commission,
                    dbs_commission,
                    fbs_express_commission
                )
            except:
                print('good_dataa')


def wb_logistic_add_to_db():
    """
    Записывает затраты на логистику ВБ в базу данных

    Входящие переменные:
        TOKEN_WB - токен учетной записи
    """
    data_list = wb_logistic(wb_headers)
    if data_list:

        for data in data_list['warehouseList']:
            print(data)
            try:
                box_delivery_and_storage_expr = float(
                    str(data['boxDeliveryAndStorageExpr']).replace(',', '.'))
            except:
                box_delivery_and_storage_expr = None
            try:
                box_delivery_base = float(
                    str(data['boxDeliveryBase']).replace(',', '.'))
            except:
                box_delivery_base = None
            try:
                box_delivery_liter = float(
                    str(data['boxDeliveryLiter']).replace(',', '.'))
            except:
                box_delivery_liter = None
            try:
                box_storage_base = float(
                    str(data['boxStorageBase']).replace(',', '.'))
            except:
                box_storage_base = None
            try:
                box_storage_liter = float(
                    str(data['boxStorageLiter']).replace(',', '.'))
            except:
                box_storage_liter = None

            WbLogisticTariffs(
                box_delivery_and_storage_expr=box_delivery_and_storage_expr,
                box_delivery_base=box_delivery_base,
                box_delivery_liter=box_delivery_liter,
                box_storage_base=box_storage_base,
                box_storage_liter=box_storage_liter,
                warehouseName=data['warehouseName'],
                date_start=data_list['dtTillMax']
            ).save()
    # box_delivery_base = 0
    # box_delivery_liter = 0
    # comission = 0
    # if data_list:
    #     for data in data_list:
    #         if data['warehouseName'] == 'Коледино':
    #             box_delivery_base = data['boxDeliveryBase']
    #             box_delivery_liter = data['boxDeliveryLiter']
    #             break
    # goods_list = Articles.objects.filter(brand__in=BRAND_LIST)
    # for good in goods_list:
    #     height = good.height
    #     width = good.width
    #     length = good.length
    #     value = height * width * length / 1000
    #     box_delivery_base = float(
    #         str(box_delivery_base).replace(',', '.'))
    #     box_delivery_liter = float(
    #         str(box_delivery_liter).replace(',', '.'))
    #     if value <= 1:
    #         comission = box_delivery_base
    #     else:
    #         comission = box_delivery_base + \
    #             box_delivery_liter * (value - 1)
    #     comission = round(comission, 2)
    #     add_marketplace_logistic_to_db(
    #         good, comission)
