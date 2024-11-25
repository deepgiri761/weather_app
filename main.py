from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import SelectField
from datetime import datetime
import requests
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

# API Configuration
API_BASE = "https://api.countrystatecity.in/v1/countries"
API_KEY = os.environ.get("API_KEY")
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
WEATHER_KEY = os.environ.get("WEATHER_KEY")
HEADERS = {'X-CSCAPI-KEY': API_KEY}


class MultiSelectForm(FlaskForm):
    country = SelectField('Select Country', choices=[])
    state = SelectField('Select State', choices=[])
    city = SelectField('Select City', choices=[])


def fetch_api_data(url):
    """Fetch data from the API and handle errors gracefully."""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return []


def fetch_weather_api_data(lat, lon):
    """Fetch data from the API and handle errors gracefully."""
    try:
        response = requests.get(WEATHER_URL, params={"lat": lat, "lon": lon, "appid": WEATHER_KEY})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return []


def get_country_choices():
    countries = fetch_api_data(API_BASE)
    return [{"name": country['name'], "iso2": country['iso2']} for country in countries]


def get_state_choices(country_iso2):
    if not country_iso2:
        return []
    url = f"{API_BASE}/{country_iso2}/states"
    states = fetch_api_data(url)
    return [{"name": state['name'], "iso2": state['iso2']} for state in states]


def get_city_choices(country_iso2, state_iso2):
    if not country_iso2 or not state_iso2:
        return []
    url = f"{API_BASE}/{country_iso2}/states/{state_iso2}/cities"
    cities = fetch_api_data(url)
    return cities


@app.route("/", methods=["POST", "GET"])
def home():
    countries = get_country_choices()
    country_choices = [(country['iso2'], country['name']) for country in countries]

    # Initialize all select forms
    form = MultiSelectForm()
    form.country.choices = country_choices
    form.state.choices = []
    form.city.choices = []

    weather_data = None
    current_date = None
    click_value = None

    # Handle POST request from user
    if request.method == "POST":
        selected_country_iso2 = request.form.get("country")
        selected_state_iso2 = request.form.get("state")
        selected_city = request.form.get("city")

        # Update state choices
        if selected_country_iso2:
            states = get_state_choices(selected_country_iso2)
            form.state.choices = [(state['iso2'], state['name']) for state in states]

        # Update city choices
        if selected_country_iso2 and selected_state_iso2:
            cities = get_city_choices(selected_country_iso2, selected_state_iso2)
            form.city.choices = [(city['name'], city['name']) for city in cities]

            #Fetch weather details from user select city
            if selected_city:
                selected_city_latitude = [city["latitude"] for city in cities if city["name"] == selected_city]
                selected_city_longitude = [city["longitude"] for city in cities if city["name"] == selected_city]
                weather_data = fetch_weather_api_data(selected_city_latitude, selected_city_longitude)
                current_date = datetime.now().strftime("%A, %B %d, %Y")

    #Handle user select degree
    if request.method == "POST":
        click_value = request.form.get('unit')

    return render_template(
        "index.html",
        form=form,
        data=weather_data,
        date=current_date,
        change_value=click_value
    )


if __name__ == "__main__":
    app.run(debug=False)
