select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select day_period
from "tfm_mobility"."gold"."dim_time"
where day_period is null



      
    ) dbt_internal_test