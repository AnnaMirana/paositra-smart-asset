from pptx import Presentation
from pptx.util import Inches, Pt

out = "PAOSITRA_Kit_Express_2_Serializers_Views_URLs_Settings_Tests.pptx"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

def add_slide(title, bullets, subtitle=None):
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(12.1), Inches(0.7))
    p = title_box.text_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(28)
    p.font.bold = True
    
    if subtitle:
        sub = slide.shapes.add_textbox(Inches(0.65), Inches(1.05), Inches(12), Inches(0.45))
        sp = sub.text_frame.paragraphs[0]
        sp.text = subtitle
        sp.font.size = Pt(15)
    
    body = slide.shapes.add_textbox(Inches(0.8), Inches(1.55), Inches(11.8), Inches(5.35))
    tf = body.text_frame
    tf.word_wrap = True
    tf.clear()
    for i, item in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if isinstance(item, tuple):
            text, level = item
        else:
            text, level = item, 0
        p.text = text
        p.level = level
        p.font.size = Pt(19 if level == 0 else 16)
        p.space_after = Pt(10 if level == 0 else 5)
    return slide

# Cover
slide = prs.slides.add_slide(prs.slide_layouts[5])
tb = slide.shapes.add_textbox(Inches(0.8), Inches(1.4), Inches(11.8), Inches(2.0))
p = tb.text_frame.paragraphs[0]
p.text = "PAOSITRA SMART ASSET 🚀"
p.font.size = Pt(36); p.font.bold = True
p2 = tb.text_frame.add_paragraph()
p2.text = "Kit Express — serializers.py → views.py → URLs → settings → tests"
p2.font.size = Pt(24)
p3 = tb.text_frame.add_paragraph()
p3.text = "Objectif : comprendre le trajet COMPLET d’une requête, pas mémoriser du code."
p3.font.size = Pt(18)

add_slide("🧭 Le grand voyage d’une requête", [
    "React / navigateur 📱",
    "↓ HTTP : GET / POST / PUT / DELETE",
    "inventaire/urls.py → quelle route ?",
    "views.py → que fait-on avec la requête ?",
    "serializer.py → comment transformer / valider les données ?",
    "services.py → logique métier",
    "models.py / ORM → PostgreSQL",
    "↑ réponse JSON → React",
], "Si tu comprends cette chaîne, tu comprends déjà une grosse partie de Django REST.")

add_slide("4️⃣ serializers.py — son vrai rôle", [
    "Un serializer = traducteur entre objets Django et JSON.",
    "Django pense en objets/modèles ; React pense en JSON.",
    "Il peut aussi VALIDER les données reçues par l’API.",
    "Il ne doit pas devenir le lieu principal de la logique métier complexe.",
    "Exemple : Article Django → { id, ref_article, marque, type_article, ... }"
])

add_slide("🧠 ModelSerializer : le raccourci magique", [
    "class ArticleSerializer(serializers.ModelSerializer):",
    "→ DRF regarde le modèle Article.",
    "→ Il construit automatiquement beaucoup de champs.",
    "Meta.model = Article",
    "Meta.fields = [...] → contrôle précisément ce que l’API expose.",
    "Donc : modèle ≠ serializer, mais le serializer s’appuie sur le modèle."
])

add_slide("🔒 read_only_fields — pourquoi ?", [
    "Exemple actuel : ArticleSerializer",
    "ref_article, type_article, ligne_entree sont read_only.",
    "Pourquoi ? Parce que ces valeurs sont décidées par le backend.",
    "Cela évite qu’un client envoie : type_article = ordinateur alors que l’article appartient à imprimante.",
    "Règle pédagogique : ce que le métier doit contrôler côté serveur ne doit pas être librement modifiable par React."
])

add_slide("📦 LigneEntreeInputSerializer", [
    "Celui-ci n’est pas un ModelSerializer.",
    "Il décrit une entrée API simple :",
    "→ type_article",
    "→ quantite",
    "quantite = IntegerField(min_value=1) : DRF refuse 0 ou négatif.",
    "C’est exactement ce qu’on veut pour POST /entrees/{id}/ajouter_ligne/."
])

add_slide("👀 SerializerMethodField : afficher une info calculée", [
    "Exemple : EntreeSerializer → lignes = SerializerMethodField().",
    "get_lignes(self, obj) construit la représentation envoyée.",
    "On peut donc afficher le nom du type sans modifier la structure SQL.",
    "À retenir : un serializer peut préparer une réponse pratique pour le frontend."
])

add_slide("⚠️ Petit piège à connaître", [
    "read_only_fields ≠ sécurité métier complète.",
    "Et ModelSerializer ne connaît pas automatiquement toutes les règles métier.",
    "Exemple : « une sortie ne doit être possible que si le BS est validé ».",
    "Cette règle doit être imposée côté serveur (service / validation / permission), pas seulement par React.",
])

add_slide("5️⃣ views.py — le chef d’orchestre 🎬", [
    "Une ViewSet reçoit une requête HTTP.",
    "Elle identifie l’action.",
    "Elle récupère / valide les données.",
    "Elle appelle la logique métier si nécessaire.",
    "Elle renvoie une Response HTTP.",
    "Exemple : POST /entrees/12/ajouter_ligne/ → EntreeViewSet.ajouter_ligne()."
])

add_slide("🔁 ViewSet classique", [
    "ModelViewSet donne plusieurs actions prêtes à l’emploi :",
    "GET liste → list",
    "GET /id → retrieve",
    "POST → create",
    "PUT/PATCH → update",
    "DELETE → destroy",
    "Mais cela ne veut PAS dire que toutes ces actions sont automatiquement adaptées au métier."
])

add_slide("🛡️ IsAuthenticated", [
    "permission_classes = [IsAuthenticated]",
    "→ l’utilisateur doit être connecté.",
    "Mais actuellement, cela ne signifie pas : « seul DSID peut autoriser ».",
    "Le contrôle par rôle est encore une fonctionnalité métier à compléter.",
    "Donc : authentification ≠ autorisation."
])

add_slide("🎯 @action : ajouter une route métier", [
    "Exemple : @action(detail=True, methods=['post'])",
    "→ crée une action personnalisée sur une ressource.",
    "POST /api/entrees/12/ajouter_ligne/",
    "Ici, ce n’est pas un CRUD banal : on déclenche enregistrer_ligne_entree().",
    "C’est utile quand une opération métier mérite son propre endpoint."
])

add_slide("📥 Le chemin d’une entrée", [
    "1. React envoie type_article + quantité.",
    "2. View → LigneEntreeInputSerializer valide.",
    "3. View → services.enregistrer_ligne_entree(...).",
    "4. Service → crée LigneEntree.",
    "5. Individualisé → crée N Article + N mouvements.",
    "6. Consommable → augmente TypeArticle.quantite_stock + mouvement avec quantité.",
    "7. View → Response JSON."
])

add_slide("📊 CORRECTION IMPORTANTE : le stock global", [
    "Décision validée : TypeArticle.quantite_stock = STOCK TOTAL DU TYPE.",
    "Même si gestion_individuelle=True.",
    "Exemple : 3 ordinateurs entrent → 3 Articles créés + 3 mouvements + quantite_stock = 3.",
    "Puis 1 ordinateur sort → quantite_stock = 2 + mouvement de sortie pour l’article.",
    "Donc : Article sert à tracer chaque pièce ; TypeArticle sert à voir combien il en reste."
])

add_slide("🚨 Le bug que vous avez trouvé", [
    "Ancien code : stock_disponible() retournait quantite_stock.",
    "Pour les ordinateurs, quantite_stock restait à 0.",
    "Résultat : une sortie de 1 ordinateur pouvait être refusée alors qu’il existait 3 Articles.",
    "La correction : le stock global doit être mis à jour aussi pour les individualisés.",
    "Très bon exemple de pourquoi tester le métier et pas seulement « est-ce que Django démarre ? »."
])

add_slide("📤 effectuer_sortie() — logique", [
    "1. Vérifier le stock pour chaque type.",
    "2. Si demandé > disponible → sortie refusée.",
    "3. Créer Sortie + ses LigneSortie.",
    "4. Individualisé → sélectionner les Articles disponibles + créer leurs mouvements.",
    "5. Consommable → diminuer quantite_stock + mouvement avec quantité.",
    "6. Le stock global du TypeArticle doit donc diminuer dans LES DEUX CAS."
])

add_slide("🧩 views.py : ce qui reste à améliorer", [
    "Le vertical slice actuel simplifie le vrai workflow.",
    "Aujourd’hui : effectuer_sortie prend directement les quantités demandées.",
    "Mais le métier prévoit : demandé → autorisé/refusé → validé/rejeté → livré.",
    "Donc plus tard : les vues devront déclencher les étapes du workflow sans contourner les règles.",
])

add_slide("6️⃣ inventaire/urls.py — les routes de l’app", [
    "DefaultRouter() enregistre automatiquement les ViewSets.",
    "router.register('categories', CategorieViewSet)",
    "router.register('entrees', EntreeViewSet)",
    "router.register('sorties', SortieViewSet)",
    "router.register('mouvements', MouvementViewSet)",
    "C’est la table de correspondance « URL → ViewSet »."
])

add_slide("🔗 Et @action alors ?", [
    "Le router voit aussi les actions personnalisées.",
    "Exemple : ajouter_ligne sur EntreeViewSet.",
    "→ /api/entrees/{id}/ajouter_ligne/",
    "Exemple : effectuer sur SortieViewSet.",
    "→ /api/sorties/effectuer/",
    "À retenir : urls.py expose les portes ; views.py décide ce qui se passe derrière."
])

add_slide("7️⃣ config/urls.py — les routes globales 🌍", [
    "admin/ → interface Django Admin.",
    "api/ → tout ce qui vient de inventaire.urls.",
    "Donc /api/categories/, /api/articles/, etc. passent par là.",
    "Pourquoi deux urls.py ?",
    "→ config = projet global ; inventaire = routes de l’application métier."
])

add_slide("8️⃣ settings.py — le tableau de bord Django ⚙️", [
    "Ce fichier configure le comportement global du projet.",
    "INSTALLED_APPS → applications activées.",
    "AUTH_USER_MODEL → notre Utilisateur personnalisé.",
    "MIDDLEWARE → traitement des requêtes/réponses.",
    "ROOT_URLCONF → où trouver les routes globales.",
    "DATABASES → PostgreSQL.",
    "STATIC_URL → fichiers statiques.",
])

add_slide("🔐 settings.py : sécurité / environnement", [
    "SECRET_KEY → secret Django, à protéger.",
    "DEBUG=True → pratique en développement, pas pour production.",
    "ALLOWED_HOSTS → hôtes autorisés.",
    ".env → stocker les secrets/config sensibles hors du code.",
    "Dans ton projet : DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT viennent de l’environnement."
])

add_slide("🌍 TIME_ZONE — petit détail, gros effet", [
    "Le projet actuel est configuré en UTC.",
    "USE_TZ=True → Django gère les dates avec fuseaux horaires.",
    "Pour un projet Paositra utilisé à Madagascar, il faudra décider si l’affichage doit être adapté à l’heure locale.",
    "À distinguer : stockage technique des dates vs affichage pour l’utilisateur."
])

add_slide("9️⃣ test_scenarios.py — pourquoi tester ?", [
    "Un scénario de test vérifie un comportement métier.",
    "Pas seulement : « le serveur démarre ».",
    "Exemples :",
    "→ entrée de 3 ordinateurs crée 3 Articles.",
    "→ stock TypeArticle devient 3.",
    "→ sortie de 1 ordinateur → stock devient 2.",
    "→ sortie de 50 alors que stock = 2 → refus.",
    "→ entrée de 50 consommables → pas de 50 Articles individualisés."
])

add_slide("🧪 Le bon réflexe : tester les deux mondes", [
    "CAS A — gestion_individuelle=True",
    "TypeArticle = Ordinateur portable",
    "Entrée 3 → Articles 3 + stock global 3 + mouvements 3.",
    "Sortie 1 → Article sorti + stock global 2 + mouvement sortie.",
    "",
    "CAS B — gestion_individuelle=False",
    "TypeArticle = Cartouche d’encre",
    "Entrée 50 → aucun Article + stock 50 + mouvement quantité 50.",
    "Sortie 10 → stock 40 + mouvement quantité 10."
])

add_slide("❌ Ce qu’un test doit aussi attraper", [
    "Stock insuffisant.",
    "Quantité 0 ou négative.",
    "Double sortie du même BS.",
    "Article individualisé déjà sorti.",
    "Mouvement sans article ET sans type_article.",
    "Mouvement avec article ET type_article en même temps.",
    "Et plus tard : sortie avant validation du BS."
])

add_slide("🧠 Le chemin complet à retenir", [
    "UTILISATEUR",
    "↓",
    "React / navigateur",
    "↓ HTTP",
    "URL → ViewSet",
    "↓",
    "Serializer = validation / format JSON",
    "↓",
    "Service = logique métier",
    "↓",
    "Model / ORM",
    "↓",
    "PostgreSQL",
    "↑",
    "JSON → React"
])

add_slide("🎓 Questions jury probables", [
    "« Pourquoi un serializer ? » → transformer/valider les données API.",
    "« Pourquoi un service ? » → isoler la logique métier complexe.",
    "« Pourquoi urls.py ? » → router les requêtes vers les bonnes vues.",
    "« Pourquoi settings.py ? » → configuration globale Django.",
    "« Authentification vs autorisation ? » → connecté ≠ autorisé à tout faire.",
    "« Pourquoi TypeArticle ET Article ? » → stock global + traçabilité individuelle."
])

add_slide("🔮 Après le backend : React", [
    "React ne doit pas contenir les règles métier critiques.",
    "Il affichera : stock, articles, BS, validations, mouvements, alertes…",
    "Il appellera l’API Django.",
    "Exemple : fetch('/api/types-article/') → JSON → affichage.",
    "Objectif : construire d’abord un écran métier utile, puis enrichir."
])

add_slide("🚀 Fonctionnalités métier restantes", [
    "Workflow complet du Bon de Sortie : autorisation → validation → livraison.",
    "Permissions par rôle.",
    "Notifications dashboard / e-mail selon besoin.",
    "Avoirs par direction.",
    "Retours contrôlés.",
    "Hors service / perte / réintégration.",
    "QR pour les articles individualisés.",
    "Dashboard + alertes.",
    "Tests automatisés + sécurité."
])

add_slide("📝 Ton mini-plan d’étude", [
    "Tu n’as pas besoin de mémoriser les lignes.",
    "Tu dois savoir répondre à :",
    "1. Qui reçoit la requête ?",
    "2. Où est-elle routée ?",
    "3. Où les données sont-elles validées ?",
    "4. Où la logique métier est-elle exécutée ?",
    "5. Où les données sont-elles stockées ?",
    "6. Quel JSON revient au frontend ?"
])

add_slide("🏁 Challenge final 😈", [
    "Sans regarder le code :",
    "« Que se passe-t-il quand React envoie POST /api/entrees/12/ajouter_ligne/ avec type_article=3 et quantite=5 ? »",
    "",
    "Réponse attendue : URL → View → serializer → service → DB → mouvements/articles ou stock → Response JSON.",
    "",
    "Si tu peux raconter ça naturellement, tu as compris l’architecture. 🔥"
])

prs.save(out)
print(f"Fichier créé : {out}")
