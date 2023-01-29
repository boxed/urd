from django.test import RequestFactory
from iommi.struct import Struct


def no_auth_middleware_req(method, url='/', **data):
    return getattr(RequestFactory(HTTP_REFERER='/'), method.lower())(url, data=data)


def req(method, url='/', **data):
    request = no_auth_middleware_req(method, url=url, **data)
    request.user = Struct(is_staff=False, is_authenticated=False, is_superuser=False)
    return request


def staff_req(method, **data):
    request = req(method, **data)
    request.user = Struct(is_staff=True, is_authenticated=True, is_superuser=True)
    return request
