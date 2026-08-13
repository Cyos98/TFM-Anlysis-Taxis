select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select date_key
from "tfm_mobility"."gold"."fact_zone_daily_performance"
where date_key is null



      
    ) dbt_internal_test