select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select pickup_taxi_zone_key
from "tfm_mobility"."gold"."fact_trip"
where pickup_taxi_zone_key is null



      
    ) dbt_internal_test