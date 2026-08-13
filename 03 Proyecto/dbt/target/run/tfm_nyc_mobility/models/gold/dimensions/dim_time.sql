
  
    

  create  table "tfm_mobility"."gold"."dim_time__dbt_tmp"
  
  
    as
  
  (
    select
    hour_value::smallint as hour_key,
    make_time(hour_value, 0, 0) as hour_start,
    lpad(hour_value::text, 2, '0') || ':00' as hour_label,
    case
        when hour_value between 0 and 5 then 'overnight'
        when hour_value between 6 and 9 then 'morning_peak'
        when hour_value between 10 and 15 then 'midday'
        when hour_value between 16 and 19 then 'evening_peak'
        else 'night'
    end as day_period
from generate_series(0, 23) as hours(hour_value)
  );
  