export const DATA_BASE = "/output"

export const indexJsonPath = (): string => `${DATA_BASE}/lake_index.json`
export const lakeMetadataPath = (dowlknum: string): string => `${DATA_BASE}/metadata/lake_${dowlknum}.json`
export const lakeGeojsonPath = (dowlknum: string): string => `${DATA_BASE}/geojson/lake_${dowlknum}.geojson`
export const lakeContoursPath = (dowlknum: string): string => `${DATA_BASE}/contours/contours_${dowlknum}.geojson`



