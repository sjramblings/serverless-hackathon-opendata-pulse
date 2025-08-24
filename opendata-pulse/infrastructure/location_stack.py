"""
Location Stack - Amazon Location Service for map visualization
"""

import aws_cdk as cdk
from aws_cdk import (
    aws_location as location,
    aws_iam as iam
)
from constructs import Construct

class LocationStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Amazon Location Service Map
        self.air_quality_map = location.CfnMap(
            self, "AirQualityMap",
            map_name="nsw-air-quality-map",
            configuration={
                "style": "VectorEsriStreets"
            },
            description="Interactive map for NSW air quality data visualization"
        )
        
        # Place Index for Geocoding
        self.place_index = location.CfnPlaceIndex(
            self, "NSWPlaceIndex",
            index_name="nsw-places",
            data_source="Esri",
            data_source_configuration={
                "intendedUse": "SingleUse"
            },
            description="Geocoding index for NSW locations"
        ) 