# -*- coding: utf8 -*-

from __future__ import print_function, unicode_literals, division, absolute_import
from collections import namedtuple, OrderedDict

from decimal import Decimal as D

ZERO = D('0.00')
TITHE = D('0.1')
FICA = D('0.062')
MEDI = D('0.0145')
FICAMED = FICA + MEDI


def counter(x=0):
    while True:
        x += 1
        yield x


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


TYPEMAP = dict(A=AssetAccount, L=LiabilityAccount,
               Q=EquityAccount, R=RevenueAccount, E=ExpenseAccount,)


class ChartofAccounts:
    __slots__ = ('by_name', 'by_number')

    def __init__(self):
        self.by_name = {}
        self.by_number = {}

    def add(self, acct):
        self.by_name[acct.name] = acct
        self.by_number[acct.number] = acct

    def get(self, key, default=None):
        return self.by_name.get(key) or self.by_number.get(key, default)

    def __iter__(self):
        l = list(self.by_number.items())
        l.sort()
        yield from [v for k, v in l]

    def load_csv(self, fname):
        with open(fname, 'rt') as fi:
            import csv
            r = csv.reader(fi)
            for type, number, name in r:
                c = TYPEMAP.get(type)
                if c:
                    self.add(c(name, number))


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
    _nextid = iter(counter()).__next__

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

        tran = Transaction(self._nextid(), dtorigin, memo, entries)
        self.apply(tran)
        return tran

    def apply(self, tran):

        self.transactions.append(tran)
        for e in tran.entries:
            acct = e.account
            bal = self.balances.get(acct, ZERO)
            if e.debit == acct.DEBIT_BALANCE:
                bal += e.amount
            else:
                bal -= e.amount
            self.balances[acct] = bal

    def get_account(self, key):
        return self.coa.get(key)

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
        if self.transactions:
            print('balances as of {}'.format(self.transactions[-1].dtposted))


def closing_entries(ledger, now):
    bal = ledger.balances
    coa = ledger.coa
    income = []
    expense = []

    incomesummary = ledger.get_account('equity')

    for acct, val in bal.items():
        if isinstance(acct, RevenueAccount):
            income.append((acct, val))
        elif isinstance(acct, ExpenseAccount):
            expense.append((acct, val))

    ie = []
    rsummary = ZERO
    for acct, val in income:
        ie.append(Entry(now, now, acct, True, val, None))
        rsummary += val
    if ie:
        ie.append(Entry(now, now, incomesummary, False, rsummary, None))
        ledger.enter(now, 'close revenue accounts', *ie)

    ee = []
    esummary = ZERO
    for acct, val in expense:
        ee.append(Entry(now, now, acct, False, val, None))
        esummary += val
    if ee:
        ee.insert(0, Entry(now, now, incomesummary, True, esummary, None))
        ledger.enter(now, 'close expense accounts', *ee)

    print('\nIncome Summary for {} to {}'.format(
        ledger.transactions[0].dtposted, ledger.transactions[-1].dtposted))
    print('Income')
    for acct, v in income:
        print('{} {}'.format(str(acct), v))
    print('Expenses')
    for acct, v in expense:
        print('{} {}'.format(str(acct), v))

    ni = rsummary - esummary
    if ni >= ZERO:
        print('Net income: {}'.format(ni))
    else:
        print('Net loss: ({})'.format(-ni))


def balance_forward(balances):
    balfwd = {}
    for k, v in balances.items():
        # no need to check: isinstance(k, (AssetAccount, LiabilityAccount,
        # EquityAccount))
        if v != ZERO:
            balfwd[k] = v
    return balfwd

import heapq


class DateSelect:

    def __init__(self, recurring):
        self.pending = pending = []
        for r in recurring:
            try:
                rnext = next(r)
                pending.append((rnext, r))
            except StopIteration:
                pass

        heapq.heapify(pending)

    def earliest(self):
        if self.pending:
            return self.pending[0][0]

    def earliest_before(self, when):
        if self.pending:
            e = self.pending[0][0]
            return e if e < when else None

    def add(self, r):
        try:
            rnext = next(r)
            heapq.heappush(self.pending, (rnext, r))
        except StopIteration:
            pass

    def service_loop(self, ledger, until):
        pending = self.pending
        while len(pending) > 0:
            when, what = pending[0]
            if when > until:
                break
            try:
                v = what.service(ledger, when)
                yield v, what, when
            except Exception as e:
                yield e, what, when
            try:
                when = next(what)
                heapq.heapreplace(pending, (when, what))
            except StopIteration:
                heapq.heappop(pending)


class Recurring:
    nextid = iter(counter()).__next__

    def __init__(self, recur):
        self.order = self.nextid()
        self.it = iter(recur)

    def __next__(self):
        return next(self.it)

    def __lt__(self, other):
        return self.order < other.order

    def service(self, ledger, when):
        raise NotImplemented()


class Echo(Recurring):

    def __init__(self, recur, fmt):
        super(Echo, self).__init__(recur)
        self.fmt = fmt

    def service(self, ledger, when):
        print(self.fmt.format(ledger, when))


class BCM(Recurring):

    def __init__(self, recur, service):
        super(BCM, self).__init__(recur)
        self._service = service

    def service(self, ledger, when):
        return self._service(ledger, when)


class Mission(Recurring):

    def __init__(self, recur, amount):
        super(Mission, self).__init__(recur)
        self.amount = amount

    def service(self, ledger, when):
        source = ledger.get_account('midterm fund')
        destination = ledger.get_account('missionary')
        t = ledger.enter(when, 'pay mission fund',
                         Entry(when, None, destination,
                               True, self.amount, None),
                         Entry(when, None, source, False, self.amount, None),)
        return t


class Tithing(Recurring):

    def service(self, ledger, when):
        return paytithing(ledger, when)


class DedicatedSavings(Recurring):

    def __init__(self, src, acct, term, rate, amount):
        self.acct = acct
        self.term = term
        self.rate = rate
        self.amount = amount
        self.transactions = []
        super(DedicatedSavings, self).__init__(
            rrule(MONTHLY, dtstart=now, count=term))

    def add(self, ledger, now, source, amount):
        self.transactions.append(
            ledger.enter(self.start, 'transfer to dedicated savings',
                         Entry(now, None, self.acct, True, amount, None),
                         Entry(now, None, source, False, amount, None)
                         ))

    def service(self, ledger, now):
        self.add(ledger, now, self.src, self.amount)


class Paycheck(Recurring):

    def __init__(self, recur, name, hours, rate):
        super(Paycheck, self).__init__(recur)
        self.name = name
        self.hours = hours
        self.rate = rate

    def service(self, ledger, when):
        return payday(ledger, when, self.hours, self.rate, self.name)


def payday(ledger, now, hours, rate, source):
    gross = (hours * rate).quantize(ZERO)
    tithe = gross * TITHE
    fit = (gross * TITHE).quantize(ZERO)  # XXX too simple
    fica = (gross * FICA).quantize(ZERO)
    medi = (gross * MEDI).quantize(ZERO)
    net = gross - fica - medi - fit

    cash = ledger.get_account('cash')

    income = ledger.get_account('w-2 income')
    ttp = ledger.get_account('allocated tithing')
    ledger.enter(now, 'paycheck from {}'.format(source),
                 Entry(now, now, cash, True, net, 'net deposit'),
                 Entry(now, now, ledger.get_account('Federal Income Tax'), True, fit,
                       'Federal income tax deducted'),
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

    giving = tithe / 2
    ledger.enter(now, 'reserve other giving',
                 Entry(now, now, ledger.get_account(
                     'allocated giving'), True, giving, None),
                 Entry(now, now, cash, False, giving, None),
                 )
    saving = tithe + giving
    ledger.enter(now, 'reserve saving',
                 Entry(now, now, ledger.get_account(
                     'allocated saving'), True, saving, None),
                 Entry(now, now, cash, False, saving, None),
                 )

    return gross


def paytithing(ledger, now):
    ttp = ledger.get_account('allocated tithing')
    tp = ledger.get_account('tithing')
    amount = ledger.get_balance(ttp).quantize(ZERO)
    if amount > ZERO:
        t = ledger.enter(now, 'pay thithing',
                         Entry(now, None, tp, True, amount, None),
                         Entry(now, None, ttp, False, amount, None),)
        return t


def paymission(ledger, now, amount):
    source = ledger.get_account('midterm fund')
    destination = ledger.get_account('missionary')
    t = ledger.enter(now, 'pay mission fund',
                     Entry(now, None, destination, True, amount, None),
                     Entry(now, None, source, False, amount, None),)
    return t


def bcm1(ledger, now):
    paytithing(ledger, now)
    efund = ledger.get_account('emergency fund')
    ebal = ledger.get_balance(efund)
    cash = ledger.get_account('cash')
    cashbal = ledger.get_balance(cash)
    eneed = D('500.00') - ebal
    if eneed > ZERO:
        have = cashbal - eneed
        eadd = cashbal if have < ZERO else eneed

        ledger.enter(now, 'transfer to emergency fund',
                     Entry(now, None, efund, True, eadd, None),
                     Entry(now, None, cash, False, eadd, None),
                     )
        cashbal -= eadd

    if cashbal > ZERO:
        lfund = ledger.get_account('allocated living')
        lneed = cashbal * D('0.03')  # 3 percent of disposable income

        if lneed > ZERO:
            ledger.enter(now, 'allocate for living expenses',
                         Entry(now, None, lfund, True, lneed, None),
                         Entry(now, None, cash, False, lneed, None),
                         )
            cashbal -= lneed
        # sweep everything else into midterm savings
        mfund = ledger.get_account('midterm fund')
        ledger.enter(now, 'save for mission',
                     Entry(now, None, mfund, True, cashbal, None),
                     Entry(now, None, cash, False, cashbal, None),
                     )

    # sweep 15% saving into Roth IRA
    save = ledger.get_account('allocated saving')
    savebal = ledger.get_balance(save)
    if savebal > ZERO:
        rfund = ledger.get_account('Roth IRA')
        ledger.enter(now, 'save for retirement',
                     Entry(now, None, rfund, True, savebal, None),
                     Entry(now, None, save, False, savebal, None),
                     )
