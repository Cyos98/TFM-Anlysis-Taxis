
    
    

select
    taxi_zone_key as unique_field,
    count(*) as n_records

from "tfm_mobility"."gold"."dim_taxi_zone"
where taxi_zone_key is not null
group by taxi_zone_key
having count(*) > 1


