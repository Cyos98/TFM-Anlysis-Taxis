{% set scenario = var('profitability_scenario') %}

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
    {{ scenario['commission_rate'] }}::numeric as assumed_commission_rate,
    {{ scenario['variable_cost_per_mile'] }}::numeric as assumed_variable_cost_per_mile,
    {{ scenario['fixed_cost_per_trip'] }}::numeric as assumed_fixed_cost_per_trip,
    case
        when daily.revenue_observation_count > 0 then
            daily.observed_trip_amount
            - (daily.observed_trip_amount * {{ scenario['commission_rate'] }})
            - (coalesce(daily.average_trip_distance, 0) * daily.trip_count
                * {{ scenario['variable_cost_per_mile'] }})
            - (daily.trip_count * {{ scenario['fixed_cost_per_trip'] }})
    end as estimated_net_contribution_scenario
from {{ ref('fact_zone_daily_performance') }} as daily
join {{ ref('dim_taxi_zone') }} as zone
    on daily.taxi_zone_key = zone.taxi_zone_key
