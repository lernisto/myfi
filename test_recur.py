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

from simple import DateSelect, Echo, Recurring, Ledger, ChartofAccounts, Mission, Tithing, D, Paycheck, bcm1, BCM
coa = ChartofAccounts()
coa.load_csv('accounts.csv')

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
    BCM(rrule(WEEKLY, dtstart=t1, until=eop, byweekday=TH), bcm1),
    Echo(eomonth, "{1} end of month")
])
ledger = Ledger(coa, None)
for v in ds.service_loop(ledger, eop):
    # print(v)
    pass
ledger.show_transactions()
ledger.show_balances()
