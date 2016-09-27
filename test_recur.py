# -*- coding: utf8 -*-

from dateutil.rrule import *
from dateutil.relativedelta import *
from datetime import date, datetime, timedelta

now = date(2015, 1, 1)
eop = datetime(now.year + 5, 1, 1)

sunday = rrule(WEEKLY, dtstart=now, byweekday=SU)
eomonth = rrule(MONTHLY, dtstart=now, bymonthday=(31, -1), bysetpos=1)


day = timedelta(1)
week = timedelta(7)

# DateSelect, Echo, Recurring, Ledger, ChartofAccounts, Mission, Tithing, D, Paycheck, bcm1, BCM,Savings
from simple import *

from f1040ez import f1040ez

coa = ChartofAccounts()
coa.load_csv('accounts.csv')


def giveaway(ledger, when):
    yesterday = when + relativedelta(days=-1)
    giving = ledger.get_account('allocated giving')
    giveto = ledger.get_account('temple patron')
    give = ledger.get_balance(giving)
    if give >ZERO:
        ledger.enter(yesterday,'empty giving envelope',
            Entry(now,None,giveto,True,give,None),
            Entry(now,None,giving,False,give,None),
            )

    living = ledger.get_account('allocated living')
    liveto = ledger.get_account('misc expenses')
    live = ledger.get_balance(living)
    if live >ZERO:
        ledger.enter(yesterday,'empty living envelope',
            Entry(now,None,liveto,True,live,None),
            Entry(now,None,living,False,live,None),
            )


def yearend(ledger, when):
    yesterday = when + relativedelta(days=-1)
    print("\nyear end: {}".format(yesterday.date()))

    balances = ledger.balances.copy()
    closing_entries(ledger, yesterday, 'year')
    f = f1040ez(ledger, balances, when + relativedelta(months=1))
    for k, v in sorted(f.items()):
        print('{:5} {:>10}'.format(k, v))

t1 = now
t2 = datetime(now.year, 6, 1) + relativedelta(days=1, weekday=TH)
t3 = t2 + week
t4 = datetime(now.year, 8, 31) + relativedelta(weekday=MO(-1))
t5 = t4 + week
t6 = datetime(now.year + 1, 6, 1) + relativedelta(days=1, weekday=TH)
t7 = t6 + week
t8 = datetime(now.year + 1, 8, 31) + relativedelta(weekday=MO(-1))
t9 = t8 + week
t10 = datetime(now.year + 1, 12, 31)
t11 = t10 + week
t12 = datetime(now.year + 2, 6, 1) + relativedelta(days=1, weekday=TH)
t13 = t12 + week
t14 = datetime(now.year + 2, 8, 31) + relativedelta(weekday=MO(-1))
t15 = t14 + week
t16 = t15 + relativedelta(years=2)

startofmonth = rrule(MONTHLY, dtstart=t1, bymonthday=1, until=eop)
startofyear = rrule(YEARLY, dtstart=t1 + relativedelta(years=1), until=eop)
ds = DateSelect([
    Paycheck(rrule(WEEKLY, dtstart=t1,
                   until=t2, byweekday=TH), "IFA", D('16.0'), D('7.25')),
    Paycheck(rrule(WEEKLY, dtstart=t3,
                   until=t4, byweekday=TH), "IFB", D('40.0'), D('8.00')),
    Paycheck(rrule(WEEKLY, dtstart=t5,
                   until=t6, byweekday=TH), "IFC", D('16.0'), D('8.50')),
    Paycheck(rrule(WEEKLY, dtstart=t7,
                   until=t8, byweekday=TH), "IFD", D('40.0'), D('9.00')),
    Paycheck(rrule(WEEKLY, dtstart=t9,
                   until=t10, byweekday=TH), "IFE", D('16.0'), D('9.00')),
    Paycheck(rrule(WEEKLY, dtstart=t11,
                   until=t12, byweekday=TH), "IFF", D('16.0'), D('9.50')),
    Paycheck(rrule(WEEKLY, dtstart=t13,
                   until=t14, byweekday=TH), "IFG", D('40.0'), D('12.50')),
    Mission(rrule(MONTHLY, dtstart=t15,
                  count=24), D('450.00')),
    Paycheck(rrule(WEEKLY, dtstart=t16,
                   until=eop, byweekday=TH), "IFF", D('40.0'), D('13.50')),
    Savings(startofmonth,
            coa.get('non-taxable interest'), coa.get('Roth IRA'), D('0.12') / 12
            ),
    Savings(startofmonth,
            coa.get('interest earned'), coa.get(
                'emergency fund'), D('0.0065') / 12
            ),
    Savings(startofmonth,
            coa.get('interest earned'), coa.get(
                'midterm fund'), D('0.0065') / 12
            ),
    BCM(rrule(WEEKLY, dtstart=t1, until=eop, byweekday=TH), bcm1),
    BCM(rrule(YEARLY, dtstart=t1 + relativedelta(years=1), until=t15), giveaway),
    BCM(startofyear, yearend),
])
ledger = Ledger(coa, None)
for v in ds.service_loop(ledger, eop):
    # print(v)
    pass
ledger.show_transactions()
ledger.show_balances()
