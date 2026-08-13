
    
    

select
    service_type_key as unique_field,
    count(*) as n_records

from "tfm_mobility"."gold"."dim_service_type"
where service_type_key is not null
group by service_type_key
having count(*) > 1


