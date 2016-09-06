
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import DECIMAL
Base = declarative_base()

Money = DECIMAL(precision=8, scale=2)


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    rtn = Column(String(9))
    number = Column(String)
    accttype = Column(Integer)

    def __repr__(self):
        return '{}:{}:{}'.format(self.rtn, self.number, self.accttype)


class Statement(Base):
    __tablename__ = 'statements'

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    account = relationship("Account", back_populates="statements")
    start_date = Column(Date)
    end_date = Column(Date)
    balance = Column(Money)
    avail_balance = Column(Money)

Account.statements = relationship(
    "Statement", order_by=Statement.end_date, back_populates="account")


class Entry(Base):
    __tablename__ = 'entries'

    id = Column(Integer, primary_key=True)
    statement_id = Column(Integer, ForeignKey("statements.id"))
    statement = relationship("Statement", back_populates="entries")
    account_id = Column(Integer, ForeignKey("accounts.id"))
    account = relationship("Account", back_populates="entries")
    dtorigin = Column(Date)
    dtposted = Column(Date)
    trntype = Column(String)
    fitid = Column(String)
    amount = Column(Money)
    checkno = Column(Integer)
    name = Column(String)
    memo = Column(String)

Statement.entries = relationship(
    'Entry', order_by=Entry.fitid, back_populates="statement")
Account.entries = relationship(
    'Entry', order_by=Entry.fitid, back_populates="account")

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    seq = Column(Integer)
    entry_id = Column(Integer, ForeignKey("entries.id"))
#    entries = relationship("Entry", back_populates="transaction")

#Entry.transaction = relationship(
#    'Transaction', order_by=Transaction.seq, back_populates="transaction")
