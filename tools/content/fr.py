# Texte français. Formulations reprises du texte en ligne de la page Steam (appdetails, l=french) ;
# faits des mises à jour (ligne de la dernière mise à jour) tirés des annonces publiées sur Steam.
# _typo() pose les espaces insécables de la typographie française (avant : ; ! ? et dans « »).
import re


def _typo(obj):
    if isinstance(obj, str):
        s = re.sub(r" ([:;!?»])", " \\1", obj)
        return s.replace("« ", "« ")
    if isinstance(obj, list):
        return [_typo(x) for x in obj]
    if isinstance(obj, tuple):
        return tuple(_typo(x) for x in obj)
    if isinstance(obj, dict):
        return {k: _typo(v) for k, v in obj.items()}
    return obj


C = _typo({
    "code": "fr",
    "lang": "fr",
    "hreflang": "fr",
    "og_locale": "fr_FR",
    "steam_l": "french",
    "native": "Français",
    "short": "FR",
    "path": "/fr/",
    "title": "Rikogol — Foot arcade à la physique réelle, en ligne entre amis",
    "description": "Du foot arcade à la physique bien réelle, en ligne avec tes amis : du duel 1v1 au derby 11v11 avec "
                   "un entraîneur de chaque côté. En accès anticipé sur Steam.",
    "og_image_alt": "Illustration de Rikogol : un disque rouge et un disque bleu se disputent le ballon au point central, "
                    "sous le logo Rikogol.",
    "ui": {
        "skip": "Aller au contenu",
        "nav_label": "Menu principal",
        "nav": ["Points forts", "Captures", "Communauté", "Kit presse"],
        "lang_label": "Langue",
        "cta": "Liste de souhaits ou achat sur Steam",
        "watch": "Voir la bande-annonce",
        "play": "Lancer la bande-annonce",
        "trailer_title": "Bande-annonce de gameplay",
        "trailer_caption": "Rikogol — Bande-annonce de gameplay (0:50) · en anglais (version française sur la page Steam)",
        "video_fallback": "Ton navigateur ne peut pas lire cette vidéo.",
        "download_mp4": "Télécharger la bande-annonce (MP4)",
        "widget_title": "Rikogol sur Steam",
        "close": "Fermer",
        "prev": "Capture précédente",
        "next": "Capture suivante",
        "full": "Taille réelle (JPG 1920×1080)",
        "viewer": "Visionneuse de captures",
        "footer_nav": "Liens",
        "contact": "Contact",
        "store_link": "Rikogol sur Steam",
        "dev_link": "Deniz Durusoy sur Steam",
        "press": "Kit presse (en anglais)",
        "not_affiliated": "Rikogol n’est pas affilié à Haxball.",
        "made_by": "Par Deniz Durusoy",
    },
    "hero": {
        "tagline": "Du foot arcade à la physique bien réelle, en ligne avec tes amis.",
        "sub": "Du duel 1v1 au derby 11v11 avec un entraîneur de chaque côté. "
               "Deux commandes, zéro statistique, ni faute ni hors-jeu — juste du talent.",
        "facts": ["Accès anticipé", "Windows et macOS", "Jusqu’à 24 joueurs", "8 langues"],
    },
    "band": {
        "kicker": "Disponible",
        "title": "Jouable dès maintenant en accès anticipé",
        "text": "Rikogol est sorti sur Steam le 14 septembre 2026. La dernière mise à jour, Coop canapé (v1.6), "
                "apporte le jeu à deux sur un seul PC en mode Contre les Bots et la prise en charge complète des "
                "manettes, puis son hotfix v1.6.1 a ajouté trois petits correctifs.",
        "link": "Lire les notes de mise à jour",
    },
    "pitch": {
        "kicker": "Le jeu",
        "title": "Bouge. Tire. Marque.",
        "paras": [
            "Rikogol, c’est du football arcade que tu joues en ligne avec tes amis. Deux commandes — bouger et tirer — "
            "et un moteur physique s’occupe du reste : chaque passe, chaque rebond sur le mur, chaque tir qui frôle le "
            "poteau et rentre. Pas de stats de joueurs, pas de dés, pas de fautes, pas de hors-jeu. Tu gagnes, tu l’as "
            "mérité. Tu perds, tu sais exactement pourquoi.",
            "Si tu as grandi avec le foot physique vu du dessus dans un onglet de navigateur, tu sais déjà jouer. "
            "Aujourd’hui, ça vit sur Steam — avec des salons, ta liste d’amis et un terrain à 24 joueurs.",
        ],
        "fans": "Pensé pour les fans de foot physique à la Haxball, et pour tous ceux qui veulent un match rapide entre "
                "amis.",
    },
    "features": [
        {
            "id": "match-sizes",
            "kicker": "Du 1v1 au 11v11",
            "title": "Du duel 1v1 au derby 11v11",
            "body": [
                "Règle ça en un contre un sur un minuscule terrain, enchaîne des 3v3 rapides, ou remplis un stade "
                "immense avec 22 joueurs et un entraîneur de chaque côté. Quatre stades, des équipes de 1 à 11, et les "
                "règles du salon t’appartiennent : limite de buts, chrono, puissance de tir, mot de passe.",
            ],
            "stat": ["24", "joueurs dans un même match : 22 sur le terrain, un entraîneur de chaque côté"],
            "img": 7,
        },
        {
            "id": "head-coach",
            "kicker": "La touche propre à Rikogol",
            "title": "Sois l’entraîneur",
            "body": [
                "Un joueur par équipe peut quitter le terrain et diriger l’équipe depuis la touche. Change de formation "
                "en plein match, pose des pings sur la pelouse — passe, monte, recule — et trace des flèches que seule "
                "ton équipe voit.",
                "L’adversaire ne reçoit jamais tes pings ni tes flèches : l’hôte les filtre avant qu’ils ne partent.",
            ],
            "img": 2,
        },
        {
            "id": "bots",
            "kicker": "Contre les Bots",
            "title": "Salon pas plein ? Joue tout de suite",
            "body": [
                "Entraînement › Contre les Bots, c’est un vrai match, mi-temps et écran de résultats compris, jouable "
                "même hors ligne. Choisis la taille d’équipe de 1v1 à 11v11, le stade, les limites de buts et de temps "
                "et la difficulté des bots (Facile, Moyenne ou Difficile) : ils complètent ton équipe et forment toute "
                "l’équipe adverse.",
                "Dans les salons en ligne, l’hôte ajoute des bots aux équipes ou active « Compléter avec des Bots », et "
                "un ami qui rejoint le salon prend aussitôt la place d’un bot, même en plein match. Les bots ne jouent "
                "que sur le terrain : ils ne prennent jamais la place de l’entraîneur.",
            ],
            "img": 5,
        },
        {
            "id": "invites",
            "kicker": "Invitations Steam",
            "title": "Des amis sur le terrain en quelques secondes",
            "list": [
                "Invite directement depuis ta liste d’amis Steam, ou rejoins un salon ouvert via le navigateur de parties",
                "Steam Relay sous le capot : pas de redirection de port, pas de compte en plus, aucune configuration",
                "Jusqu’à 24 joueurs dans un match — 22 sur le terrain, un entraîneur de chaque côté",
                "Chat de salon et chat en match",
            ],
            "img": 3,
        },
        {
            "id": "atmospheres",
            "kicker": "Atmosphères et supporters",
            "title": "Chaque but a des airs de finale",
            "body": [
                "Projecteurs de nuit, soleil de midi, coucher de soleil doré, neige ou pluie : cinq atmosphères, à toi "
                "de choisir. Plus il y a de joueurs, plus les tribunes sont pleines — et quand le ballon fait trembler "
                "les filets, les supporters derrière le but explosent de joie.",
                "Chaque joueur sur le terrain porte son nom et son numéro de maillot, et le nom du buteur apparaît sur "
                "le bandeau du but. L’atmosphère ne change que ton propre écran — personne ne peut faire pleuvoir sur "
                "son adversaire.",
            ],
            "img": 10,
        },
    ],
    "extras_title": "Et aussi",
    "extras": [
        {
            "icon": "access",
            "title": "Accessibilité",
            "text": "Des palettes d’équipe adaptées aux daltoniens et un mode contraste élevé. Toutes les commandes sont "
                    "réassignables, et les menus s’utilisent entièrement au clavier.",
        },
        {
            "icon": "trophy",
            "title": "65 succès Steam",
            "text": "L’entraînement à tout moment : affûte tes tirs en solo ou affronte des bots. Steam Cloud garde tes "
                    "réglages sur chaque machine.",
        },
        {"icon": "globe", "title": "8 langues", "langs": True},
    ],
    "gallery": {
        "kicker": "Captures",
        "title": "Sur le terrain",
        "hint": "Sélectionne une capture pour l’agrandir.",
    },
    "alts": {
        1: "But ! Le bandeau de but affiche le nom du buteur pendant que les confettis tombent devant une tribune pleine.",
        2: "Coup d’envoi d’un match 11v11 pendant qu’un entraîneur choisit la formation sur le tableau tactique.",
        3: "Le salon : deux équipes de onze au complet et les réglages de l’hôte pour le stade, la taille d’équipe, les "
           "limites de buts et de temps, la puissance de tir, le mode entraîneur et le mot de passe.",
        4: "Des bots, chacun avec l’étiquette BOT à côté de son nom, s’approchent du but en seconde période.",
        5: "Un bot marque : le bandeau de but affiche son nom pendant que les confettis volent autour du filet.",
        6: "Un duel en un contre un sous la neige.",
        7: "Les deux équipes alignées pour le coup d’envoi d’un 11v11, tribunes pleines de supporters rouges et bleus.",
        8: "Un 3v3 autour du rond central, en plein jour.",
        9: "Un match de jour près de la ligne médiane, devant des tribunes remplies de supporters rouges et bleus.",
        10: "Un match sous la pluie : les gouttes rebondissent sur la pelouse, près d’une tribune pleine.",
        11: "Un match sous un coucher de soleil doré : un joueur file vers le but, ballon au pied.",
        12: "Un ping de l’entraîneur et une flèche de passe sur un terrain bien rempli.",
        13: "Le navigateur de parties, qui liste les salons ouverts avec leur stade, leur taille d’équipe, leur limite "
            "de buts et leur durée.",
        14: "Le bandeau de seconde période à la reprise d’un match 11v11 sous la pluie.",
        15: "Fin du match : le bandeau de résultat annonce le vainqueur, avec le bouton de retour au salon.",
        16: "Le menu principal (Entraînement, En ligne, Paramètres) sur fond de terrain animé.",
    },
    "community": {
        "kicker": "Communauté",
        "title": "Rikogol Cup",
        "text": "Des tournois communautaires se préparent. Tu veux en organiser un pour tes amis, ton club ou ta ligue ? "
                "Écris à {email} et parle-nous de ton projet.",
        "button": "Organiser un tournoi",
        "subject": "Rikogol Cup",
    },
    "finale": {
        "title": "Rendez-vous sur le terrain",
        "text": "Rikogol est disponible en accès anticipé sur Steam pour Windows et macOS.",
        "dev": "Rikogol est un jeu indépendant développé en Turquie par {dev}.",
    },
})
