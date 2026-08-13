select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select source_file_id
from "tfm_mobility"."staging"."stg_trip_records"
where source_file_id is null



      
    ) dbt_internal_test