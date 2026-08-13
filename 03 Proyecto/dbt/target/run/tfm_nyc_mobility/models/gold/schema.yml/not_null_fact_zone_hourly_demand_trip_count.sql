select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select trip_count
from "tfm_mobility"."gold"."fact_zone_hourly_demand"
where trip_count is null



      
    ) dbt_internal_test