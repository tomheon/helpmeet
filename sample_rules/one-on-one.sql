with attendee_counts as (

  select
    v.vevent_id as vevent_id,
    count(*) as num_attendees
  from
    vevents v natural join attendees
  group by
    v.vevent_id
),

attendee_counts_and_summaries as (

  select
    v.vevent_id as vevent_id,
    v.summary as summary,
    ac.num_attendees as num_attendees
  from
    vevents v natural join attendee_counts ac

)
    
select vevent_id from attendee_counts_and_summaries
where
summary like '%1:1%' or
upper(summary) like '%ONE ON ONE%' or
(summary like '%/%' and num_attendees = 2);
