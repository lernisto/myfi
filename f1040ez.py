# -*- coding: utf8 -*-

SINGLE = 0
from decimal import Decimal as D
from simple import Entry
ZERO = D('0.00')


def f1040ez(ledger, balances, when, filestatus=SINGLE, dependents=0):
    '''complete tax form, deposit refund on when
    '''

    wts = balances.get(ledger.get_account("w-2 income"))
    tintr = balances.get(ledger.get_account("interest earned"))
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

    ttax = tinc * D('.1')
    refund = max(ZERO, fit - ttax)
    if refund > ZERO:
        ledger.enter(when, 'Federal Income Tax Refund for {}'.format(when.year - 1),
                     Entry(when, None, ledger.get_account(
                         'cash'), True, refund, None),
                     Entry(when, None, fitacct, False, refund, None),
                     )
