
import datetime
from decimal import Decimal

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine('sqlite:///test.db', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

from models import Base, Account, Transaction, Statement
Base.metadata.create_all(engine)

if False:
    acct = Account(rtn='324377516', number='644930~1', accttype=1)
    session.add(acct)
    t1 = Transaction(account=acct, dtposted=datetime.date.today(),
                     trntype='debit', amount=Decimal("4.65"),
                     name="Ridley's", memo='donuts')
    session.commit()
