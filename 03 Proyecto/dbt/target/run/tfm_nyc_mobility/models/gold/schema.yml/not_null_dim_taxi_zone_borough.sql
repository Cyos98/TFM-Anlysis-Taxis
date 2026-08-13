select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select borough
from "tfm_mobility"."gold"."dim_taxi_zone"
where borough is null



      
    ) dbt_internal_test