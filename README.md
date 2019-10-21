# geometry-to-spatialite

[![Build Status](https://travis-ci.org/chris48s/geometry-to-spatialite.svg?branch=master)](https://travis-ci.org/chris48s/geometry-to-spatialite)
[![Coverage Status](https://coveralls.io/repos/github/chris48s/geometry-to-spatialite/badge.svg?branch=master)](https://coveralls.io/github/chris48s/geometry-to-spatialite?branch=master)
[![PyPI Version](https://img.shields.io/pypi/v/geometry-to-spatialite.svg)](https://pypi.org/project/geometry-to-spatialite/)
![License](https://img.shields.io/pypi/l/geometry-to-spatialite.svg)
![Python Support](https://img.shields.io/pypi/pyversions/geometry-to-spatialite.svg)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)


Import geographic and spatial data from files into a SpatiaLite DB.

This project is primarily useful for browsing and publishing geographic and spatial data with [datasette](https://github.com/simonw/datasette) and [datasette-leaflet-geojson](https://github.com/simonw/datasette-leaflet-geojson). It is inspired by [csvs-to-sqlite](https://github.com/simonw/csvs-to-sqlite) and provides a similar interface.

## Setup

```
pip install geometry-to-spatialite
```

You'll need python >=3.6 and the [SpatiaLite](https://www.gaia-gis.it/fossil/libspatialite/index) module for SQLite. 

### Install SpatiaLite on Debian/Ubuntu

```
apt install spatialite-bin libsqlite3-mod-spatialite
```

### Install SpatiaLite on Mac

```
brew update
brew install spatialite-tools
```

## Usage

### On the console

Geometry-to-spatialite installs two commands: `shapefile-to-spatialite` and `geojson-to-spatialite`. Both provide the same arguments.

Basic usage

```
shapefile-to-spatialite myfile.shp mydatabase.db
```

This will create a new SQLite database called `mydatabase.db` containing a single table, `myfile`

You can provide multiple files:

```
shapefile-to-spatialite one.shp two.shp bundle.db
```

The `bundle.db` database will contain two tables, `one` and `two`.

This means you can use wildcards:

```
shapefile-to-spatialite ~/Downloads/*.shp mydownloads.db
```

If you pass a path to one or more directories, the script will recursively search those directories for files and create tables for each one:

```
shapefile-to-spatialite ~/path/to/directory all-my-shapefiles.db
```

For more help on usage and arguments, run `shapefile-to-spatialite --help` or `geojson-to-spatialite --help`

### As a library

```py
from shapefile_to_spatialite import (
    geojson_to_spatialite,
    shp_to_spatialite,
    DataImportError
)


# Use the defaults
try:
    geojson_to_spatialite('mydatabase.db', 'myfile.geojson')
except DataImportError:
    raise


# With optional params
# geojson_to_spatialite() and shp_to_spatialite() support the same argument list
try:
    geojson_to_spatialite(
        'mydatabase.db',
        'myfile.geojson',
        table_name='custom',  # set a custom table name (defaults to the filename)
        srid=3857,            # specify a custom SRID (default is 4326)
        pk='id',              # field (str) or fields (list/tuple) to use as a
                              # primary key (default is no primary key)
        write_mode='append',  # pass 'replace' or 'append' to overwrite
                              # or append to an existing table

        # In most cases the spatialite extension will be automatically detected and loaded
        # If not you can manully pass a path to the .so .dylib or .dll file
        spatialite_extension='path/to/mod_spatialite.so'
    )
except DataImportError:
    raise
```

## Troubleshooting

### Failed to load the SpatiaLite extension

Geometry-to-spatialite requires [SpatiaLite](https://www.gaia-gis.it/fossil/libspatialite/index) to be installed. See [Setup](#setup). Geometry-to-spatialite will attempt to automatically load the extension. If you've installed the extension and you're still seeing this error, you can use the `--spatialite-extension` flag (using on the console) or `spatialite_extension` (using as a library) to manually specify the path to the SpatiaLite extension.
