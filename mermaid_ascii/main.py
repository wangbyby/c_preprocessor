from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Dict, List, Tuple, Union
import logging

import sys
import os
sys.path.append(os.path.dirname(__file__))

from layout import Layout
from parsing import Parser


if __name__ == "__main__":
    # Enable logging for debugging
    logging.basicConfig(level=logging.INFO)

    test1 = """
    graph TB        
        Sub1[s10000000000000000000000000000000000] & Sub2[s2] --> Merge[merge]
    """

    print("Parsing Mermaid diagram...")
    p = Parser()
    p.parse(test1)

    if p.graph_roots:
        g = p.graph_roots[0]

        print("\nGenerating ASCII diagram using pydot layout...")

        layout = Layout(g)

        asci = layout.draw()

        res = asci.to_string()

        with open("a.tmp", "w", encoding="utf-8") as f:
            f.write(res)

    else:
        print("No graph found in the input")
