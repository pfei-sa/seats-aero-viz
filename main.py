from datetime import datetime, timedelta
from typing import List, Tuple

import streamlit as st

from src.api import Availability
from src.plot import plot_route


@st.cache_data
def load_availabilities(time: datetime) -> Tuple[List[Availability], datetime]:
    return Availability.fetch(), time.now()

st.title("Aero Seats Availability Visualizer")

col1, col2 = st.columns([5, 1])


def canonicalize_route(route: str) -> List[Tuple[str, str]]:
    """
    >>> canonicalize_route("JFK -> HND -> BKK,HND -> JFK")
    'JFK -> HND, HND -> BKK, HND -> JFK'
    """
    route = route.replace(" ", "")
    segs = route.split(",")
    res = []
    for seg in segs:
        stops = seg.split("->")
        res.extend([(org, dest) for org, dest in zip(stops[:-1], stops[1:])])
    return res

# Force cache refresh every 15 minutes by setting the cache key to
# the current time rounded down to the nearest 15 minutes.
clamped_time = datetime.now().replace(second=0, microsecond=0)
excess = clamped_time.minute % 15
clamped_time -= timedelta(minutes=excess)

availabilities, cache_freshness = load_availabilities(clamped_time)

route = st.text_input("Route", "JFK -> HND -> BKK -> HND -> JFK")

route_to_plot = [
    "JFK",
    "HND",
    "BKK",
    "HND",
    "JFK",
]
st.caption(f"Last data refresh: {cache_freshness}")
st.altair_chart(
    plot_route(
        availabilities, canonicalize_route(route), airline="NH", class_code="J"
    ).interactive(),
    use_container_width=True,
    theme=None
)
# %%
