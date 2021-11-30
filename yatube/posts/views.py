from django.http import HttpResponse


# Create your views here.

def index(request):
    return HttpResponse('Главная страница')


def group_posts(request, group_name):
    return HttpResponse(f'Посты группы {group_name}')
