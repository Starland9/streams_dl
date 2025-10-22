# Guide de Déploiement - Streams DL

Ce guide explique comment déployer l'application Streams DL sur un VPS en tant que service systemd.

## Prérequis

- Un VPS avec Linux (Ubuntu, Debian, CentOS, etc.)
- Accès SSH au VPS
- Python 3 installé
- Git installé
- Accès sudo

## Étapes de Déploiement

### 1. Cloner le Projet

```bash
cd /home/landry/Dev/Python
git clone https://github.com/Starland9/streams_dl.git
cd streams_dl
```

### 2. Créer l'Environnement Virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurer sudo sans Mot de Passe (Recommandé)

Pour pouvoir lancer le déploiement sans saisir votre mot de passe à chaque fois :

```bash
sudo visudo
```

À la fin du fichier, ajoutez cette ligne :

```
landry ALL=(ALL) NOPASSWD: /home/landry/Dev/Python/streams_dl/deploy/deploy.sh
```

Sauvegardez et quittez (Ctrl+X, Y, Entrée pour nano).

### 4. Lancer le Déploiement

```bash
cd /home/landry/Dev/Python/streams_dl
sudo ./deploy/deploy.sh
```

Le script va :
- ✓ Copier le service systemd dans `/etc/systemd/system/`
- ✓ Recharger les configurations systemd
- ✓ Activer le service au démarrage automatique
- ✓ Démarrer le service immédiatement
- ✓ Afficher les logs du déploiement

### 5. Vérifier le Statut

```bash
sudo systemctl status streams_dl
```

### 6. Consulter les Logs

Pour voir les logs en temps réel :

```bash
sudo journalctl -u streams_dl -f
```

Pour voir les 50 dernières lignes :

```bash
sudo journalctl -u streams_dl -n 50
```

Pour voir les logs du déploiement :

```bash
sudo tail -f /var/log/streams_dl_deploy.log
```

## Gestion du Service

### Arrêter le service

```bash
sudo systemctl stop streams_dl
```

### Redémarrer le service

```bash
sudo systemctl restart streams_dl
```

### Désactiver le service (ne plus démarrer au boot)

```bash
sudo systemctl disable streams_dl
```

### Réactiver le service

```bash
sudo systemctl enable streams_dl
```

### Voir le statut détaillé

```bash
sudo systemctl status streams_dl
```

## Mise à Jour du Code

Si vous avez modifié le code et voulez redéployer :

```bash
cd /home/landry/Dev/Python/streams_dl
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart streams_dl
```

## Dépannage

### Le service ne démarre pas

1. Vérifiez les logs :
```bash
sudo journalctl -u streams_dl -n 50
```

2. Vérifiez que le fichier `api.py` existe :
```bash
ls -la /home/landry/Dev/Python/streams_dl/api.py
```

3. Vérifiez que le venv est correct :
```bash
ls -la /home/landry/Dev/Python/streams_dl/.venv/bin/python
```

### Permission denied

Assurez-vous que vous avez bien configuré sudo sans mot de passe (voir étape 3).

### Port en utilisation

Si le port est déjà utilisé, modifiez `api.py` pour utiliser un autre port, puis redémarrez :
```bash
sudo systemctl restart streams_dl
```

## Configuration du Firewall

Si vous utilisez un firewall (UFW, etc.), assurez-vous que le port est ouvert :

```bash
sudo ufw allow 8000/tcp
```

(Remplacez 8000 par le port utilisé par votre API)

## Notes de Sécurité

- ⚠️ Le fichier sudoers autorise le script sans mot de passe. Limitez les permissions sur le script :
```bash
sudo chmod 750 /home/landry/Dev/Python/streams_dl/deploy/deploy.sh
```

- ⚠️ Les logs du déploiement sont stockés dans `/var/log/streams_dl_deploy.log`. Vérifiez régulièrement les erreurs.

- ⚠️ Assurez-vous que les secrets/tokens ne sont pas en dur dans le code. Utilisez des variables d'environnement.

## Logs de Déploiement

Tous les événements du déploiement sont enregistrés dans :
```
/var/log/streams_dl_deploy.log
```

Vous pouvez consulter cet historique pour tracer les problèmes :
```bash
sudo tail -f /var/log/streams_dl_deploy.log
```

## Support

Pour plus d'informations sur le projet :
- README : `README.md`
- IMPLEMENTATION : `IMPLEMENTATION.md`
- CHANGELOG : `CHANGELOG.md`
