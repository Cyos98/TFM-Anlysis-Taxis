select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      select trip_id
from "tfm_mobility"."silver"."trips"
where duration_minutes < 0
      
    ) dbt_internal_test