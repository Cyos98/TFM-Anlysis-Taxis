select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      select *
from "tfm_mobility"."gold"."fact_trip"
where duration_minutes < 0
   or trip_distance < 0
   or average_speed_mph < 0
      
    ) dbt_internal_test