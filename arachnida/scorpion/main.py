from PIL import Image
from PIL.ExifTags import TAGS
import piexif
import argparse
import os

parser = argparse.ArgumentParser(description="Scorpion - image metadata viewer")
parser.add_argument("files", nargs="+", help="image files to analyze")
parser.add_argument("-s", action="store_true", help="strip all metadata from images")
args = parser.parse_args()

for file in args.files:
    print(f"\n=== {file} ===")
    try:
        size = os.path.getsize(file)
        time = os.path.getctime(file)
        print(f"File size: {size}")
        print(f"Time created: {time}")

        if (not file.lower().endswith((".gif", ".bmp"))):
            image = Image.open(file)
            exif_data = image._getexif() # returns a dict of {tag_id: value}

            if (exif_data):
                if (args.s):
                    if (file.lower().endswith((".jpg", ".jpeg"))):
                        piexif.remove(file)
                    else:
                        print("Strip only supported for JPEG files")
                else:
                    for tag_id, value in exif_data.items():
                        tag_name = TAGS.get(tag_id, tag_id) # numeric id to readable name
                        print(f"{tag_name}: {value}")
            else:
                print("No EXIF data found")

    except FileNotFoundError:
        print(f"Error: file '{file}' not found")
    except Exception as e:
        print(f"Error processing '{file}': {e}")
