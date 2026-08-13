select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select zone_day_service_key
from "tfm_mobility"."gold"."fact_zone_daily_performance"
where zone_day_service_key is null



      
    ) dbt_internal_test