import click
from ofxparse import OfxParser

from bs4 import BeautifulSoup
import csv

@click.command()
@click.argument('dest',nargs=1)
@click.argument('src',nargs=-1)
def main(dest,src):
    ids = {}
    with open(dest,"wt") as fo:
        w = csv.writer(fo)
        for fname in src:
            with open(fname,'rb') as fi:
                o = OfxParser.parse(fi)
            a = o.account
            acctid = '{}:{}:{}'.format(a.routing_number,a.number,a.type)
            aid = ids.get(acctid)
            if aid is None:
                aid = len(ids)+1
                ids[acctid]= aid

            st = a.statement
            w.writerow((st.end_date,acctid,"balance",st.start_date,st.balance,st.available_balance))
            print(acctid,len(st.transactions))
            for tran in st.transactions:
                if tran.memo.startswith(tran.payee):
                    memo = tran.memo.lower()
                elif tran.memo:
                    if tran.id.endswith("INT"):
                        memo = tran.memo.lower()#('{1} ({0})'.format(tran.payee,tran.memo)).lower()
                    else:
                        print('{}|{}|{}'.format(tran.id,tran.payee,tran.memo))
                else:
                    memo = tran.payee.lower()
                w.writerow((tran.date.date(),aid,tran.id,tran.type,tran.checknum,tran.amount,memo))

    for k,v in ids.items():
        print(v,k)

if __name__=='__main__':
    main()
