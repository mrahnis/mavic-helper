'''campos'''

import os
import glob
import logging
import ctypes as CT
from ctypes import *
from importlib.resources import files

import click
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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
        'utc': 'str'
    },
}


@click.command()
@click.argument('src', nargs=1, type=click.Path(exists=True))
@click.argument('output', nargs=1, type=click.Path())
@click.option('-v', '--verbose', default=False, is_flag=True, help="Enables verbose mode")
@click.version_option(version=plugin_version, message='v%(version)s')
@click.pass_context
def shade(ctx, src, output, verbose):

    logger = logging.getLogger()

    if verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.ERROR)




    infiles = glob.glob(src+'/*_T.JPG')

    with click.progressbar(
        length=len(infiles),
        label='Files done:') as bar:

        val_arr = []
        idx_arr = []

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
            ral = float(xmp_desc['RelativeAltitude'])

            logger.info(f'GPS Lon-Lat: {lon}, {lat}')

            arr = bytearray()
            for x in range(3, 14):
                arr.extend(img_pillow.applist[x][1])

            # create image from bytes
            tim = Image.frombytes('I;16L', (640, 512), arr)
            temps = np.array(tim)

            #val_arr.append([np.datetime64(utc), temps.mean(), temps.min(), temps.max()])
            val_arr.append([temps.mean(), temps.min(), temps.max(), np.quantile(temps,0.05), np.quantile(temps,0.95)])
            idx_arr.append(utc)

            img_pillow.close()

            i += 1
            bar.update(1)


        #val_df = pd.DataFrame(val_arr, columns=['datetime','mean','min','max'])
        val_df = pd.DataFrame(val_arr, index=pd.to_datetime(idx_arr, utc=True), columns=['mean','min','max','q05','q95'])
        print('')
        print(val_df.head())

        fig, ax = plt.subplots()
        #val_df['mean'].plot(ax=ax, label='mean')
        #val_df['min'].plot(ax=ax, c='gray', label='min')
        #val_df['max'].plot(ax=ax, c='gray', label='max')
        ax.plot(x=val_df.index, y=val_df['mean'], marker='.', linestyle='none', label='mean')
        ax.plot(x=val_df.index, y=val_df['q05'], marker='.', linestyle='none', c='blue', label='q05')
        ax.plot(x=val_df.index, y=val_df['q95'], marker='.', linestyle='none', c='blue', label='q95')
        ax.plot(x=val_df.index, y=val_df['min'], marker='.', linestyle='none', c='gray', label='min')
        ax.plot(x=val_df.index, y=val_df['max'], marker='.', linestyle='none', c='gray', label='max')
        plt.show()
