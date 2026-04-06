import argparse
import cProfile
import io
import pstats
import tempfile
from pathlib import Path

from PIL import Image

from app.classifier import CivicClassifier


def _make_sample_image(path: Path) -> None:
    img = Image.new("RGB", (256, 256), color=(220, 220, 220))
    img.save(path, format="JPEG")


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile analyze classification path")
    parser.add_argument("--image", type=str, default="", help="Path to image to classify")
    parser.add_argument("--top", type=int, default=25, help="Top functions to print")
    parser.add_argument("--sort", type=str, default="cumulative", help="pstats sort key")
    args = parser.parse_args()

    image_path: Path
    temp_file = None

    if args.image:
        image_path = Path(args.image).resolve()
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
    else:
        temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        image_path = Path(temp_file.name)
        temp_file.close()
        _make_sample_image(image_path)

    profiler = cProfile.Profile()
    classifier = CivicClassifier()

    try:
        profiler.enable()
        result = classifier.classify(str(image_path))
        profiler.disable()

        print("[profile] classification method:", result.get("method"))
        print("[profile] timings:", result.get("timings", {}))

        output = io.StringIO()
        stats = pstats.Stats(profiler, stream=output).sort_stats(args.sort)
        stats.print_stats(args.top)

        print("\n[profile] top functions")
        print(output.getvalue())
    finally:
        if temp_file:
            try:
                image_path.unlink(missing_ok=True)
            except Exception:
                pass


if __name__ == "__main__":
    main()
