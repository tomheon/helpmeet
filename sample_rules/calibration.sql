select vevent_id from vevents
where
upper(summary) like '%CALIBRATION%' or
upper(summary) like '%CALIBRATE%';

