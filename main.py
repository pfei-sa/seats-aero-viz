from datetime import datetime, timedelta
from typing import List, Tuple

import streamlit as st
import humanize
import altair as alt

from src.api import Availability, PARTNERS
from src.plot import get_route_df
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

if "route" not in st.session_state:
    st.session_state.route = "JFK -> HND -> BKK -> NRT, HND -> JFK"

route = st.text_input(
    "Route", max_chars=100, key="route"
).upper()

col1, col2 = st.columns(2)

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


def canonicalize_route(route: str) -> List[Tuple[str, str]]:
    route = route.replace(" ", "")
    segs = route.split(",")
    res = []
    for seg in segs:
        stops = seg.split("->")
        res.extend([(org, dest) for org, dest in zip(stops[:-1], stops[1:])])
    return res


time_since_cache = time.now() - cache_freshness

route_df = get_route_df(availabilities, canonicalize_route(route), airlines, fares)

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
            sort=[f"{org} -> {dest}" for org, dest in canonicalize_route(route)],
            header=alt.Header(labelAngle=0, labelAlign="left", labelFontSize=14),
            title=None,
        ),
    )
)

st.caption(f"Data last refreshed {humanize.naturaldelta(time_since_cache)} ago")
st.altair_chart(
    chart,
    use_container_width=True,
    theme=None,
)

for org, dest in canonicalize_route(route):
    seg_str = f"{org} -> {dest}"
    if seg_str not in route_df["route"].unique():
        st.warning(f"No availability found for {seg_str}")
