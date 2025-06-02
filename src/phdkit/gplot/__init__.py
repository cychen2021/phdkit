"""A wrapper over matplotlib to easy plotting for research papers.

TODO
"""

from ..mid import infix


class Layer: ...


@infix
def on(top_layer: Layer, bottom_layer: Layer) -> Layer: ...
