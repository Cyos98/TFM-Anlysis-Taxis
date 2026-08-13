select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

with all_values as (

    select
        service_type_key as value_field,
        count(*) as n_records

    from "tfm_mobility"."gold"."dim_service_type"
    group by service_type_key

)

select *
from all_values
where value_field not in (
    'yellow','green','fhv','fhvhv'
)



      
    ) dbt_internal_test