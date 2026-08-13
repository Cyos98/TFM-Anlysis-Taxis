
  create view "tfm_mobility"."gold"."mart_congestion_proxy__dbt_tmp"
    
    
  as (
    select
    hourly.zone_hour_service_key,
    hourly.date_key,
    hourly.hour_key,
    hourly.taxi_zone_key,
    zone.borough,
    zone.zone_name,
    hourly.service_type_key,
    hourly.trip_count,
    hourly.average_duration_minutes,
    hourly.average_trip_distance,
    hourly.average_speed_mph,
    case
        when hourly.average_trip_distance > 0
            then hourly.average_duration_minutes / hourly.average_trip_distance
    end as minutes_per_mile_proxy
from "tfm_mobility"."gold"."fact_zone_hourly_demand" as hourly
join "tfm_mobility"."gold"."dim_taxi_zone" as zone
    on hourly.taxi_zone_key = zone.taxi_zone_key
  );