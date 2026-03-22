#!/usr/bin/env python3

import sys
from functools import cached_property

if not __package__ and not hasattr(sys, "frozen"):
    import os.path

    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))


if __name__ == "__main__":
    from lncrawl import main

    main()


class CrawlerConfig:
    @cached_property
    def selenium_grid(self) -> str:
        return "true"
