import os
import logging
import ctypes as CT
from ctypes import *
from importlib.resources import files

import click
import requests
import numpy as np
from PIL import Image, ExifTags
from pyproj import CRS, Transformer
import matplotlib.pyplot as plt

from dji_thermal_sdk.dji_sdk import *
from dji_thermal_sdk.utility import rjpeg_to_heatmap

from mavic_helper import __version__ as plugin_version


@click.command()
@click.argument('rjpeg', nargs=1, type=click.Path(exists=True))
@click.argument('output', nargs=1, type=click.Path())
@click.option('--distance', nargs=1, type=click.FLOAT, help="Object distance")
@click.option('--emissivity', nargs=1, type=click.FLOAT, help="Object emissivity")
@click.option('--temperature', nargs=1, type=click.FLOAT, help="Ambient temperature")
@click.option('--humidity', nargs=1, type=click.FLOAT, help="Relative humidity")
@click.option('--altitude', 'altitude', type=click.Choice(['hagl', 'relative', 'existing']), default='existing',
              help="Calculate HAGL from USGS Elevation API, else use DJI relative altitude for Object Distance")
@click.option('--dtype', 'dtype', type=click.Choice(['float32', 'int16', 'uint16']), default='float32', help="Image data type")
@click.option('-v', '--verbose', default=False, is_flag=True, help="Enables verbose mode")
@click.version_option(version=plugin_version, message='v%(version)s')
@click.pass_context
def totiff(ctx, rjpeg, output, distance, emissivity, temperature, humidity, altitude, dtype, verbose):
    '''Convert Mavic RJPEG to TIFF containing temperature values.

    '''
    logger = logging.getLogger()

    if verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.ERROR)

    libdirp_path = files('mavic_helper.dji_sdk').joinpath('libdirp.dll') 
    dji_init(libdirp_path)

    # GpsAltitudeRef = b'\x00' is supposed to mean above sea level (GpsAltitudeRef = b'\x00' is below sea) but seems not reliable

    # if AltitudeType = 'RtkAlt'
    from_crs = CRS.from_epsg('4979')         # WGS84+ellipsoidal height
    # if AltitudeType = 'GpsFusionAlt'
    #   keep as-is and call it NAVD88?

    to_crs = CRS.from_epsg('6318+5703')      # NAD2011+NAVD88 height
    transformer = Transformer.from_crs(from_crs, to_crs)

    # *** GET THE EXIF AND XMP DATA ***
    img_pillow = Image.open(rjpeg)
    exif = img_pillow.getexif()
    xmp = img_pillow.getxmp()

    # get decimal degree lat-lon from the xmp data
    xmp_desc = xmp['xmpmeta']['RDF']['Description']

    lat = xmp_desc['GpsLatitude']
    lon = xmp_desc['GpsLongitude']
    alt = float(xmp_desc['AbsoluteAltitude'])
    relative_alt = float(xmp_desc['RelativeAltitude'])
    alt_type = xmp_desc['AltitudeType']

    # get the XMP bytestring for transfer to the TIFF
    xmp_str = img_pillow.app['APP1']
    marker, xmp_tags = xmp_str.split(b"\x00")[:2]
    if marker == b"http://ns.adobe.com/xap/1.0/":
        logger.info('XMP is present')
    else:
        logger.info('XMP is absent')

    logger.info(f'GPS Position :: Lon-Lat: {lon}, {lat}; Alt: {alt}, {alt_type}')

    img_pillow.close()

    # get the distance param
    if altitude == 'hagl':

        _, _, cam_ht = transformer.transform(lat, lon, alt)

        try:
            # Get elevation from USGS Elevation Point Query Service: https://apps.nationalmap.gov/epqs/
            usgs_url = 'https://epqs.nationalmap.gov/v1/json'
            # usgs_res = requests.get(f'https://epqs.nationalmap.gov/v1/json?x={lon}&y={lat}&units=Meters&wkid=4326&includeDate=True')
            usgs_res = requests.get(usgs_url, params={'x':lon, 'y':lat, 'units':'Meters', 'wkid':4326, 'includeDate':True})
        except requests.exceptions.RequestException as e:
            logger.error('Unable to get USGS Point Elevation API')
            raise SystemExit(e)

        gnd_ht = float(usgs_res.json()['value'])
        distance = cam_ht - gnd_ht

        logger.info(f'GPS Altitude (HAE): {alt}, DJI Relative Altitude: {relative_alt}')
        logger.info(f'GPS NAVD88 Height: {cam_ht:.3f}, Ground Height: {gnd_ht:.3f}, GPS HAGL: {distance:.3f}')
    elif altitude == 'relative':
        distance = relative_alt
        logger.info(f'GPS Altitude (HAE): {alt}, GPS RelativeAltitude: {relative_alt}')
    else:
        distance = None

    # *** CONVERT TO TEMPERATURES USING DJI THERMAL SDK ***
    with open(rjpeg, 'rb') as f:
        content = f.read()

    rjpeg_data = CT.create_string_buffer(len(content))
    rjpeg_data.value = content

    # create an image handle
    ret = dirp_create_from_rjpeg(rjpeg_data, len(content), CT.byref(DIRP_HANDLE))
    if ret != 0:
        logger.error(f'Failed at dirp_create_from_rjpeg(): ret = {ret}')

    # get the existing measurement params from the image
    meas_params = dirp_measurement_params_t()
    ret = dirp_get_measurement_params(DIRP_HANDLE, CT.byref(meas_params))
    if ret != 0:
        logger.error(f'Failed at dirp_get_measurement_params(): ret = {ret}')
    logger.info(f'Stored params: {{ distance: {meas_params.distance:.1f}, humidity: {meas_params.humidity:.1f}, emissivity: {meas_params.emissivity:.2f}, reflection: {meas_params.reflection:.1f} }}')
    

    # get the allowed params range
    params_range = dirp_measurement_params_range_t()
    ret = dirp_get_measurement_params_range(DIRP_HANDLE, CT.byref(params_range))
    if ret != 0:
        logger.error(f'Failed at dirp_get_measurement_params_range(): ret = {ret}')

    # set the new distance param, clamping out of range values
    if distance and params_range.distance.min <= distance <= params_range.distance.max:
        meas_params.distance = distance
        logger.info(f'Distance within accepted range, using {distance}')
    elif distance and distance >= params_range.distance.max:
        meas_params.distance = params_range.distance.max
        logger.info(f'Distance exceeds range maximum, using {params_range.distance.max}')
    elif distance and distance <= meas_params.distance.min:
        meas_params.distance = rjpeg.distance.min
        logger.info(f'Distance below range minimum, using {params_range.distance.min}')
    else:
        pass

    # set the other params
    if temperature:
        meas_params.reflection = temperature
    if humidity:
        meas_params.humidity = humidity
    if emissivity:
        meas_params.emissivity = emissivity

    ret = dirp_set_measurement_params(DIRP_HANDLE, CT.byref(meas_params))
    if ret != 0:
        logger.error(f'Failed at dirp_set_measurement_params(): ret = {ret}')

    logger.info(f'Updated params: {{ distance: {meas_params.distance:.1f}, humidity: {meas_params.humidity:.1f}, emissivity: {meas_params.emissivity:.2f}, reflection: {meas_params.reflection:.1f} }}')

    resolution = dirp_resolution_t()
    ret = dirp_get_rjpeg_resolution(DIRP_HANDLE, CT.byref(resolution))
    if ret != 0:
        print("Failed dirp_get_rjpeg_resolution(): ret = {ret}")


    if dtype == 'int16':
        buffer_size = resolution.height * resolution.width *  CT.sizeof(c_int16)
        image_buffer = CT.create_string_buffer(buffer_size)

        ret = dirp_measure(DIRP_HANDLE, CT.byref(image_buffer), buffer_size)
        if ret != 0:
            print('Failed dirp_measure(): ret = {ret}')
        arr = np.frombuffer(image_buffer, dtype=np.int16)
    elif dtype == 'uint16':
        buffer_size = resolution.height * resolution.width * CT.sizeof(c_float)
        image_buffer = CT.create_string_buffer(buffer_size)

        ret = dirp_measure_ex(DIRP_HANDLE, CT.byref(image_buffer), buffer_size)
        if ret != 0:
            print('Failed dirp_measure_ex(): ret = {ret}')
        arr_flt = np.frombuffer(image_buffer, dtype=np.float32)
        arr = (np.rint((arr_flt + 100.0)*100.0)).astype(np.uint16)
    else:
        buffer_size = resolution.height * resolution.width * CT.sizeof(c_float)
        image_buffer = CT.create_string_buffer(buffer_size)

        ret = dirp_measure_ex(DIRP_HANDLE, CT.byref(image_buffer), buffer_size)
        if ret != 0:
            print('Failed dirp_measure_ex(): ret = {ret}')
        arr = np.frombuffer(image_buffer, dtype=np.float32)

    image = np.reshape(arr, (resolution.height, resolution.width))
    logger.info(f'Temperature mean: {image.mean():.1f}, min: {image.min():.1f}, max: {image.max():.1f}')

    '''
        # *** MAKE PLOT ***
        # compare to defaults converted to float32
        # this will always use the defaults stored in the image
        heatmap = rjpeg_to_heatmap(rjpeg, dtype='float32')
    
        # get pre-converted data for comparison
        exe_file = 'DJI_20240123154823_0116_T.measure.raw'
        exe_arr = np.fromfile(exe_file, dtype=np.float32)
        exe_image = np.reshape(exe_arr, (512, 640))
    
        fig, axs = plt.subplots(1, 3)
        axs[0].imshow(heatmap, label='defaults')
        axs[1].imshow(image, label='updated')
        axs[2].imshow(heatmap - image, label='difference')
        plt.show()
    '''

    # *** SAVE A NEW TEMPS IMAGE *** 

    # make the XMP go in with the exif
    exif[700] = xmp_str

    rtiff = Image.fromarray(image)
    rtiff.save(output, exif=exif, xmp=xmp, format='TIFF')
    rtiff.close()
