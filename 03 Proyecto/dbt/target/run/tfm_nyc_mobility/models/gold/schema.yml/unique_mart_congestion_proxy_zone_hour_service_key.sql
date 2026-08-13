select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    zone_hour_service_key as unique_field,
    count(*) as n_records

from "tfm_mobility"."gold"."mart_congestion_proxy"
where zone_hour_service_key is not null
group by zone_hour_service_key
having count(*) > 1



      
    ) dbt_internal_test