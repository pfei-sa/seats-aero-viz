from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import altair as alt
import pandas as pd

from src.api import Availability


def plot_route(
    availabilities: List[Availability],
    canonical_route: List[Tuple[str, str]],
    airline: Optional[str] = None,
    class_code: Optional[str] = "J",
) -> alt.Chart:
    avail_dict = defaultdict(list)
    for availability in availabilities:
        leg = (
            availability.route.origin_airport,
            availability.route.destination_airport,
        )
        if leg not in avail_dict:
            avail_dict[leg] = []
        avail_dict[leg].append(availability)
    res = []
    for org, dest in canonical_route:
        for availability in avail_dict[(org, dest)]:
            res.append(
                {
                    "date": availability.parsed_date,
                    "route": availability.route_str(),
                    "airlines": availability.airline_str(),
                    "fare": availability.fare_code_str(),
                }
            )
    df = pd.DataFrame(res, columns=["date", "route", "airlines", "fare"])
    df = df[df["fare"].str.contains(class_code)]
    if airline:
        df = df[df["airlines"].str.contains(airline)]
    return (
        alt.Chart(df)
        .mark_circle(size=90)
        .encode(
            y=alt.Y(
                "route",
                scale=alt.Scale(domain=[f"{org} -> {dest}" for org, dest in canonical_route]),
                sort=[f"{org} -> {dest}" for org, dest in canonical_route]
            ),
            x=alt.X("date", scale=alt.Scale(zero=False, clamp=True, nice=True)),
            color="fare",
            tooltip=["airlines", "fare", "date"],
        )
    )
