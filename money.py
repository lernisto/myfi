import click

from ofxparse import OfxParser

import datetime
from decimal import Decimal

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Account, Entry, Statement

ZERO = Decimal('0.00')


@click.group()
@click.option('--database', '-d', default='test.db',metavar='DB',help='database file for storage')
@click.option('--new', is_flag=True, default=False,help='initialize the database')
@click.option('--echo', is_flag=True, default=False,help='echo SQL commands (very noisy)')
@click.pass_context
def main(ctx,database,new,echo):
    engine = create_engine('sqlite:///{}'.format(database), echo=echo)

    if new:
        from models import Base
        Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    ctx.obj = session

@main.command()
@click.pass_obj
@click.argument('src', nargs=-1, metavar='<ofxfile>...')
def loadofx(session, src):
    """Import OFX files into the database.
    """
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
