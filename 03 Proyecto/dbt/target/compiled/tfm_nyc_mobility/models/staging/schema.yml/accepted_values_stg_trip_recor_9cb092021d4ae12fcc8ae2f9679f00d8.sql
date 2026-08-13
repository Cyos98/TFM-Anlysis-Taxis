
    
    

with all_values as (

    select
        service_type as value_field,
        count(*) as n_records

    from "tfm_mobility"."staging"."stg_trip_records"
    group by service_type

)

select *
from all_values
where value_field not in (
    'yellow','green','fhv','fhvhv'
)


