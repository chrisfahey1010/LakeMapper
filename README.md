# LakeMapper 🗺️

**LakeMapper** is a Python-based data processing tool designed to convert Minnesota DNR lake shapefiles into game-ready formats for a browser-based fishing simulation game called **LakeSim**. This tool is part of a larger ecosystem simulation effort aiming to realistically model the underwater environments of real Minnesota lakes.

## 🎯 Objective

LakeMapper creates a robust data processing pipeline that:

- **Loads and parses** two separate MN DNR shapefiles:
  1. **Bathymetry Contours** – Lake depth lines (polygon/line geometries with depth values)
  2. **Fish Survey Lake Outlines** – Surveyed lake outlines with biological metadata
- **Identifies lakes** that exist in **both datasets** by comparing their `DOWLKNUM` (unique lake ID) fields
- **Merges segmented lake bathymetry polygons** (e.g. Lake Minnetonka and its bays) into unified logical lakes
- **Exports lake data** into:
  - **GeoJSON** for use in vector-based top-down map rendering
  - **Metadata JSON** files with lake information and fish survey URLs
  - **Summary reports** and lake indices for easy data management

Only lakes with **both** bathymetric and fish survey data are processed and included.

## 🏗️ Architecture

LakeMapper follows modern Python best practices with a modular, function-based architecture:

```
LakeMapper/
├── data/                  
│   └── raw/               # DNR shapefiles (not tracked in git)
├── output/                # Generated outputs
│   ├── geojson/           # Individual lake GeoJSON files
│   ├── metadata/          # Lake metadata JSON files
│   └── raster/            # Future raster outputs
├── lakemapper/            # Core Python package
│   ├── __init__.py        # Package initialization
│   ├── config.py          # Configuration constants
│   ├── utils.py           # Utility functions and logging
│   ├── loader.py          # Shapefile loading and validation
│   ├── matcher.py         # Lake matching and filtering
│   ├── merger.py          # Bathymetry contour merging
│   └── exporter.py        # Data export to various formats
├── scripts/               
│   └── generate.py        # Main orchestrator script
├── tests/                 # Test suite (future)
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Minnesota DNR shapefiles:
  - `bathymetry_contours.shp` (bathymetry data)
  - `fish_survey.shp` (fish survey data)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd LakeMapper
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Place your shapefiles:**
   ```bash
   mkdir -p data/raw
   # Copy your bathymetry_contours.shp and fish_survey.shp files to data/raw/
   ```

### Usage

Run the complete pipeline:

```bash
python scripts/generate.py
```

This will:
1. Load and validate both shapefiles
2. Find lakes that exist in both datasets
3. Merge bathymetry contours for each lake
4. Export results to `output/` directory

## 📊 Data Schema

### Bathymetry Contours Shapefile
- **DOWLKNUM**: Unique lake identifier (8-digit string)
- **DEPTH**: Depth value in feet
- **abs_depth**: Absolute depth value
- **Shape_Leng**: Length of the contour line
- **LAKE_NAME**: Name of the lake

### Fish Survey Shapefile
- **DOWLKNUM**: Unique lake identifier (8-digit string)
- **ACRES**: Lake area in acres
- **CITY_NAME**: Nearest city name
- **SURVEY_URL**: URL to detailed fish survey data
- **SHAPE_Leng**: Perimeter length
- **SHAPE_Area**: Lake area

## 🔧 Configuration

Key configuration settings in `lakemapper/config.py`:

- **BUFFER_DISTANCE_METERS**: Distance (10m) for merging bathymetry contours
- **CRS_EPSG**: Coordinate reference system (26915 for UTM Zone 15N)
- **MIN_LAKE_AREA_ACRES**: Minimum lake area to process (1.0 acres)
- **MAX_LAKE_AREA_ACRES**: Maximum lake area (1,000,000 acres)

## 📤 Output Files

After running the pipeline, you'll find:

```
output/
├── geojson/
│   ├── lake_27013300.geojson
│   ├── lake_48000200.geojson
│   └── ...
├── metadata/
│   ├── lake_27013300.json
│   ├── lake_48000200.json
│   └── ...
├── merged_lakes.geojson      # All lakes in one file
├── summary_report.json       # Processing statistics
└── lake_index.csv           # Lake listing with metadata
```

### Individual Lake Files

Each lake gets two files:

**GeoJSON file** (`lake_27013300.geojson`):
```json
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "geometry": {
      "type": "MultiPolygon",
      "coordinates": [...]
    },
    "properties": {
      "dowlknum": "27013300",
      "lake_name": "Lake Minnetonka",
      "contour_count": 45,
      "min_depth": 0,
      "max_depth": 113,
      "acres": 14223.5,
      "city_name": "Minnetonka"
    }
  }]
}
```

**Metadata file** (`lake_27013300.json`):
```json
{
  "dowlknum": "27013300",
  "lake_name": "Lake Minnetonka",
  "contour_count": 45,
  "depth_range": {"min": 0, "max": 113},
  "acres": 14223.5,
  "city_name": "Minnetonka",
  "survey_url": "http://www.dnr.state.mn.us/lakefind/showreport.html?downum=27013300",
  "geometry_type": "MultiPolygon",
  "area_sq_meters": 57560000.0,
  "export_timestamp": "2024-01-15T10:30:00"
}
```

## 🧪 Testing

Run the test suite (when implemented):

```bash
pytest tests/
```

## 🔍 Troubleshooting

### Common Issues

1. **"No matching lakes found"**
   - Check that both shapefiles have valid DOWLKNUM values
   - Verify the shapefiles are in the correct location (`data/raw/`)

2. **"Missing required fields"**
   - Ensure shapefiles have the expected column names
   - Check the data schema documentation above

3. **Memory issues with large datasets**
   - The bathymetry file is large (~171MB)
   - Consider processing in batches for very large datasets

### Logging

LakeMapper provides detailed logging. Check the console output for:
- Data loading progress
- Matching statistics
- Processing errors
- Export summaries

## 🚧 Future Enhancements

- **Raster export**: Generate depth maps and heatmaps
- **Fish species data**: Web scraping from survey URLs
- **Parallel processing**: Multi-core processing for large datasets
- **Smoothing algorithms**: Remove tiered bathymetry artifacts
- **Additional formats**: PDF, JPEG, and other export formats
- **Web interface**: Browser-based data exploration tool

## 🤝 Contributing

This project follows modern Python development practices:

- **Type hints** for all function parameters and return values
- **Comprehensive docstrings** for all public functions
- **Modular design** with clear separation of concerns
- **Error handling** with informative logging
- **Configuration management** for easy customization

## 📄 License

[Add your license information here]

## 🙏 Acknowledgments

- Minnesota Department of Natural Resources for providing the shapefile data
- The open-source geospatial Python community for excellent tools like GeoPandas and Shapely

---

**LakeMapper** - Transforming Minnesota's lake data into game-ready formats, one lake at a time! 🎣
