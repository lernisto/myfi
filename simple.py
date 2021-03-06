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


def Debit(dtorig, account, amount, memo=None):
    return Entry(dtorig, None, account, True, amount, memo)


def Credit(dtorig, account, amount, memo=None):
    return Entry(dtorig, None, account, False, amount, memo)


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


def bynumber(pair):
    return pair[0].number


def closing_entries(ledger, now, period='year'):
    now = now.date()
    bal = ledger.balances
    coa = ledger.coa

    income = []
    expense = []

    incomesummary = ledger.get_account('equity')

    for acct, val in bal.items():
        if isinstance(acct, RevenueAccount):
            income.append((acct, val.quantize(ZERO)))
        elif isinstance(acct, ExpenseAccount):
            expense.append((acct, val.quantize(ZERO)))
    income.sort(key=bynumber)
    expense.sort(key=bynumber)

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

    print('\nIncome Summary for {} ending {}'.format(period, now))
    print('Income')
    for acct, v in income:
        print('{:30} {:>10}'.format(str(acct), v.quantize(ZERO)))
    print('total income:                             {:>10}'.format(rsummary))
    print('Expenses')
    for acct, v in expense:
        print('{:30} {:>10}'.format(str(acct), v.quantize(ZERO)))
    print('total expenses:                           {:>10}'.format(esummary))

    ni = (rsummary - esummary).quantize(ZERO)
    if ni >= ZERO:
        print('Net income:                               {:>10}'.format(ni))
    else:
        print('Net loss:                                ({:>10})'.format(-ni))

    print('\nBalance Sheet as of {}'.format(now))
    asset = []
    liability = []
    equity = []
    for acct, val in bal.items():
        if isinstance(acct, AssetAccount):
            asset.append((acct, val.quantize(ZERO)))
        elif isinstance(acct, LiabilityAccount):
            liability.append((acct, val.quantize(ZERO)))
        elif isinstance(acct, EquityAccount):
            equity.append((acct, val.quantize(ZERO)))

    asset.sort(key=bynumber)
    acc1 = ZERO
    for acct, v in asset:
        acc1 += v
        print('{:30} {:>10}'.format(str(acct), v))
    print('  total assets:                           {:>10}\n'.format(acc1))

    liability.sort(key=bynumber)
    acc2 = ZERO
    for acct, v in liability:
        acc2 += v
        print('{:30} {:>10}'.format(str(acct), v))
    print('  total liabilities:                      {:>10}\n'.format(acc2))

    equity.sort(key=bynumber)
    acc3 = ZERO
    for acct, v in equity:
        acc3 += v
        print('{:30} {:>10}'.format(str(acct), v))
    print('  total equity:                           {:>10}\n'.format(acc3))

    print(
        '  total liabilities+equity:               {:>10}\n'.format(acc2 + acc3))


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
            # try:
            v = what.service(ledger, when)
            yield v, what, when
            # except Exception as e:
            #    yield e, what, when
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
                         Debit(when, destination, self.amount),
                         Credit(when, source, self.amount),)
        return t


class Tithing(Recurring):

    def service(self, ledger, when):
        return paytithing(ledger, when)


class Savings(Recurring):

    def __init__(self, recur, src, dest, rate):
        super(Savings, self).__init__(recur)
        self.src = src
        self.dest = dest
        self.rate = rate
        self.pbal = ZERO
        self.transactions = []

    def add(self, ledger, now, source, amount):
        if amount > ZERO:
            self.transactions.append(
                ledger.enter(self.start, 'transfer to savings',
                             Debit(now, self.dest, amount),
                             Credit(now, source, amount)
                             ))

    def service(self, ledger, now):
        # print(now,self.pbal,ledger.get_balance(self.dest))
        intr = (self.rate * self.pbal).quantize(ZERO)  # conservative estimate
        if intr > ZERO:
            self.transactions.append(
                ledger.enter(now, 'interest received',
                             Debit(now, self.dest, intr),
                             Credit(now, self.src, intr)
                             ))

        self.pbal = ledger.get_balance(self.dest)


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
                         Debit(now, tp, amount),
                         Credit(now, ttp, amount),)
        return t


def paymission(ledger, now, amount):
    source = ledger.get_account('midterm fund')
    destination = ledger.get_account('missionary')
    t = ledger.enter(now, 'pay mission fund',
                     Debit(now, destination, amount),
                     Credit(now, source, amount),)
    return t


def bcm1(ledger, now, efundlevel=D('500.00')):
    paytithing(ledger, now)
    efund = ledger.get_account('emergency fund')
    ebal = ledger.get_balance(efund)
    cash = ledger.get_account('cash')
    cashbal = ledger.get_balance(cash)
    save = ledger.get_account('allocated saving')
    savebal = ledger.get_balance(save)
    eneed = efundlevel - ebal
    if eneed > ZERO:
        if eneed > savebal:
            if cashbal > ZERO:
                avail = cashbal + savebal
                if avail < eneed:
                    ee = [
                        Debit(now, efund, avail),
                        Credit(now, save, savebal),
                        Credit(now, cash, cashbal),
                    ]
                    savebal = cashbal = ZERO
                else:
                    sc = eneed - savebal
                    ee = [
                        Debit(now, efund, eneed),
                        Credit(now, save, savebal),
                        Credit(now, cash, sc),
                    ]
                    savebal = ZERO
                    cashbal -= sc
            else:
                ee = [
                    Debit(now, efund, savebal),
                    Credit(now, save, savebal),
                ]
                savebal = ZERO
        else:
            ee = [
                Debit(now, efund, eneed),
                Credit(now, save, eneed),
            ]
            savebal -= eneed

        ledger.enter(now, 'transfer to emergency fund', *ee)

    if cashbal > ZERO:
        lfund = ledger.get_account('allocated living')
        lneed = cashbal * D('0.03')  # 3 percent of disposable income

        if lneed > ZERO:
            ledger.enter(now, 'allocate for living expenses',
                         Debit(now, lfund, lneed),
                         Credit(now, cash, lneed),
                         )
            cashbal -= lneed
        # sweep everything else into midterm savings
        mfund = ledger.get_account('midterm fund')
        ledger.enter(now, 'save for mission',
                     Debit(now, mfund, cashbal),
                     Credit(now, cash, cashbal),
                     )

    # sweep 15% saving into Roth IRA
    save = ledger.get_account('allocated saving')
    savebal = ledger.get_balance(save)
    if savebal > ZERO:
        rfund = ledger.get_account('Roth IRA')
        ledger.enter(now, 'save for retirement',
                     Debit(now, rfund, savebal),
                     Credit(now, save, savebal),
                     )
