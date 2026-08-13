
    
    

select
    trip_id as unique_field,
    count(*) as n_records

from "tfm_mobility"."staging"."stg_trip_records"
where trip_id is not null
group by trip_id
having count(*) > 1


