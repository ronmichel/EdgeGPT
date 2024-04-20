from enum import Enum

try:
    from typing import Literal, Union
except ImportError:
    from typing_extensions import Literal
from typing import Optional


class LocationHint(Enum):
    USA = {
        "locale": "en-US",
        "LocationHint": [
            {
                "SourceType": 1,
                "RegionType": 2,
                "Center": {
                    "Latitude": 34.05189895529883,
                    "Longitude": -118.26219950185547
                },
                "Radius": 24902,
                "Name": "Los Angeles, California",
                "Accuracy": 24902,
                "FDConfidence": 0.5,
                "CountryName": "United States",
                "CountryConfidence": 8,
                "Admin1Name": "California",
                "PopulatedPlaceName": "Los Angeles",
                "PopulatedPlaceConfidence": 5,
                "PostCodeName": "90017",
                "UtcOffset": -8,
                "Dma": 803
            }
        ]
    }
    CHINA = {
        "locale": "zh-CN",
        "LocationHint": [
            {
                "SourceType": 1,
                "RegionType": 2,
                "Center": {
                    "Latitude": 39.9042,
                    "Longitude": 116.4074,
                },
                "Radius": 24902,
                "Name": "Beijing",
                "Accuracy": 24902,
                "FDConfidence": 0.5,
                "CountryName": "China",
                "CountryConfidence": 8,
                "Admin1Name": "Kowloon City",
                "PopulatedPlaceName": "Kowloon City District",
                "PopulatedPlaceConfidence": 5,
                "UtcOffset": 8,
                "Dma": 0
            },
        ],
    }
    HONGKONG = {
        "locale": "zh-HK",
        "LocationHint": [
            {
                "SourceType": 1,
                "RegionType": 2,
                "Center": {
                    "Latitude": 22.32819938659668,
                    "Longitude": 114.19159698486328
                },
                "Radius": 24902,
                "Name": "Kowloon City District, Kowloon City",
                "Accuracy": 24902,
                "FDConfidence": 0.5,
                "CountryName": "Hong Kong",
                "CountryConfidence": 8,
                "Admin1Name": "Kowloon City",
                "PopulatedPlaceName": "Kowloon City District",
                "PopulatedPlaceConfidence": 5,
                "UtcOffset": 8,
                "Dma": 0
            },
        ],
    }
    TW = {
        "locale": "zh-TW",
        "LocationHint": [
            {
                "SourceType": 1,
                "RegionType": 2,
                "Center": {
                    "Latitude": 24.14189910888672,
                    "Longitude": 120.68060302734375
                },
                "Radius": 24902,
                "Name": "Central District, Taichung City",
                "Accuracy": 24902,
                "FDConfidence": 0.800000011920929,
                "CountryName": "Taiwan",
                "CountryConfidence": 8,
                "Admin1Name": "Taichung City",
                "PopulatedPlaceName": "Central District",
                "PopulatedPlaceConfidence": 8,
                "UtcOffset": 8,
                "Dma": 0
            },
        ],
    }
    EU = {
        "locale": "en-IE",
        "LocationHint": [
            {
                "country": "Norway",
                "state": "",
                "Name": "Oslo",
                "timezoneoffset": 1,
                "countryConfidence": 8,
                "Center": {
                    "Latitude": 59.9139,
                    "Longitude": 10.7522,
                },
                "RegionType": 2,
                "SourceType": 1,
            },
        ],
    }
    UK = {
        "locale": "en-GB",
        "LocationHint": [
            {
                "country": "United Kingdom",
                "state": "",
                "Name": "London",
                "timezoneoffset": 0,
                "countryConfidence": 8,
                "Center": {
                    "Latitude": 51.5074,
                    "Longitude": -0.1278,
                },
                "RegionType": 2,
                "SourceType": 1,
            },
        ],
    }


LOCATION_HINT_TYPES = Optional[Union[LocationHint, Literal["USA", "CHINA", "HONGKONG", "EU", "UK", "TW"]]]
