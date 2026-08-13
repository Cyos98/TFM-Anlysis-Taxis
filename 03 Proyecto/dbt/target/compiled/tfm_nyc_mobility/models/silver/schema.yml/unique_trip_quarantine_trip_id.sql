
    
    

select
    trip_id as unique_field,
    count(*) as n_records

from "tfm_mobility"."silver"."trip_quarantine"
where trip_id is not null
group by trip_id
having count(*) > 1


