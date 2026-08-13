
    
    

select
    location_id as unique_field,
    count(*) as n_records

from "tfm_mobility"."reference"."taxi_zone_lookup"
where location_id is not null
group by location_id
having count(*) > 1


