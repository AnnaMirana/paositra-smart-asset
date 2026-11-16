from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventaire', '0009_utilisateur_doit_changer_mot_de_passe_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entree',
            name='fournisseur',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='entrees',
                to='inventaire.fournisseur',
            ),
        ),
    ]
