import argparse
import datetime

from classify import classify_in_place
from extract import extract_from_file
import repo
from report import render_reports


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ical_file", type=argparse.FileType())
    parser.add_argument("start_date", type=datetime.datetime.fromisoformat)
    parser.add_argument("end_date", type=datetime.datetime.fromisoformat)
    parser.add_argument("--calendar_owner")
    parser.add_argument("--db_file", default=":memory:")
    parser.add_argument("--rules_dir", default="sample_rules")
    parser.add_argument("--reports_dir", default="sample_reports")
    parser.add_argument("--format_file", default="output_format.txt.jinja2")

    args = parser.parse_args()
    with repo.init(args.db_file) as db:
        extract_from_file(args.ical_file, args.start_date, args.end_date, args.calendar_owner, db)
        classify_in_place(db, args.rules_dir)
        print(render_reports(db, args.reports_dir, args.format_file))


if __name__ == '__main__':
    main()
