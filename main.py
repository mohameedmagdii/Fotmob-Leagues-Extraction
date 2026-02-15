import streamlit as st
import pandas as pd
import numpy as np
import requests
import random
from datetime import datetime, timedelta

class FotmobAPI:
    @staticmethod
    def get_id_from_url(url):
        # Extract the league ID from the URL
        try:
            return url.split('/')[4]
        except IndexError:
            raise ValueError("Invalid URL format")

    @staticmethod
    def add_hours_and_format(utc_time):
        # Handle input with optional milliseconds
        if "." in utc_time:
            dt = datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            dt = datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%SZ")

        # Add 3 hours to the time
        new_time = dt + timedelta(hours=2)

        # Return the time in the desired format 'YYYY-MM-DD HH:MM:SS'
        return new_time.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def request_send(link):
        uastrings = [
            "Mozilla/5.0 (Linux; U; Android 2.3.4; fr-fr; HTC Desire Build/GRJ22) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14931",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
            "Mozilla/5.0 (Linux; U; Android 2.3.5; en-us; HTC Vision Build/GRI40) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.71 Safari/537.36",
        ]
        user_agent = random.choice(uastrings)
        headers = {'User-Agent': user_agent}
        response = requests.get(link, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        return response_json

    @staticmethod
    def get_league_matches(league_id):
        league_api_url = f"https://www.fotmob.com/api/leagues?id={league_id}&ccode3=EGY"
        league_matches = FotmobAPI.request_send(league_api_url)
        try:
            matchesDf = pd.DataFrame(columns=['id', 'match_datetime', 'home_team', 'home_team_id', 'away_team', 'away_team_id',
                                              'league_id', 'season_id', 'Round', 'match_uri', 'finished', 'started',
                                              'cancelled'])
            matches_list = league_matches['matches']['allMatches']
            rows_list = [
                [
                    match.get('id'),
                    match.get('status', {}).get('utcTime'),
                    match.get('home', {}).get('name'),
                    match.get('home', {}).get('id'),
                    match.get('away', {}).get('name'),
                    match.get('away', {}).get('id'),
                    league_matches.get('details', {}).get('id'),
                    league_matches.get('details', {}).get('selectedSeason'),
                    match.get('round'),
                    match.get('pageUrl'),
                    match.get('status', {}).get('finished'),
                    match.get('status', {}).get('started'),
                    match.get('status', {}).get('cancelled')
                ]
                for match in matches_list
            ]

            rows_array = np.array(rows_list)
            matchesDf = pd.concat([matchesDf, pd.DataFrame(rows_array, columns=matchesDf.columns)], ignore_index=True)
            matchesDf['match_datetime'] = matchesDf['match_datetime'].apply(FotmobAPI.add_hours_and_format)
            matchesDf['match_name'] = matchesDf['home_team'] + ' vs ' + matchesDf['away_team']
            matchesDf.insert(0, 'match_name', matchesDf.pop('match_name'))
            return matchesDf
        except requests.exceptions.RequestException as e:
            st.error(f"Error: {e}")
            return pd.DataFrame()

# Streamlit application
st.title('League Matches Downloader')

url = st.text_input('Enter the league URL', '')
x_mas = st.text_input('Enter the X-Mas Header', '')
# Add a submit button
if st.button('Submit'):
    if url:
        try:
            league_id = FotmobAPI.get_id_from_url(url)
            st.write(f"League ID extracted: {league_id}")

            matches_df = FotmobAPI.get_league_matches(league_id)

            if not matches_df.empty:
                st.write("Matches data:")
                st.dataframe(matches_df)

                # Convert DataFrame to CSV and provide download link
                csv = matches_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name='league_matches.csv',
                    mime='text/csv'
                )
            else:
                st.write("No matches data available.")
        except ValueError as e:
            st.error(str(e))
    else:
        st.error("Please enter a URL.")


