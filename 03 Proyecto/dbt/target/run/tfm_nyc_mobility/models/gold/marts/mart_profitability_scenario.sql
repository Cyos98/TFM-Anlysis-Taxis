
  create view "tfm_mobility"."gold"."mart_profitability_scenario__dbt_tmp"
    
    
  as (
    

select
    daily.zone_day_service_key,
    daily.date_key,
    daily.taxi_zone_key,
    zone.borough,
    zone.zone_name,
    daily.service_type_key,
    daily.trip_count,
    daily.revenue_observation_count,
    daily.observed_trip_amount,
    daily.average_trip_distance,
    0.2::numeric as assumed_commission_rate,
    0.35::numeric as assumed_variable_cost_per_mile,
    1.5::numeric as assumed_fixed_cost_per_trip,
    case
        when daily.revenue_observation_count > 0 then
            daily.observed_trip_amount
            - (daily.observed_trip_amount * 0.2)
            - (coalesce(daily.average_trip_distance, 0) * daily.trip_count
                * 0.35)
            - (daily.trip_count * 1.5)
    end as estimated_net_contribution_scenario
from "tfm_mobility"."gold"."fact_zone_daily_performance" as daily
join "tfm_mobility"."gold"."dim_taxi_zone" as zone
    on daily.taxi_zone_key = zone.taxi_zone_key
  );