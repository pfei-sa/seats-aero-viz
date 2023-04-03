from datetime import datetime, timedelta
from typing import List, Tuple

import streamlit as st
import humanize

from src.api import Availability, PARTNERS
from src.plot import plot_route
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
    "Route", "JFK -> HND -> BKK -> NRT, HND -> JFK", max_chars=100
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

st.caption(f"Data last refreshed {humanize.naturaldelta(time_since_cache)} ago")
st.altair_chart(
    plot_route(
        availabilities, canonicalize_route(route), airlines, fares
    ).interactive(),
    use_container_width=True,
    theme=None,
)
