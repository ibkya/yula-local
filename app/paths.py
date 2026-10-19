"""Every file location in one place. Run-time files live in data/, separate from the code."""
from pathlib import Path

APP = Path(__file__).resolve().parent
ROOT = APP.parent
DATA = ROOT / 'data'
DATA.mkdir(exist_ok=True)

STATE = DATA / 'tur-kaydi.json'          # Tour progress. Never delete after an uncertain send.
STATUS = DATA / 'durum.json'             # Live status for the panel.
CONTROL = DATA / 'kontrol-istegi.json'   # Stop requests from the panel.
LOCK = DATA / 'calisiyor.kilit'          # Prevents two runners at once.
CHECK_IMAGE = DATA / 'kontrol-ekran.png' # Frame saved by the screen check.
TESSDATA = ROOT / '.tessdata'            # Windows OCR language data.
VISION = ROOT / '.build/yula-vision'     # macOS OCR helper, built by mac/setup.sh.
