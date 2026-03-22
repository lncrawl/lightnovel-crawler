import re

from bs4 import BeautifulSoup

from .platforms import Platform

__re_line_breaks = re.compile(r"[\r\n]+")


def extract_text(html: str) -> str:
    html = html.replace("</p><p", "</p>\n<p")
    soup = BeautifulSoup(html, "lxml")
    text = "\n\n".join(soup.stripped_strings)
    if Platform.posix:
        text = __re_line_breaks.sub("\n", text)
    return text
