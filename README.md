# T20 Player Comparison

Streamlit app to compare two T20 players (batting or bowling) by year range and competition: strike rate, dot ball %, boundary %, phase splits (powerplay, middle, death), first 10 balls vs after, economy and more.

Run locally:

    pip install -r requirements.txt
    streamlit run app.py

`prep.py` rebuilds the summary tables from the Cricsheet `all_json.zip` download.

Data: ball-by-ball data from [Cricsheet](https://cricsheet.org), licensed under the Open Data Commons Attribution License. Matches involving Afghanistan and some older matches are not included, so totals can be lower than official figures.
