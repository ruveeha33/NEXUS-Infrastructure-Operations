"""Compact resource telemetry with explicit adaptive scales."""

import math

from rich.text import Text
from textual.widgets import Static


def graph_scale(samples):

    values = [
        max(0.0, min(100.0, float(value)))
        for value in samples
        if math.isfinite(float(value))
    ]

    peak = max(values, default=0)

    return next(
        scale
        for scale in (1, 5, 10, 25, 50, 75, 100)
        if peak <= scale
    )


class CompactGraph(Static):

    LEVELS = "▁▂▃▄▅▆▇█"

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.samples = []

    def set_samples(self, samples):

        self.samples = [
            max(0.0, min(100.0, float(value)))
            for value in samples
            if math.isfinite(float(value))
        ][-120:]

        self.refresh_graph()

    def on_resize(self, event):

        self.refresh_graph()

    def refresh_graph(self):

        scale = graph_scale(self.samples)

        width = max(
            8,
            min(75, self.size.width - 3),
        )

        samples = self.samples[-width:]

        color = {
            "cpu-graph": "#59dfc4",
            "memory-graph": "#83b8eb",
            "disk-graph": "#b6a5e4",
        }.get(self.id, "#59dfc4")

        result = Text()

        if not samples:

            result.append(
                "Collecting telemetry...",
                style="#819eaf",
            )

        else:

            for value in samples:

                if value == 0:

                    result.append(
                        "·",
                        style="#38505e",
                    )

                else:

                    level = min(
                        7,
                        max(
                            0,
                            math.ceil(
                                value / scale * 8
                            ) - 1,
                        ),
                    )

                    result.append(
                        self.LEVELS[level],
                        style=color,
                    )

        result.append(
            f"\nAdaptive scale: 0–{scale}%"
            f"  |  {len(samples)} samples",
            style="#819eaf",
        )

        self.update(result)
