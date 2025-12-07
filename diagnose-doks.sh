#!/bin/bash
set -e

echo "========================================"
echo "🔧 ПОЛНАЯ ДИАГНОСТИКА DOKS КЛАСТЕРА"
echo "========================================"
echo ""

# Проверка 1: Контекст
echo "✅ ПРОВЕРКА 1: Текущий контекст"
kubectl config current-context

# Проверка 2: Pods
echo ""
echo "✅ ПРОВЕРКА 2: Pods"
kubectl get pods -n production

# Проверка 3: Services
echo ""
echo "✅ ПРОВЕРКА 3: Services"
kubectl get svc -n production

# Проверка 4: Deployments
echo ""
echo "✅ ПРОВЕРКА 4: Deployments"
kubectl get deployments -n production

# Проверка 5: CronJobs
echo ""
echo "✅ ПРОВЕРКА 5: CronJobs"
kubectl get cronjobs -n production 2>/dev/null || echo "No cronjobs found"

echo ""
echo "========================================"
echo "📊 ИТОГ"
echo "========================================"
