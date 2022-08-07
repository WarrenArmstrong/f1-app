# %%
import pandas as pd
from sqlalchemy import create_engine
import os
from kaggle.api.kaggle_api_extended import KaggleApi
# %%
# download latest data from kaggle
api = KaggleApi()
api.authenticate()
api.dataset_download_files(
    'rohanrao/formula-1-world-championship-1950-2020', 'data',
    force=True,
    unzip=True,
)
# %%
# connect to database
local_engine = create_engine('sqlite:///../data.db')
# %%
# load csvs into database
for filename in os.listdir('data/'):
    table_name = 'stg_' + filename[:-4]

    with local_engine.connect() as con:
        con.execute(f'DROP TABLE IF EXISTS {table_name}')

    with pd.read_csv(f'data/{filename}', na_values='\\N', chunksize=1000) as reader:
        for chunk in reader:
            chunk.to_sql(
                con=local_engine,
                name=table_name,
                if_exists='append',
                index=False,
            )
# %%
# build database
with local_engine.connect() as con:
    con.execute('DROP TABLE IF EXISTS dim_circuit')
    con.execute(f'''
        --sql
        
        CREATE TABLE dim_circuit AS
            SELECT
                circuitId AS circuit_k,
                circuitRef AS ref,
                name,
                location,
                country,
                lat AS latitude,
                lng AS longitude,
                alt AS altitude,
                url AS wiki_url
            FROM stg_circuits;
    ''')
    # con.execute(f'''
    #     CREATE INDEX "circuit_circuit_k" ON "dim_circuit" (
    #         "circuit_k"
    #     );
    # ''')


    con.execute('DROP TABLE IF EXISTS dim_constructor')
    con.execute(f'''
        --sql
        
        CREATE TABLE dim_constructor AS
            SELECT
                c.constructorId AS constructor_k,
                c.constructorRef AS ref,
                c.name,
                c.nationality,
                c.url AS wiki_url,
                CAST(COALESCE(cs.custom_color, cs.auto_color) AS TEXT) AS color
            FROM
                stg_constructors AS c
                LEFT JOIN stg_constructor_color AS cs
                    ON c.constructorId = cs.constructorId;
    ''')
    # con.execute(f'''
    #     CREATE INDEX "constructor_constructor_k" ON "dim_constructor" (
    #         "constructor_k"
    #     );
    # ''')


    con.execute('DROP TABLE IF EXISTS dim_driver')
    con.execute(f'''
        --sql
        
        CREATE TABLE dim_driver AS
            SELECT
                driverId AS driver_k,
                driverRef AS ref,
                number,
                code,
                forename AS first_name,
                surname AS last_name,
                CAST(forename || ' ' || surname AS TEXT) AS full_name,
                dob,
                nationality,
                url AS wiki_url
            FROM stg_drivers;
    ''')
    # con.execute(f'''
    #     CREATE INDEX "driver_driver_k" ON "dim_driver" (
    #         "driver_k"
    #     );
    # ''')


    con.execute('DROP TABLE IF EXISTS fact_lap')
    con.execute(f'''
        --sql
        
        CREATE TABLE fact_lap AS
            WITH
                lap_zero AS (
                    SELECT
                        rr.raceId AS race_k,
                        rr.driverId AS driver_k,
                        CAST(0 AS INTEGER) AS lap,
                        rr.grid AS position,
                        CAST(NULL AS INTEGER) AS time,
                        CAST(NULL AS INTEGER) AS milliseconds
                    FROM stg_results AS rr
                    WHERE rr.grid <> 0
                ),
                real_laps AS (
                    SELECT
                        raceId AS race_k,
                        driverId AS driver_k,
                        lap,
                        position,
                        time,
                        milliseconds
                    FROM stg_lap_times
                ),
                zero_and_real_laps AS (
                    SELECT * FROM lap_zero
                    UNION ALL
                    SELECT * FROM real_laps
                ),
                dnf_laps AS (
                    WITH
                        max_laps AS (
                            SELECT
                                race_k,
                                MAX(lap) AS max_lap
                            FROM zero_and_real_laps
                            GROUP BY race_k
                        ),
                        last_laps AS (
                            SELECT
                                race_k,
                                driver_k,
                                lap,
                                position,
                                time,
                                milliseconds,
                                ROW_NUMBER() OVER (PARTITION BY race_k, driver_k ORDER BY lap DESC) = 1 AS is_final
                            FROM zero_and_real_laps
                        )
                    SELECT
                        ll.race_k,
                        ll.driver_k,
                        ll.lap + 1 AS lap,
                        CAST(rr.positionOrder AS INTEGER) AS position,
                        NULL AS time,
                        NULL AS milliseconds
                    FROM
                        last_laps AS ll
                        LEFT JOIN max_laps AS ml
                            ON ll.race_k = ml.race_k
                        LEFT JOIN stg_results AS rr
                            ON ll.race_k = rr.raceId
                            AND ll.driver_k = rr.driverId
                        LEFT JOIN stg_status AS s
                            ON rr.statusId = s.statusId
                    WHERE TRUE
                        AND ll.is_final
                        AND ll.lap < ml.max_lap
                        AND NOT s.status LIKE '+% Lap%'
                ),
                combined_laps AS (
                    SELECT * FROM lap_zero
                    UNION ALL
                    SELECT * FROM real_laps
                    UNION ALL
                    SELECT * FROM dnf_laps
                )
            SELECT
                race_k,
                driver_k,
                lap,
                position,
                time,
                milliseconds,
                CAST(
                    ROW_NUMBER() OVER (
                        PARTITION BY race_k, driver_k
                        ORDER BY lap DESC
                    ) = 1 AS INTEGER
                ) AS is_final
            FROM combined_laps;
    ''')


    con.execute('DROP TABLE IF EXISTS fact_pit_stop')
    con.execute(f'''
        --sql
        
        CREATE TABLE fact_pit_stop AS
            SELECT
                raceId AS race_k,
                driverId AS driver_k,
                lap,                
                stop,
                time,
                duration,
                milliseconds
            FROM stg_pit_stops;
    ''')


    con.execute('DROP TABLE IF EXISTS fact_qualifying')
    con.execute(f'''
        --sql
        
        CREATE TABLE fact_qualifying AS
            SELECT
                raceId AS race_k,
                driverId AS driver_k,
                constructorId AS constructor_k,
                number,
                position,
                q1,
                q2,
                q3
            FROM stg_qualifying;
    ''')

    
    con.execute('DROP TABLE IF EXISTS dim_race')
    con.execute(f'''
        --sql
        
        CREATE TABLE dim_race AS
            SELECT
                raceId AS race_k,
                circuitId AS circuit_k,
                year,
                round,
                name,
                CAST(CASE
                    WHEN date LIKE '%/%' THEN
                        CASE
                            WHEN CAST(substr(date, 7, 2) AS INTEGER) >= 50 THEN '19'
                            ELSE '20'
                        END || substr(date, 7, 2) || '-' ||
                        substr(date, 4, 2) || '-' ||
                        substr(date, 1, 2)
                    ELSE date
                END AS TEXT) AS date,
                date,
                time,
                url AS wiki_url
            FROM stg_races;
    ''')
    # con.execute(f'''
    #     CREATE INDEX "race_race_k" ON "dim_race" (
    #         "race_k"
    #     );
    # ''')


    con.execute('DROP TABLE IF EXISTS fact_race_result')
    con.execute(f'''
        --sql
        
        CREATE TABLE fact_race_result AS
            SELECT
                r.raceId AS race_k,
                r.driverId AS driver_k,
                r.constructorId AS constructor_k,
                CAST(FALSE AS INTEGER) AS is_sprint,
                r.number,
                r.grid,
                CAST(r.position AS INTEGER) AS position,
                r.positionText AS position_text,
                CAST(r.positionOrder AS INTEGER) AS position_order,
                r.points,
                r.laps,
                r.time,
                r.milliseconds,
                r.fastestLap AS fastest_lap,
                r.rank,
                r.fastestLapTime AS fastest_lap_time,
                r.fastestLapSpeed AS fastest_lap_speed,
                s.status
            FROM
                stg_results AS r
                LEFT JOIN stg_status AS s
                    ON r.statusId = s.statusId
            UNION ALL
            SELECT
                sr.raceId AS race_k,
                sr.driverId AS driver_k,
                sr.constructorId AS constructor_k,
                CAST(TRUE AS INTEGER) AS is_sprint,
                sr.number,
                sr.grid,
                CAST(NULLIF(sr.position, '\\N') AS INTEGER) AS position,
                sr.positionText AS position_text,
                CAST(sr.positionOrder AS INTEGER) AS position_order,
                sr.points,
                sr.laps,
                sr.time,
                sr.milliseconds,
                sr.fastestLap AS fastest_lap,
                NULL AS rank,
                sr.fastestLapTime AS fastest_lap_time,
                NULL AS fastest_lap_speed,
                s.status
            FROM
                stg_sprint_results AS sr
                LEFT JOIN stg_status AS s
                    ON sr.statusId = s.statusId;
    ''')


    con.execute('DROP TABLE IF EXISTS dim_season')
    con.execute(f'''
        --sql
        
        CREATE TABLE dim_season AS
            SELECT
                year,
                url AS wiki_url
            FROM stg_seasons;
    ''')
    # con.execute(f'''
    #     CREATE INDEX "season_year" ON "dim_season" (
    #         "year"
    #     );
    # ''')


    con.execute('DROP TABLE IF EXISTS dim_driver_constructor')
    con.execute(f'''
        --sql
        
        CREATE TABLE dim_driver_constructor AS
            WITH
                driver_constructor_races AS (
                    SELECT
                        ra.year,
                        re.constructorId,
                        re.driverId,
                        ROW_NUMBER() OVER (
                            PARTITION BY
                                ra.year,
                                re.driverId
                            ORDER BY
                                COUNT(DISTINCT re.raceId) DESC
                        ) AS row_num
                    FROM
                        stg_results AS re
                        LEFT JOIN stg_races AS ra
                            ON re.raceId = ra.raceId
                    GROUP BY
                        ra.year,
                        re.constructorId,
                        re.driverId
                )
            SELECT
                year,
                constructorId AS constructor_k,
                driverId AS driver_k
            FROM driver_constructor_races
            WHERE row_num = 1;
    ''')
    # con.execute(f'''
    #     CREATE INDEX "driver_constructor_driver_k" ON "dim_driver_constructor" (
    #         "driver_k"
    #     );
    # ''')
# %%
# drop staging tables
stg_tables = pd.read_sql(
    con=local_engine,
    sql="SELECT tbl_name FROM sqlite_master WHERE tbl_name LIKE 'stg_%'"
)['tbl_name']

for stg_table in stg_tables:
    with local_engine.connect() as con:
        con.execute(f'DROP TABLE IF EXISTS {stg_table}')
# %%
# generate reports
with local_engine.connect() as con:
    con.execute('DROP TABLE IF EXISTS report_seasons_metrics')
    con.execute(f'''
        --sql
        
        CREATE TABLE report_seasons_metrics AS
            WITH
                vector(idx) AS (
                    SELECT 0 AS idx
                    UNION ALL
                    SELECT idx + 1 AS idx
                    FROM vector
                    WHERE vector.idx <= 10
                ),
                driver_metrics AS (
                    SELECT
                        r.year,
                        'Driver' AS type,
                        d.driver_k AS id,
                        d.full_name AS name,
                        COALESCE(c.name, 'No Constructor') AS constructor_name,
                        COALESCE(c.color, '#BAB0AC') AS constructor_color,
                        d.wiki_url,
                        s.wiki_url AS season_wiki_url,
                        SUM(rr.points) AS points,
                        SUM(CASE WHEN NOT rr.is_sprint THEN rr.position = 1 ELSE 0 END) AS race_wins,
                        SUM(CASE WHEN NOT rr.is_sprint THEN rr.position BETWEEN 1 AND 3 ELSE 0 END) AS podiums,
                        ROW_NUMBER() OVER (PARTITION BY r.year ORDER BY SUM(rr.points) DESC) = 1 AS championships
                    FROM
                        dim_driver AS d
                        CROSS JOIN dim_season AS s
                        LEFT JOIN dim_race AS r
                            ON s.year = r.year
                        LEFT JOIN fact_race_result AS rr
                            ON r.race_k = rr.race_k
                            AND d.driver_k = rr.driver_k
                        LEFT JOIN dim_driver_constructor AS dc
                            ON r.year = dc.year
                            AND d.driver_k = dc.driver_k
                        LEFT JOIN dim_constructor AS c
                            ON dc.constructor_k = c.constructor_k
                    GROUP BY
                        r.year,
                        d.driver_k
                ),
                constructor_metrics AS (
                    SELECT
                        r.year,
                        'Constructor' AS type,
                        c.constructor_k AS id,
                        c.name,
                        c.name AS constructor_name,
                        c.color AS constructor_color,
                        c.wiki_url,
                        s.wiki_url AS season_wiki_url,
                        SUM(rr.points) AS points,
                        SUM(CASE WHEN NOT rr.is_sprint THEN rr.position = 1 ELSE 0 END) AS race_wins,
                        SUM(CASE WHEN NOT rr.is_sprint THEN rr.position BETWEEN 1 AND 3 ELSE 0 END) AS podiums,
                        ROW_NUMBER() OVER (PARTITION BY r.year ORDER BY SUM(rr.points) DESC) = 1 AS championships
                    FROM
                        dim_constructor AS c
                        CROSS JOIN dim_season AS s
                        LEFT JOIN dim_race AS r
                            ON s.year = r.year
                        LEFT JOIN fact_race_result AS rr
                            ON r.race_k = rr.race_k
                            AND c.constructor_k = rr.constructor_k
                    GROUP BY
                        r.year,
                        c.constructor_k
                ),
                combined_metrics AS (
                    SELECT * FROM driver_metrics
                    UNION ALL
                    SELECT * FROM constructor_metrics
                ),
                unpivoted_metrics AS (
                    SELECT
                        m.year,
                        m.type,
                        m.id,
                        m.name,
                        m.constructor_name,
                        m.constructor_color,
                        m.wiki_url,
                        m.season_wiki_url,
                        CASE
                            WHEN v.idx = 0 THEN 'Points'
                            WHEN v.idx = 1 THEN 'Race Wins'
                            WHEN v.idx = 2 THEN 'Podiums'
                            WHEN v.idx = 3 THEN 'Championships'
                        END AS metric,
                        CASE
                            WHEN v.idx = 0 THEN m.points
                            WHEN v.idx = 1 THEN m.race_wins
                            WHEN v.idx = 2 THEN m.podiums
                            WHEN v.idx = 3 THEN m.championships
                        END AS metric_value
                    FROM
                        combined_metrics AS m
                        CROSS JOIN vector AS v
                    WHERE v.idx <= 3
                ),
                rankings AS (
                    SELECT
                        year,
                        type,
                        id,
                        name,
                        constructor_name,
                        constructor_color,
                        wiki_url,
                        season_wiki_url,
                        metric,
                        metric_value,
                        ROW_NUMBER() OVER (PARTITION BY year, type, metric ORDER BY metric_value DESC) AS position
                    FROM unpivoted_metrics
                )
            SELECT * FROM rankings
            ORDER BY year, metric, type, position DESC;
    ''')
    con.execute(f'''
        CREATE INDEX "report_seasons_metrics_year_metric" ON "report_seasons_metrics" (
            "year",
            "metric"
        );
    ''')


    con.execute('DROP TABLE IF EXISTS report_season_metrics')
    con.execute(f'''
        --sql
        
        CREATE TABLE report_season_metrics AS
            WITH
                vector(idx) AS (
                    SELECT 0 AS idx
                    UNION ALL
                    SELECT idx + 1 AS idx
                    FROM vector
                    WHERE idx <= 10
                ),
                season_drivers AS (
                    SELECT
                        r.year,
                        d.*
                    FROM
                        fact_race_result AS rr
                        LEFT JOIN dim_race AS r
                            ON rr.race_k = r.race_k
                        LEFT JOIN dim_driver AS d
                            ON rr.driver_k = d.driver_k
                    GROUP BY
                        r.year,
                        d.driver_k
                ),
                season_constructors AS (
                    SELECT
                        r.year,
                        c.*
                    FROM
                        fact_race_result AS rr
                        LEFT JOIN dim_race AS r
                            ON rr.race_k = r.race_k
                        LEFT JOIN dim_constructor AS c
                            ON rr.constructor_k = c.constructor_k
                    GROUP BY
                        r.year,
                        c.constructor_k
                ),
                driver_metrics AS (
                    SELECT
                        r.year,
                        r.name AS race,
                        r.date AS race_date,
                        'Driver' AS type,
                        d.driver_k AS id,
                        d.full_name AS name,
                        COALESCE(c.name, 'No Constructor') AS constructor_name,
                        COALESCE(c.color, '#BAB0AC') AS constructor_color,
                        d.wiki_url,
                        r.wiki_url AS race_wiki_url,
                        cir.wiki_url AS circuit_wiki_url,
                        s.wiki_url AS season_wiki_url,
                        SUM(rr.points) AS points,
                        SUM(CASE WHEN NOT rr.is_sprint THEN rr.position = 1 ELSE 0 END) AS race_wins,
                        SUM(CASE WHEN NOT rr.is_sprint THEN rr.position BETWEEN 1 AND 3 ELSE 0 END) AS podiums
                    FROM
                        season_drivers AS d
                        INNER JOIN dim_race AS r
                            ON d.year = r.year
                        LEFT JOIN fact_race_result AS rr
                            ON r.race_k = rr.race_k
                            AND d.driver_k = rr.driver_k
                        LEFT JOIN dim_constructor AS c
                            ON rr.constructor_k = c.constructor_k
                        LEFT JOIN dim_circuit AS cir
                            ON r.circuit_k = cir.circuit_k
                        LEFT JOIN dim_season AS s
                            ON r.year = s.year
                    GROUP BY
                        r.year,
                        r.race_k,
                        d.driver_k
                ),
                constructor_metrics AS (
                    SELECT
                        r.year,
                        r.name AS race,
                        r.date AS race_date,
                        'Constructor' AS type,
                        c.constructor_k AS id,
                        c.name AS name,
                        c.name AS constructor_name,
                        c.color AS constructor_color,
                        c.wiki_url,
                        r.wiki_url AS race_wiki_url,
                        cir.wiki_url AS circuit_wiki_url,
                        s.wiki_url AS season_wiki_url,
                        SUM(rr.points) AS points,
                        SUM(CASE WHEN NOT rr.is_sprint THEN rr.position = 1 ELSE 0 END) AS race_wins,
                        SUM(CASE WHEN NOT rr.is_sprint THEN rr.position BETWEEN 1 AND 3 ELSE 0 END) AS podiums
                    FROM
                        season_constructors AS c
                        INNER JOIN dim_race AS r
                            ON c.year = r.year
                        LEFT JOIN fact_race_result AS rr
                            ON r.race_k = rr.race_k
                            AND c.constructor_k = rr.constructor_k
                        LEFT JOIN dim_circuit AS cir
                            ON r.circuit_k = cir.circuit_k
                        LEFT JOIN dim_season AS s
                            ON r.year = s.year
                    GROUP BY
                        r.year,
                        r.race_k,
                        c.constructor_k
                ),
                combined_metrics AS (
                    SELECT * FROM driver_metrics
                    UNION ALL
                    SELECT * FROM constructor_metrics
                ),
                unpivoted_metrics AS (
                    SELECT
                        m.year,
                        m.race,
                        m.race_date,
                        m.type,
                        m.id,
                        m.name,
                        m.constructor_name,
                        m.constructor_color,
                        m.wiki_url,
                        m.race_wiki_url,
                        m.circuit_wiki_url,
                        m.season_wiki_url,
                        CASE
                            WHEN v.idx = 0 THEN 'Points'
                            WHEN v.idx = 1 THEN 'Race Wins'
                            WHEN v.idx = 2 THEN 'Podiums'
                        END AS metric,
                        CASE
                            WHEN v.idx = 0 THEN m.points
                            WHEN v.idx = 1 THEN m.race_wins
                            WHEN v.idx = 2 THEN m.podiums
                        END AS metric_value,
                        FALSE AS is_cumulative
                    FROM
                        combined_metrics AS m
                        CROSS JOIN vector AS v
                    WHERE v.idx <= 2
                ),
                cumulative_unpivoted_metrics AS (
                    SELECT
                        year,
                        race,
                        race_date,
                        type,
                        id,
                        name,
                        constructor_name,
                        constructor_color,
                        wiki_url,
                        race_wiki_url,
                        circuit_wiki_url,
                        season_wiki_url,
                        metric,
                        SUM(COALESCE(metric_value, 0)) OVER (
                            PARTITION BY
                                year,
                                id,
                                type,
                                metric
                            ORDER BY
                                race_date
                            ROWS BETWEEN
                                UNBOUNDED PRECEDING
                                AND CURRENT ROW
                        ) AS metric_value,
                        TRUE AS is_cumulative
                    FROM unpivoted_metrics
                ),
                combined_unpivoted_metrics AS (
                    SELECT * FROM unpivoted_metrics
                    UNION ALL
                    SELECT * FROM cumulative_unpivoted_metrics
                ),
                rankings AS (
                    SELECT
                        year,
                        race,
                        race_date,
                        type,
                        id,
                        name,
                        constructor_name,
                        constructor_color,
                        wiki_url,
                        race_wiki_url,
                        circuit_wiki_url,
                        season_wiki_url,
                        metric,
                        metric_value,
                        is_cumulative,
                        ROW_NUMBER() OVER (PARTITION BY year, race, type, is_cumulative, metric ORDER BY metric_value DESC) AS position
                    FROM combined_unpivoted_metrics
                )
            SELECT * FROM rankings
            ORDER BY year, race_date, is_cumulative, metric, type, position DESC;
    ''')
    con.execute(f'''
        CREATE INDEX "report_season_metrics_year_metric_is_cumulative_position" ON "report_season_metrics" (
            "year",
            "metric",
            "is_cumulative",
            "position"
        );
    ''')


    con.execute('DROP TABLE IF EXISTS report_race_metrics')
    con.execute(f'''
        --sql
        
        CREATE TABLE report_race_metrics AS
            WITH
                lap_data AS (
                    SELECT
                        r.year,
                        r.name AS race_name,
                        r.date AS race_date,
                        c.name AS constructor_name,
                        c.color AS constructor_color,
                        d.full_name AS driver_name,
                        COALESCE(d.code, '#NA') AS driver_code,
                        CASE WHEN l.is_final THEN rr.status END AS ending_status,
                        l.lap,
                        l.position,
                        l.time AS lap_time,
                        l.milliseconds AS lap_milliseconds,
                        ps.time AS pit_stop_time,
                        ps.milliseconds AS pit_stop_milliseconds,
                        l.milliseconds - COALESCE(ps.milliseconds, 0) AS net_lap_milliseconds,
                        ps.race_k NOT NULL AS is_pit_lap,
                        SUM(ps.race_k NOT NULL) OVER (PARTITION BY l.race_k, l.driver_k ORDER BY l.lap) + 1 AS stint_number
                    FROM
                        fact_lap AS l
                        LEFT JOIN fact_pit_stop AS ps
                            ON l.race_k = ps.race_k
                            AND l.driver_k = ps.driver_k
                            AND l.lap = (ps.lap + 1)
                        LEFT JOIN fact_race_result AS rr
                            ON l.race_k = rr.race_k
                            AND l.driver_k = rr.driver_k
                        LEFT JOIN dim_race AS r
                            ON l.race_k = r.race_k
                        LEFT JOIN dim_driver AS d
                            ON l.driver_k = d.driver_k
                        LEFT JOIN dim_constructor AS c
                            ON rr.constructor_k = c.constructor_k
                    WHERE TRUE
                        AND NOT rr.is_sprint
                ),
                tire_age AS (
                    SELECT
                        *,
                        ROW_NUMBER() OVER (PARTITION BY year, race_name, driver_name, stint_number ORDER BY lap) AS tire_age
                    FROM lap_data
                )
            SELECT *
            FROM tire_age
            ORDER BY year, race_date, constructor_name, driver_name, lap;
    ''')
    con.execute(f'''
        CREATE INDEX "report_race_metrics_year_race_name" ON "report_race_metrics" (
            "year",
            "race_name"
        );
    ''')
# %%
# cleanup
with local_engine.connect() as con:
        con.execute('ANALYZE')
        con.execute('VACUUM')
# %%
