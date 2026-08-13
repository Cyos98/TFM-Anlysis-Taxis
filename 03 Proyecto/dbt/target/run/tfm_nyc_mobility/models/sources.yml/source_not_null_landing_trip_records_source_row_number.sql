select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select source_row_number
from "tfm_mobility"."landing"."trip_records"
where source_row_number is null



      
    ) dbt_internal_test