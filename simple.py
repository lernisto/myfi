# -*- coding: utf8 -*-

from __future__ import print_function, unicode_literals, division, absolute_import
from collections import namedtuple, OrderedDict

from decimal import Decimal as D

ZERO = D('0.00')
TITHE = D('0.1')
FICA = D('0.062')
MEDI = D('0.0145')
FICAMED = FICA + MEDI


class Account:
    DEBIT_BALANCE = True

    def __init__(self, name, number):
        self.name = name
        self.number = number

    def __str__(self):
        fmt = '{:>8} {}' if '.' in self.number else '{:>6}   {}'
        return fmt.format(self.number, self.name)

    def __repr__(self):
        return '<{} {}>'.format(self.number, self.name)


class AssetAccount(Account):
    pass


class LiabilityAccount(Account):
    DEBIT_BALANCE = False


class EquityAccount(Account):
    DEBIT_BALANCE = False


class RevenueAccount(Account):
    DEBIT_BALANCE = False


class ExpenseAccount(Account):
    pass

TYPEMAP = dict(A=AssetAccount,L=LiabilityAccount,Q=EquityAccount,R=RevenueAccount,E=ExpenseAccount,)

class ChartofAccounts:
    __slots__ = ('by_name', 'by_number')

    def __init__(self):
        self.by_name = {}
        self.by_number = {}

    def add(self, acct):
        self.by_name[acct.name] = acct
        self.by_number[acct.number] = acct

    def __iter__(self):
        l = list(self.by_number.items())
        l.sort()
        yield from [v for k, v in l]

    def load_csv(self,fname):
        with open(fname,'rt') as fi:
            import csv
            r = csv.reader(fi)
            for type,number,name in r:
                c = TYPEMAP.get(type)
                if c:
                    self.add(c(name,number))


class Entry:

    def __init__(self, dtorig, dtposted, account, debit, amount, memo):
        self.dtorig = dtorig
        self.dtposted = dtposted
        self.account = account
        self.debit = debit
        self.amount = amount
        self.memo = memo

    def __str__(self):
        memo = self.memo or ''
        amount = self.amount.quantize(ZERO)
        if self.debit:
            return '{:30} {:>10}                {}'.format(str(self.account), amount, memo)
        else:
            return '       {:30}        {:>10}  {}'.format(str(self.account), amount, memo)


class Transaction(namedtuple('Transaction', 'tid,dtposted,memo,entries')):

    def __str__(self):
        l = ['{1:10} {0:>4} {2}'.format(
            self.tid, self.dtposted.isoformat(), self.memo)]
        for e in self.entries:
            l.append(str(e))
        return '\n    '.join(l)


class Ledger:

    def __init__(self, coa, balances=None,):
        self.coa = coa
        self.transactions = []
        if balances is None:
            balances = {}
        self.opening = balances.copy()
        self.balances = balances

    def enter(self, dtorigin, memo, *entries):
        dr = cr = ZERO
        for e in entries:
            if e.debit:
                dr += e.amount
            else:
                cr += e.amount
        if dr != cr:
            raise ValueError('entries do not balance {}!={}'.format(dr, cr))

        tran = Transaction(len(self.transactions) + 1, dtorigin, memo, entries)

        self.transactions.append(tran)
        for e in tran.entries:
            acct = e.account
            bal = self.balances.get(acct, ZERO)
            if e.debit == acct.DEBIT_BALANCE:
                bal += e.amount
            else:
                bal -= e.amount
            self.balances[acct] = bal

    def get_account(self, name):
        return self.coa.by_name[name]

    def get_balance(self, acct):
        return self.balances.get(acct, ZERO)

    def show_transactions(self):
        for tran in self.transactions:
            print(tran)

    def show_balances(self):
        for acct in self.coa:
            bal = self.balances.get(acct)
            if bal is not None:
                print('{:30} {:>10}'.format(str(acct), bal.quantize(ZERO)))


def payday(ledger, now, hours, rate, source):
    gross = (hours * rate).quantize(ZERO)
    tithe = gross * TITHE
    fica = (gross * FICA).quantize(ZERO)
    medi = (gross * MEDI).quantize(ZERO)
    net = gross - fica - medi

    cash = ledger.get_account('cash')

    income = ledger.get_account('w-2 income')
    ttp = ledger.get_account('allocated tithing')
    ledger.enter(now, 'paycheck from {}'.format(source),
                 Entry(now, now, cash, True, net, 'net deposit'),
                 Entry(now, now, ledger.get_account('FICA'), True, fica,
                       'FICA payroll tax deducted'),
                 Entry(now, now, ledger.get_account('Medicare'), True, medi,
                       'Medicare payroll tax deducted'),
                 Entry(now, now, income, False, gross,
                       'gross pay: {} hours @ ${}'.format(hours, rate)),
                 )
    ledger.enter(now, 'reserve tithing',
                 Entry(now, now, ttp, True, tithe, None),
                 Entry(now, now, cash, False, tithe, None),
                 )
    return gross


def paytithing(ledger, now):
    ttp = ledger.get_account('allocated tithing')
    tp = ledger.get_account('tithing')
    amount = ledger.get_balance(ttp).quantize(ZERO)
    ledger.enter(now, 'pay thithing',
                 Entry(now, None, tp, True, amount, None),
                 Entry(now, None, ttp, False, amount, None),)
    return amount
