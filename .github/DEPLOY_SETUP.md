# Configuration des Secrets GitHub pour le Déploiement

Pour que le déploiement automatique fonctionne, vous devez configurer les secrets suivants dans votre repository GitHub.

## Étapes de Configuration

### 1. Aller dans les paramètres du repository

1. Allez sur votre repository : `https://github.com/Starland9/streams_dl`
2. Cliquez sur **Settings** (Paramètres)
3. Dans le menu de gauche, cliquez sur **Secrets and variables** → **Actions**
4. Cliquez sur **New repository secret**

### 2. Créer les Secrets

Créez les secrets suivants :

#### `VPS_HOST`
- **Nom** : `VPS_HOST`
- **Valeur** : L'adresse IP ou le nom de domaine de votre VPS
- **Exemple** : `192.168.1.100` ou `mon-vps.example.com`

#### `VPS_USERNAME`
- **Nom** : `VPS_USERNAME`
- **Valeur** : Nom d'utilisateur pour se connecter au VPS
- **Exemple** : `landry`

#### `VPS_SSH_KEY`
- **Nom** : `VPS_SSH_KEY`
- **Valeur** : Clé SSH privée pour se connecter au VPS (voir ci-dessous)

#### `VPS_PORT`
- **Nom** : `VPS_PORT`
- **Valeur** : Port SSH du VPS
- **Exemple** : `22` (port par défaut)

### 3. Générer une Clé SSH (si vous n'en avez pas)

Sur votre machine locale :

```bash
# Générer une nouvelle paire de clés SSH
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/vps_deploy_key

# Afficher la clé publique
cat ~/.ssh/vps_deploy_key.pub
```

### 4. Ajouter la Clé Publique sur le VPS

Connectez-vous à votre VPS et ajoutez la clé publique :

```bash
# Sur votre VPS
ssh landry@votre-vps-ip

# Créer le fichier authorized_keys si nécessaire
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Ajouter la clé publique
echo "votre-clé-publique-ici" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 5. Copier la Clé Privée dans GitHub

Sur votre machine locale :

```bash
# Afficher la clé privée (à copier dans GitHub)
cat ~/.ssh/vps_deploy_key
```

Copiez **tout le contenu** (y compris `-----BEGIN OPENSSH PRIVATE KEY-----` et `-----END OPENSSH PRIVATE KEY-----`) et collez-le dans le secret `VPS_SSH_KEY` sur GitHub.

### 6. Configurer sudo sans Mot de Passe

Sur votre VPS, configurez sudo pour permettre le redémarrage du service sans mot de passe :

```bash
sudo visudo
```

Ajoutez cette ligne à la fin :

```
landry ALL=(ALL) NOPASSWD: /bin/systemctl restart streams_dl
landry ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart streams_dl
landry ALL=(ALL) NOPASSWD: /bin/systemctl status streams_dl
landry ALL=(ALL) NOPASSWD: /usr/bin/systemctl status streams_dl
landry ALL=(ALL) NOPASSWD: /bin/journalctl
landry ALL=(ALL) NOPASSWD: /usr/bin/journalctl
```

## Test du Déploiement

Une fois les secrets configurés :

1. Faites un commit et push sur la branche `main` :
```bash
git add .
git commit -m "Test deploy"
git push origin main
```

2. Allez dans l'onglet **Actions** de votre repository GitHub
3. Vous devriez voir le workflow "Deploy to VPS" en cours d'exécution
4. Cliquez dessus pour voir les logs en temps réel

## Déclenchement du Déploiement

Le déploiement se déclenche automatiquement :

- ✅ Lors d'un **push** sur la branche `main`
- ✅ Lors d'une **Pull Request mergée** vers `main`

## Dépannage

### Erreur de connexion SSH

Si vous avez une erreur de connexion SSH :

1. Vérifiez que les secrets sont correctement configurés
2. Testez la connexion SSH manuellement :
```bash
ssh -i ~/.ssh/vps_deploy_key landry@votre-vps-ip
```

### Permission denied

Si vous avez une erreur "permission denied" :

1. Vérifiez que la clé publique est bien dans `~/.ssh/authorized_keys` sur le VPS
2. Vérifiez les permissions :
```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### Erreur sudo

Si le redémarrage du service échoue :

1. Vérifiez la configuration sudo (étape 6)
2. Testez manuellement sur le VPS :
```bash
sudo systemctl restart streams_dl
```

## Sécurité

⚠️ **Important** :
- Ne partagez jamais votre clé privée SSH
- Utilisez une clé SSH dédiée pour GitHub Actions
- Limitez les permissions sudo aux commandes strictement nécessaires
- Gardez vos secrets GitHub confidentiels

## Structure du Workflow

Le workflow effectue les actions suivantes :

1. 📦 Se connecte au VPS via SSH
2. 💾 Sauvegarde le fichier service local
3. 🔄 Récupère les dernières modifications du code
4. 📚 Met à jour les dépendances Python
5. 🔄 Redémarre le service systemd
6. ✅ Vérifie le statut du service
7. 📋 Affiche les derniers logs

## Logs du Déploiement

Pour voir les logs du déploiement :

1. Allez sur GitHub → Repository → **Actions**
2. Cliquez sur le workflow "Deploy to VPS"
3. Cliquez sur le job "deploy"
4. Vous verrez tous les logs du déploiement