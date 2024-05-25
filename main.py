from datetime import datetime, timedelta
from datetime import datetime as time
from itertools import product
from typing import List, Set, Tuple

import altair as alt
import humanize
import pandas as pd
import streamlit as st

from seats_aero.airport import city_expansion_dict, country_expansion_dict
from seats_aero.api import Availability, Route, partners, partners_mapping
from seats_aero.plot import get_route_df

st.set_page_config(
    page_title="Seats.aero Availability Visualizer",
    page_icon=":airplane:",
)

st.title("✈️Seats.aero Availability Visualizer")

with st.sidebar:
    st.title("Partners")
    default_partner = "aeroplan"
    partner = (
        st.radio(
            "Partners",
            partners,
            format_func=partners_mapping.get,
            label_visibility="hidden",
        )
        or default_partner
    )


default_route = "US - LHR - NYC, CA - HKG"
route = st.text_input("Route", default_route, max_chars=300, key="route").upper()


@st.cache_data(ttl=timedelta(minutes=15))
def load_availabilities(partner: str) -> Tuple[List[Availability], datetime]:
    routes = Route.fetch()
    route_map = {r.id: r for r in routes}
    return Availability.fetch(route_map, partner), time.now()


availabilities, cache_freshness = load_availabilities(partner)

all_possible_routes = set(
    (a.route.origin_airport, a.route.destination_airport) for a in availabilities
)

all_fares = ["Y", "W", "F", "J"]
all_airlines: Set[str] = set()
for a in availabilities:
    for fare in all_fares:
        all_airlines.update(
            f.strip() for f in a.airlines(fare).split(",") if f.strip() != ""
        )

col1, col2, col3 = st.columns([3, 3, 2])

with col1:
    airlines = st.multiselect(
        "Airlines to include (e.g. UA)",
        all_airlines,
    )

with col2:
    fares = st.multiselect(
        "Fares to include (e.g. J)",
        all_fares,
    )

with col3:
    expand_country = st.checkbox(
        "Expand country",
        value=True,
        help="ISO 3166-1 alpha-2 codes. See https://en.wikipedia.org/wiki/ISO_3166-1#Current_codes.",
    )
    expand_city = st.checkbox(
        "Expand city",
        value=True,
        help=f"Currently only supports {', '.join(city_expansion_dict().keys())}",
    )


def canonicalize_route(
    route: str, expand_country: bool = False, expand_city: bool = False
) -> List[Tuple[str, str]]:
    route = route.replace(" ", "").replace("->", "-")
    segs = route.split(",")
    res = []
    for seg in segs:
        stops = seg.split("-")
        res.extend([(org, dest) for org, dest in zip(stops[:-1], stops[1:])])
    return expand_route(res, expand_country, expand_city)


def expand_route(
    route: List[Tuple[str, str]], expand_country: bool, expand_city: bool
) -> List[Tuple[str, str]]:
    res: List[Tuple[str, str]] = []
    for org, dest in route:
        res.extend(
            product(
                expand_code(org, expand_country, expand_city),
                expand_code(dest, expand_country, expand_city),
            )
        )
    return res


def expand_code(code: str, expand_country: bool, expand_city: bool) -> List[str]:
    if expand_country and code in country_expansion_dict():
        return country_expansion_dict()[code]
    if expand_city and code in city_expansion_dict():
        return city_expansion_dict()[code]
    return [code]


time_since_cache = time.now() - cache_freshness

canonicalized_route = canonicalize_route(route, expand_city, expand_country)
filtered_route = [
    route for route in canonicalized_route if route in all_possible_routes
]

route_df = get_route_df(availabilities, filtered_route, airlines, fares)

st.caption(
    f"Fetched {humanize.intword(len(availabilities))} availabilities {humanize.naturaldelta(time_since_cache)} ago"
)

if len(route_df) == 0:
    st.error("No route found")
    st.stop()

chart = (
    alt.Chart(route_df)
    .mark_point(size=100, filled=True)
    .encode(
        y=alt.Y(
            "fare",
            axis=alt.Axis(
                title=None,
                labels=False,
                ticks=False,
                domain=False,
                domainWidth=0,
            ),
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
        tooltip=["airlines", "fare", "date", "freshness", "direct"],
        row=alt.Row(
            "route",
            sort=[f"{org} -> {dest}" for org, dest in filtered_route],
            header=alt.Header(
                labelAngle=0, labelAlign="left", labelFontSize=14, labelFont="monospace"
            ),
            title=None,
            spacing=-10,
        ),
        opacity=alt.condition(
            alt.datum.direct,
            alt.value(1),
            alt.value(0.5),
        ),  # type: ignore
    )
    .properties(height=alt.Step(12))
    .interactive()
)

st.altair_chart(
    chart,
    use_container_width=True,
    theme=None,
)

displayed_route = set(route_df["route"].unique())

with st.expander("Raw data"):
    st.write(route_df)

with st.expander("Route without availability"):
    st.write(
        pd.DataFrame(
            [
                f"{org} -> {dest}"
                for i, (org, dest) in enumerate(canonicalized_route)
                if (org, dest) not in displayed_route and i < 1000
            ],
            columns=["Route"],
        )
    )
    if len(canonicalized_route) > 1000:
        st.write(f"and {len(canonicalized_route) - 1000} more...")
