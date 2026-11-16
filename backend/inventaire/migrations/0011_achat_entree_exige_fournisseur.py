from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventaire', '0010_fournisseur_optionnel_pour_don'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='entree',
            constraint=models.CheckConstraint(
                condition=models.Q(origine='don') | models.Q(fournisseur__isnull=False),
                name='entree_achat_exige_fournisseur',
            ),
        ),
    ]
