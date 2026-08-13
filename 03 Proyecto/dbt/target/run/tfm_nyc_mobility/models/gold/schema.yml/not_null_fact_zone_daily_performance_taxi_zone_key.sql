select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select taxi_zone_key
from "tfm_mobility"."gold"."fact_zone_daily_performance"
where taxi_zone_key is null



      
    ) dbt_internal_test