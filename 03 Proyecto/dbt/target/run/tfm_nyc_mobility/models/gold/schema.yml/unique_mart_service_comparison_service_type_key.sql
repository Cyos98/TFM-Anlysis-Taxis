select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    service_type_key as unique_field,
    count(*) as n_records

from "tfm_mobility"."gold"."mart_service_comparison"
where service_type_key is not null
group by service_type_key
having count(*) > 1



      
    ) dbt_internal_test