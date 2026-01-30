from django.db import migrations
from datetime import date


def _shift_years(d, years):
    try:
        return d.replace(year=d.year - years)
    except ValueError:
        return d.replace(year=d.year - years, month=2, day=28)


def clamp_candidate_dobs(apps, schema_editor):
    Candidate = apps.get_model('candidates', 'Candidate')
    today = date.today()
    min_dob = _shift_years(today, 100)
    max_dob = _shift_years(today, 12)

    qs = Candidate.objects.exclude(date_of_birth__isnull=True)
    for c in qs.iterator():
        dob = c.date_of_birth
        if dob < min_dob:
            c.date_of_birth = min_dob
            c.save(update_fields=['date_of_birth'])
        elif dob > max_dob:
            c.date_of_birth = max_dob
            c.save(update_fields=['date_of_birth'])


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0009_alter_candidate_nationality'),
    ]

    operations = [
        migrations.RunPython(clamp_candidate_dobs, migrations.RunPython.noop),
    ]
