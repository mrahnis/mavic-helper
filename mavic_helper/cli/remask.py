'''transfer agisoft band mask to band data as nodata'''

import click
import numpy as np
import rasterio

from mavic_helper import __version__ as plugin_version


@click.command()
@click.argument('image', metavar='IMAGE', nargs=1, type=click.Path(exists=True))
@click.argument('output', nargs=1, type=click.Path())
@click.option('-v', '--verbose', default=False, is_flag=True, help="Enables verbose mode")
@click.version_option(version=plugin_version, message='v%(version)s')
@click.pass_context
def remask(ctx, image, output, verbose):
    '''Transfer band mask to nodata values

    Thermal orthomosaics may contain a mask in Band 2. This command transfers the mask to Band 1 as nodata values. 
    '''
    nodata = np.finfo(np.float32).min

    with rasterio.open(image) as src:
        data = src.read(1)
        mask = src.read(2)
        result = np.where((mask == 0), nodata, data)

        profile = src.profile
        profile.update(
                dtype=rasterio.float32,
                nodata=nodata,
                count=1,
                compress='lzw',
                bigtiff='YES')

        with rasterio.open(output, 'w', **profile) as dst:
            w, s, e, n = src.bounds
            window = rasterio.windows.from_bounds(w, s, e, n, transform=src.transform)
            dst.write(result.astype(profile['dtype']), 1, window=window)

