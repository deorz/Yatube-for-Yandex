from django.core.paginator import Paginator

from django.conf import settings


def paginator(request, obj_list):
    """Разбивает obj_list по страницам"""
    paginator_obj = Paginator(obj_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator_obj.get_page(page_number)
    return page_obj
