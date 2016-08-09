# coding:utf-8
from datetime import datetime

class Payment(object):

    def __init__(self, captured, option_code, form_code, total, created_at):
        self.captured = captured
        self.option_code = option_code
        self.form_code = form_code
        self.total = total
        self.created_at = created_at


class Request(object):

    def __init__(self, uid, code, status, status_time, test, payment):
        self.uid = uid
        self.code = code
        self.status = status
        self.status_time = status_time
        self.payment = payment
        self.test = (test == '1')

    @classmethod
    def create_from_dict(cls, **kw):
        payment = Payment(kw['pagamento']['capturado'],
            kw['pagamento']['codigo'],
            kw['pagamento']['forma'],
            kw['pagamento']['total'],
            datetime.strptime(kw['pagamento']['data'] +
                kw['pagamento']['hora'], '%d%m%Y%H%M%S'))

        return cls(kw['uid'],
            kw['codigo'],
            kw['status'],
            datetime.strptime(kw['data-status'] + kw['hora-status'],
            '%d%m%Y%H%M%S'),
            kw.get('teste', None),
            payment
        )
