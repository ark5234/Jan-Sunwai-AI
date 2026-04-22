from PIL.ExifTags import TAGS

from app import geotagging


GPS_INFO_TAG = next(tag for tag, name in TAGS.items() if name == "GPSInfo")


class DummyImage:
    def __init__(self, exif_data):
        self._exif_data = exif_data

    def getexif(self):
        return self._exif_data


def test_get_geotagging_reads_public_getexif() -> None:
    img = DummyImage(
        {
            GPS_INFO_TAG: {
                1: "N",  # GPSLatitudeRef
                2: (28, 30, 0),  # GPSLatitude
                3: "E",  # GPSLongitudeRef
                4: (77, 10, 0),  # GPSLongitude
            }
        }
    )

    geotags = geotagging.get_geotagging(img)

    assert geotags is not None
    assert geotags["GPSLatitudeRef"] == "N"
    assert geotags["GPSLongitudeRef"] == "E"


def test_extract_location_keeps_coordinates_when_reverse_lookup_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        geotagging,
        "get_geotagging",
        lambda _img: {
            "GPSLatitude": (28, 30, 0),
            "GPSLatitudeRef": "N",
            "GPSLongitude": (77, 10, 0),
            "GPSLongitudeRef": "E",
        },
    )

    class FailingNominatim:
        def __init__(self, *args, **kwargs):
            pass

        def reverse(self, *_args, **_kwargs):
            raise RuntimeError("network unavailable")

    monkeypatch.setattr(geotagging, "Nominatim", FailingNominatim)

    result = geotagging.extract_location(object())

    assert result["coordinates"] is not None
    assert result["coordinates"]["lat"] == 28.5
    assert round(result["coordinates"]["lon"], 6) == round(77.1666666667, 6)
    assert result["address"] == "Address lookup failed"
