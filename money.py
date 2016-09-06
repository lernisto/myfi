import click
from bs4 import BeautifulSoup
from ofxparse import OfxParser


import datetime
from decimal import Decimal

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Account, Entry, Statement

ZERO = Decimal('0.00')


@click.command()
@click.argument('dest', nargs=1)
@click.argument('src', nargs=-1)
def main(dest, src):
    engine = create_engine('sqlite:///{}'.format(dest), echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    for fname in src:
        with open(fname, 'rb') as fi:
            o = OfxParser.parse(fi)
        a = o.account
        account = Account(rtn=a.routing_number,
                          number=a.number, accttype=a.type)
        # TODO: look up the account

        st = a.statement
        statement = Statement(
            account=account,
            balance=st.balance,
            avail_balance=st.available_balance,
            start_date=st.start_date,
            end_date=st.end_date,
        )

        for tran in st.transactions:

            if tran.memo.startswith(tran.payee):
                name = tran.memo.lower()
                memo = None
            elif tran.memo:
                if tran.id.endswith("INT"):
                    name = tran.payee.lower()
                    memo = tran.memo.lower()
                else:
                    print('{}|{}|{}'.format(tran.id, tran.payee, tran.memo))
            else:
                memo = tran.payee.lower()
                name = None
            entry = Entry(
                account=account,
                statement=statement,
                dtposted=tran.date.date(),
                fitid=tran.id,
                trntype=tran.type.lower(),
                checkno=tran.checknum,
                amount=Decimal(tran.amount).quantize(ZERO),
                name=name,
                memo=memo,
            )

        session.add(account)
        session.commit()

if __name__ == '__main__':
    main()
