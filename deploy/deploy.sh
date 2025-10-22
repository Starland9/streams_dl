#!/bin/bash

# Script de déploiement du service streams_dl
# Ce script copie le service systemd, le démarre et l'active au démarrage

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_FILE="$SCRIPT_DIR/systemd/streams_dl.service"
SYSTEMD_DIR="/etc/systemd/system"
SERVICE_NAME="streams_dl.service"
LOG_FILE="/var/log/streams_dl_deploy.log"

# Fonction pour logger les messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Vérifier que le script est exécuté en tant que root, sinon le relancer avec sudo
if [[ $EUID -ne 0 ]]; then
   echo "Relancement du script avec les droits sudo..."
   exec sudo "$0" "$@"
fi

log "=== Démarrage du déploiement du service streams_dl ==="
log "Script: $0"
log "Service: $SERVICE_FILE"
log "Destination: $SYSTEMD_DIR/$SERVICE_NAME"

# Vérifier que le fichier service existe
if [[ ! -f "$SERVICE_FILE" ]]; then
    log "❌ Erreur: Le fichier service n'existe pas: $SERVICE_FILE"
    exit 1
fi

log "✓ Fichier service trouvé"

# Copier le service dans le répertoire systemd
log "Copie du service dans $SYSTEMD_DIR..."
cp "$SERVICE_FILE" "$SYSTEMD_DIR/$SERVICE_NAME"
log "✓ Service copié"

# Recharger les configurations systemd
log "Rechargement des configurations systemd..."
systemctl daemon-reload
log "✓ Configurations rechargées"

# Arrêter le service s'il est déjà en cours d'exécution
if systemctl is-active --quiet "$SERVICE_NAME"; then
    log "Le service est actuellement en cours d'exécution, arrêt..."
    systemctl stop "$SERVICE_NAME"
    log "✓ Service arrêté"
fi

# Activer le service au démarrage
log "Activation du service au démarrage..."
systemctl enable "$SERVICE_NAME"
log "✓ Service activé pour le démarrage automatique"

# Démarrer le service
log "Démarrage du service..."
systemctl start "$SERVICE_NAME"
log "✓ Service démarré"

# Vérifier le statut du service
log "Vérification du statut du service..."
systemctl status "$SERVICE_NAME"

# Afficher les logs
log ""
log "=== Affichage des derniers logs du service ==="
journalctl -u "$SERVICE_NAME" -n 20 --no-pager

log ""
log "=== ✓ Déploiement terminé avec succès ==="
log "Pour consulter les logs: journalctl -u $SERVICE_NAME -f"
log "Pour arrêter le service: systemctl stop $SERVICE_NAME"
log "Pour désactiver le service: systemctl disable $SERVICE_NAME"
