============
Mavic Helper
============

Mavic Helper is a collection of CLI tools to assist in preparing thermal orthomosaics.

It uses the `DJI Thermal SDK <https://www.dji.com/downloads/softwares/dji-thermal-sdk>`_ and the `dji_thermal_sdk <https://github.com/lyuhaitao/dji_thermal_sdk/>`_ Python bindings to convert the radiometric data to temperature.

Installation
============

To install from source use pip install from the root of the source directory.

.. code:: console

	cd ~/mavic-helper
	python -pip install .


Examples
========

There are currently three utilities, each a subcommand to the main command 'mav'. You can get the online help by for each using the --help option.

mav positions
-------------

Takes a set of images and creates a GeoJSON file of camera positions from the image metadata.

mav remask
----------

Takes the band mask (Band 2) from a Metashape thermal orthomosaic and converts it to nodata values in a single-band TIFF.

mav totiff
----------

Converts embedded radiometric data in Mavic M3T RJPEG thermal images to TIFF format containing temperature and image metadata. CLI options specify the conversion parameters. Object distance may be calculated based upon drone height above ground level, where ground elevation is retrieved queried from the USGS Elevation API. Caution is warranted, however, as the DJI SDK only accepts maximum object distance of 25 meters.

