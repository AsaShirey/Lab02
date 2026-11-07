import json
import requests
import trafilatura
from pathlib import Path


def analyzeArticles(target_year=None):
    # Read the article links
    dataPath = Path(__file__).resolve().parent / "data.json"
    resultsPath = Path(__file__).resolve().parent / "results.json"

    with open(dataPath, "r") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("data.json must contain a dictionary")

    results = {}
    if resultsPath.exists():
        with open(resultsPath, "r") as file:
            oldResults = json.load(file)
            if isinstance(oldResults, dict):
                for year, numbers in oldResults.items():
                    if str(year).isdigit() and isinstance(numbers, dict):
                        results[year] = numbers

    failed = []

    for year, articles in data.items():
        if not str(year).isdigit() or not isinstance(articles, dict):
            continue
        if target_year is not None and str(year) != str(target_year):
            continue

        resultsForYear = {}
        completed = 0

        for title, link in articles.items():
            if not isinstance(link, str) or not link.startswith(("http://", "https://")):
                failed.append(str(link))
                continue

            try:
                response = requests.get(link, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()
                text = trafilatura.extract(response.text)

                if text is None:
                    failed.append(link)
                    continue

                completed += 1
                currentNumber = ""

                # Count each group of consecutive digits
                for char in text + " ":
                    if char.isdigit():
                        currentNumber += char
                    elif currentNumber != "":
                        if currentNumber in resultsForYear:
                            resultsForYear[currentNumber] += 1
                        else:
                            resultsForYear[currentNumber] = 1
                        currentNumber = ""

            except requests.RequestException:
                failed.append(link)

        # Keep old results if the articles could not be downloaded
        if completed > 0 or len(articles) == 0:
            results[str(year)] = resultsForYear

    with open(resultsPath, "w") as file:
        json.dump(results, file, indent=4)

    return failed


if __name__ == "__main__":
    analyzeArticles()
