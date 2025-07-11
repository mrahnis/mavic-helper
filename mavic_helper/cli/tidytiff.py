'''transfer agisoft band mask to band data as nodata'''

import click
import numpy as np
import rasterio

from mavic_helper import __version__ as plugin_version


@click.command()
@click.argument('image', metavar='IMAGE', nargs=1, type=click.Path(exists=True))
@click.argument('output', nargs=1, type=click.Path())
@click.option('-n', '--nodata', default=None, help="Specify a nodata value; the default is minimum value float32.")
@click.option('-c', '--compress', type=click.Choice(['lzw','deflate','zstd']), default='lzw', help="Choice of compression method.")
@click.option('-v', '--verbose', default=False, is_flag=True, help="Enables verbose mode")
@click.version_option(version=plugin_version, message='v%(version)s')
@click.pass_context
def tidytiff(ctx, image, output, nodata, compress, verbose):
    '''Transfer band mask to nodata values

    Thermal orthomosaics may contain a mask in Band 2.
    This command transfers the mask to Band 1 as nodata values. 
    '''

    with rasterio.open(image) as src:
        data = src.read(1)
        mask = src.read(2)

        profile = src.profile

        dtype = profile['dtype']

        # determine nodata
        if nodata is None:
            if dtype == 'float32':
                nodata = np.finfo(np.float32).min
            elif dtype == 'int16':
                nodata = np.finfo(np.int16).min
        else:
            pass

        # determine compression predictor
        if dtype == 'float32':
            predictor = 3
        elif dtype == 'int16':
            predictor = 2
        else:
            predictor = 1

        # update profile with keyword options
        profile.update(
                count=1,
                nodata=nodata,
                compress=compress,
                predictor=predictor,
                bigtiff='YES')

        # transfer the mask to nodata values
        result = np.where((mask == 0), nodata, data)

        with rasterio.open(output, 'w', **profile) as dst:
            w, s, e, n = src.bounds
            window = rasterio.windows.from_bounds(w, s, e, n, transform=src.transform)
            dst.write(result.astype(profile['dtype']), 1, window=window)

