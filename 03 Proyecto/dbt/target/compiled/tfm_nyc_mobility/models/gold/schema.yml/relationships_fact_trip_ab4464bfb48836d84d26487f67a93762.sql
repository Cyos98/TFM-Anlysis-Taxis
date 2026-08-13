
    
    

with child as (
    select pickup_taxi_zone_key as from_field
    from "tfm_mobility"."gold"."fact_trip"
    where pickup_taxi_zone_key is not null
),

parent as (
    select taxi_zone_key as to_field
    from "tfm_mobility"."gold"."dim_taxi_zone"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


