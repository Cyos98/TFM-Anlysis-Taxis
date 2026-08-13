select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select taxi_zone_key
from "tfm_mobility"."gold"."dim_taxi_zone"
where taxi_zone_key is null



      
    ) dbt_internal_test