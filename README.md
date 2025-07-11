# About

Mavic Helper is a collection of CLI tools to assist in preparing thermal orthomosaics.

Drone flights can produce many RJPEGs. These are colorized thermal images represent relative temperature differences as RGB colors on a color-ramp. The files also embed sensor data and metadata required to calculate temperature. If you want to see the temperature data you can use the DJI Thermal Tool. If howver you need to extract temperature data for mosaicing and further processing, then the DJI software provides limited options.

Mavic Helper uses the [DJI Thermal SDK](https://www.dji.com/downloads/softwares/dji-thermal-sdk) and the [dji_thermal_sdk](https://github.com/lyuhaitao/dji_thermal_sdk/) Python bindings to convert the radiometric data to temperature. This package includes the DJI SDK for Windows only and will not work on Linux or MacOS.

## Installation

### Using pixi

Pixi solves for installation dependencies and creates virtual environments, installing the necessary packages from conda-forge. Install pixi according to the instructions at [https://pixi.sh](https://pixi.sh).

Once you have pixi installed you can:

```bash
	cd ~/mavic-helper
	pixi install --manifest-path ./pyproject.toml --environment default
	pixi shell
``` 

### Using pip

To install from source use `pip install` from the root of the package directory.

```bash
	cd ~/mavic-helper
	python -pip install .
```

## Usage

Mavic Helper currently includes three utilities, each a subcommand to the main command 'mav'. You can get the online help by for each using the --help option or on the [CLI Command Reference](./cli/) page.

### mav positions

Takes a set of images and creates a GeoJSON file of camera positions from the image metadata. It is meant to be a simple GIS-friendly way to map the photo positions.

### mav tidytiff

Takes the band mask (Band 2) from a Metashape thermal orthomosaic and converts it to nodata values in a single-band TIFF.

### mav totiff

Converts embedded radiometric data in Mavic M3T RJPEG thermal images to TIFF format containing temperature and image metadata. CLI options specify the conversion parameters. Object distance may be calculated based upon drone height above ground level, where ground elevation is retrieved queried from the USGS Elevation API. Caution is warranted, however, as the DJI SDK only accepts a maximum object distance of 25 meters.

## PowerShell Scripts

The scripts directory in the source tree includes two powershell scripts. These require you have installed a modern version of PowerShell such as PowerShell 7, not the Windows PowerShell 5.1 that is included in the Windows operating system by default. You can get the current version of PowerShell at its homepage, [https://learn.microsoft.com/en-us/powershell/](https://learn.microsoft.com/en-us/powershell/)

Once you have powershell installed you will need to enable running of local scripts and scripts downloaded from the internet.