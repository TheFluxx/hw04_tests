from django.core.paginator import Paginator

from yatube.settings import num_posts


def get_page_context(queryset, request):
    paginator = Paginator(queryset, num_posts)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
