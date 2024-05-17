'''positions'''

import os
import glob
import logging
import ctypes as CT
from ctypes import *
from importlib.resources import files

import click
import requests
import numpy as np
from PIL import Image, ExifTags
import fiona
from shapely.geometry import Point, mapping

from mavic_helper import __version__ as plugin_version


schema = {
    'geometry': 'Point',
    'properties': {
        'id': 'int',
        'lon': 'float',
        'lat': 'float',
        'hae': 'float',
        'utc': 'str',
        'file': 'str'
    },
}


@click.command()
@click.argument('src', nargs=1, type=click.Path(exists=True))
@click.argument('output', nargs=1, type=click.Path())
@click.option('-v', '--verbose', default=False, is_flag=True, help="Enables verbose mode")
@click.version_option(version=plugin_version, message='v%(version)s')
@click.pass_context
def positions(ctx, src, output, verbose):

    logger = logging.getLogger()

    if verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.ERROR)




    infiles = glob.glob(src+'/*_T.JPG')

    with fiona.open(
        output, 'w', driver='GeoJSON', crs=fiona.crs.from_epsg(4326), schema=schema
        ) as dst:

        with click.progressbar(
            length=len(infiles),
            label='Files done:') as bar:

            i = 0
            for f in infiles:

                # *** GET THE EXIF AND XMP DATA ***
                img_pillow = Image.open(f)
                exif = img_pillow.getexif()
                xmp = img_pillow.getxmp()

                # get decimal degree lat-lon from the xmp data
                xmp_desc = xmp['xmpmeta']['RDF']['Description']
                lat = xmp_desc['GpsLatitude']
                lon = xmp_desc['GpsLongitude']
                hae = float(xmp_desc['AbsoluteAltitude'])
                utc = xmp_desc['UTCAtExposure']
                rel = float(xmp_desc['RelativeAltitude'])

                logger.info(f'GPS Lon-Lat: {lon}, {lat}')
                print(f'GPS Lon-Lat: {lon}, {lat}; HAE: {hae}')

                geom = Point(lon, lat)
                dst.write({
                    'geometry': mapping(geom),
                    'properties': {
                        'id': i,
                        'lon': float(lon),
                        'lat': float(lat),
                        'hae': hae,
                        'utc': utc,
                        'file': os.path.basename(f)
                    }
                })
                img_pillow.close()

                i += 1
                bar.update(1)

        '''
        # get the distance param
        if altitude == 'hagl':
            try:
                # Get the GEOID height from NOAA
                noaa_url = 'https://geodesy.noaa.gov/api/geoid/ght'
                # noaa_res = requests.get(f'https://geodesy.noaa.gov/api/geoid/ght?lat={lat}&lon={lon}')
                noaa_res = requests.get(noaa_url, params={'lat': lat, 'lon': lon})
            except requests.exceptions.RequestException as e:
                logger.error('Unable to get NOAA GEOID API')
                raise SystemExit(e)

            try:
                # Get elevation from USGS Elevation Point Query Service: https://apps.nationalmap.gov/epqs/
                usgs_url = 'https://epqs.nationalmap.gov/v1/json'
                # usgs_res = requests.get(f'https://epqs.nationalmap.gov/v1/json?x={lon}&y={lat}&units=Meters&wkid=4326&includeDate=True')
                usgs_res = requests.get(usgs_url, params={'x':lon, 'y':lat, 'units':'Meters', 'wkid':4326, 'includeDate':True})
            except requests.exceptions.RequestException as e:
                logger.error('Unable to get USGS Point Elevation API')
                raise SystemExit(e)

            geoid_ht = float(noaa_res.json()['geoidHeight'])
            ortho_ht = float(usgs_res.json()['value'])

            distance = hae - geoid_ht - ortho_ht
                        
        '''