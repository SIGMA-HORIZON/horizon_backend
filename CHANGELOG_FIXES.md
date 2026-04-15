# Horizon Backend - Note de Mise à Jour (Bug Fixes)

Ce document récapitule l'ensemble des corrections majeures et des ajustements de configuration apportés au backend pour stabiliser le système d'approbation et de gestion des ressources.

## 1. Conflits de Port PostgreSQL
**Problème** : Le backend n'arrivait pas à se connecter à la base de données car le port `5432` était déjà occupé par une autre instance PostgreSQL locale sur la machine.
**Solution** : 
- Arrêt des services conflictuels et utilisation stricte du conteneur Docker `db` configuré dans le `docker-compose.yml`.
- Mise à jour de `alembic.ini` pour pointer faire correspondre les identifiants corrects (`horizon_user:horizon_pass`) afin que les migrations de base de données (`alembic upgrade head`) s'exécutent avec succès.

## 2. Configuration SMTP & Notifications Administrateurs
**Problème** : Les requêtes d'approbation n'envoyaient pas de mail après traitement.
**Solution** : 
- Mise à jour du script de développement (`scripts/seed.py`) pour attribuer un vrai compte Gmail (`billnelson113@gmail.com`) au compte administrateur.
- Configuration du `.env` en mode `smtp` via Gmail (Nécessite d'utiliser un Mot de passe d'Application Google à 16 caractères pour contourner la validation 2FA de Google). 

## 3. Crash lors de l'Approbation de compte (Erreur 500 & Uniqueness)
**Problème** : En acceptant une demande de compte (`/requests/{request_id}/approve`), si l'adresse e-mail existait déjà en base de données, l'API s'effondrait ("Internal Server Error") avec l'exception base de données `IntegrityError: duplicate key value violates unique constraint "users_email_key"`.
**Solution** : 
- Modification du contrôleur `approve_account_request` dans `service.py` pour valider l'existence de l'e-mail **avant** de forcer l'insertion dans la DB.
- L'API rejette désormais poliment l'action avec une erreur `HTTP 409 Conflict` pour prévenir l'administrateur sans planter le backend.

## 4. Masquage des erreurs de politique métier (AttributeError)
**Problème** : Toutes les erreurs d'invalidation du projet (`PolicyError`) comme le manque de quotas ou la demande de compte introuvable entraînaient des "Erreurs 500" abstraites. 
**Explication** : Le gestionnaire global d'exceptions dans `main.py` appelait `exc.message`, alors que l'objet `PolicyError` (héritant de HTTPException) sauvegarde son message dans l'attribut `exc.detail`.
**Solution** : 
- Substitution de `exc.message` en `exc.detail` dans `policy_exception_handler`. Les messages exacts remontent correctement au client frontend.

## 5. Crash inattendu "ValueError" lors des processus avec IDs
**Problème** : Occasionnellement, la création de VM et l'approbation du quota généraient l'erreur de conversion de chaîne : `ValueError: badly formed hexadecimal UUID string`.
**Explication** : Le Frontend envoyait la valeur JS `"null"`, `"undefined"` ou des chaînes vides `""` en tant que *chaîne de caractères*. Etant donné que la chaîne `"null"` n'est pas identifiée comme vide en Python, `uuid.UUID("null")` crashe.
**Solution** :
- Sécurisation du traitement des champs clés (`iso_image_id`, `quota_policy_id`). Tout mot réservé ou mal formé est désormais systématiquement filtré et converti en `None`, ou repoussé via l'erreur API HTTP `422`.
