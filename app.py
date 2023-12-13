import os
import html
import streamlit as st
import googlemaps
import openai
import re


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        if st.session_state["password"] == st.secrets["general"]["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        return True


if check_password():
    # Obtain the API key from the environment variables
    GOOGLEMAPS_API_KEY = st.secrets["general"]["GOOGLEMAPS_API_KEY"]
    OPENAI_API_KEY = st.secrets["general"]["OPENAI_API_KEY"]

    # Initialize the Google Maps client
    gmaps = googlemaps.Client(key=GOOGLEMAPS_API_KEY)
    openai.api_key = OPENAI_API_KEY

    sample_prompt = """If I am leaving from 7709 W 20th Ave, Hialeah, FL 33014. Make me a fuel efficient route to visit all these addresses. They don't have to be in that order. Just go based off distance and whatever is nearby.

    15750 SW 72nd St, Miami, FL 33193
    6954 Bottle Brush Dr, Miami Lakes, FL 33014
    6715 W 26th Dr Bldg 6 Apt. 104, Hialeah, FL, 33016
    9728 NW 25th Ave, Miami, FL, 33147
    14982 SW 71st St, Miami, FL. 33193
    8600 NW 107 AVENUE, DORAL, FL 33178
    265 E 5 STREET, HIALEAH, FL 33010
    450 BIRD ROAD, CORAL GABLES, FL 33146
    4899 NW 24 AVENUE, MIAMI, FL 33142
    18180 SW 122 AVENUE, MIAMI, FL 33177
    1901 North Federal Highway, Hollywood, FL 33020
    7709 W 20th Ave, Hialeah, FL 33014
    """

    st.title("Z Roofing AI Route Planner")
    conversation = st.text_area(
        "Enter your request (start with the main address and then list the rest of the addresses one per line)",
        height=200,
        value=sample_prompt,
    )

    if st.button("Plan route"):
        # Generate a response from ChatGPT
        response = openai.ChatCompletion.create(
            model="text-davinci-003",
            messages=[
                {"role": "system", "content": "ZRW Route Creation"},
                {"role": "user", "content": conversation},
            ],
        )

        # Extract the addresses from the user's input
        addresses = re.findall(r"\d{1,5} .+, .+, .+ \d{5}", conversation)

        # Assume the first address is the origin and the last address is the destination
        # Other addresses are considered as waypoints
        origin = addresses[0]
        destination = addresses[-1]
        waypoints = addresses[1:-1]

        # Request directions with driving mode
        # Request directions with driving mode
        try:
            directions_result = gmaps.directions(
                origin=origin,
                destination=destination,
                waypoints=waypoints,
                mode="driving",
                optimize_waypoints=True,
            )
        except googlemaps.exceptions.ApiError as e:
            st.write(f"Error generating directions: {e}")
            st.stop()

        # Process the directions_result
        for i, leg in enumerate(directions_result[0]["legs"]):
            start_address = leg["start_address"]
            if i != len(directions_result[0]["legs"]) - 1:
                st.write(f"Step {i + 1}\n\n{start_address}\n")
            else:
                end_address = leg["end_address"]
                st.write(f"Step {i + 1}\n\n{start_address}\n\n{end_address}\n")

            # Process the directions_result
            optimized_order = directions_result[0]["waypoint_order"]

            # Create the URL for Google Maps
            url = "https://www.google.com/maps/dir/"

            # Add the start location to the URL
            url += origin.replace(" ", "+")

            # Add each waypoint in the optimized order to the URL
            for index in optimized_order:
                waypoint = waypoints[index].replace(" ", "+")
                url += "/" + waypoint

            # Add the destination to the URL
            url += "/" + destination.replace(" ", "+")

            st.write(f"[Open in Google Maps]({url})")
