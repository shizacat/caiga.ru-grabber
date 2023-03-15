# Description

Get Aeronautical Information Publication (AIP) of Russian airports as one pdf file,
from http://www.caiga.ru/common/AirInter/validaip/html/rus.htm.

Supported only international airports.

# Usage

Requirents: Python 3.8 or above

Environment:

```bash
python -m venv venv
source venv/bin/acitave
pip install -r requiremnts.txt
```

Run:

```bash
source venv/bin/acitave
cd source
./create_pdf_by_airport.py --airport UHSS
```
