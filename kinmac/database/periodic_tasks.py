from api_requests.wb_requests import wb_article_data_from_api
from celery_tasks.celery import app

from kinmac.constants_file import wb_headers

from .models import Articles


@app.task
def update_info_about_articles():
    common_data = wb_article_data_from_api(wb_headers)
    if common_data:
        for data in common_data:
            if Articles.objects.filter(
                nomenclatura_wb=data['nmID']
            ).exists():
                Articles.objects.filter(
                nomenclatura_wb=data['nmID']
            ).update(
                common_article=data['vendorCode'],
                brand=data['brand'],
                barcode=data['sizes'][0]['skus'][0],
                predmet=data['subjectName'],
                size=data['sizes'][0]['techSize'],
                name=data['title']
            )
            else:
                Articles(
                    nomenclatura_wb=data['nmID'],
                    common_article=data['vendorCode'],
                    brand=data['brand'],
                    barcode=data['sizes'][0]['skus'][0],
                    predmet=data['subjectName'],
                    size=data['sizes'][0]['techSize'],
                    name=data['title']
                ).save()



    