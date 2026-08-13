with silver_total as (
    select count(*)::bigint as trip_count from {{ ref('trips') }}
),
gold_total as (
    select sum(trip_count)::bigint as trip_count from {{ ref('fact_zone_daily_performance') }}
)
select silver_total.trip_count as silver_count, gold_total.trip_count as gold_count
from silver_total
cross join gold_total
where silver_total.trip_count <> gold_total.trip_count
