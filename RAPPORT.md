# 📋 Rapport du Projet — AI Performance Testing

## 1. Présentation du projet

**AI Performance Testing** est une plateforme de **génération automatique de tests de charge
JMeter pilotée par l'IA**. À partir d'une spécification **OpenAPI** (Swagger 2.0 / OpenAPI 3.x),
le système :

1. **Parse** la spécification et en extrait les endpoints.
2. **Analyse** les opérations (GET/POST/PUT/DELETE/PATCH, authentification, opérations bancaires).
3. **Génère** un scénario réaliste via le **LLM Groq** (`llama-3.3-70b-versatile`).
4. **Produit** un fichier de test JMeter validé (`.jmx`).
5. **Exécute** le test de charge avec Apache JMeter (async).
6. **Monitore** les métriques en temps réel via **Prometheus + Grafana**.
7. **Archive** les résultats (JTL, rapport HTML, logs).

**Année / Version :** 2.0.

---

## 2. Architecture générale

```
Développeur
      │
      ▼
   Git Repository (OpenAPI spec)
      │
      ▼
 Jenkins Pipeline
      │
      ├─────────────► Webhook
      │                   │
      │                   ▼
      │           Serveur IA (FastAPI + Groq)
      │                   │
      │           Génération script JMX
      │                   │
      ├─────────────► JMeter
      │                   │
      │            Exécution test de charge
      │                   │
      │         ┌─────────┼──────────┐
      │         ▼         ▼          ▼
      │   Prometheus   Grafana    Archives
      │   (métriques) (dashboard) (JTL/HTML)
```

### Déroulement d'un test (flux)

1. L'utilisateur envoie une spec OpenAPI via `POST /generateScenario`.
2. Le backend vérifie le fichier, le sauvegarde dans `uploads/`.
3. `OpenApiParser` valide la spec avec `prance` et en extrait une version simplifiée.
4. `ApiAnalyzer` compte les endpoints, méthodes, et détecte l'authentification / opérations bancaires.
5. `ScenarioGenerator` construit le prompt envoyé à `GroqClient`.
6. `JsonCleaner` nettoie la réponse JSON du LLM.
7. `Scenario` (Pydantic) valide le scénario généré.
8. `TargetResolver` détermine l'URL cible (localhost / Prism mock).
9. `JmxGenerator` génère le fichier `.jmx`.
10. `JobStore` crée un job et `JMeterExecutor` l'exécute en tâche de fond.
11. Les résultats sont téléchargeables et les métriques poussées vers Prometheus.

---

## 3. Stack technique

| Couche | Technologie |
|--------|-------------|
| Langage | Python 3.11 |
| Framework web | FastAPI 0.115 |
| Serveur ASGI | Uvicorn 0.34 |
| Validation | Pydantic 2.10 |
| LLM | Groq API (`llama-3.3-70b-versatile`) |
| Test de charge | Apache JMeter 5.6.3 |
| Mocking API | Prism CLI (`@stoplight/prism-cli`) |
| Parsing OpenAPI | `prance`, `openapi-spec-validator`, PyYAML |
| Monitoring | Prometheus + Pushgateway + Grafana |
| Orches. & CI/CD | Docker Compose, Dockerfile, Jenkins Pipeline |
| OS cible | Windows (scripts `.bat`) / Linux |

### Dépendances Python (`requirements.txt`)
```
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.4
PyYAML==6.0.2
python-dotenv==1.0.1
python-multipart==0.0.20
groq==0.13.1
prometheus-client==0.21.0
requests>=2.32.0
prance
openapi-spec-validator
```

---

## 4. Structure du projet

```
├── app.py                        # Application FastAPI (point d'entrée)
├── api/
│   └── routes.py                 # Endpoints API (generateScenario, status, download)
├── models/
│   ├── scenario_model.py         # Modèles Pydantic (Configuration, Transaction, Assertion, Scenario)
│   └── request_models.py         # Modèles requête/réponse de l'API
├── prompts/
│   ├── system_prompt.py          # Prompt système envoyé au LLM
│   └── scenario_prompt.py        # Construction du prompt (analyse + spec compacte)
├── services/
│   ├── api_analyzer.py           # Analyse des endpoints (méthodes, auth, banking)
│   ├── openapi_parser.py         # Parsing/validation OpenAPI (prance)
│   ├── groq_client.py            # Client IA Groq
│   ├── scenario_generator.py     # Builder de prompt
│   ├── json_cleaner.py           # Nettoyage de la réponse JSON du LLM
│   ├── jmx_generator.py          # Génération du fichier JMX
│   ├── jmeter_executor.py        # Exécution JMeter asynchrone + gestion erreurs
│   ├── job_store.py              # Store de jobs en mémoire (thread-safe)
│   ├── target_resolver.py        # Résolution de l'URL cible (réel / Prism)
│   ├── prism_service.py          # Démarrage/arrêt du mock Prism
│   ├── file_service.py           # Gestion fichiers (ZIP ouvert, recherche OpenAPI)
│   └── push_metrics_to_prometheus.py  # Parse .jtl → métriques Pushgateway
├── templates/
│   └── jmeter_template.jmx       # Template JMX de base
├── monitoring/
│   ├── prometheus.yml            # Config Prometheus (scrape)
│   └── grafana/
│       ├── provisioning/          # Datasource + dashboards provisionnés
│       └── dashboards/            # Dashboard JMeter (JSON)
├── scripts/
│   ├── setup_monitoring.bat      # Démarrage Docker (Prometheus + Grafana + IA)
│   └── start_test.bat            # Exécution complète d'un test
├── generated/                    # Fichiers générés (JMX, résultats)
├── uploads/                      # Specs OpenAPI déposées
├── workspace/                    # Espace de travail
├── logs/                         # Logs
├── docker-compose.yml            # Orchestration (FastAPI, Prometheus, Grafana, Pushgateway)
├── Dockerfile                    # Image Docker du serveur IA (+ JMeter + Prism)
├── Jenkinsfile                   # Pipeline CI/CD
├── README-webhook.md             # Doc webhook GitHub
└── requirements.txt
```

---

## 5. Modèle de données (scénario IA)

Le LLM retourne un JSON structuré, validé par Pydantic :

```json
{
  "configuration": {
    "threads": 50,
    "rampUp": 10,
    "loops": 5,
    "thinkTimeMin": 200,
    "thinkTimeMax": 500
  },
  "transactions": [
    {
      "name": "GetPetById",
      "method": "GET",
      "path": "/pet/{petId}",
      "weight": 30,
      "headers": {},
      "body": {},
      "pathValues": { "petId": 12 }
    }
  ],
  "assertions": [
    { "path": "/pet/{petId}", "method": "GET", "expectedStatus": 200 }
  ]
}
```

- **Configuration** : threads, rampUp, loops, thinkTime (min/max).
- **Transactions** : chaque opération avec méthode, chemin, poids, en-têtes, corps, valeurs de chemin.
- **Assertions** : codes de statut attendus par endpoint/méthode.

---

## 6. API (endpoints)

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/` | Message de bienvenue (« AI Server Running ») |
| GET | `/health` | État du service (`{"status": "UP"}`) |
| POST | `/generateScenario` | Génère et exécute un test (multipart : `file`, `threads`, `rampUp`, `loops`) |
| GET | `/status/{jobId}` | Statut du job (QUEUED/RUNNING/COMPLETED/FAILED) |
| GET | `/download/{jobId}/log` | Log détaillé JMeter |
| GET | `/download/{jobId}/stdout` | Sortie standard de la commande JMeter |
| GET | `/download/{jobId}/report` | Rapport HTML JMeter (zippé) |
| GET | `/download/{jobId}/jtl` | Fichier de résultats bruts (`.jtl`) |

### Exemple d'utilisation
```bash
# Générer et lancer un test
curl -X POST http://localhost:8000/generateScenario \
  -F "file=@mon_api.yaml" \
  -F "threads=50" -F "rampUp=10" -F "loops=5"

# Vérifier le statut
curl http://localhost:8000/status/JOB_ID
```

**Gestion des erreurs :**
- `400` : fichier invalide/vide, erreur de parsing.
- `404` : job inconnu, fichier introuvable.
- `409` : rapport demandé alors que le job n'est pas terminé / a échoué.
- `502` : scénario IA invalide (échec de validation Pydantic).

---

## 7. Résolution de la cible (TargetResolver)

Le backend choisit la cible du test dans cet ordre :

1. **`target_host` explicite** → utilisé directement.
2. **Mode mock forcé** → URL Prism (`http://localhost:4010`).
3. **Aucune `baseUrl`** → Prism mock.
4. **URL absolue** (`servers` OpenAPI) → l'URL réelle.
5. **URL relative** → Prism mock.

**Prism** (`PrismService`) démarre automatiquement un serveur mock à partir de la spec
lorsque le mode mock est activé, puis l'arrête à la fin.

---

## 8. Génération JMX (`JmxGenerator`)

Le générateur construit un `jmeterTestPlan` valide (JMeter 5.6.3) :

- **Thread Group** : `num_threads`, `ramp_time`, `loops` (configurables).
- **Think Time** : `UniformRandomTimer` (intervalle min/max).
- **HTTP Samplers** : domaine, port, protocole, chemin, méthode, headers, body.
- **Résolution des paramètres de chemin** : `{petId}` → `12` (URL-encodé).
- **Assertions** : `ResponseAssertion` sur le code de statut attendu.
- **Warnings** si des placeholders de chemin restent non résolus.

Le fichier est généré dans `generated/scenario_<uuid>.jmx`.

---

## 9. Exécution JMeter (`JMeterExecutor`)

- **Résolution du binaire** : variable `JMETER_EXECUTABLE`, PATH, ou chemins Windows/Linux connus.
- **Validation** du fichier JMX (XML) avant exécution.
- **Commande** : `jmeter -n -t <jmx> -l <jtl> -e -o <report> -j <log> -f`.
- **Gestion des erreurs** : timeout, code de retour non nul, fichiers manquants.
- **Sorties** stockées dans `generated/<job_id>/` :
  - `results.jtl`, `report/` (HTML), `jmeter.log`, `stdout.log`, et `report.zip`.
- **Cycle de vie du job** : QUEUED → RUNNING → COMPLETED / FAILED.

---

## 10. Monitoring (Prometheus / Grafana)

### Facilité de déploiement
`docker-compose.yml` orchestre 4 services : **FastAPI (8000)**, **Pushgateway (9091)**,
**Prometheus (9090)**, **Grafana (3000)**.

### Pushgateway
Un script `push_metrics_to_prometheus.py` parse le fichier `.jtl` et calcule :
- `jmeter_total_requests`, `jmeter_total_errors`, `jmeter_error_rate_percent`
- Latences : moyenne, min, max, P90, P95, P99
- `jmeter_throughput_req_per_sec`

Puis pousse ces métriques vers le Pushgateway (grouping par `job`/`instance`).

### Configuration Prometheus (`monitoring/prometheus.yml`)
- Scrape interval : 15s.
- Jobs : `prometheus` (localhost:9090) et `pushgateway` (pushgateway:9091, `honor_labels: true`).

### Dashboard Grafana
Dashboard JMeter provisionné affichant :
- **TPS** (transactions/seconde)
- **Temps de réponse** (moyenne, P50, P95, P99)
- **Taux d'erreur** (jauge colorimétrique)
- **Threads actifs**
- **Transactions par endpoint** (Top 10)
- **Erreurs par type**

**Identifiants par défaut :** `admin` / `admin`.

---

## 11. CI/CD — Jenkins Pipeline

Le `Jenkinsfile` (déclaratif) automatise :
1. **Checkout** du dépôt.
2. **Installation** des dépendances Python et Prism.
3. **Localisation** de la spec OpenAPI (`openapi.yaml`, `swagger.json`, etc.).
4. **Démarrage de Prism** (si pas de `TARGET_HOST`).
5. **Génération du scénario** via `POST /generateScenario`.
6. **Publication** du rapport HTML (`publishHTML`).
7. **Nettoyage** (arrêt Prism) et **archivage** des artefacts (`generated/**`).

### Webhook
Le pipeline peut être déclenché par webhook GitHub (voir `README-webhook.md` et
`Build Triggers > GitHub hook trigger`).

---

## 12. Scripts DevOps (Windows)

### `scripts/setup_monitoring.bat`
- Vérifie que Docker est installé.
- Crée `.env` depuis `.env.example` si absent.
- Lance `docker-compose up -d`.
- Affiche les URLs des services.

### `scripts/start_test.bat`
- Vérifie que le serveur IA tourne (`/health`).
- Envoie la spec OpenAPI à `/generateScenario` (avec overrides optionnels threads/rampUp/loops).
- Affiche les commandes pour suivre le statut et télécharger les résultats.

---

## 13. Sécurité & points d'attention

> ⚠️ **Action urgente** : Une clé API Groq a été exposée dans le dépôt Git.
> **Révoguer immédiatement cette clé** dans la console Groq et en générer une nouvelle.
> Le fichier `.env` n'est plus versionné (voir `.gitignore`).

### Limites connues
- **Job store en mémoire** : process unique. Pour du multi-worker/replica, remplacer
  `services/job_store.py` par un backend partagé (Redis, SQL).
- **Pas d'authentification** sur l'API — à ajouter avant toute exposition hors réseau interne.
- Dépendance à la **clé API Groq** (obligatoire, sinon `RuntimeError` au démarrage).

---

## 14. Installation & démarrage

### Local (Windows/Linux)
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # éditer GROQ_API_KEY, JMETER_BIN

uvicorn app:app --host 0.0.0.0 --port 8000
```

### Docker (recommandé — inclut Prometheus + Grafana)
```bash
cp .env.example .env
scripts\setup_monitoring.bat
```
Services : IA → `http://localhost:8000`, Prometheus → `http://localhost:9090`,
Grafana → `http://localhost:3000`.

---

## 15. Conclusion

Ce projet est une **plateforme complète et fonctionnelle** de génération de tests de charge
**pilotée par IA**, alliant **FastAPI + LLM (Groq) + JMeter + Prometheus/Grafana + Jenkins**.
Il est structuré en couches claires, bien documenté, containerisé (Docker) et automatisé
(Jenkins + scripts `.bat`). 

Les points d'amélioration prioritaires restent la **sécurisation de l'API**, la **révocation de
la clé Groq exposée**, et la **persistance du job store** (pour la scalabilité).

---

# 🧠 Partie 2 — Explication du Projet, Logique Métier & Agents

## 16. Explication détaillée du projet

### 16.1. Pourquoi ce projet existe-t-il ?

La création manuelle de tests de charge JMeter est :
- **Longue** : il faut écrire des `.jmx` (XML verbeux) à la main.
- **Complexe** : il faut définir les threads, ramp-up, loops, think-times, assertions, poids des requêtes.
- **Coûteuse** : elle exige un expert performance qui connaît à la fois JMeter et l'API testée.

**AI Performance Testing** automatise toute cette chaîne : l'utilisateur fournit uniquement sa
**spécification OpenAPI**, et le système génère, exécute et monitore le test de charge de bout en bout.

### 16.2. Valeur ajoutée

| Bénéfice | Détail |
|----------|--------|
| **Automatisation totale** | D'une spec OpenAPI → résultat JTL + rapport HTML + métriques Grafana |
| **Zéro écriture JMX** | Le LLM génère le scénario, `JmxGenerator` produit le XML valide |
| **Scénarios réalistes** | Le LLM détermine threads, ramp-up, poids des transactions selon l'API |
| **Mock intégré** | Prism simule l'API quand aucune cible réelle n'est fournie |
| **Monitoring temps réel** | Prometheus + Pushgateway + Grafana sans configuration manuelle |
| **CI/CD prêt** | Jenkins pipeline déclenchable par webhook Git |

---

## 17. Logique métier détaillée

### 17.1. Règles métier et cas traités

#### A. Validation des fichiers d'entrée
- **Règle** : seuls `.yaml`, `.yml`, `.json`, `.zip` sont acceptés (`routes.py`).
- **Règle** : le fichier ne doit pas être vide.
- **Cas particulier** : un `.zip` contenant un projet OpenAPI complet est décompressé et le
  fichier principal est recherché automatiquement (`find_openapi_file`).

#### B. Parsing OpenAPI
- **Règle** : la spec doit contenir au moins **un endpoint**, sinon erreur « Aucun endpoint trouvé ».
- **Règle** : seules les méthodes HTTP valides sont conservées (get, post, put, delete, patch, head, options).
- **Détail** : `_extract_base_url` priorise les `servers` OpenAPI 3.x, puis `host`/`basePath` Swagger 2.0.

#### C. Analyse heuristique (ApiAnalyzer)
Comptabilise les endpoints par méthode HTTP et détecte via mots-clés :
- **Authentification** : mots-clés `auth`, `login`, `token` dans le chemin → booléen.
- **Opérations bancaires** : `transfer`, `payment`, `transaction`, `account`, `beneficiary`, etc.

> 💡 **Pourquoi ?** Ces heuristiques enrichissent le prompt LLM (le modèle sait si l'API a besoin
> d'authentification ou si c'est une API bancaire sensible).

#### D. Génération du scénario par l'IA
- **Règle** : le LLM doit retourner **uniquement** du JSON valide (pas de markdown, pas de ```` ``` ````, pas d'explications).
- **Règle** : seuls les endpoints présents dans la spec peuvent être utilisés (« Do NOT invent endpoints »).
- **Règle** : les `pathValues` (valeurs des paramètres de chemin) doivent être copiées **à l'identique** depuis la spec.
- **Règle** : les poids des transactions doivent totaliser ~100.
- **Règle** : `thinkTimeMin < thinkTimeMax`.
- **Règle** : les `expectedStatus` des assertions doivent correspondre aux réponses documentées.
- **Tolérance** : `JsonCleaner` accepte une réponse avec des fences markdown ou du texte parasite autour du JSON.

#### E. Résolution de la cible (TargetResolver)
Ordre de priorité (de la plus forte à la plus faible) :
1. `target_host` explicite fourni par l'utilisateur.
2. Mode mock forcé (`use_mock=True`) → Prism (`http://localhost:4010`).
3. Pas de `baseUrl` dans la spec → Prism.
4. `baseUrl` absolue (`http(s)://...`) → l'URL réelle annoncée par l'API.
5. `baseUrl` relative → Prism.

La logique retourne un couple `(url_cible, use_prism)` pour décider si **Prism** doit être
démarré (mock) avant l'exécution.

#### F. Génération JMX
- **Règle** : le fichier `.jmx` doit être un XML valide JMeter 5.6.3.
- **Règle** : les chemins avec placeholders `{param}` sont résolus via `pathValues` (URL-encodés).
- **Règle** : si un placeholder reste non résolu → warning (ne bloque pas).
- **Règle** : les assertions sont associées au couple (chemin, méthode), avec repli sur le chemin seul si le LLM n'a pas précisé la méthode (en évitant les doublons de statut).

#### G. Exécution du test (JMeterExecutor)
- **Règle** : le fichier JMX est validé (XML) avant exécution.
- **Règle** : si le binaire JMeter est introuvable → job `FAILED`.
- **Règle** : si timeout (1800 s) ou code de retour ≠ 0 → job `FAILED`.
- **Règle** : un `.jtl` doit être produit, sinon `FAILED`.
- **Règle** : si le rapport HTML existe → zippé (`report.zip`).

### 17.2. Automate d'états du job

```
        create()
            │
            ▼
      ┌─────────┐     execute() début      ┌─────────┐
      │  QUEUED  │ ───────────────────────► │ RUNNING │
      └─────────┘                            └─────────┘
            │                                     │
            │                                     ├──(succès + fichiers OK)──► COMPLETED
            │                                     └──(erreur/timeout/returncode≠0/fichier manquant)──► FAILED
            ▼
     (timestamps : createdAt, startedAt, finishedAt, returnCode, error)
```

Le `JobStore` (thread-safe, verrou `Lock`) alimente les réponses `GET /status/{jobId}`.

### 17.3. Boucle de feedback métier → monitoring

1. JMeter produit `results.jtl` (CSV).
2. `push_metrics_to_prometheus.py` calcule : total requêtes, erreurs, taux d'erreur, latences
   (moyenne, min, max, P90, P95, P99), débit (req/s).
3. Les métriques sont poussées en `Gauge` vers le **Pushgateway** (grouping job/instance).
4. **Prometheus** scrape le Pushgateway (15s).
5. **Grafana** (dashboard provisionné) visualise les métriques.

---

## 18. Les agents du système

Le projet fonctionne comme une **pipeline d'agents spécialisés**, chacun remplissant une
responsabilité unique dans la chaîne de valeur. Voici la présentation de chaque agent.

### 18.1. Carte globale des agents

```
[Entrée] Spec OpenAPI (.yaml/.json/.zip)
    │
    ▼
┌───────────────────────────┐
│ 1. Agent Réceptionnaire   │ FileService + routes.py
│    (validation fichier)  │
└───────────────────────────┘
    │
    ▼
┌───────────────────────────┐
│ 2. Agent Parseur          │ OpenApiParser (prance)
│    (compréhension spec)  │
└───────────────────────────┘
    │
    ▼
┌───────────────────────────┐
│ 3. Agent Analyste         │ ApiAnalyzer
│    (heuristiques)        │
└───────────────────────────┘
    │
    ▼
┌───────────────────────────┐
│ 4. Agent Architecte IA    │ ScenarioGenerator + GroqClient
│    (création scénario)   │                          + prompts
└───────────────────────────┘
    │
    ▼
┌───────────────────────────┐
│ 5. Agent Parsing IA       │ JsonCleaner + modèle Scenario (Pydantic)
│    (nettoyage/validation)│
└───────────────────────────┘
    │
    ▼
┌───────────────────────────┐
│ 6. Agent Résolveur        │ TargetResolver + PrismService
│    (choix de la cible)   │
└───────────────────────────┘
    │
    ▼
┌───────────────────────────┐
│ 7. Agent Géniteur JMX     │ JmxGenerator
│    (production .jmx)     │
└───────────────────────────┘
    │
    ▼
┌───────────────────────────┐
│ 8. Agent Exécuteur        │ JMeterExecutor + JobStore
│    (lancement JMeter)    │
└───────────────────────────┘
    │
    ▼
┌───────────────────────────┐
│ 9. Agent Télémétrie       │ push_metrics_to_prometheus.py
│    (métriques)           │        + Pushgateway + Prometheus + Grafana
└───────────────────────────┘
    │
    ▼
┌───────────────────────────┐
│ 10. Agent Orchestrateur   │ Jenkins Pipeline + scripts .bat
│    (intégration CI/CD)   │
└───────────────────────────┘
    │
    ▼
[Résultats] JTL / Rapport HTML / Logs / Dashboards
```

### 18.2. Détail de chaque agent

#### Agent 1 — Réceptionnaire & Gardien des fichiers
- **Rôle** : recevoir la spec, vérifier extension (`yaml/yml/json/zip`), contenu non vide, sauvegarder dans `uploads/`.
- **Composants** : `api/routes.py`, `services/file_service.py`.
- **Décisions prises** : accepter/refuser l'entrée (HTTP 400 si invalide), décompresser un ZIP.

#### Agent 2 — Parseur de spécifications
- **Rôle** : transformer une spec OpenAPI/Swagger en structure Python exploitable et **simplifiée** pour l'IA.
- **Composants** : `services/openapi_parser.py` (via `prance.ResolvingParser`).
- **Décisions prises** : valider la spec, extraire `baseUrl`, endpoints (méthode, chemin, paramètres,
  pathValues, corps, réponses, sécurité), générer des valeurs d'exemple pour les paramètres de chemin.

#### Agent 3 — Analyste heuristique
- **Rôle** : produire une **analyse statistique** de l'API pour guider l'IA.
- **Composants** : `services/api_analyzer.py`.
- **Décisions prises** : compter les endpoints par méthode, détecter l'authentification et les
  opérations bancaires (mots-clés) → ajoutées au prompt.

#### Agent 4 — Architecte IA (le « cerveau »)
- **Rôle** : concevoir un scénario de test de charge **réaliste**.
- **Composants** : `services/scenario_generator.py`, `services/groq_client.py`, `prompts/system_prompt.py`,
  `prompts/scenario_prompt.py`.
- **Modèle** : `llama-3.3-70b-versatile` (Groq), `temperature=0.2` (déterministe).
- **Entrée** : spec compacte + analyse (en JSON).
- **Sortie** : JSON brut avec configuration (threads, rampUp, loops, thinkTime) + transactions + assertions.
- **Décisions prises** : combien de threads, ramp-up, loops, think-times ; quels endpoints charger ;
  quels poids ; quels statuts attendus.

#### Agent 5 — Nettoyeur & Valideur de la réponse IA
- **Rôle** : transformer la réponse brute du LLM en objet `Scenario` valide.
- **Composants** : `services/json_cleaner.py`, `models/scenario_model.py`.
- **Décisions prises** : supprimer les fences markdown, extraire le premier objet JSON valide,
  appliquer les overrides utilisateur (`threads`, `rampUp`, `loops` dans `routes.py`),
  valider avec Pydantic (HTTP 502 si scénario invalide).

#### Agent 6 — Résolveur de cible & Mock
- **Rôle** : décider **où** envoyer le trafic de test.
- **Composants** : `services/target_resolver.py`, `services/prism_service.py`.
- **Décisions prises** : URL réelle ou Prism mock ; démarrage/arrêt automatique de Prism
  (attente max 20 s, arrêt propre ou kill).

#### Agent 7 — Géniteur de fichiers JMX
- **Rôle** : produire le plan de test JMeter au format XML (**`.jmx`**).
- **Composants** : `services/jmx_generator.py`, `templates/jmeter_template.jmx`.
- **Décisions prises** : décomposition de l'URL (domaine/protocole/port/chemin), résolution des
  placeholders de chemin, construction des samplers, think-time, assertions, headers, body JSON.

#### Agent 8 — Exécuteur de tests & Gardien des jobs
- **Rôle** : lancer JMeter (non-bloquant, en tâche de fond) et tenir l'état du job à jour.
- **Composants** : `services/jmeter_executor.py`, `services/job_store.py`.
- **Décisions prises** : localiser le binaire JMeter, valider le JMX, construire la commande
  (`-n -l -e -o -j -f`), suivre l'automate QUEUED → RUNNING → COMPLETED/FAILED, zipper le rapport.

#### Agent 9 — Télémétrie & Monitoring
- **Rôle** : rendre les résultats visibles et exploitables en temps réel.
- **Composants** : `services/push_metrics_to_prometheus.py`, `monitoring/prometheus.yml`,
  `monitoring/grafana/`, `docker-compose.yml`.
- **Décisions prises** : calculer les agrégats (latences P90/P95/P99, taux d'erreur, débit),
  pousser vers Pushgateway, configurer les règles d'alerte (taux d'erreur > 5 %, P99 > 5 s,
  aucun thread actif).

#### Agent 10 — Orchestrateur CI/CD
- **Rôle** : automatiser le déclenchement et l'archivage des tests dans une chaîne d'intégration continue.
- **Composants** : `Jenkinsfile`, `scripts/setup_monitoring.bat`, `scripts/start_test.bat`,
  `README-webhook.md`.
- **Décisions prises** : localiser la spec OpenAPI, démarrer Prism si nécessaire, envoyer
  `/generateScenario`, publier le rapport HTML, archiver les artefacts, nettoyer les processus.

### 18.3. Synthèse — qui est « l'agent IA » au sens strict ?

En pratique, seul **Agent 4 (Architecte IA)** est un vrai agent LLM (Groq). Le reste de la
chaîne est un ensemble d'**agents logiciels (services)** qui encadrent l'IA pour obtenir une
**sortie fiable et exécutable** :

| Agent | Type | Intelligence |
|-------|------|--------------|
| Agent 1-3 | Traitement déterministe | Règles + heuristiques |
| **Agent 4** | **LLM (Groq)** | **Génération créative du scénario** |
| Agent 5 | Parseur + Validateur | Règles (Regex, Pydantic) |
| Agent 6-8 | Exécution | Logique conditionnelle déterministe |
| Agent 9-10 | Monitoring + CI/CD | Configuration + orchestration |

**Le point clé de l'architecture** : l'IA est **contrainte** par le prompt (JSON strict, endpoints
limités à la spec), **nettoyée** (`JsonCleaner`), **validée** (Pydantic), puis transformée en
**artefact exécutable** (JMX). C'est cette chaîne de garde-fous qui rend l'application fiable.

---

## 19. Points d'extension / améliorations possibles

1. **Agent multi-LLM** : ajouter un second passage de l'IA pour relire/optimiser les scénarios.
2. **Persistance des jobs** : remplacer le store mémoire par Redis/PostgreSQL (scalabilité).
3. **Authentification & RBAC** : sécuriser les endpoints (OAuth2/API Key).
4. **Gestion des secrets** : passer par un vault pour `GROQ_API_KEY` au lieu des variables d'env.
5. **Rapports comparatifs** : historiser les métriques build après build dans Prometheus.
6. **Notifications** : alertes Slack/Teams sur échec ou dépassement de seuils (Prometheus Alertmanager).
