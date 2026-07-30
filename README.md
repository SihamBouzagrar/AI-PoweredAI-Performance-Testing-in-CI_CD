# AI Performance Testing — Generateur de scenarios JMeter par IA

Service FastAPI qui prend une specification OpenAPI, la fait analyser par Groq (LLM)
pour concevoir un scenario de test de charge realiste, genere un fichier `.jmx`
correspondant et l'execute avec Apache JMeter. Metriques temps reel visualisees
dans Grafana via Prometheus.

## Architecture

```
Developpeur
      |
      v
   Git Repository (OpenAPI spec)
      |
      v
 Jenkins Pipeline
      |
      +---------> Webhook
      |               |
      |               v
      |       Serveur IA (FastAPI + Groq)
      |               |
      |       Generation script JMX
      |               |
      +---------> JMeter
                      |
                Execution test de charge
                      |
         +------------+------------+
         |            |            |
         v            v            v
   Prometheus    Grafana     Archives
   (metriques)   (dashboard) (JTL/HTML)
```

## ⚠️ Action immediate requise

L'ancien fichier `.env` contenait une cle API Groq exposee dans le depot Git.
**Revoguez cette cle dans la console Groq et genevez-en une nouvelle** avant
toute autre chose. Le fichier `.env` n'est plus versionne (voir `.gitignore`).

## Installation

### Option 1: Installation locale (Windows/Linux)

```bash
# Creer l'environnement virtuel
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# Installer les dependances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Editez .env : GROQ_API_KEY, JMETER_BIN
```

### Option 2: Avec Docker (recommandé - inclut Prometheus + Grafana)

```bash
# Copier et editer la configuration
cp .env.example .env

# Demarrer toute l'infrastructure
scripts\setup_monitoring.bat
```

Le script `setup_monitoring.bat` demarre automatiquement :
- Serveur IA (FastAPI) sur http://localhost:8000
- Prometheus sur http://localhost:9090
- Grafana sur http://localhost:3000

## Utilisation

### Demarrer le serveur

```bash
# Local
uvicorn app:app --host 0.0.0.0 --port 8000

# Ou avec Docker compose
docker-compose up -d
```

### Generer et executer un test

```bash
# Avec le script automatique
scripts\start_test.bat mon_api.yaml 50 10 5

# Manuellement avec curl
curl -X POST http://localhost:8000/generateScenario \
  -F "file=@mon_api.yaml" \
  -F "threads=50" \
  -F "rampUp=10" \
  -F "loops=5"
```

### Surveiller le status

```bash
# Status du job
curl http://localhost:8000/status/JOB_ID

# Logs JMeter
curl -o jmeter.log http://localhost:8000/download/JOB_ID/log

# Sortie standard JMeter
curl -o stdout.log http://localhost:8000/download/JOB_ID/stdout
```

## API

### `POST /generateScenario`
Multipart form :
- `file` : specification OpenAPI (.yaml/.yml/.json) — **requis**
- `threads`, `rampUp`, `loops` : overrides optionnels (sinon decides par l'IA)

Retourne immediatement (le test tourne en tache de fond) :
```json
{ "jobId": "...", "status": "QUEUED", "jmxFile": "generated/scenario_xxx.jmx" }
```

### `GET /status/{jobId}`
```json
{ "jobId": "...", "status": "RUNNING|COMPLETED|FAILED", "error": null, ... }
```

### `GET /download/{jobId}/log`
Log JMeter detaille pour le debogage.

### `GET /download/{jobId}/stdout`
Sortie standard de la commande JMeter.

### `GET /download/{jobId}/jtl`
Fichier de resultats bruts JMeter (`.jtl`).

### `GET /download/{jobId}/report`
Rapport HTML JMeter, zippe.

## Infrastructure de Monitoring

### Prometheus (http://localhost:9090)

Metriques exposees en temps reel :
- `jmeter_transactions_total` - Nombre de transactions par endpoint
- `jmeter_response_duration_seconds` - Duree des reponses (avg, p50, p95, p99)
- `jmeter_errors_total` - Erreurs par type
- `jmeter_active_threads` - Threads actifs

Regles d'alerte preconfigurees :
- Taux d'erreur > 5% pendant 30s → CRITICAL
- Latence P99 > 5s pendant 1min → WARNING
- Aucun thread actif pendant 1min → WARNING

### Grafana (http://localhost:3000)

Dashboard JMeter preconfigure avec :
- **TPS** : Transactions par seconde (graphique temps reel)
- **Temps de reponse** : Moyenne, P50, P95, P99
- **Taux d'erreur** : Pourcentage d'erreurs (jauge colorimetrique)
- **Threads actifs** : Nombre de threads JMeter
- **Transactions par endpoint** : Top 10 endpoints
- **Erreurs par type** : Distribution des erreurs

Identifiants par defaut : admin / admin

## Pipeline Jenkins

Le `Jenkinsfile` fourni automatise le processus complet :
1. Verification de l'infrastructure (Prometheus + Grafana)
2. Generation du scenario par IA (Groq)
3. Execution du test JMeter avec monitoring
4. Telechargement des artefacts (JTL, rapport HTML, logs)
5. Publication des metriques dans Prometheus
6. Archivage des resultats

### Integration Git

Le pipeline peut etre declenche automatiquement par webhook :
- Configuration dans Jenkins : "Build Triggers" > "Poll SCM" ou "GitHub hook trigger"
- Les webhooks GitHub pointent vers : `http://JENKINS_URL/github-webhook/`

## Structure du Projet

```
├── api/
│   ├── routes.py              # Endpoints API
├── grafana/
│   ├── dashboards/            # Dashboards Grafana provisionnes
│   │   ├── dashboards.yml
│   │   └── jmeter-dashboard.json
│   ├── datasources/           # Datasource Prometheus
│   │   └── datasource.yml
├── generated/                 # Fichiers generes (JMX, resultats)
├── models/
│   ├── scenario_model.py      # Modele du scenario
│   ├── request_models.py      # Modeles de requete/reponse
├── prometheus/
│   ├── prometheus.yml         # Configuration Prometheus
│   ├── alert_rules.yml        # Regles d'alerte
├── prompts/
│   ├── scenario_prompt.py     # Prompt envoye a l'IA
│   ├── system_prompt.py       # Prompt systeme
├── scripts/
│   ├── setup_monitoring.bat   # Demarrage infrastructure monitoring
│   ├── start_test.bat         # Execution test automatisee
├── services/
│   ├── api_analyzer.py        # Analyse des endpoints API
│   ├── groq_client.py         # Client IA Groq
│   ├── jmeter_executor.py     # Execution JMeter asynchrone
│   ├── jmx_generator.py       # Generation du fichier JMX
│   ├── job_store.py           # Stockage des jobs en memoire
│   ├── json_cleaner.py        # Nettoyage de la reponse JSON de l'IA
│   ├── openapi_parser.py      # Analyse des specs OpenAPI
│   ├── prometheus_exporter.py # Export metriques Prometheus temps reel
│   ├── scenario_generator.py  # Generation du prompt
├── templates/
│   ├── jmeter_template.jmx    # Template JMX de base
├── app.py                     # Application FastAPI
├── docker-compose.yml         # Orchestration Docker
├── Dockerfile                 # Image Docker du serveur IA
├── Jenkinsfile                # Pipeline CI/CD Jenkins
├── requirements.txt           # Dependances Python
```

## Dependances

- FastAPI - Framework web
- Uvicorn - Serveur ASGI
- Groq - Client API Groq (LLM)
- Pydantic - Validation de donnees
- PyYAML - Parsing OpenAPI
- Prometheus Client - Export de metriques
- JMeter 5.6.3+ - Test de charge

## Depannage

### Erreur 409 lors du telechargement du rapport
Le job n'est pas encore termine. Verifiez le status :
```bash
curl http://localhost:8000/status/JOB_ID
```
Utilisez les endpoints `/download/JOB_ID/log` et `/download/JOB_ID/stdout`
pour obtenir des informations de debogage.

### JMeter ne trouve pas le chemin
Verifiez que `JMETER_BIN` dans `.env` pointe vers le bon executable JMeter :
```env
JMETER_BIN=C:\jmeter\apache-jmeter-5.6.3\bin\jmeter.bat
```

### Prometheus ne scrape pas les metriques
Verifiez que le serveur IA expose bien les metriques :
```bash
curl http://localhost:8000/metrics
```
Si le port 8000 est utilise, l'exporter Prometheus est sur le port 9090 :
```bash
curl http://localhost:9090/metrics
```

## Limites connues

- Le job store est en memoire (process unique). Pour plusieurs workers/replicas,
  remplacez `services/job_store.py` par un backend partage (Redis, base SQL).
- Pas d'authentification sur l'API — a ajouter avant toute exposition hors
  reseau interne.
