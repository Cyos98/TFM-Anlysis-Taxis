select
    hourly.zone_hour_service_key,
    hourly.date_key,
    hourly.hour_key,
    hourly.taxi_zone_key,
    zone.borough,
    zone.zone_name,
    hourly.service_type_key,
    hourly.trip_count,
    hourly.observed_trip_amount,
    hourly.occupied_hours,
    hourly.observed_trip_amount
        / nullif(hourly.occupied_hours, 0) as observed_amount_per_occupied_hour,
    100.0 * hourly.trip_count
        / nullif(max(hourly.trip_count) over (
            partition by hourly.date_key, hourly.hour_key, hourly.service_type_key
        ), 0) as relative_demand_score
from "tfm_mobility"."gold"."fact_zone_hourly_demand" as hourly
join "tfm_mobility"."gold"."dim_taxi_zone" as zone
    on hourly.taxi_zone_key = zone.taxi_zone_key