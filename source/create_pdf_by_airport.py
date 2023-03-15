#!/usr/bin/env python3

"""
Create the pdf file with all documents for the airport.
"""

import io
import argparse
from typing import Optional, List

from pypdf import PdfReader, PdfWriter

from lib.caiga import Caiga


class CreatePdfByAirport:
    def __init__(self, airport: str, output: Optional[str] = None):
        """
        Args:
            airport: Airport ICAO name
            output: Output file name
        """
        self.airport = airport
        self.caiga = Caiga()
        self.output = output or f"{airport}.pdf"

    def run(self):
        items = self.caiga.get_aip_by_airport_icao(self.airport)

        merger = PdfWriter()
        for item in items:
            merger.append(
                PdfReader(io.BytesIO(self.caiga.download_aip_pdf(item.url)))
            )

        merger.write(self.output)
        merger.close()


def arguments(args: Optional[List[str]] = None):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--airport", required=True, type=str, help="Airport ICAO name")
    parser.add_argument(
        "--output", type=str, help="Output file name")
    return parser.parse_args(args)


if __name__ == "__main__":
    CreatePdfByAirport(**vars(arguments())).run()
