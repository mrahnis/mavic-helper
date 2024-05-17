import sys
import logging
from pkg_resources import iter_entry_points

import click
from click_plugins import with_plugins

import mavic_helper


logger = logging.getLogger(__name__)

@with_plugins(
    ep for ep in list(iter_entry_points("mavic_helper.mav_commands")) + list(iter_entry_points("mavic_helper.mav_plugins"))
)
@click.group()
@click.option('-v', '--verbose', default=False, is_flag=True, help="Enables verbose mode")
@click.version_option(version=mavic_helper.__version__, message='v%(version)s')
@click.pass_context
def cli(ctx, verbose):
    ctx.obj = {}
    ctx.obj['verbose'] = verbose
    if verbose:
        logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    else:
        logging.basicConfig(stream=sys.stderr, level=logging.ERROR)


if __name__ == "__main__":
    cli()