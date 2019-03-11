# US Building Footprints

This is a dataset derived from Microsoft's [US Building Footprints](https://github.com/Microsoft/USBuildingFootprints) dataset.
It consists of one shapefile per county, spatially indexed, along with some additional attributes (area in sq. m., centroid, etc.).
Buildings that intersect multiple counties appear in multiple shapefiles.

I transformed the original dataset because shapefiles are convenient for spatial indexing and storing computed attributes for the
shapes. The max size for a shapefile is 2 GB, and the largest geojson files in the original dataset are larger than this.

The dataset can be found here: `s3://glr-ds-us-building-footprints`. Individual files are called `{fips_code}.{extension}`, eg. `06075.shp`.
To download and use the files locally, you'll need the files with the following extensions: `.dbf`, `.prj`, `.qix`, `.shp`, `.shx`.

NOTE: You need valid AWS credentials to interact with the bucket. Set these up with `aws configure` from the CLI. CLI docs here: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html 

The [example](example.py) script demonstrates loading a shapefile, performing an intersection, and computing some basic information
about the intersecting buildings. The example requires a version of fiona with s3 support: see [requirements](requirements.txt).
