from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from itertools import product

import streamlit as st
import humanize
import altair as alt
import airportsdata

from src.api import Availability, PARTNERS
from src.plot import get_route_df
from src.airport import city_expansion_dict, country_expansion_dict
from datetime import datetime as time

st.set_page_config(
    page_title="Seats.aero Availability Visualizer",
    page_icon=":airplane:",
)

with st.sidebar:
    st.title("Partners")
    partner = st.radio(
        "Partners",
        PARTNERS,
        index=PARTNERS.index("lifemiles"),
        label_visibility="hidden",
    )


@st.cache_data(ttl=timedelta(minutes=15))
def load_availabilities(partner: str) -> Tuple[List[Availability], datetime]:
    return Availability.fetch(partner), time.now()


st.title("✈️Seats.areo Availability Visualizer")

availabilities, cache_freshness = load_availabilities(partner)

all_fares = ["Y", "W", "F", "J"]
all_airlines = set()
for a in availabilities:
    for fare in all_fares:
        all_airlines.update(
            f.strip() for f in a.airlines(fare).split(",") if f.strip() != ""
        )

route = st.text_input(
    "Route", "JFK -> HND -> BKK -> NRT, HND -> JFK", max_chars=300, key="route"
).upper()

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
    expand_country = st.checkbox("Expand country", value=True)
    expand_city = st.checkbox("Expand city", value=True)


def canonicalize_route(
    route: str, expand_country: bool = False, expand_city: bool = False
) -> List[Tuple[str, str]]:
    route = route.replace(" ", "")
    segs = route.split(",")
    res = []
    for seg in segs:
        stops = seg.split("->")
        res.extend([(org, dest) for org, dest in zip(stops[:-1], stops[1:])])
    return expand_route(res, expand_country, expand_city)


def expand_route(
    route: List[Tuple[str, str]], expand_country: bool, expand_city: bool
) -> List[Tuple[str, str]]:
    res = []
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

route_df = get_route_df(availabilities, canonicalized_route, airlines, fares)

chart = (
    alt.Chart(route_df)
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
            sort=[f"{org} -> {dest}" for org, dest in canonicalized_route],
            header=alt.Header(labelAngle=0, labelAlign="left", labelFontSize=14),
            title=None,
            spacing=-10,
        ),
    )
)

st.caption(f"Data last refreshed {humanize.naturaldelta(time_since_cache)} ago")
st.altair_chart(
    chart,
    use_container_width=True,
    theme=None,
)

with st.expander("Route without availability"):
    for org, dest in canonicalized_route:
        seg_str = f"{org} -> {dest}"
        if seg_str not in route_df["route"].unique():
            st.warning(f"No availability found for {seg_str}")
