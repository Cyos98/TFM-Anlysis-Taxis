
    
    

select
    trip_id as unique_field,
    count(*) as n_records

from "tfm_mobility"."gold"."fact_trip"
where trip_id is not null
group by trip_id
having count(*) > 1


