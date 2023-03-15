"""
Library for request to http://www.caiga.ru
"""

import io
import os
import re
import glob
import logging
from dataclasses import dataclass, field
from typing import Optional, List

import requests


@dataclass
class ItemLink:
    url: str
    title: str


@dataclass
class ItemBegin:
    number: str
    url: str
    title: str
    sub_item: List["ItemBegin"] = field(default_factory=list)
    links: List[ItemLink] = field(default_factory=list)

    def __repr__(self):
        return f"{self.number} {self.title}"


class CaigaMenu:
    def __init__(self, content: str):
        self.content = content
        self._parser()

    def _parser(self):
        self._root = []

        is_open = False
        stack_item: List[ItemBegin] = []
        item_begin_count: int = 0

        for line in self.content.splitlines():
            if line.startswith("OpenTab();"):
                is_open = True
                continue
            if line.startswith("ClosTab();"):
                break
            if not is_open:
                continue
            if line.startswith("ItemBegin"):
                # ItemBegin("7000", "../aip/aip-tit.pdf","AIP. Сборник АНИ");
                values = re.match(
                    r"ItemBegin\(\"(\d+)\",\s?\"(.*)\",\s?\"(.+)\"\);", line)
                if values is None:
                    raise ValueError(f"Can't parse line: {line}")
                item = ItemBegin(*values.groups())
                item_begin_count += 1

                if len(stack_item) == 0:
                    self._root.append(item)
                else:
                    stack_item[-1].sub_item.append(item)

                stack_item.append(item)
                continue

            if line.startswith("ItemEnd"):
                if len(stack_item) == 0:
                    print("WARNING: Find ItemEnd without ItemBegin: {line}")
                    continue

                stack_item.pop()
                continue

            if line.startswith("ItemLink"):
                # ItemLink("../aip/gen/gen0/gen0.1.pdf","GEN 0.1 Предисловие");
                values = re.match(r"ItemLink\(\"(.*)\",\s?\"(.*)\"\);", line)
                if values is None:
                    raise ValueError(f"Can't parse line: {line}")
                item = ItemLink(*values.groups())

                if len(stack_item) == 0:
                    raise ValueError(f"Find ItemLink without ItemBegin: {line}")
                stack_item[-1].links.append(item)
                continue

        logging.info("Menu parsed, begin count: %s", item_begin_count)

    def find_sub_menu_by_title(self, title: str) -> ItemBegin:
        for item in self._check_item(self._root):
            if item.title == title:
                return item
        raise ValueError(f"Can't find menu by title: {title}")

    def _check_item(self, item: ItemBegin) -> ItemBegin:
        if isinstance(item, list):
            for next in item:
                for v in self._check_item(next):
                    yield v
        else:
            yield item
            for v in self._check_item(item.sub_item):
                yield v


class Caiga:

    default_base_url = 'http://www.caiga.ru'

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or self.default_base_url
        self._session: requests.Session = None

    def get_aip_by_airport_icao(self, airport_icao: str) -> List[ItemLink]:
        """
        Return list of url with pdf files by airport icao name.
        Only for international airports.
        """
        content = self._request(
            "/common/AirInter/validaip/html/menurus.htm", "GET")

        # Create menu
        menu = CaigaMenu(content)
        # Find sub menu by title
        item = menu.find_sub_menu_by_title("AD 2. Аэродромы")
        # Find airoport
        for item in menu._check_item(item):
            if item.title.startswith(airport_icao):
                break
        return item.links

    def download_aip_pdf(self, relative_path: str) -> bytes:
        """Download aip document"""
        return self._download_file(
            f"/common/AirInter/validaip/html/{relative_path}")

    def _get_url(self, path: str) -> str:
        """Return url by path"""
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.base_url}{path}"

    def _request(self, path: str, method: str) -> str:
        """
            Return content of page by path.
        """
        r = self.session.request(method, self._get_url(path))
        r.raise_for_status()
        return r.text

    def _download_file(self, path: str) -> bytes:
        r = self.session.request("GET", self._get_url(path))
        r.raise_for_status()
        return r.content

    @property
    def session(self):
        """Return session"""
        if self._session is None:
            self._session = requests.Session()
        return self._session
