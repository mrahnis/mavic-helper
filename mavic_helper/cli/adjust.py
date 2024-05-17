'''sample control points from an image'''

import logging

import click
import numpy as np
import rasterio
from shapely.geometry import Point, mapping

from mavic_helper import __version__ as plugin_version


schema = {
    'geometry': 'Point',
    'properties': {
        'id': 'int',
        'name':
        'intensity': 'float'
    },
}


@click.command()
@click.argument('image', metavar='IMAGE', nargs=1, type=click.Path(exists=True))
@click.argument('control', metavar='CONTROL', nargs=1, type=click.Path(exists=True))
@click.argument('output', nargs=1, type=click.Path())
@click.option('-v', '--verbose', default=False, is_flag=True, help="Enables verbose mode")
@click.version_option(version=plugin_version, message='v%(version)s')
@click.pass_context
def adjust(ctx, image, control, output, verbose):
    """
    Take an image and sensor locations. Output sensor locations with the image intensity added.

    Need to get image time (from seamlines or positions) for lookup in a sensor timeseries 
    """
    with rasterio.open(image) as src:
        data = src.read()
        with fiona.open(control) as ctlsrc:
            with fiona.open(output, 'w', driver=driver, crs=ctlsrc.crs, schema=schema) as dst:
                for feature in ctlsrc:
                    try:
                        coords = feature['geometry']['coordinates']
                        intensity = src.sample(coords, indexes=src.indexes)

                        dst.write({
                            'geometry': mapping(feature['geometry']),
                            'properties': feature['properties'],
                            'intensity': intensity
                        })
                    except Exception:
                        logging.exception("Error processing feature %s:", feature['id'])                    dst.write({
                        })
