
    
    

select
    zone_day_service_key as unique_field,
    count(*) as n_records

from "tfm_mobility"."gold"."fact_zone_daily_performance"
where zone_day_service_key is not null
group by zone_day_service_key
having count(*) > 1


