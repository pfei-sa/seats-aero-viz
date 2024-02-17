# [Seats.aero](https://Seats.aero) visualizer

> This is a personal project to visualize the seat map of an aircraft. It is not affiliated with [Seats.aero](https://Seats.aero) in any way.

Booking a multi-segment flight can be a pain. Checking the availability of seats on each leg manually using [Seats.aero](https://Seats.aero) is not fun. This project aims to make it easier to scan the availability of your preferred route. 

## Features

- Visualize the availability of seats over time across multiple legs
- Filter by cabin classes and airlines
- Country and city code expansion
  - For example, `US` will expand to all US airports and `NYC` will expand to all airports in New York City.

# [✈️Try Now!✈️](https://seats-aero-viz.streamlit.app/)

## Screenshot
> ![image](https://user-images.githubusercontent.com/4657356/231931895-d5d7b6a7-e46c-43ce-bc75-7bc5cded2bad.png)

## Running Locally

- Clone the repo
- Install the requirements using `poetry install`
- Run the app using `streamlit run main.py`
- Create file `.streamlit/secrets.toml` with `api_key = "YOUR_API_KEY"`