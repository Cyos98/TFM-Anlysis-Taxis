select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select pickup_location_id
from "tfm_mobility"."silver"."trips"
where pickup_location_id is null



      
    ) dbt_internal_test