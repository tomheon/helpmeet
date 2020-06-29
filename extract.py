import argparse
import datetime

import icalendar
import recurring_ical_events

import repo
import template_variables


def is_accepted(a):
    partstat = (a.params.get('partstat') or '')
    return partstat.upper() == 'ACCEPTED'


def is_individual(a):
    cutype = (a.params.get('cutype') or '')
    return cutype.upper() == 'INDIVIDUAL'


def store_attendees(db, v_id, attendees, default_attendee):
    final_attendees = []
    if not attendees:
        final_attendees.append((str(default_attendee), True))
    else:
        if not isinstance(attendees, list):
            attendees = [attendees]
        final_attendees = [(str(a), is_accepted(a)) for a in attendees if is_individual(a)]

    db.executemany('insert into attendees (vevent_id, attendee, accepted) values (?, ?, ?)',
                   [(v_id, a, accepted) for (a, accepted) in final_attendees])


def safe_dt(v, field):
    f = v.get(field)
    if not f:
        return None
    else:
        return f.dt

    
def store_vevent(db, v, default_attendee):
    db.execute("""
               insert into vevents 
                 (uid, summary, dtstart, dtend, is_recurring, organizer)
                 values 
                 (?, ?, ?, ?, ?, ?)
               """,
               (v.get('uid'),
                v.get('summary'),
                safe_dt(v, 'dtstart'),
                safe_dt(v, 'dtend'),
                bool(v.get('recurrence-id')),
                v.get('organizer')))
    db.execute('select last_insert_rowid()')
    v_id = db.fetchone()[0]

    store_attendees(db, v_id, v.get('attendee'), default_attendee)


def is_vevent(component):
    return component.name == 'VEVENT'


def extract_from_file(ical_file, start_date, end_date, calendar_owner, db):
    ical = icalendar.Calendar.from_ical(ical_file.read())
    extract(ical, start_date, end_date, calendar_owner, db)

    
def extract(ical, start_date, end_date, calendar_owner, db):
    filtered = icalendar.Calendar()
    calendar_name = ical.get('X-WR-CALNAME')
    template_variables.set(db, 'calendar_name', calendar_name)
    template_variables.set(db, 'start_date', start_date)
    template_variables.set(db, 'end_date', end_date)
    if calendar_owner:
        template_variables.set(db, 'calendar_owner', calendar_owner)
    for c in ical.walk():
        if c.get('dtstart') and c.get('dtend'):
            filtered.add_component(c)
    vevents = recurring_ical_events.of(filtered).between(start_date, end_date)

    for v in vevents:
        store_vevent(db, v, calendar_owner or calendar_name)

    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ical_file", type=argparse.FileType())
    parser.add_argument("start_date", type=datetime.datetime.fromisoformat)
    parser.add_argument("end_date", type=datetime.datetime.fromisoformat)
    parser.add_argument("--calendar_owner")
    parser.add_argument("db_file")

    args = parser.parse_args()
    with repo.init(args.db_file) as db:
        extract_from_file(ical_file, args.start_date, args.end_date, args.calendar_owner, db)


if __name__ == '__main__':
    main()
