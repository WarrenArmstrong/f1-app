## Links
Access my site at [dash.f1.warrenarmstrong.io](http://dash.f1.warrenarmstrong.io)  
[Github repo](https://github.com/WarrenArmstrong/f1-app)

## Table of Contents

- [Links](#links)
- [Table of Contents](#table-of-contents)
- [About](#about)
- [Screenshots](#screenshots)
- [Technologies](#technologies)
- [Setup](#setup)
- [Status](#status)
- [Credits](#credits)
- [License](#license)

## About
This app allows the user to view metrics and visualizations of Formula 1 data. It does this by taking the [Formula 1 World Championship](https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020) dataset from Kaggle, building it into a snowflake schema relational database. The app executes queries against this database in order to serve metrics and visualizations to the user.

## Screenshots

2021 Driver/Constructor World Championship Results:

![2021 Driver/Constructor World Championship Results](app/assets/readme_images/season_exhibit_700px.png?raw=true)  

Snowflake schema ER diagram:

![Snowflake schema ER diagram](app/assets/readme_images/er_diagram_700px.png?raw=true)

## Technologies
The webapp is written using [Plotly Dash](https://dash.plotly.com), a python library built on top of [Flask](https://flask.palletsprojects.com/en/2.2.x/) and [React.js](https://reactjs.org/). The ETL code is written using the [sqlalchemy](https://www.sqlalchemy.org/) python package, and the database is [Sqlite 3](https://www.sqlite.org/index.html).

## Setup
- download or clone the repository
- set the `KAGGLE_USERNAME` and `KAGGLE_KEY` environment variables
- run `pip install -r requirements.txt`
- run `( cd etl && python etl.py )`
- run `python app/index.py`
- connect at http://127.0.0.1:8050


## Status

The overall results page is nearly complete, others will likely come in the future.

- [ ] Overall results page
  - [x] Aggregate metrics across seasons
    - [x] Cumulative/non-cumulative metrics
    - [x] Dynamic start year
    - [x] Wiki integration
  - [x] Aggregate metrics across races within a season
    - [x] Cumulative/non-cumulative metrics
    - [x] Wiki integration
  - [ ] Race bump chart
    - [x] Individual driver focus
    - [ ] Button to remove driver focus


## Credits
- [Rohan Rao](https://www.kaggle.com/rohanrao) for maintaining the kaggle dataset

## License

gpl-3.0 license @ warren armstrong