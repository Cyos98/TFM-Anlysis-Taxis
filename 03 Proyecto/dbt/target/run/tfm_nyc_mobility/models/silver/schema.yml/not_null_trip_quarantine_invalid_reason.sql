select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select invalid_reason
from "tfm_mobility"."silver"."trip_quarantine"
where invalid_reason is null



      
    ) dbt_internal_test