from django.db import migrations


def forwards(apps, schema_editor):
    Candidate = apps.get_model('candidates', 'Candidate')
    CandidateActivity = apps.get_model('candidates', 'CandidateActivity')
    CandidateEnrollment = apps.get_model('candidates', 'CandidateEnrollment')

    User = apps.get_model('users', 'User')

    ModularResult = apps.get_model('results', 'ModularResult')
    FormalResult = apps.get_model('results', 'FormalResult')
    WorkersPasResult = apps.get_model('results', 'WorkersPasResult')

    from django.db.models import Min, Max, Count
    from django.utils import timezone
    from datetime import datetime, time

    def _actor_from_staff(staff_obj):
        if not staff_obj:
            return None
        user_id = getattr(staff_obj, 'user_id', None)
        if not user_id:
            return None
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    def _ensure(candidate_id, action, created_at, actor=None, description='', details=None):
        if not created_at:
            return
        exists = CandidateActivity.objects.filter(
            candidate_id=candidate_id,
            action=action,
            created_at=created_at,
        ).exists()
        if exists:
            return
        CandidateActivity.objects.create(
            candidate_id=candidate_id,
            actor=actor,
            action=action,
            description=description or '',
            details=details,
            created_at=created_at,
        )

    # Candidate-level events
    candidates = Candidate.objects.all().select_related(
        'created_by',
        'updated_by',
        'verified_by',
        'payment_cleared_by',
    )

    for c in candidates.iterator():
        _ensure(
            c.id,
            'candidate_created',
            getattr(c, 'created_at', None),
            actor=_actor_from_staff(getattr(c, 'created_by', None)),
            description='Candidate created',
        )

        updated_at = getattr(c, 'updated_at', None)
        created_at = getattr(c, 'created_at', None)
        if updated_at and (not created_at or updated_at != created_at):
            _ensure(
                c.id,
                'candidate_updated',
                updated_at,
                actor=_actor_from_staff(getattr(c, 'updated_by', None)),
                description='Candidate updated',
            )

        verification_date = getattr(c, 'verification_date', None)
        if verification_date:
            status = getattr(c, 'verification_status', None)
            if status == 'verified':
                _ensure(
                    c.id,
                    'candidate_verified',
                    verification_date,
                    actor=_actor_from_staff(getattr(c, 'verified_by', None)),
                    description='Candidate verified',
                )
            elif status == 'declined':
                _ensure(
                    c.id,
                    'candidate_declined',
                    verification_date,
                    actor=_actor_from_staff(getattr(c, 'verified_by', None)),
                    description='Candidate declined',
                    details={'reason': getattr(c, 'decline_reason', '')},
                )

        if getattr(c, 'payment_cleared', False) and getattr(c, 'payment_cleared_date', None):
            payment_date = c.payment_cleared_date
            # payment_cleared_date is a DateField
            dt = datetime.combine(payment_date, time.min)
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_current_timezone())
            _ensure(
                c.id,
                'payment_cleared',
                dt,
                actor=_actor_from_staff(getattr(c, 'payment_cleared_by', None)),
                description='Payment cleared',
            )

    # Enrollment events (actor unknown)
    for e in CandidateEnrollment.objects.select_related('assessment_series').all().iterator():
        _ensure(
            e.candidate_id,
            'candidate_enrolled',
            getattr(e, 'enrolled_at', None),
            actor=None,
            description='Candidate enrolled',
            details={
                'assessment_series_id': getattr(e, 'assessment_series_id', None),
                'assessment_series_name': getattr(getattr(e, 'assessment_series', None), 'name', None),
                'enrollment_id': e.id,
                'total_amount': str(getattr(e, 'total_amount', '')),
            },
        )

    # Results events
    def _actor_from_user_id(user_id):
        if not user_id:
            return None
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    # Modular results grouped by candidate + series + entered_by
    modular_groups = ModularResult.objects.values(
        'candidate_id',
        'assessment_series_id',
        'assessment_series__name',
        'entered_by_id',
    ).annotate(
        first_entered_at=Min('entered_at'),
        last_updated_at=Max('updated_at'),
        count=Count('id'),
    )

    for g in modular_groups.iterator():
        actor = _actor_from_user_id(g.get('entered_by_id'))
        created_at = g.get('first_entered_at')
        _ensure(
            g['candidate_id'],
            'modular_results_saved',
            created_at,
            actor=actor,
            description='Modular results saved',
            details={
                'assessment_series_id': g.get('assessment_series_id'),
                'assessment_series_name': g.get('assessment_series__name'),
                'count': g.get('count'),
            },
        )
        last_updated = g.get('last_updated_at')
        if last_updated and created_at and last_updated != created_at:
            _ensure(
                g['candidate_id'],
                'modular_results_updated',
                last_updated,
                actor=actor,
                description='Modular results updated',
                details={
                    'assessment_series_id': g.get('assessment_series_id'),
                    'assessment_series_name': g.get('assessment_series__name'),
                    'count': g.get('count'),
                },
            )

    # Formal results grouped by candidate + series + level + entered_by
    formal_groups = FormalResult.objects.values(
        'candidate_id',
        'assessment_series_id',
        'assessment_series__name',
        'level_id',
        'level__level_name',
        'entered_by_id',
    ).annotate(
        first_entered_at=Min('entered_at'),
        last_updated_at=Max('updated_at'),
        count=Count('id'),
    )

    for g in formal_groups.iterator():
        actor = _actor_from_user_id(g.get('entered_by_id'))
        created_at = g.get('first_entered_at')
        _ensure(
            g['candidate_id'],
            'formal_results_saved',
            created_at,
            actor=actor,
            description='Formal results saved',
            details={
                'assessment_series_id': g.get('assessment_series_id'),
                'assessment_series_name': g.get('assessment_series__name'),
                'level_id': g.get('level_id'),
                'level_name': g.get('level__level_name'),
                'count': g.get('count'),
            },
        )
        last_updated = g.get('last_updated_at')
        if last_updated and created_at and last_updated != created_at:
            _ensure(
                g['candidate_id'],
                'formal_results_updated',
                last_updated,
                actor=actor,
                description='Formal results updated',
                details={
                    'assessment_series_id': g.get('assessment_series_id'),
                    'assessment_series_name': g.get('assessment_series__name'),
                    'level_id': g.get('level_id'),
                    'level_name': g.get('level__level_name'),
                    'count': g.get('count'),
                },
            )

    # Workers PAS results grouped by candidate + series + entered_by
    workers_groups = WorkersPasResult.objects.values(
        'candidate_id',
        'assessment_series_id',
        'assessment_series__name',
        'entered_by_id',
    ).annotate(
        first_entered_at=Min('entered_at'),
        last_updated_at=Max('updated_at'),
        count=Count('id'),
    )

    for g in workers_groups.iterator():
        actor = _actor_from_user_id(g.get('entered_by_id'))
        created_at = g.get('first_entered_at')
        _ensure(
            g['candidate_id'],
            'workers_pas_results_saved',
            created_at,
            actor=actor,
            description="Worker's PAS results saved",
            details={
                'assessment_series_id': g.get('assessment_series_id'),
                'assessment_series_name': g.get('assessment_series__name'),
                'count': g.get('count'),
            },
        )
        last_updated = g.get('last_updated_at')
        if last_updated and created_at and last_updated != created_at:
            _ensure(
                g['candidate_id'],
                'workers_pas_results_updated',
                last_updated,
                actor=actor,
                description="Worker's PAS results updated",
                details={
                    'assessment_series_id': g.get('assessment_series_id'),
                    'assessment_series_name': g.get('assessment_series__name'),
                    'count': g.get('count'),
                },
            )


def backwards(apps, schema_editor):
    CandidateActivity = apps.get_model('candidates', 'CandidateActivity')

    backfill_actions = [
        'candidate_created',
        'candidate_updated',
        'candidate_verified',
        'candidate_declined',
        'payment_cleared',
        'candidate_enrolled',
        'modular_results_saved',
        'modular_results_updated',
        'formal_results_saved',
        'formal_results_updated',
        'workers_pas_results_saved',
        'workers_pas_results_updated',
    ]

    CandidateActivity.objects.filter(action__in=backfill_actions).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0011_candidateactivity'),
        ('results', '0004_workerspasresult'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
