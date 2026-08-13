
    
    

with all_values as (

    select
        day_period as value_field,
        count(*) as n_records

    from "tfm_mobility"."gold"."dim_time"
    group by day_period

)

select *
from all_values
where value_field not in (
    'overnight','morning_peak','midday','evening_peak','night'
)


