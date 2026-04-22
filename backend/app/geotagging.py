from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from geopy.geocoders import Nominatim


def _read_exif_data(image: Image.Image):
    """Read EXIF using Pillow's public API first, then private fallback."""
    get_exif_public = getattr(image, "getexif", None)
    if callable(get_exif_public):
        try:
            exif_obj = get_exif_public()
            if exif_obj:
                if hasattr(exif_obj, "items"):
                    exif_data = dict(exif_obj.items())
                else:
                    exif_data = dict(exif_obj)
                if exif_data:
                    return exif_data
        except Exception:
            pass

    # Backward compatibility for older Pillow flows.
    get_exif_private = getattr(image, "_getexif", None)
    if callable(get_exif_private):
        try:
            exif_data = get_exif_private()
            if exif_data:
                return exif_data
        except Exception:
            pass

    return None


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
        return None
    
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal

def get_geotagging(image: Image.Image):
    exif_data = _read_exif_data(image)
    if not exif_data:
        return None

    geotagging = {}
    
    # Try modern get_ifd approach first for GPSInfo (34853)
    try:
        exif_obj = image.getexif()
        # 0x8825 is the tag for GPSInfo
        gps_ifd = exif_obj.get_ifd(0x8825)
        if gps_ifd:
            for t in gps_ifd:
                sub_decoded = GPSTAGS.get(t, t)
                geotagging[sub_decoded] = gps_ifd[t]
            return geotagging
    except Exception:
        pass

    # Fallback to manual dictionary parsing
    for (tag, value) in exif_data.items():
        decoded = TAGS.get(tag, tag)
        if decoded == "GPSInfo":
            # Ensure value is actually a dictionary before iterating
            if isinstance(value, dict):
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    geotagging[sub_decoded] = value[t]
            break

    if not geotagging:
        return None

    return geotagging

def extract_location(image: Image.Image):
    geotags = get_geotagging(image)
    if not geotags:
        return {"address": "Location not found in image metadata", "coordinates": None}

    try:
        lat = get_decimal_from_dms(geotags["GPSLatitude"], geotags["GPSLatitudeRef"])
        lon = get_decimal_from_dms(geotags["GPSLongitude"], geotags["GPSLongitudeRef"])
    except KeyError:
        return {"address": "Incomplete GPS metadata in image", "coordinates": None}

    if lat is None or lon is None:
        return {"address": "Invalid GPS metadata in image", "coordinates": None}

    coordinates = {"lat": lat, "lon": lon}

    try:
        geolocator = Nominatim(user_agent="jan_sunwai_ai", timeout=4)
        # geolocator.reverse is synchronous in geopy
        location = geolocator.reverse((lat, lon))  # type: ignore

        # Access address safely; location might be None
        address_str = getattr(location, "address", None) if location else None
        if not address_str:
            address_str = f"{lat:.6f}, {lon:.6f}"

        return {
            "address": address_str,
            "coordinates": coordinates,
        }
    except Exception as e:
        # Preserve extracted coordinates even when reverse-geocoding fails.
        return {
            "address": "Address lookup failed",
            "coordinates": coordinates,
            "error": str(e),
        }
