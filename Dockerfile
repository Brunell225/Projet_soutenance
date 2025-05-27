# Dockerfile

# Utilise une image officielle de Python
FROM python:3.10

# Crée un répertoire pour ton code
WORKDIR /app

# Copie le code source
COPY . /app

# Installe les dépendances
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Collecte les fichiers statiques (si besoin)
RUN python manage.py collectstatic --noinput

# Lance le serveur
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
