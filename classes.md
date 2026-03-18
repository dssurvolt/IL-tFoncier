# Codelab Kids T1 - Récapitulatif des Séances

## Informations Générales

- **Cible :** Enfants de la 6e à la 3e
- **Durée totale :** 24 heures (12 séances de 2h)
- **Outils :** PC, VS Code, Internet
- **Projet fil rouge :** "Mon Bénin Numérique"

---

## Séance 1 : Découverte et Mise en Route

### Objectif
Accueillir les apprenants, établir les règles de vie et découvrir le fonctionnement du web.

### Notions Abordées
- Fonctionnement du web
- Rôle des navigateurs et éditeurs de code
- Règles de vie de la classe numérique

### Déroulement
- Accueil et installation
- Icebreaker (présentation par paires)
- Présentation du programme T1
- Activité 1 : Fixons nos règles ensemble
- Activité 2 : Comment fonctionne le web ?
- Activité 3 : Navigateurs et éditeurs de code
- Kahoot de validation

---

## Séance 2 : Introduction au HTML

### Objectif
Comprendre ce qu'est un site web, créer sa première page HTML avec titres, paragraphes et images.

### Notions Abordées
- Composantes du web (navigateur, URL, fichiers)
- Structure de base d'un fichier HTML
- Balises fondamentales :
  - `<html>`, `<head>`, `<body>`
  - `<h1>`, `<h2>` (titres)
  - `<p>` (paragraphes)
  - `<img src="..." width="...">` (images)
- Droits d'auteur et images libres de droit
- Sources d'images libres : Pixabay, Unsplash, Freepik

### Déroulement
- Rappel interactif des notions passées
- Activité guidée : création du fichier `index.html` dans un dossier `codelab_Prénom`
- Activité guidée : ajout d'une image libre de droit
- Exploration autonome : personnalisation de la page

### Livrable
Page **Hello Bénin** contenant :
- Un titre
- Au moins deux paragraphes
- Une image libre correctement citée

---

## Séance 3 : Introduction au CSS

### Objectif
Découvrir les propriétés CSS de base et comprendre la différence entre HTML (structure) et CSS (style).

### Notions Abordées
- Rôle du CSS : séparer le contenu de la présentation
- Syntaxe CSS : `sélecteur { propriété: valeur; }`
- Insertion du CSS via la balise `<style>`
- Propriétés CSS de base :
  - `color` : couleur du texte
  - `background-color` : couleur de fond
  - `font-size` : taille du texte
  - `font-family` : police de caractères
  - `border` : bordure
  - `text-align` : alignement du texte
- Sélecteurs de base : `h1`, `p`, `body`
- Codes couleurs hexadécimaux (ex: `#f9f3d9`, `#d14`, `#333`)

### Déroulement
- Rappel interactif HTML
- Comparaison pages sans CSS vs avec CSS
- Activité 1 : Introduction au CSS (sélecteur → propriété → valeur)
- Atelier guidé : Styliser "Hello Bénin"
  - Changer la couleur du titre
  - Changer la police du paragraphe
  - Modifier la taille du texte
  - Choisir un fond de page
- Activité 2 : Challenge créatif (tirage au sort)
  - Ajouter une bordure à l'image
  - Centrer le texte
  - Mettre un encadré coloré autour d'un paragraphe

### Livrable
Page HTML stylisée avec :
- Au moins 3 propriétés CSS différentes
- Un fond de page personnalisé
- Un style spécifique pour titres et paragraphes
- Mise en valeur d'un élément choisi

---

## Séance 4 : Site Multi-Pages et Navigation

### Objectif
Comprendre la structure d'un petit site et créer un site à 3 pages reliées entre elles.

### Notions Abordées
- Logique multipage d'un site web
- Structure de fichiers et dossiers d'un projet web
- Création de plusieurs fichiers HTML :
  - `index.html` (Accueil)
  - `ville.html` (Ville)
  - `culture.html` (Culture)
- Balise `<a href="">` : création de liens hypertextes
- Notion de chemin relatif entre fichiers
- Navigation bar (menu de navigation)
- Balise `<title>` et cohérence entre pages

### Déroulement
- Mise en contexte : exemples de sites réels multi-pages
- Activité 1 : Création des 3 pages HTML avec squelette minimal
- Présentation de la balise `<a href="">`
- Activité 2 guidée : Création d'une navbar simple (Accueil – Ville – Culture)
- Activité 3 : Ajout de contenu (titre + 2 paragraphes par page)
- Test et correction des liens entre pages

### Livrable
Mini-site à 3 pages reliées entre elles avec navigation fonctionnelle.

---

## Séance 5 : CSS Externe

### Objectif
Créer une feuille de style externe et lier toutes les pages au même fichier CSS.

### Notions Abordées
- Différence entre CSS interne (`<style>`) et CSS externe (fichier `.css`)
- Création d'un fichier `style.css` dans un dossier `css/`
- Liaison du CSS aux pages HTML via :
  ```html
  <link rel="stylesheet" href="css/style.css">
  ```
- Notion de chemin d'accès relatif
- Propriétés CSS appliquées :
  - Couleur de fond
  - Couleur des titres
  - Taille du texte
  - Police simple
  - Couleur header/footer
  - Marges et alignements

### Déroulement
- Activité 1 : Explication du rôle du CSS externe (avant/après)
- Activité 2 guidée :
  - Création du fichier `style.css`
  - Liaison aux 3 pages
  - Application des propriétés CSS
- Atelier libre : Personnalisation (header, footer, marges, alignements)
- Débrief collectif

### Livrable
Les 3 pages du site liées à une feuille de style externe commune et personnalisée.

---

## Séance 6 : Structure Sémantique HTML

### Objectif
Comprendre la structure sémantique d'une page web et organiser correctement le contenu d'un site.

### Notions Abordées
- Notion de sémantique HTML
- Balises de structure :
  - `<header>` : en-tête de la page
  - `<nav>` : barre de navigation
  - `<main>` : contenu principal
  - `<footer>` : pied de page
- Différence entre une page désorganisée et une page structurée
- Bonne pratique : déplacer les titres, menus et contenus dans les bonnes sections
- Lisibilité et maintenabilité du code

### Déroulement
- Rappel : HTML (contenu), CSS (apparence), navigation entre pages
- Activité 1 : Découverte des balises de structure via schéma visuel
- Activité 2 guidée : Structuration des 3 pages avec les balises sémantiques
- Activité 3 autonome :
  - Restructuration des pages
  - Test de l'affichage
  - Vérification de la cohérence sur les 3 pages
- Débrief collectif et questions/réponses

### Livrable
Les 3 pages du site structurées avec les balises `<header>`, `<nav>`, `<main>`, `<footer>`.

---

## Récapitulatif des Compétences Acquises (Séances 1 à 6)

| Séance | Compétence Clé |
|--------|----------------|
| 1 | Comprendre le fonctionnement du web |
| 2 | Créer une page HTML avec titres, paragraphes et images |
| 3 | Appliquer du style CSS de base (couleurs, polices, tailles) |
| 4 | Créer un site multi-pages avec navigation |
| 5 | Lier une feuille de style externe à plusieurs pages |
| 6 | Structurer une page HTML avec des balises sémantiques |

---

## Projet Fil Rouge : "Mon Bénin Numérique"

- 3 pages HTML (Accueil, Ville, Culture)
- Design CSS externe
- Navigation complète entre les pages
- Sources d'images citées
- Structure sémantique complète