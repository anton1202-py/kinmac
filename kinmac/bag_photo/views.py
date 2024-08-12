from django.shortcuts import redirect, render

from .forms import MultiFileUploadForm
from .models import BagImage


def bag_photo_view(request):
    """Отображает страницу с фотографиями рюкзаков"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Фото рюкзаков'
    if request.method == 'POST':
        files = request.FILES.getlist('files')  # Получаем список загруженных файлов
        print(files)
        for f in files:
            BagImage.objects.create(image=f)
        return render(request, 'bag_photo/upload_image.html')  # Создайте этот шаблон
    
    
    images = BagImage.objects.all() 

    
    context = {
        'page_name': page_name,
        'images': images,
    }
    
    return render(request, 'bag_photo/upload_image.html', context)