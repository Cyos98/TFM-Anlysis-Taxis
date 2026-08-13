select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select hour_key
from "tfm_mobility"."gold"."fact_zone_hourly_demand"
where hour_key is null



      
    ) dbt_internal_test