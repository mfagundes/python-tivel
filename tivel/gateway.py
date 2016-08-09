# coding: utf-8
from __future__ import print_function
import hashlib
import requests
import logging
import json

from django.utils.translation import ugettext as _

from error import TivelException
from tivel import settings
from repository import loads

# TODO: break dependency from local module
from shipping.models import Country

TivelPaymentOption = (
    (1,  (u'Diners', 'Komerci', 'Redecard')),
    (2,  (u'Mastercard', 'Komerci', 'Redecard')),
    (3,  (u'Cartões Bradesco (Pagamento Fácil)', 'Comércio Eletrônico (SPS)',
           'Banco Bradesco')),
    (11, (u'American Express', 'WebPOS', 'American Express')),
    (14, (u'Cartões Itaucard', 'Itaú Shopline', 'Banco Itaú')),
    (25, (u'Diners', 'Komerci WebService', 'Redecard')),
    (26, (u'Mastercard', 'Komerci WebService', 'Redecard')),
    (28, (u'American Express', 'WebPOS Webservice', 'American Express')),
    (34, (u'Visa', 'Komerci', 'Redecard')),
    (35, (u'Visa', 'Komerci Webservice', 'Redecard')),
    (36, (u'Visa', 'Buy Page Cielo', 'Cielo')),
    (38, (u'Visa', 'Buy Page Loja', 'Cielo')),
    (40, (u'Mastercard', 'Buy Page Cielo', 'Cielo')),
    (41, (u'Mastercard', 'Buy Page Loja', 'Cielo')),
    (44, (u'Elo', 'Buy Page Cielo', 'Cielo')),
    (45, (u'Elo', 'Buy Page Loja', 'Cielo')),
    (48, (u'Diners', 'Buy Page Cielo', 'Cielo')),
    (49, (u'Diners', 'Buy Page Loja', 'Cielo')),
    (17, (u'Cartões Real (Visa)', 'Real Pague Internet', 'Banco Real')),
    (32, (u'Mastercard', 'Moset', 'Cielo')),
    (27, (u'Visa', 'Moset', 'Cielo')),
    (7,  (u'Visa', 'Verified by Visa', 'Cielo')),
    (31, (u'Hipercard', 'Hipercommerce', 'Hipercard')),
    (39, (u'Mastercard', 'Verified by Visa', 'Cielo')),
    (46, (u'Discover', 'Buy Page Cielo', 'Cielo')),
    (47, (u'Discover', 'Buy Page Loja', 'Cielo'))
)


# formas de pagamento
TivelPaymentForm = (
    ('A01', u'à vista'),
    ('A02', u'2x sem juros'),
    ('A03', u'3x sem juros'),
    ('A04', u'4x sem juros'),
    ('A03', u'3x sem juros'),
    ('A06', u'6x sem juros'),
    ('A07', u'7x sem juros'),
    ('A08', u'8x sem juros'),
    ('A09', u'9x sem juros'),
    ('A10', u'10x sem juros'),
    ('A11', u'11x sem juros'),
    ('A12', u'12x sem juros'),
    # ('B02', u'2x com juros'),
    # ('B03', u'3x com juros'),
    # ('B04', u'4x com juros'),
    # ('B05', u'5x com juros'),
    # ('B06', u'6x com juros'),
    # ('B07', u'7x com juros'),
    # ('B08', u'8x com juros'),
    # ('B09', u'9x com juros'),
    # ('B10', u'10x com juros'),
    # ('B11', u'11x com juros'),
    # ('B12', u'12x com juros')
)


class TivelGateway(object):

    def __init__(self,
                 sandbox=False,
                 url=settings.TIVEL_URL,
                 token=settings.TIVEL_GATEWAY_TOKEN,
                 idw=settings.TIVEL_GATEWAY_IDW,
                 timeout=90):
        assert isinstance(url, str)
        assert isinstance(token, str)
        assert isinstance(idw, str)

        self.url = url
        self.token = token
        self.idw = idw
        self.sandbox = sandbox
        self.timeout = timeout
        self.version = '1'
        self.gateway_redirect_page = "{0}/?t={1}&idw={2}".format(url, token, idw)

        self.available_payment_forms = \
            {
                "28":                                     # American Express
                    {
                        "valor_minimo": 0.01,
                        "max_parcelas": 3,
                        "min_parcela": 50.00,
                        "cartao_exterior": True,
                        "parcelado": True
                    },
                "38":                                     # Visa
                    {
                        "valor_minimo": 0.01,
                        "max_parcelas": 3,
                        "min_parcela": 50.00,
                        "cartao_exterior": True,
                        "parcelado": True
                    },
                "41":                                     # Mastercard
                    {
                        "valor_minimo": 0.01,
                        "max_parcelas": 3,
                        "min_parcela": 50.00,
                        "cartao_exterior": True,
                        "parcelado": False
                    },
                "49": {                                  # Diners
                        "valor_minimo": 0.01,
                        "max_parcelas": 3,
                        "min_parcela": 50.00,
                        "cartao_exterior": True,
                        "parcelado": False
                }
            }

    def _make_request(self, token, sale, params=None, version=None):
        params = params or {}
        version = version or self.version

        url_servico = "%s%s" % (self.url, params.get('servico'))

        assert isinstance(token, str)
        assert isinstance(params, dict)

        default_params = {
            'versao': version
        }

        data = {
            'sale': loads([sale])[0],
            'saleitems': loads(sale.saleitems.all()),
            'addresses': loads(sale.addresses.all()),
            'billets': loads(
                sale.billets.all(),
                fields=(
                    'barcode',
                    'status',
                    'doc_value',
                    'sale',
                    'maturity',
                    'created',
                    'our_number'
                )
            )
        }

        for a in data["addresses"]:
            a['country'] = Country.objects.get(id=a['country']).iso

        #TODO: break dependency from local modules
        for item in data['saleitems']:
            sale_item = sale.saleitems.get(id=item['id'])
            if sale_item.item:
                sale_item = sale_item.item
                if sale_item.edition:
                    edition = sale_item.edition
                    item['edition_id'] = edition.erp_reference
            else:
                sale_item = sale_item.package

            item['item_erp_reference'] = sale_item.erp_reference

        params.update(default_params)

        response = requests.post(
            url_servico,
            data=json.dumps(data),
            headers={"chave": settings.TIVEL_CHAVE},
            verify=False,
            timeout=self.timeout
        )

        if response.status_code == 200:
            sale.erp_reference = response.json()['id']
            sale.save()
            return response.json()
        else:
            sale.erp_error = True
            sale.erp_error_message = response.json()['error']['msg']
            sale.save()

            message = '<strong>Falha ao notificar o ERP</strong>' + '<p>' + response.text + '</p>' + '<p>' + json.dumps(
                data) + '</p>'
            # nc.erro_venda(exception=message)
            logging.error(response.text)

            #TODO: configurable error messages, including translations
            return {'erro': _(u'Ocorreu um erro no processamento da sua compra. Por favor, entre em contato.')}


    def payment_options(self, total):
        """Recupera as formas de pagamento disponíveis no Tivel

        exemplo de retorno:
        >>> [{
        >>>   'formas': [u'\xe0 vista', u'2x sem juros'],
        >>>   'instituicao': 'American Express',
        >>>   'convenio': 'WebPOS Webservice',
        >>>   'nome': 'American Express'
        >>> }]

        :Parameter:
          - `total`: valor total da compra como inteiro.
             por exemplo: R$110,10 ficaria 11010
        """
        assert isinstance(total, int)

        PAYMENT_OPTIONS = dict(TivelPaymentOption)
        PAYMENT_FORMS = dict(TivelPaymentForm)

        prepared_payment_options = []
        for payment_option in self.get_tivel_payment_options(total):
            try:
                nome, convenio, instituicao = PAYMENT_OPTIONS[int(payment_option['codigo'])]
            except KeyError:
                logging.warn('meio de pagamento desconhecido %s' % payment_option)
                continue

            forms = []

            payment_forms = payment_option['formas']
            if not isinstance(payment_forms, list):
                payment_forms = [payment_forms['forma']]

            for payment_form in payment_forms:
                codigo = str(payment_form['codigo'])
                forms.append((codigo, PAYMENT_FORMS.get(codigo)))

            prepared_payment_options.append({
                'nome': nome,
                'convenio': convenio,
                'instituicao': instituicao,
                'codigo': payment_option['codigo'],
                'formas': forms
            })

        return prepared_payment_options

    def get_tivel_payment_options(self, total):
        available_forms = []
        for form in self.available_payment_forms:
            # form {28: {"valor_minimo": 0.01,"max_parcelas": 3,"min_parcela": 50.00,"cartao_exterior": True}}
            form_config = self.available_payment_forms[form]
            if total >= form_config['valor_minimo']:
                max_parcelas = int((total/100) / int(form_config['min_parcela'])) if form_config['parcelado'] else 1
                all_options = []
                for i in range(1, max_parcelas + 1):
                    cod_parcelas = 'A0{0}'.format(i)
                    all_options.append({'valor_total': total, 'codigo': cod_parcelas})
                available_forms.append({'formas': all_options, 'codigo': form})

        return available_forms

    def process_payment(self, sale, total, **kwargs):
        """Processar pagamentos pela Integração Checkout Cielo
        """
        tivel_service = "/{service}}".format(service=settings.TIVEL_SERVICES['POST_VENDA'])

        params = {
            'total': total,
            'servico': tivel_service
        }

        params.update(kwargs)

        response = self._make_request(settings.TIVEL_CHAVE, sale, params=params)

        return response
