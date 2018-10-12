from functools import partial, reduce
import os

import fiona
import pyproj
from shapely.geometry import shape
from shapely.ops import transform

S3_PATH = 's3://glr-ds-us-building-footprints'

def get_buildings(plot_shp, county_fips):
    src_path = os.path.join(S3_PATH, f'{county_fips}.shp')
    bbox = plot_shp.bounds

    buildings = []
    building_shps = []
    with fiona.open(src_path) as src:
        src_meta = src.meta
        candidates = list(src.items(bbox=bbox))
        candidate_shps = [shape(candidate[1]['geometry']) for candidate in candidates]

        for i, candidate_shp in enumerate(candidate_shps):
            if candidate_shp.intersects(plot_shp):
                buildings.append(candidates[i])
                building_shps.append(candidate_shp)

    return buildings, building_shps, src_meta

def get_footprint_intersection_single_building(building, plot):
    return plot.intersection(building).area

def get_building_features(plot, buildings):
    '''
    Calculates number of intersecting buildings, total building footprint, and proportion of the
    plot that is covered by buildings.

    Parameters
    ----------
    plot : shapely.shape
        Plot to query.

    buildings : list[shapely.shape]
        List of buildings that intersect the plot. Assumes that all buildings DO intersect the
        plot.

    Returns
    -------
    building_features : dict
        Keys: 'total_building_footprint', 'building_proportion', 'n_buildings'
    '''
    building_features = {}

    # Reproject to albers equal area for area calculations in meters.
    project = partial(
        pyproj.transform,
        pyproj.Proj(init='epsg:4326'),
        pyproj.Proj(init='epsg:2163'),
    )

    plot_projected = transform(project, plot)
    buildings_projected = (transform(project, building) for building in buildings)

    get_footprint_partial = partial(
        get_footprint_intersection_single_building,
        plot=plot_projected
    )

    total_building_footprint = reduce(
        lambda x, y: x + get_footprint_partial(y),
        buildings_projected,
        0
    )

    building_proportion = total_building_footprint / plot_projected.area

    n_buildings = len(buildings)

    building_features['total_building_footprint'] = total_building_footprint
    building_features['building_proportion'] = building_proportion
    building_features['n_buildings'] = n_buildings

    return building_features

def query_buildings(plot_shp, county_fips):
    # Wrapper to export
    buildings, building_shps, src_meta = get_buildings(plot_shp, county_fips)

    building_features = get_building_features(plot_shp, building_shps)

    return building_features

def test():
    test_geom_w_buildings = {
        "type": "Polygon",
        "coordinates": [
            [
                [
                    -122.40870237350462,
                    37.78318894806247
                ],
                [
                    -122.39876747131348,
                    37.78318894806247
                ],
                [
                    -122.39876747131348,
                    37.78836966314214
                ],
                [
                    -122.40870237350462,
                    37.78836966314214
                ],
                [
                    -122.40870237350462,
                    37.78318894806247
                ]
            ]
        ]
    }

    test_geom_wo_buildings = {
        "type": "Polygon",
        "coordinates": [
            [
                [
                    -122.44197471761457,
                    37.768773390348009
                ],
                [
                    -122.440887982900122,
                    37.768983204915301
                ],
                [
                    -122.440764246104024,
                    37.768095527899852
                ],
                [
                    -122.442076932114745,
                    37.767944891800255
                ],
                [
                    -122.441974714761457,
                    37.768773390348009
                ]
            ]
        ]
    }

    test_county_fips = '06075'

    test_shp_w_buildings = shape(test_geom_w_buildings)
    test_buildings, test_building_shps, meta = get_buildings(test_shp_w_buildings, test_county_fips)
    assert len(test_buildings) == 71

    test_shp_wo_buildings = shape(test_geom_wo_buildings)
    test_no_buildings, test_no_building_shps, meta_no_buildings = get_buildings(test_shp_wo_buildings, test_county_fips)
    assert len(test_no_buildings) == 0

    print(query_buildings(test_shp_w_buildings, test_county_fips))
    print(query_buildings(test_shp_wo_buildings, test_county_fips))

    with fiona.open(
            'test.shp',
            'w',
            **meta) as sink:
        for building in test_buildings:
            sink.write(
                {
                    'geometry': building[1]['geometry'],
                    'properties': building[1]['properties']
                }
            )


if __name__ == '__main__':
    test()
