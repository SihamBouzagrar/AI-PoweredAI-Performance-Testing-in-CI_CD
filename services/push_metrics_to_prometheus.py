#!/usr/bin/env python3
"""
push_metrics_to_prometheus.py

Parse un fichier .jtl (résultats JMeter, format CSV) et pousse des
métriques agrégées vers un Prometheus Pushgateway, pour que Grafana
puisse les afficher dans des dashboards.

Usage:
    python3 push_metrics_to_prometheus.py \
        --jtl results.jtl \
        --job my-jenkins-job \
        --instance 42 \
        --pushgateway-url http://localhost:9091

Dépendance : prometheus_client
    pip install prometheus_client --break-system-packages
"""

import argparse
import csv
import sys

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway


def parse_jtl(jtl_path: str) -> dict:
    """
    Lit le fichier .jtl (CSV) généré par JMeter et calcule des métriques
    agrégées : total de requêtes, erreurs, taux d'erreur, latences
    (moyenne, min, max, p90, p95, p99), débit approximatif.
    """
    total = 0
    errors = 0
    latencies = []
    min_ts = None
    max_ts = None

    with open(jtl_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError(f"Fichier JTL vide ou invalide : {jtl_path}")

        for row in reader:
            total += 1

            success = row.get("success", "true").strip().lower()
            if success != "true":
                errors += 1

            elapsed = row.get("elapsed")
            if elapsed is not None:
                try:
                    latencies.append(int(elapsed))
                except ValueError:
                    pass

            timestamp = row.get("timeStamp")
            if timestamp is not None:
                try:
                    ts = int(timestamp)
                    min_ts = ts if min_ts is None else min(min_ts, ts)
                    max_ts = ts if max_ts is None else max(max_ts, ts)
                except ValueError:
                    pass

    if total == 0:
        raise ValueError(f"Aucune ligne exploitable dans le fichier JTL : {jtl_path}")

    latencies.sort()

    def percentile(data, pct):
        if not data:
            return 0
        k = (len(data) - 1) * (pct / 100)
        f = int(k)
        c = min(f + 1, len(data) - 1)
        if f == c:
            return data[f]
        return data[f] + (data[c] - data[f]) * (k - f)

    duration_seconds = ((max_ts - min_ts) / 1000.0) if (min_ts is not None and max_ts is not None and max_ts > min_ts) else 0

    return {
        "total_requests": total,
        "total_errors": errors,
        "error_rate_percent": (errors / total * 100) if total else 0.0,
        "latency_avg_ms": sum(latencies) / len(latencies) if latencies else 0,
        "latency_min_ms": min(latencies) if latencies else 0,
        "latency_max_ms": max(latencies) if latencies else 0,
        "latency_p90_ms": percentile(latencies, 90),
        "latency_p95_ms": percentile(latencies, 95),
        "latency_p99_ms": percentile(latencies, 99),
        "throughput_req_per_sec": (total / duration_seconds) if duration_seconds > 0 else 0.0,
    }


def push_metrics(metrics: dict, job: str, instance: str, pushgateway_url: str) -> None:
    registry = CollectorRegistry()

    gauges = {}
    for name, value in metrics.items():
        metric_name = f"jmeter_{name}"
        gauges[metric_name] = Gauge(
            metric_name,
            f"Métrique JMeter : {name}",
            registry=registry,
        )
        gauges[metric_name].set(value)

    push_to_gateway(
        pushgateway_url,
        job=job,
        grouping_key={"instance": instance},
        registry=registry,
    )


def main():
    parser = argparse.ArgumentParser(description="Pousse les métriques JMeter (.jtl) vers Prometheus Pushgateway")
    parser.add_argument("--jtl", required=True, help="Chemin du fichier .jtl à analyser")
    parser.add_argument("--job", required=True, help="Nom du job Prometheus (ex: nom du job Jenkins)")
    parser.add_argument("--instance", required=True, help="Identifiant d'instance (ex: numéro de build Jenkins)")
    parser.add_argument("--pushgateway-url", required=True, help="URL du Pushgateway, ex: http://localhost:9091")

    args = parser.parse_args()

    try:
        metrics = parse_jtl(args.jtl)
    except Exception as exc:
        print(f"Erreur lors du parsing du JTL : {exc}", file=sys.stderr)
        sys.exit(1)

    print("Métriques calculées :")
    for k, v in metrics.items():
        print(f"  {k} = {v}")

    try:
        push_metrics(metrics, args.job, args.instance, args.pushgateway_url)
    except Exception as exc:
        print(f"Erreur lors de l'envoi vers Pushgateway : {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Métriques envoyées avec succès vers {args.pushgateway_url} (job={args.job}, instance={args.instance})")


if __name__ == "__main__":
    main()