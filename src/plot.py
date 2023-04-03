from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import altair as alt
import pandas as pd

from src.api import Availability


def plot_route(
    availabilities: List[Availability],
    canonical_route: List[Tuple[str, str]],
    airlines: List[str] = [],
    class_code: List[str] = [],
) -> alt.Chart:
    airlines_set = set(airlines)
    class_code_set = set(class_code)
    avail_dict: Dict[Tuple[str, str], List[Availability]] = defaultdict(list)
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
            for fare in ["Y", "W", "F", "J"]:
                if not availability.available(fare):
                    continue
                res.append(
                    {
                        "date": availability.parsed_date,
                        "route": availability.route_str(),
                        "airlines": availability.airlines(fare),
                        "fare": fare,
                        "freshness": availability.computed_last_seen,
                    }
                )
    if len(airlines_set) > 0:
        res = [r for r in res if len(set(r["airlines"].split(",")) & airlines_set) > 0]
    if len(class_code_set) > 0:
        res = [r for r in res if len(set(r["fare"].split(" ")) & class_code_set) > 0]
    df = pd.DataFrame(res, columns=["date", "route", "airlines", "fare", "freshness"])
    return (
        alt.Chart(df)
        .mark_circle(size=90)
        .encode(
            y=alt.Y(
                "fare",
                axis=None,
            ),
            x=alt.X(
                "date:T",
                axis=alt.Axis(format="%Y-%m-%d"),
                scale=alt.Scale(zero=False, clamp=True, nice=True),
            ),
            color=alt.Color(
                "fare",
                legend=alt.Legend(
                    orient="top",
                ),
                title="Fare",
                scale=alt.Scale(
                    domain=["Y", "W", "J", "F"],
                    range=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
                ),
            ),
            tooltip=["airlines", "fare", "date", "freshness"],
            row=alt.Row(
                "route",
                sort=[f"{org} -> {dest}" for org, dest in canonical_route],
                header=alt.Header(labelAngle=0, labelAlign="left", labelFontSize=14),
                title=None,
            ),
        )
    )
