# -*- coding: utf8 -*-

import datetime
from dateutil.rrule import *

from simple import *



def test_simple():
    coa = ChartofAccounts()
    coa.load_csv('accounts.csv')
    if False:
        for acct in (
            AssetAccount('checking', '1011'),
            AssetAccount('allocated tithing', '1011.1'),

            RevenueAccount('income', '3011'),

            ExpenseAccount('tithing', '5011'),

            ExpenseAccount('taxes', '5021'),
            ExpenseAccount('FICA', '5021.1'),
            ExpenseAccount('medicare', '5021.2'),
            ExpenseAccount('FIT', '5021.3'),

        ):
            coa.add(acct)

    ledger = Ledger(coa)



    now = datetime.date(2015,1,1)
    for w in range(4):
        payday(ledger, now, D('16.0'), D('7.25'), 'IFA')
        paytithing(ledger,now)
        now += datetime.timedelta(7)

    ledger.show_transactions()

    ledger.show_balances()

    print(ledger.get_balance(ledger.get_account('allocated tithing')))

if __name__ == '__main__':
    test_simple()
