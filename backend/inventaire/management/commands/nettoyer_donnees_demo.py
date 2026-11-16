
from getpass import getpass
from pathlib import Path
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from inventaire.models import (
    Article, BonSortie, Categorie, Entite, Entree,
    Fournisseur, Intervient, LigneBSortie, LigneEntree,
    LigneSortie, Mouvement, Sortie, TypeArticle,
)


class Command(BaseCommand):
    help = "Supprime les données fictives en conservant le code et les migrations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep-media",
            action="store_true",
            help="Conserve les fichiers justificatifs."
        )

    def handle(self, *args, **options):
        User = get_user_model()

        self.stdout.write(self.style.WARNING(
            "Cette opération supprimera les données métier fictives "
            "et les comptes non-superutilisateurs."
        ))

        confirmation = input(
            'Tape exactement "SUPPRIMER DONNEES FICTIVES" pour confirmer : '
        )

        if confirmation != "SUPPRIMER DONNEES FICTIVES":
            raise CommandError("Opération annulée.")

        superusers = list(User.objects.filter(is_superuser=True))

        with transaction.atomic():

            # 1. Supprimer les mouvements et interventions.
            Mouvement.objects.all().delete()
            Intervient.objects.all().delete()

            # 2. Supprimer les sorties et les articles.
            LigneSortie.objects.all().delete()
            Sortie.objects.all().delete()
            Article.objects.all().delete()

            # 3. Supprimer les bons de sortie.
            LigneBSortie.objects.all().delete()
            BonSortie.objects.all().delete()

            # 4. Supprimer les entrées.
            LigneEntree.objects.all().delete()
            Entree.objects.all().delete()

            # 5. Supprimer les référentiels.
            TypeArticle.objects.all().delete()
            Categorie.objects.all().delete()
            Fournisseur.objects.all().delete()

            # 6. Préserver les administrateurs.
            for admin in superusers:
                admin.entites.clear()
                admin.role = "admin"
                admin.actif = True
                admin.is_active = True
                admin.save()

            Entite.objects.all().delete()

            # 7. Supprimer les autres comptes.
            User.objects.exclude(is_superuser=True).delete()

            # 8. Nettoyer les sessions et les journaux fictifs.
            Session.objects.all().delete()
            LogEntry.objects.all().delete()

            # 9. Créer un administrateur si nécessaire.
            if not User.objects.filter(is_superuser=True).exists():

                self.stdout.write(
                    "Aucun superutilisateur trouvé. Création nécessaire."
                )

                username = input("Nom d'utilisateur : ").strip()
                email = input("Adresse e-mail : ").strip()

                if not username or not email:
                    raise CommandError("Nom d'utilisateur et e-mail obligatoires.")

                password = getpass("Mot de passe : ")
                confirmation_password = getpass("Confirmer le mot de passe : ")

                if not password or password != confirmation_password:
                    raise CommandError("Mot de passe invalide ou différent.")

                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    role="admin",
                    actif=True,
                )

        # 10. Supprimer les documents après validation de la transaction.
        documents_dir = Path(settings.MEDIA_ROOT) / "documents"

        if not options["keep_media"] and documents_dir.exists():
            shutil.rmtree(documents_dir)

        self.stdout.write(self.style.SUCCESS(
            "Purge terminée. Le code et les migrations sont conservés."
        ))
