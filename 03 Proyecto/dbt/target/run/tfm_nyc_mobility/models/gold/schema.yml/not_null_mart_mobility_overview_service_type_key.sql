select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select service_type_key
from "tfm_mobility"."gold"."mart_mobility_overview"
where service_type_key is null



      
    ) dbt_internal_test