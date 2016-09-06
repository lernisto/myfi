import click
from money.cli import pass_context


@click.command('loadofx', short_help='Import OFX files.')
@click.argument('ofxfile', nargs=-1)
@pass_context
def cli(ctx, ofxfile):
    """Import OFX files."""
    from money.loadofx import loadofx
    loadofx(ctx.session, ofxfile)
