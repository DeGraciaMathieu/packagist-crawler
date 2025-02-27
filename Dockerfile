# Image de base avec PHP et Python
FROM php:8.2-cli

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Installer Composer et PHP Metrics
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
RUN composer global require phpmetrics/phpmetrics

# Créer un environnement virtuel Python et y installer les dépendances
RUN python3 -m venv /app/venv
RUN /app/venv/bin/pip install requests tqdm mysql-connector-python

# Ajouter l'environnement virtuel au PATH
ENV PATH="/app/venv/bin:$PATH"

# Ajout du binaire composer global au PATH
ENV PATH="/root/.composer/vendor/bin:${PATH}"

# Création des dossiers pour stocker les dépôts et les rapports
WORKDIR /app
RUN mkdir repos reports

# Copier le script Python dans l'image
COPY script-file.py /app/script.py

# Définir la commande d'exécution
CMD ["python3", "/app/script.py"]
