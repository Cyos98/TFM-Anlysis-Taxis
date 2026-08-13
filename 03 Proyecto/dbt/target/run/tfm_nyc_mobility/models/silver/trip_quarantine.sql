
  
    

  create  table "tfm_mobility"."silver"."trip_quarantine__dbt_tmp"
  
  
    as
  
  (
    select
    *,
    current_timestamp as quarantined_at
from "tfm_mobility"."staging"."stg_trip_records"
where invalid_reason is not null
  );
  