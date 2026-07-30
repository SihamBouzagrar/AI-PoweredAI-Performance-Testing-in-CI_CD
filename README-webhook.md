# Configuration du webhook Git → Jenkins

Ce document explique comment déclencher automatiquement le pipeline
Jenkins (`Jenkinsfile`) à chaque push sur le dépôt Git.

---

## 1. Prérequis côté Jenkins

### Plugins requis
Installer via *Manage Jenkins → Plugins* :
- **GitHub** (ou **GitLab**, selon ton hébergeur)
- **HTML Publisher** (pour afficher le rapport JMeter dans Jenkins)
- **Pipeline: Stage View** (optionnel, confort visuel)
- **Credentials Binding**

### Credentials à créer
Aller dans *Manage Jenkins → Credentials → System → Global credentials*,
et créer deux credentials de type **Secret text** :

| ID                | Valeur                                   |
|-------------------|------------------------------------------|
| `ai-server-url`   | URL du serveur FastAPI, ex. `http://127.0.0.1:8000` |
| `pushgateway-url` | URL du Pushgateway, ex. `http://localhost:9091`     |

Ces IDs correspondent exactement à ceux référencés dans le `Jenkinsfile` :
```groovy
environment {
    AI_SERVER_URL   = credentials('ai-server-url')
    PUSHGATEWAY_URL = credentials('pushgateway-url')
}
```

> Si ton serveur FastAPI et Jenkins tournent sur des machines différentes,
> remplace `127.0.0.1` par l'adresse IP/nom d'hôte réellement accessible
> depuis l'agent Jenkins (pas `127.0.0.1` du poste Jenkins lui-même).

---

## 2. Créer le job Jenkins (Pipeline)

1. *New Item* → nom du job → type **Pipeline**
2. Dans *Pipeline* :
   - **Definition** : `Pipeline script from SCM`
   - **SCM** : Git
   - **Repository URL** : l'URL de ton dépôt
   - **Script Path** : `Jenkinsfile` (à la racine du repo)
3. Coche **GitHub hook trigger for GITScm polling** dans *Build Triggers*
   (nécessite le plugin GitHub installé à l'étape 1).
4. Sauvegarde.

---

## 3. Configurer le webhook côté GitHub

1. Sur ton dépôt GitHub → **Settings → Webhooks → Add webhook**
2. Renseigne :
   - **Payload URL** : `http://<adresse-jenkins>:8080/github-webhook/`
     (l'URL exacte de ton serveur Jenkins, suivie de `/github-webhook/`)
   - **Content type** : `application/json`
   - **Secret** : optionnel mais recommandé (à valider côté plugin GitHub Jenkins)
   - **Which events** : sélectionne *Just the push event* (ou ajoute
     *Pull requests* si tu veux aussi déclencher sur PR)
3. Sauvegarde → GitHub enverra un ping de test ; vérifie la coche verte
   dans l'onglet *Recent Deliveries*.

### Variante GitLab
- *Settings → Webhooks*
- **URL** : `http://<adresse-jenkins>:8080/project/<nom-du-job>`
- **Trigger** : *Push events*
- Nécessite le plugin **GitLab** côté Jenkins et la coche
  **Build when a change is pushed to GitLab** dans le job.

---

## 4. Rendre Jenkins accessible depuis GitHub (cas local/dev)

Si Jenkins tourne en local (`127.0.0.1`) et n'est pas exposé publiquement,
GitHub ne pourra pas atteindre le webhook. Deux options :

- **Tunnel temporaire** (dev/test uniquement) :
  ```bash
  ngrok http 8080
  ```
  Utilise l'URL HTTPS générée par ngrok comme *Payload URL* dans GitHub.

- **Exposition réelle** : héberger Jenkins sur un serveur/VM avec une IP
  publique ou un nom de domaine, avec un reverse proxy HTTPS (nginx/Caddy)
  devant Jenkins.

---

## 5. Vérification de bout en bout

1. Fais un `git push` sur une branche surveillée.
2. Le webhook GitHub notifie Jenkins → le job se déclenche automatiquement.
3. Le pipeline :
   - envoie la spec OpenAPI à ton serveur FastAPI (`/generateScenario`)
   - attend la fin du test JMeter (`/status/{jobId}`)
   - télécharge rapport HTML + `.jtl`
   - publie le rapport dans Jenkins (onglet *Rapport JMeter*)
   - pousse les métriques agrégées vers Prometheus Pushgateway
4. Ouvre Grafana (`http://localhost:3000`) et crée un dashboard basé sur
   les métriques `jmeter_error_rate_percent`, `jmeter_latency_p95_ms`,
   `jmeter_throughput_req_per_sec`, etc. (voir section 6).

---

## 6. Exemple de requêtes PromQL pour Grafana

| Métrique                      | Requête PromQL                                      |
|--------------------------------|-----------------------------------------------------|
| Taux d'erreur par build        | `jmeter_error_rate_percent`                         |
| Latence p95 dans le temps       | `jmeter_latency_p95_ms`                              |
| Débit (req/s)                  | `jmeter_throughput_req_per_sec`                      |
| Total de requêtes par build     | `jmeter_total_requests`                              |

Ajoute un panel "Time series" dans Grafana avec la source de données
Prometheus (`http://prometheus:9090` si Grafana tourne dans le même
docker-compose, ou `http://localhost:9090` sinon), et utilise ces
requêtes pour visualiser l'évolution des performances build après build.
