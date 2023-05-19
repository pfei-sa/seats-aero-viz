from collections import defaultdict
from typing import Dict, List, Tuple

import pandas as pd

from seats_aero.api import Availability


def get_route_df(
    availabilities: List[Availability],
    canonical_route: List[Tuple[str, str]],
    airlines: List[str] = [],
    class_code: List[str] = [],
) -> pd.DataFrame:
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
                        "direct": availability.direct(fare),
                    }
                )
    if len(airlines_set) > 0:
        res = [
            r
            for r in res
            if len(
                set(airline.strip() for airline in r["airlines"].split(","))
                & airlines_set
            )
            > 0
        ]
    if len(class_code_set) > 0:
        res = [r for r in res if len(set(r["fare"].split(" ")) & class_code_set) > 0]
    df = pd.DataFrame(res)
    return df
