from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('inventaire', '0007_mouvement_operation_ref_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='entree',
            name='document_fichier',
            field=models.FileField(blank=True, null=True, upload_to='documents/entrees/%Y/%m/'),
        ),
        migrations.AddField(
            model_name='bonsortie',
            name='document_fichier',
            field=models.FileField(blank=True, null=True, upload_to='documents/bons-sortie/%Y/%m/'),
        ),
        migrations.AddField(
            model_name='sortie',
            name='document_livraison',
            field=models.FileField(blank=True, null=True, upload_to='documents/livraisons/%Y/%m/'),
        ),
    ]
