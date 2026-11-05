"""Création locale interactive du premier administrateur. N'enregistre jamais le mot de passe dans Git.

Sur QNAP (une fois le conteneur démarré) :
    docker exec -it sichosana-app python -m server.bootstrap_admin

L'opérateur saisit Sicho, son email et le mot de passe provisoire.
Le changement est imposé lors de la première connexion.
"""
from getpass import getpass
import sqlite3
from server.app import initialize, connection
from server.accounts import create_admin, AccountError


def main():
    initialize()
    print("SichoSana — création du premier administrateur")
    print("Cette opération est refusée si un administrateur existe déjà.")
    pseudo = input("Pseudo initial [Sicho] : ").strip() or "Sicho"
    email = input("Email de l'administrateur : ").strip()
    password = getpass("Mot de passe provisoire (non affiché) : ")
    confirmation = getpass("Confirmer : ")
    if password != confirmation:
        raise SystemExit("Les mots de passe diffèrent.")
    try:
        with connection() as conn:
            create_admin(conn, pseudo, email, password)
    except (AccountError, sqlite3.IntegrityError) as exc:
        raise SystemExit(str(exc))
    print("Compte administrateur créé. Changement de mot de passe obligatoire dès la première connexion.")


if __name__ == "__main__":
    main()
