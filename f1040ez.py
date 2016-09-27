# -*- coding: utf8 -*-

SINGLE = 0
import datetime
from decimal import Decimal as D
from simple import Debit,Credit
ZERO = D('0.00')


def f1040ez(ledger, balances, when, filestatus=SINGLE, dependents=0):
    '''complete tax form, deposit refund on when
    '''

    wts = balances.get(ledger.get_account("w-2 income"))
    tintr = balances.get(ledger.get_account("interest earned")).quantize(ZERO)
    uicomp = ZERO

    agi = wts + tintr + uicomp

    def wks5():
        a = wts + D('350.00')
        b = D('1050.00')
        c = max(a, b)
        d = D('6300.00') if filestatus == SINGLE else D('12600.00')
        e = min(c, d)
        f = D('4000.00') * dependents
        return e + f

    stded = wks5()
    tinc = max(ZERO, agi - stded)

    fitacct = ledger.get_account('Federal Income Tax')
    fit = balances.get(fitacct)
    eic = ZERO
    ntcpe = ZERO
    tpc = fit + eic

    tax = (tinc * D('.1')).quantize(ZERO)
    obama = ZERO
    ttax = tax + obama

    refund = tpc - ttax
    if refund < 0:
        owe = -refund
        refund = ZERO
    else:
        owe = ZERO

    if refund > ZERO:
        ledger.enter(when, 'Federal Income Tax Refund for {}'.format(when.year - 1),
                     Debit(when, ledger.get_account('cash'), refund),
                     Credit(when, ledger.get_account(
                         'Federal Tax Refund'), refund),
                     )
    else:
        then = datetime.date(when.year, 4, 15)
        ledger.enter(when, 'Federal Income Tax due for {}'.format(when.year - 1),
                     Debit(then, fitacct, owe),
                     Credit(then, ledger.get_account('cash'), owe),
                     )

    return dict(
        Form='1040ez',
        L01=wts,
        L02=tintr,
        L03=uicomp,
        L04=agi,
        L05=stded,
        L06=tinc,
        L07=fit,
        L08a=eic,
        L08b=ntcpe,
        L09=tpc,
        L10=tax,
        L11=obama,
        L12=ttax,
        L13a=refund,
        L14=owe,
    )
