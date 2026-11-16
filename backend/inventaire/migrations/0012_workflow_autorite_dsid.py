from django.db import migrations, models
import django.db.models.deletion


def reouvrir_bons_en_cours(apps, schema_editor):
    BonSortie = apps.get_model('inventaire', 'BonSortie')
    LigneBSortie = apps.get_model('inventaire', 'LigneBSortie')
    ids = list(BonSortie.objects.filter(
        statut__in=['en_attente_autorisation', 'en_attente_validation']
    ).values_list('id', flat=True))
    if ids:
        LigneBSortie.objects.filter(bon_sortie_id__in=ids).update(
            etat_ligne='demandee', quantite_autorisee=None, quantite_validee=None
        )
        BonSortie.objects.filter(id__in=ids).update(
            statut='en_attente_choix_autorite', autorite_choisie=None,
            autorite_choisie_par=None, autorite_choisie_le=None
        )


def annuler_reouverture(apps, schema_editor):
    # Les anciennes décisions restent dans Intervient ; la migration inverse
    # ne peut pas reconstituer sans ambiguïté l'ancien état de chaque ligne.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('inventaire', '0011_achat_entree_exige_fournisseur'),
    ]

    operations = [
        migrations.AddField(
            model_name='bonsortie',
            name='autorite_choisie',
            field=models.CharField(blank=True, choices=[('dg', 'Directeur Général (DG)'), ('dga', 'Directeur Général Adjoint (DGA)'), ('directeur_dsid', 'Directeur DSID')], max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='bonsortie',
            name='autorite_choisie_le',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='bonsortie',
            name='autorite_choisie_par',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='choix_autorite_bons_sortie', to='inventaire.utilisateur'),
        ),
        migrations.AlterField(
            model_name='utilisateur',
            name='role',
            field=models.CharField(choices=[('admin', 'Administrateur'), ('agent_dsid', 'Agent DSID'), ('agent_validation', 'Ancien agent de validation (DCA)'), ('dg', 'Directeur Général (DG)'), ('dga', 'Directeur Général Adjoint (DGA)'), ('directeur_dsid', 'Directeur DSID'), ('agent_came', 'Agent CAME'), ('demandeur', 'Demandeur'), ('agent_direction', 'Agent de direction'), ('auditeur', 'Auditeur')], max_length=30),
        ),
        migrations.AlterField(
            model_name='bonsortie',
            name='statut',
            field=models.CharField(choices=[('brouillon', 'Brouillon'), ('en_attente_choix_autorite', 'En attente du choix de l’autorité par le DSID'), ('en_attente_autorisation', 'En attente de la décision de l’autorité'), ('en_attente_validation', 'Ancienne étape de validation DCA'), ('valide', 'Validé'), ('refuse', 'Refusé'), ('sorti', 'Sorti')], default='brouillon', max_length=30),
        ),
        migrations.RunPython(reouvrir_bons_en_cours, annuler_reouverture),
    ]
