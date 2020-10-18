# Usage

## On the console

Geometry-to-spatialite installs two commands: `shapefile-to-spatialite` and `geojson-to-spatialite`. Both provide the same arguments.

Basic usage

```bash
shapefile-to-spatialite myfile.shp mydatabase.db
```

This will create a new SQLite database called `mydatabase.db` containing a single table, `myfile`

You can provide multiple files:

```bash
shapefile-to-spatialite one.shp two.shp bundle.db
```

The `bundle.db` database will contain two tables, `one` and `two`.

This means you can use wildcards:

```bash
shapefile-to-spatialite ~/Downloads/*.shp mydownloads.db
```

If you pass a path to one or more directories, the script will recursively search those directories for files and create tables for each one:

```bash
shapefile-to-spatialite ~/path/to/directory all-my-shapefiles.db
```

For more help on usage and arguments, run

```bash
shapefile-to-spatialite --help
```

or

```bash
geojson-to-spatialite --help
```

## As a library

### Basic usage

```py
from geometry_to_spatialite import (
    geojson_to_spatialite,
    shp_to_spatialite,
    DataImportError
)


try:
    # Import myfile.geojson into mydatabase.db using the default settings
    geojson_to_spatialite('mydatabase.db', 'myfile.geojson')
except DataImportError:
    raise
```


### API Reference

```{eval-rst}
.. automodule:: geometry_to_spatialite
  :members: geojson_to_spatialite, shp_to_spatialite, DataImportError
  :member-order: bysource
```
