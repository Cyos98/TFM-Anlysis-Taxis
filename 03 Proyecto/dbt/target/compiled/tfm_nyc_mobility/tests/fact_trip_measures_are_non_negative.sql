select *
from "tfm_mobility"."gold"."fact_trip"
where duration_minutes < 0
   or trip_distance < 0
   or average_speed_mph < 0