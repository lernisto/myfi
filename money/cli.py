import os
import sys
import click

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

CONTEXT_SETTINGS = dict(auto_envvar_prefix='MONEY')

class Context:

    def __init__(self):
        self.verbose = False
        self.home = os.getcwd()

    def log(self, msg, *args, **kw):
        """Logs a message to stderr."""
        if args:
            msg = msg.format(*args)
        elif kw:
            msg = msg.format(**kw)
        click.echo(msg, file=sys.stderr)

    def vlog(self, msg, *args, **kw):
        """Logs a message to stderr only if verbose is enabled."""
        if self.verbose:
            self.log(msg, *args, **kw)


pass_context = click.make_pass_decorator(Context, ensure=True)
cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                          'commands'))


class ComplexCLI(click.MultiCommand):

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(cmd_folder):
            if filename.endswith('.py') and \
               filename.startswith('cmd_'):
                rv.append(filename[4:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            if sys.version_info[0] == 2:
                name = name.encode('ascii', 'replace')
            mod = __import__('money.commands.cmd_' + name,
                             None, None, ['cli'])
        except ImportError:
            return
        return mod.cli


@click.command(cls=ComplexCLI, context_settings=CONTEXT_SETTINGS)
@click.option('-v', '--verbose', is_flag=True,
              help='Enables verbose mode.')
@click.option('--database', '-d', default='test.db', metavar='DB',
              help='database file for storage')
@click.option('--new', is_flag=True, default=False,
              help='initialize the database')
@click.option('--echo', is_flag=True, default=False,
              help='echo SQL commands (very noisy)')
@pass_context
def cli(ctx, verbose, database, new, echo):

    ctx.dbengine = create_engine(
        'sqlite:///{}'.format(database), echo=echo)

    if new:
        from money.models import Base
        Base.metadata.create_all(ctx.dbengine)

    Session = sessionmaker(bind=ctx.dbengine)
    session = Session()
    ctx.session = session
