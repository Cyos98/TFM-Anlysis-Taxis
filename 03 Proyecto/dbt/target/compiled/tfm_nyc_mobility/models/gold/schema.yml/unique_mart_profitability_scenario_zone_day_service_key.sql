
    
    

select
    zone_day_service_key as unique_field,
    count(*) as n_records

from "tfm_mobility"."gold"."mart_profitability_scenario"
where zone_day_service_key is not null
group by zone_day_service_key
having count(*) > 1


