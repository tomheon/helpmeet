select vevent_id from vevents
where
upper(summary) like '%HEADS DOWN%' or
upper(summary) like '%HEADS-DOWN%' or
upper(summary) like '%DESK TIME%';

