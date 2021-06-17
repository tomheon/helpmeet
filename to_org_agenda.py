import argparse
from datetime import datetime
import re

from pytz import timezone, utc, all_timezones
from tzlocal import get_localzone

import template_variables
import path
import repo


ORG_FORMAT_FILE = "org_agenda.txt"


def to_org_datetime(dt):
    tz = get_localzone()
    return dt.astimezone(tz).strftime("<%Y-%m-%d %a %H:%M>")


def strip_mailto(a):
   return re.sub('^mailto:', '', a)


def normalize_attendees(attendees):
    return [strip_mailto(a) for a in attendees.split(';')]


def augment(e):
    dtstart = datetime.fromisoformat(e['dtstart'])
    dtend = datetime.fromisoformat(e['dtend'])
    dts = f"{to_org_datetime(dtstart)}--{to_org_datetime(dtend)}"
    e['time'] = dts
    e['attendees'] = normalize_attendees(e['attendees'])
    return e

    
def to_dict(e):
    return {k: e[k] for k in e.keys()}


def augment_events(events):
    return [augment(to_dict(e)) for e in events]


def select_vevents(db):
    db.execute("""select
                    vevent_id, 
                    summary,
                    description,
                    location,
                    dtstart,
                    dtend,
                    organizer,
                    group_concat(attendee, ';') as attendees
                  from 
                    vevents natural join attendees
                  group by vevent_id
                  order by julianday(dtstart)""")
    res = db.fetchall()
    return dict(events=augment_events(res))


def render_org_agenda(date, db):
    extra_context = select_vevents(db)
    extra_context['date'] = date
    return template_variables.render_file(db, path.relative_file_name(ORG_FORMAT_FILE), extra_context=extra_context)


def parse_emails_to_names(file_name):
    if not file_name:
        return dict()
    


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("date")
    parser.add_argument("db_file")
    parser.add_argument("--emails-to-names")
    
    args = parser.parse_args()

    emails_to_names = parse_emails_to_names(args.emails_to_names)

    with repo.connect(args.db_file) as db:
        print(render_org_agenda(args.date, db))

    

if __name__ == '__main__':
    main()
