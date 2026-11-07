import streamlit as st
import pandas as pd
import csv
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from Analyze import analyzeArticles

st.set_page_config(page_title="Survey", page_icon="📝")

# Page title and directions
st.title("Data Collection Survey 📝")
st.write("Please fill out the form below to add your data to the dataset.")
st.write("Enter the Title, Year of publication, and the link to your publicly accessible article.")

csvPath = Path(__file__).resolve().parent.parent / "data.csv"
jsonPath = Path(__file__).resolve().parent.parent / "data.json"

with st.form("survey_form"):
    title = st.text_input("Title")
    year = st.text_input("Year")
    link = st.text_input("Link")
    submitted = st.form_submit_button("Submit Data")

if submitted:
    title = title.strip()
    year = year.strip()
    link = link.strip()

    parsedLink = urlparse(link)

    if title == "":
        st.error("Please enter a title.")
    elif len(year) != 4 or not year.isdigit():
        st.error("Please enter a four-digit year.")
    elif parsedLink.scheme not in ("http", "https") or parsedLink.netloc == "":
        st.error("Please enter a valid article link.")
    else:
        try:
            # Read the JSON before adding the new article
            if jsonPath.exists():
                with open(jsonPath, "r") as file:
                    data = json.load(file)
            else:
                data = {}

            if not isinstance(data, dict):
                raise ValueError("data.json must contain a dictionary")

            # Add the article to the CSV
            addHeader = not csvPath.exists() or csvPath.stat().st_size == 0
            with open(csvPath, "a", newline="") as file:
                writer = csv.writer(file)
                if addHeader:
                    writer.writerow(["Title", "Year", "Link"])
                writer.writerow([title, year, link])

            # Add the article to the JSON dictionary
            if year in data:
                data[year][title] = link
            else:
                data[year] = {title: link}

            with open(jsonPath, "w") as file:
                json.dump(data, file, indent=4)

            st.success("Article saved!")

            try:
                with st.spinner("Analyzing articles..."):
                    failed = analyzeArticles(year)
                if len(failed) > 0:
                    st.warning("Some articles could not be analyzed.")
                else:
                    st.success("The results have been updated.")
            except (OSError, ValueError, json.JSONDecodeError) as error:
                st.warning(f"The article was saved, but analysis failed: {error}")

        except (OSError, ValueError, json.JSONDecodeError) as error:
            st.error(f"Could not save the article: {error}")

# Display the current CSV data
st.divider()
st.header("Current Data in CSV")

if csvPath.exists() and csvPath.stat().st_size > 0:
    try:
        currentData = pd.read_csv(csvPath)
        if currentData.empty:
            st.info("No articles have been submitted yet.")
        else:
            st.dataframe(currentData)
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError):
        st.error("Could not read the CSV file.")
else:
    st.info("No articles have been submitted yet.")
