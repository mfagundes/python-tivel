from django.conf import settings

DEBUG = "False"

TIVEL_GATEWAY_URL = getattr(settings, 'TIVEL_GATEWAY_URL', None)
TIVEL_GATEWAY_TOKEN = getattr(settings, 'TIVEL_GATEWAY_TOKEN', 1)
TIVEL_GATEWAY_IDW = getattr(settings, 'TIVEL_GATEWAY_IDW', 1)

TIVEL_URL = getattr(settings, 'ERP_API_URL')
TIVEL_CHAVE = getattr(settings, 'ERP_API_CHAVE')

# TODO: make configurable

TIVEL_SERVICES = {
    "POST_VENDA": "postVenda"
}