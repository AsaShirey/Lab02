import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def visualize():
    resultsPath = Path(__file__).resolve().parent.parent / "results.json"
    csvPath = Path(__file__).resolve().parent.parent / "data.csv"

    st.title("How Has Number Usage Changed Over Time?")

    # Read the number counts from results.json
    data = {}
    if resultsPath.exists():
        try:
            with open(resultsPath, "r") as file:
                savedData = json.load(file)

            if not isinstance(savedData, dict):
                st.error("results.json is not a dictionary.")
            else:
                for year, numbers in savedData.items():
                    if not str(year).isdigit() or not isinstance(numbers, dict):
                        continue
                    data[year] = {}
                    for number, count in numbers.items():
                        if str(number).isdigit() and type(count) == int and count >= 0:
                            data[year][number] = count
        except (OSError, ValueError, json.JSONDecodeError) as error:
            st.error(f"Could not read results.json: {error}")
    else:
        st.warning("No results found yet.")

    if len(data) > 0:
        st.header("Total Number Frequency by Year")
        years = []
        totals = []

        for year, numbers in data.items():
            total = 0
            for number, count in numbers.items():
                total += count
            years.append(int(year))
            totals.append(total)

        fig, ax = plt.subplots()
        ax.scatter(years, totals)
        ax.set_title("Number Frequency Over Time")
        ax.set_xlabel("Year")
        ax.set_ylabel("Total Numerical Occurrences")
        st.pyplot(fig)
        plt.close(fig)

        st.header("Frequency of a Specific Number")
        allNumbers = []
        for year, numbers in data.items():
            for number in numbers:
                if number not in allNumbers:
                    allNumbers.append(number)
        allNumbers.sort(key=int)

        if len(allNumbers) > 0:
            if st.session_state.get("selectedNumber") not in allNumbers:
                st.session_state.selectedNumber = allNumbers[0]

            st.selectbox("Select a number:", allNumbers, key="selectedNumber")
            selected = st.session_state.selectedNumber

            years = []
            frequencies = []
            for year, numbers in data.items():
                years.append(int(year))
                frequencies.append(numbers.get(selected, 0))

            df = pd.DataFrame({"Year": years, "Frequency": frequencies})
            df = df.sort_values("Year").set_index("Year")
            st.line_chart(df)
        else:
            st.info("No numbers found in the articles.")
    else:
        st.info("No valid results to graph yet.")

    # Graphs from the survey CSV
    st.divider()
    st.header("Submitted Articles")

    if not csvPath.exists() or csvPath.stat().st_size == 0:
        st.info("No survey data yet.")
        return

    try:
        articles = pd.read_csv(csvPath)
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError):
        st.error("Could not read data.csv.")
        return

    if not all(column in articles.columns for column in ["Title", "Year", "Link"]):
        st.error("The CSV needs Title, Year, and Link columns.")
        return

    articles["Year"] = pd.to_numeric(articles["Year"], errors="coerce")
    articles = articles.dropna(subset=["Year"])
    if articles.empty:
        st.info("Submit articles to see the CSV graphs.")
        return

    articles["Year"] = articles["Year"].astype(int)
    yearCounts = articles.groupby("Year").size().sort_index()

    st.header("Articles Submitted per Year")
    fig, ax = plt.subplots()
    ax.bar(yearCounts.index.astype(str), yearCounts.values)
    ax.set_title("Articles by Publication Year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Articles")
    plt.xticks(rotation=45)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.header("Total Articles Through a Selected Year")
    selectedYear = st.select_slider("Select a year:", options=yearCounts.index.tolist(),
                                    value=int(yearCounts.index.max()), key="csvYear")
    totalByYear = yearCounts.cumsum()
    totalByYear = totalByYear[totalByYear.index <= selectedYear]
    st.line_chart(pd.DataFrame({"Total Articles": totalByYear}))


visualize()
