select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select borough
from "tfm_mobility"."reference"."taxi_zone_lookup"
where borough is null



      
    ) dbt_internal_test