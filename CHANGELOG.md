# Changelog

## :package: [0.5.0](https://pypi.org/project/geometry-to-spatialite/0.5.0/) - 2024-09-21

* Fix importing shapefiles with mixed geometry types - https://github.com/chris48s/geometry-to-spatialite/issues/321
* Add `geom_type` param/`--geom-type` CLI arg - https://github.com/chris48s/geometry-to-spatialite/issues/8

## :package: [0.4.3](https://pypi.org/project/geometry-to-spatialite/0.4.3/) - 2023-10-22

* Tested on python 3.12

## :package: [0.4.0](https://pypi.org/project/geometry-to-spatialite/0.4.0/) - 2023-01-08

* Tested on python 3.11
* Tested with Shapely 2
* Dropped compatibility with python <=3.7

## :package: [0.3.3](https://pypi.org/project/geometry-to-spatialite/0.3.3/) - 2021-10-17

* Tested on python 3.10

## :package: [0.3.2](https://pypi.org/project/geometry-to-spatialite/0.3.2/) - 2020-10-18

* Throw `TypeError` instead of `DataImportError` if SRID is not an int
* Tested on python 3.9
* Documentation improvements

## :package: [0.3.1](https://pypi.org/project/geometry-to-spatialite/0.3.1/) - 2020-06-07

* Ensure co-ordinates aren't rounded to 6 decimal places when importing geojson

## :package: [0.3.0](https://pypi.org/project/geometry-to-spatialite/0.3.0/) - 2020-02-16

* Requires `sqlite-utils>=2.1`

## :package: [0.2.0](https://pypi.org/project/geometry-to-spatialite/0.2.0/) - 2019-10-21

* Tested on python 3.8
* Support composite primary keys
* Add `write_mode` param, allowing user to overwrite or append to existing table

## :package: [0.1.0](https://pypi.org/project/geometry-to-spatialite/0.1.0/) - 2019-10-13

First Release
