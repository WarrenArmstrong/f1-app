# %%
import pandas as pd
from sqlalchemy import create_engine
import os
# %%
local_engine = create_engine('sqlite:///../data.db')
# %%
for filename in os.listdir('data/'):
    print(filename)
    df = pd.read_csv(f'data/{filename}')
    df.to_sql(
        con=local_engine,
        name='stg_' + filename[:-4],
        if_exists='replace',
        index=False,
    )
# %%
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
                COALESCE(cs.custom_color, cs.auto_color) AS color
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
                forename || ' ' || surname AS full_name,
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
            SELECT
                raceId AS race_k,
                driverId AS driver_k,
                lap,
                position,
                time,
                milliseconds
            FROM stg_lap_times;
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
                CASE WHEN CAST(substr(date, 7, 2) AS INTEGER) >= 50 THEN '19' ELSE '20' END || substr(date, 7, 2) || '-' ||
                    substr(date, 4, 2) || '-' ||
                    substr(date, 1, 2) AS date,
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
                FALSE AS is_sprint,
                r.number,
                r.grid,
                CAST(r.position AS INTEGER) AS position,
                r.positionText AS position_text,
                r.positionOrder AS position_order,
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
                TRUE AS is_sprint,
                sr.number,
                sr.grid,
                CAST(sr.position AS Integer) AS position,
                sr.positionText AS position_text,
                sr.positionOrder AS position_order,
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
stg_tables = pd.read_sql(
    con=local_engine,
    sql="SELECT tbl_name FROM sqlite_master WHERE tbl_name LIKE 'stg_%'"
)['tbl_name']

for stg_table in stg_tables:
    with local_engine.connect() as con:
        con.execute(f'DROP TABLE IF EXISTS {stg_table}')
# %%
with local_engine.connect() as con:
        con.execute('ANALYZE')
        con.execute('VACUUM')
# %%
