from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0010_clamp_candidate_date_of_birth'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CandidateActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, default='')),
                ('details', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='candidate_activities', to=settings.AUTH_USER_MODEL)),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='candidates.candidate')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='candidateactivity',
            index=models.Index(fields=['candidate', 'created_at'], name='candidates_candida_2ec30e_idx'),
        ),
        migrations.AddIndex(
            model_name='candidateactivity',
            index=models.Index(fields=['action'], name='candidates_candida_7a18b5_idx'),
        ),
    ]
