
  create view "tfm_mobility"."gold"."mart_service_comparison__dbt_tmp"
    
    
  as (
    select
    service.service_type_key,
    service.service_type_name,
    sum(daily.trip_count)::bigint as trip_count,
    count(distinct daily.date_key)::integer as active_days,
    count(distinct daily.taxi_zone_key)::integer as active_pickup_zones,
    sum(daily.revenue_observation_count)::bigint as revenue_observation_count,
    sum(daily.observed_trip_amount) as observed_trip_amount,
    sum(daily.occupied_hours) as occupied_hours,
    sum(daily.observed_trip_amount)
        / nullif(sum(daily.revenue_observation_count), 0) as observed_amount_per_priced_trip
from "tfm_mobility"."gold"."dim_service_type" as service
left join "tfm_mobility"."gold"."fact_zone_daily_performance" as daily
    on service.service_type_key = daily.service_type_key
group by 1, 2
  );