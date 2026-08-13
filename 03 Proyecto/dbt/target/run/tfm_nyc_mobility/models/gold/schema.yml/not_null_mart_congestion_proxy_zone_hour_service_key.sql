select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select zone_hour_service_key
from "tfm_mobility"."gold"."mart_congestion_proxy"
where zone_hour_service_key is null



      
    ) dbt_internal_test