# AssemblerNumeroterPDF

[![Interface de l'application](https://raw.githubusercontent.com/ScorpionSage510/Images/refs/heads/main/AssemblerNumeroterPDF.png)](https://raw.githubusercontent.com/ScorpionSage510/Images/refs/heads/main/AssemblerNumeroterPDF.png)

Un outil simple avec une interface graphique pour assembler plusieurs fichiers PDF en un seul document et ajouter automatiquement la numérotation des pages.

## Fonctionnalités

*   Fusionner plusieurs fichiers PDF sélectionnés en un unique fichier PDF.
*   Ajouter des numéros de page personnalisables (format, position - *fonctionnalité de position à venir peut-être*) au document fusionné.
*   Interface graphique simple et intuitive.

## Installation et Utilisation

Vous avez deux méthodes pour utiliser l'application :

### Méthode 1 : Via l'exécutable (Windows)

C'est la méthode la plus simple pour les utilisateurs Windows.

1.  Téléchargez la dernière version depuis la section [**Releases**](https://github.com/ScorpionSage510/AssemblerNumeroterPDF/releases/tag/v1.0.0). Cherchez le fichier `NumeroterPDF.zip`.
2.  Décompressez l'archive `NumeroterPDF.zip` dans le dossier de votre choix.
3.  Lancez l'exécutable `NumeroterPDF.exe`.
4.  (Optionnel) Vous pouvez créer un raccourci vers `NumeroterPDF.exe` sur votre bureau ou dans votre menu démarrer pour un accès plus facile.

### Méthode 2 : Via le code source Python

Cette méthode nécessite Python et pip installés sur votre système.

1.  Clonez ce dépôt ou téléchargez le code source :
    ```bash
    git clone https://github.com/ScorpionSage510/AssemblerNumeroterPDF.git
    cd AssemblerNumeroterPDF
    ```
2.  (Recommandé) Créez et activez un environnement virtuel :
    ```bash
    python -m venv venv
    # Sur Windows
    .\venv\Scripts\activate
    # Sur macOS/Linux
    source venv/bin/activate
    ```
3.  Installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```
4.  Lancez l'application :
    ```bash
    python numeroterPDF.py
    ```

## ⚠️ Avertissement

Des bugs peuvent survenir lors de l'utilisation de l'application. Elle est fournie telle quelle. N'hésitez pas à signaler les problèmes rencontrés en ouvrant une [Issue](https://github.com/ScorpionSage510/AssemblerNumeroterPDF/issues).

## Contribuer

L'application est actuellement très simple. Les contributions sont les bienvenues ! Si vous souhaitez corriger des bugs, ajouter de nouvelles fonctionnalités (comme plus d'options de formatage/positionnement des numéros, prévisualisation, etc.) ou optimiser le code existant :

1.  Forkez le projet.
2.  Créez une branche pour votre fonctionnalité (`git checkout -b feature/NouvelleFonctionnalite`).
3.  Commitez vos changements (`git commit -m 'Ajout de NouvelleFonctionnalite'`).
4.  Pushez vers la branche (`git push origin feature/NouvelleFonctionnalite`).
5.  Ouvrez une Pull Request.

Merci de considérer contribuer à ce projet !