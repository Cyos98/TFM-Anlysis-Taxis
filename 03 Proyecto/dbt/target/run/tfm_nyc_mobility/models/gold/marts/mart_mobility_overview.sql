
  create view "tfm_mobility"."gold"."mart_mobility_overview__dbt_tmp"
    
    
  as (
    select
    daily.date_key,
    daily.service_type_key,
    service.service_type_name,
    sum(daily.trip_count)::bigint as trip_count,
    count(distinct daily.taxi_zone_key)::integer as active_pickup_zones,
    sum(daily.revenue_observation_count)::bigint as revenue_observation_count,
    sum(daily.observed_trip_amount) as observed_trip_amount,
    sum(daily.occupied_hours) as occupied_hours,
    sum(daily.average_duration_minutes * daily.trip_count)
        / nullif(sum(daily.trip_count), 0) as weighted_average_duration_minutes,
    sum(daily.average_trip_distance * daily.trip_count)
        / nullif(sum(daily.trip_count) filter (where daily.average_trip_distance is not null), 0)
        as weighted_average_trip_distance
from "tfm_mobility"."gold"."fact_zone_daily_performance" as daily
join "tfm_mobility"."gold"."dim_service_type" as service
    on daily.service_type_key = service.service_type_key
group by 1, 2, 3
  );