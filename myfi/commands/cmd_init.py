import click
from myfi.cli import pass_context


@click.command('init', short_help='Initialize a myfi database.')
@pass_context
def cli(ctx):
    """Initialize a myfi database."""
    from myfi.models import Base
    Base.metadata.create_all(ctx.dbengine)

    ctx.log('Initialized the database')
