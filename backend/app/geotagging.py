from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from geopy.geocoders import Nominatim

def get_decimal_from_dms(dms, ref):
    # dms is likely a tuple of IFDRational, but we treat as indexable
    # Explicitly casting to float to handle Pillow's IFDRational type
    try:
        # Cast to tuple to ensure indexable
        dms_list = list(dms) # type: ignore
        degrees = float(dms_list[0])
        minutes = float(dms_list[1])
        seconds = float(dms_list[2])
    except (TypeError, IndexError, ValueError):
         # Fallback if dms isn't indexable in the way we expect, or elements aren't castable
        return 0.0
    
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal

def get_geotagging(image: Image.Image):
    # Safely access _getexif to avoid type checker errors on private attribute
    # and handle images that don't support EXIF (like PNGs)
    get_exif = getattr(image, '_getexif', None)
    
    if not get_exif:
        return None

    exif_data = get_exif()
    if not exif_data:
        return None

    geotagging = {}
    for (tag, value) in exif_data.items():
        decoded = TAGS.get(tag, tag)
        if decoded == "GPSInfo":
            for t in value:
                sub_decoded = GPSTAGS.get(t, t)
                geotagging[sub_decoded] = value[t]

    if not geotagging:
        return None

    return geotagging

def extract_location(image: Image.Image):
    geotags = get_geotagging(image)
    if not geotags:
        return {"address": "Location not found in image metadata", "coordinates": None}
    
    try:
        lat = get_decimal_from_dms(geotags['GPSLatitude'], geotags['GPSLatitudeRef'])
        lon = get_decimal_from_dms(geotags['GPSLongitude'], geotags['GPSLongitudeRef'])
        
        geolocator = Nominatim(user_agent="jan_sunwai_ai")
        # geolocator.reverse is synchronous in geopy
        location = geolocator.reverse((lat, lon)) # type: ignore
        
        # Access address safely; location might be None
        address_str = getattr(location, 'address', "Address lookup failed") if location else "Address lookup failed"

        return {
            "address": address_str,
            "coordinates": {"lat": lat, "lon": lon}
        }
    except Exception as e:
        return {"address": "Error processing location data", "coordinates": None, "error": str(e)}
