select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select dropoff_datetime
from "tfm_mobility"."silver"."trips"
where dropoff_datetime is null



      
    ) dbt_internal_test