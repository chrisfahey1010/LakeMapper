# LakeMapper

A Python tool for extracting and converting Minnesota lake data into GeoJSON or raster formats, for use in lake simulation and game development.

## Features

- Converts DNR shapefiles into game-friendly formats
- Merges multi-part lakes into unified logical lakes
- Exports GeoJSON and/or raster depth maps
- Built with `geopandas`, `shapely`, and `rasterio`

## Usage

1. Clone the repo and install dependencies:

```bash
pip install -r requirements.txt
