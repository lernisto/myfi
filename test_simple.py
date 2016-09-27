# -*- coding: utf8 -*-

from datetime import datetime, date, timedelta
from dateutil.rrule import *
from dateutil.relativedelta import *

from simple import *





def test_simple():
    coa = ChartofAccounts()
    coa.load_csv('accounts.csv')

    ledgers = []

    def newledger(old, now):
        if old:
            closing_entries(old, now)
            bal = balance_forward(old.balances)
        else:
            bal = {}
        new = Ledger(coa, bal)
        print('starting balances')
        new.show_balances()
        ledgers.append(new)
        return new

    now = datetime(2015, 1, 1) + relativedelta(days=1, weekday=TH)
    then = datetime(now.year, 6, 1) + relativedelta(days=1, weekday=TH)
    ledger = newledger(None, now)

    for now in rrule(freq=WEEKLY, dtstart=now, until=then, byweekday=TH):
        now = now.date()
        payday(ledger, now, D('16.0'), D('7.25'), 'IFA')
        bcm1(ledger, now)

    now = then + timedelta(7)
    then = datetime(now.year, 8, 31) + relativedelta(weekday=MO) + timedelta(4)
    for now in rrule(freq=WEEKLY, dtstart=now, until=then, byweekday=TH):
        now = now.date()
        # print(now)
        payday(ledger, now, D('30.0'), D('8.00'), 'IFB')
        bcm1(ledger, now)

    # print(now)
    now = then + timedelta(7)
    then = datetime(now.year, 12, 25) + \
        relativedelta(days=2, weekday=MO) + timedelta(4)
    for now in rrule(freq=WEEKLY, dtstart=now, until=then, byweekday=TH):
        now = now.date()
        print(now)
        payday(ledger, now, D('16.0'), D('8.50'), 'IFC')
        bcm1(ledger, now)

    print("here:",now)
    ledger.show_balances()
    ledger = newledger(ledger, now)
    then = datetime(now.year, 6, 1) + relativedelta(days=1, weekday=TH)

    for now in rrule(freq=WEEKLY, dtstart=now + timedelta(14),until=then, byweekday=TH):
        now = now.date()
        print(now)
        payday(ledger, now, D('16.0'), D('8.50'), 'IFC')
        bcm1(ledger, now)

    # print(now)

    for now in rrule(freq=WEEKLY, count=13, dtstart=now + timedelta(7), byweekday=TH):
        now = now.date()
        payday(ledger, now, D('30.0'), D('9.00'), 'IFD')
        bcm1(ledger, now)

    # print(now)

    for now in rrule(freq=WEEKLY, count=17, dtstart=now + timedelta(7), byweekday=TH):
        now = now.date()
        payday(ledger, now, D('16.0'), D('9'), 'IFD')
        bcm1(ledger, now)

    ledger.show_transactions()
    now += timedelta(14)
    print(now)
    ledger.show_balances()

    ledger = newledger(ledger, now)

    for now in rrule(freq=WEEKLY, count=21, dtstart=now + timedelta(14), byweekday=TH):
        now = now.date()
        payday(ledger, now, D('16.0'), D('9.00'), 'IFD')
        bcm1(ledger, now)

    # print(now)

    for now in rrule(freq=WEEKLY, count=13, dtstart=now + timedelta(7), byweekday=TH):
        now = now.date()
        payday(ledger, now, D('40.0'), D('10.00'), 'IFE')
        bcm1(ledger, now)

    now += timedelta(14)
    # print(now)
    # ledger.show_balances()
    then = now
    for now in rrule(freq=MONTHLY, count=24, dtstart=now):
        now = now.date()
        if now.year != then.year:
            ledger.show_balances()
            ledger = newledger(ledger, then)

            then = now
        paymission(ledger, now, D('450.00'))
    print(now)
    ledger.show_balances()

    ledger.show_transactions()

    #print(ledger.get_balance(ledger.get_account('allocated tithing')))



if __name__ == '__main__':
    test_simple()
