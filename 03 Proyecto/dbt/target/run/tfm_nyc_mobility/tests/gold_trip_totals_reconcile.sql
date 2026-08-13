select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      with silver_total as (
    select count(*)::bigint as trip_count from "tfm_mobility"."silver"."trips"
),
gold_total as (
    select sum(trip_count)::bigint as trip_count from "tfm_mobility"."gold"."fact_zone_daily_performance"
)
select silver_total.trip_count as silver_count, gold_total.trip_count as gold_count
from silver_total
cross join gold_total
where silver_total.trip_count <> gold_total.trip_count
      
    ) dbt_internal_test