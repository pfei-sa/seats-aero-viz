import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Set

import requests
from streamlit import secrets

PARTNERS = [
    "aeroplan",
    "aeromexico",
    "american",
    "united",
    "delta",
    "emirates",
    "etihad",
    "virginatlantic",
]


def partner_to_display_name(partner: str) -> str:
    return {
        "aeroplan": "Aeroplan",
        "aeromexico": "Aeromexico",
        "american": "American Airlines",
        "united": "United Airlines",
        "delta": "Delta Airlines",
        "emirates": "Emirates",
        "etihad": "Etihad",
        "virginatlantic": "Virgin Atlantic",
    }[partner]


@dataclass
class Route:
    id: str
    origin_airport: str
    origin_region: str
    destination_airport: str
    destination_region: str
    num_days_out: int
    distance: int
    source: str

    @staticmethod
    def from_dict(d: Dict) -> "Route":
        raw = d
        return Route(
            id=raw["ID"],
            origin_airport=raw["OriginAirport"],
            origin_region=raw["OriginRegion"],
            destination_airport=raw["DestinationAirport"],
            destination_region=raw["DestinationRegion"],
            num_days_out=raw["NumDaysOut"],
            distance=raw["Distance"],
            source=raw["Source"],
        )

    @staticmethod
    def from_json(json_str: str) -> "Route":
        return Route.from_dict(json.loads(json_str))

    @staticmethod
    def fetch() -> List["Route"]:
        url = "https://seats.aero/api/routes"
        response = requests.get(
            url, headers={"Partner-Authorization": secrets["api_key"]}
        )
        all_routes = json.loads(response.text)
        return [Route.from_dict(route) for route in all_routes]


@dataclass
class Availability:
    """From following go struct:
        type Availability struct {
        ID         string
        RouteID    string
        Route      *Route
        Date       string
        ParsedDate time.Time

        YAvailable bool
        WAvailable bool
        JAvailable bool
        FAvailable bool

        YMileageCost string
        WMileageCost string
        JMileageCost string
        FMileageCost string

        YRemainingSeats uint32
        WRemainingSeats uint32
        JRemainingSeats uint32
        FRemainingSeats uint32

        YAirlines string
        WAirlines string
        JAirlines string
        FAirlines string

        YDirect bool
        WDirect bool
        JDirect bool
        FDirect bool

        Source            string
        ComputedLastSeen  string
        APITermsOfUse     string
    }
    """

    id: str
    route_id: str
    route: Route
    date: str
    parsed_date: datetime

    y_available: bool
    w_available: bool
    j_available: bool
    f_available: bool

    y_mileage_cost: str
    w_mileage_cost: str
    j_mileage_cost: str
    f_mileage_cost: str

    y_remaining_seats: int
    w_remaining_seats: int
    j_remaining_seats: int
    f_remaining_seats: int

    y_airlines: str
    w_airlines: str
    j_airlines: str
    f_airlines: str

    y_direct: bool
    w_direct: bool
    j_direct: bool
    f_direct: bool

    source: str
    computed_last_seen: str

    def available(self, code: str) -> bool:
        raw = getattr(self, f"{code.lower()}_available")
        return raw if raw is not None else False

    def mileage_cost(self, code: str) -> str:
        raw = getattr(self, f"{code.lower()}_mileage_cost")
        return raw if raw is not None else ""

    def remaining_seats(self, code: str) -> int:
        raw = getattr(self, f"{code.lower()}_remaining_seats")
        return raw if raw is not None else 0

    def airlines(self, code: str) -> str:
        raw = getattr(self, f"{code.lower()}_airlines")
        return raw if raw is not None else ""

    def direct(self, code: str) -> bool:
        raw = getattr(self, f"{code.lower()}_direct")
        return raw if raw is not None else False

    def all_airlines(self) -> Set[str]:
        res = set()
        for code in ["Y", "W", "J", "F"]:
            res.update(
                airline.strip()
                for airline in self.airlines(code).split(",")
                if airline.strip() != ""
            )
        return res

    @staticmethod
    def from_dict(d: Dict, route_map: dict[str, Route]) -> "Availability":
        raw = d
        return Availability(
            id=raw["ID"],
            route_id=raw["RouteID"],
            route=route_map[raw["RouteID"]],
            date=raw["Date"],
            # parse from 2023-05-24T00:00:00Z to datetime
            parsed_date=datetime.strptime(raw["ParsedDate"], "%Y-%m-%dT%H:%M:%SZ"),
            y_available=raw["YAvailable"],
            w_available=raw["WAvailable"],
            j_available=raw["JAvailable"],
            f_available=raw["FAvailable"],
            y_mileage_cost=raw["YMileageCost"],
            w_mileage_cost=raw["WMileageCost"],
            j_mileage_cost=raw["JMileageCost"],
            f_mileage_cost=raw["FMileageCost"],
            y_remaining_seats=raw["YRemainingSeats"],
            w_remaining_seats=raw["WRemainingSeats"],
            j_remaining_seats=raw["JRemainingSeats"],
            f_remaining_seats=raw["FRemainingSeats"],
            y_airlines=raw["YAirlines"],
            w_airlines=raw["WAirlines"],
            j_airlines=raw["JAirlines"],
            f_airlines=raw["FAirlines"],
            y_direct=raw["YDirect"],
            w_direct=raw["WDirect"],
            j_direct=raw["JDirect"],
            f_direct=raw["FDirect"],
            source=raw["Source"],
            computed_last_seen=raw["ComputedLastSeen"],
        )

    @staticmethod
    def fetch(
        route_map: dict[str, Route], partner: str = "aeroplan"
    ) -> List["Availability"]:
        url = f"https://seats.aero/api/availability?source={partner}"
        response = requests.get(
            url, headers={"Partner-Authorization": secrets["api_key"]}
        )
        all_availabilities = json.loads(response.text)
        return [
            Availability.from_dict(availability, route_map)
            for availability in all_availabilities
        ]

    def airline_str(self) -> str:
        return "\n".join(
            [
                f"{code}: ({self.airlines(code)})"
                for code in ["Y", "J", "F"]
                if self.airlines(code)
            ]
        )

    def fare_code_str(self) -> str:
        return " ".join(code for code in ["Y", "J", "F"] if self.available(code))

    def route_str(self) -> str:
        return f"{self.route.origin_airport} -> {self.route.destination_airport}"
