# Troubleshooting

## Failed to load the SpatiaLite extension

Geometry-to-spatialite requires [SpatiaLite](https://www.gaia-gis.it/fossil/libspatialite/index) to be installed. See [Installation](installation). Geometry-to-spatialite will attempt to automatically load the extension. If you've installed the extension and you're still seeing this error, you can use the `--spatialite-extension` flag (when using on the console) or `spatialite_extension` param (when using as a library) to manually specify the path to the SpatiaLite extension.
