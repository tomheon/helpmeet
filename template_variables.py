import jinja2


def read_all(db):
    db.execute('select varname, varval from template_variables')
    res = db.fetchall()
    return dict([(r[0], r[1]) for r in res])


def set(db, varname, varval):
    sql = """
          insert into template_variables (varname, varval) values (?, ?)
          on conflict(varname) do update set varval = excluded.varval
          """
    db.execute(sql, (varname, varval))


def render_file(db, fname, extra_context=dict()):
    with open(fname, 'rb') as fh:
        return render_text(db, fh.read().decode('utf-8'), extra_context)

    
def render_text(db, text, extra_context):
    jinja_env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)
    t = jinja_env.from_string(text)
    context = read_all(db)
    context.update(extra_context)
    return t.render(context)
