# 🎮 Confrontation des LLM au Jeu de Nim

![Screenshot du jeu](urlscreenshot.png)

## 📖 À propos

Ce projet met en compétition différents modèles de langage (LLM) dans le jeu classique de Nim. J'ai développé cette application pour me pratiquer à intégrer des LLM dans des applications interactives. C'est toujours plus motivant d'apprendre en s'amusant ! 🚀

Le jeu supporte plusieurs variantes et permet de faire jouer des LLM entre eux, ou même de jouer vous-même contre un LLM.

**Connectons-nous !** 👉 [LinkedIn - Tommy Gagné](https://www.linkedin.com/in/tommygagne/)

## 🎯 Règles du Jeu

Le jeu de Nim commence avec 21 bâtonnets. Chaque joueur retire à tour de rôle un certain nombre de bâtonnets. Le joueur qui prend le dernier bâtonnet gagne la partie.

### Variantes disponibles

- **Normal** : Retirer 1 ou 2 bâtonnets
- **Variante A** : Si le nombre de bâtonnets est pair: 1, 2 ou 4 bâtonnets ; si impair: 1, 3 ou 4 bâtonnets
- **Variante B** : Retirer 1, 2 ou 3 bâtonnets. Il ne peut pas y avoir 2 tours consécutifs où le même nombre de bâtonnets est retiré

## 🚀 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/a3jeu/nim-llm-game.git
cd nim-llm-game
```

### 2. Installer les dépendances

Ce projet utilise [uv](https://github.com/astral-sh/uv) pour la gestion des dépendances Python.

```bash
# Installer uv si ce n'est pas déjà fait
pip install uv

# Installer les dépendances du projet
uv sync
```

### 3. Configurer les clés API

Créez un fichier `.env` à la racine du projet avec vos clés API :

```env
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=sk-...
GROQ_API_KEY=gsk_...
```

> **Note** : Vous n'avez pas besoin de toutes les clés API. Le jeu fonctionnera avec les modèles dont vous avez configuré les clés.

### 4. Lancer l'application

```bash
uv run app.py
```

L'interface Gradio s'ouvrira automatiquement dans votre navigateur par défaut.

## 🦙 Utiliser Ollama (Optionnel)

Ollama permet d'exécuter des modèles LLM localement sur votre machine.

### Installation d'Ollama

1. Téléchargez et installez Ollama depuis [ollama.ai](https://ollama.ai/)
2. Téléchargez un modèle, par exemple :

```bash
ollama pull llama3.2
ollama pull qwen2.5
ollama pull mistral
```

### Configuration

Le jeu détectera automatiquement les modèles Ollama disponibles si Ollama est en cours d'exécution sur votre machine (port 11434 par défaut).

Aucune configuration supplémentaire n'est nécessaire ! Les modèles Ollama apparaîtront automatiquement dans la liste des modèles disponibles.

## 🎮 Utilisation

1. **Sélectionner les joueurs** : Choisissez un modèle LLM pour chaque joueur (Rouge et Bleu), ou sélectionnez "Humain" pour jouer vous-même
2. **Choisir la variante** : Sélectionnez la variante du jeu que vous souhaitez jouer
3. **Lancer la partie** :
   - Cliquez sur "Lancer la partie" pour une partie automatique complète
   - Cliquez sur "Prochain coup" pour avancer coup par coup
4. **Consulter les classements** : Allez dans l'onglet "Classement" pour voir les statistiques ELO

## 🏆 Système de Classement

Le jeu utilise un système de classement ELO pour évaluer la performance des différents modèles :
- **ELO Global** : Performance sur toutes les variantes
- **ELO par variante** : Performance spécifique à chaque variante

## 🛠️ Technologies utilisées

- **Python 3.12+**
- **Gradio** : Interface utilisateur web
- **OpenAI API** : GPT-4, GPT-3.5
- **Anthropic API** : Claude 3.5, Claude 3
- **DeepSeek API** : DeepSeek Chat
- **Groq API** : Llama, Mixtral
- **Ollama** : Modèles locaux
- **SQLite** : Stockage des parties et classements

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

---

Développé avec ❤️ par [Tommy Gagné](https://www.linkedin.com/in/tommygagne/)
