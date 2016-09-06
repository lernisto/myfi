import click
from money.cli import pass_context


@click.command('init', short_help='Initialize a money database.')
@pass_context
def cli(ctx):
    """Initialize a money database."""

    ctx.log('Initialized the database')
