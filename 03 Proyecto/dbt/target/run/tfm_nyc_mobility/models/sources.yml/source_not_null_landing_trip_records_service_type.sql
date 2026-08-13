select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select service_type
from "tfm_mobility"."landing"."trip_records"
where service_type is null



      
    ) dbt_internal_test