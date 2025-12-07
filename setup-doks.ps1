# ===================================================================
# DIGITALOCEAN DOKS SETUP SCRIPT
# Полная автоматизация настройки Kubernetes кластера
# ===================================================================

param(
    [string]$ClusterName = "digital-twin-prod",
    [string]$Namespace = "production",
    [string]$RegistryServer = "registry.digitalocean.com",
    [string]$RegistryUsername = "dfc13921d373c3d0b4fdb9e7e8f9c0a1b2d3e4f5",
    [string]$RegistryPassword = "dopv1c4621fb5a3b61a7abbaf4f49ec0c7f9bae4ed33ea2066ac9ea4da4b1d3b72db1",
    [string]$Email = "your@email.com"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Цвета для вывода
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Step([string]$message) {
    Write-ColorOutput Green "\n[$(Get-Date -Format 'HH:mm:ss')] ✓ $message"
}

function Write-Error-Message([string]$message) {
    Write-ColorOutput Red "\n[$(Get-Date -Format 'HH:mm:ss')] ✗ $message"
}

function Write-Info([string]$message) {
    Write-ColorOutput Cyan "  → $message"
}

# ===================================================================
# ЭТАП 1: KUBECTL CONTEXT (0:00-0:05)
# ===================================================================
Write-Step "ЭТАП 1/5: Настройка kubectl контекста"

try {
    Write-Info "Проверка доступности doctl..."
    $doctlVersion = doctl version 2>$null
    if (!$doctlVersion) {
        throw "doctl не найден. Установите: https://docs.digitalocean.com/reference/doctl/"
    }
    Write-Info "doctl найден: $doctlVersion"

    Write-Info "Скачивание kubeconfig для кластера $ClusterName..."
    doctl kubernetes cluster kubeconfig save $ClusterName --set-current-context

    Write-Info "Получение списка контекстов..."
    kubectl config get-contexts

    $expectedContext = "do-nyc2-$ClusterName"
    Write-Info "Переключение на контекст $expectedContext..."
    kubectl config use-context $expectedContext

    Write-Info "Проверка подключения к кластеру..."
    kubectl get nodes

    $clusterInfo = kubectl cluster-info | Select-String -Pattern "https://"
    Write-Info "Подключён к: $clusterInfo"

    Write-Step "Контекст kubectl успешно настроен"
} catch {
    Write-Error-Message "Ошибка при настройке контекста: $_"
    exit 1
}

# ===================================================================
# ЭТАП 2: REGISTRY SECRET (0:05-0:10)
# ===================================================================
Write-Step "ЭТАП 2/5: Создание секрета для Registry"

try {
    Write-Info "Проверка существования namespace $Namespace..."
    $nsExists = kubectl get namespace $Namespace 2>$null
    if (!$nsExists) {
        Write-Info "Создание namespace $Namespace..."
        kubectl create namespace $Namespace
    }

    Write-Info "Удаление старого секрета regcred (если существует)..."
    kubectl delete secret regcred -n $Namespace --ignore-not-found=true

    Write-Info "Создание нового секрета regcred..."
    kubectl create secret docker-registry regcred `
        --docker-server=$RegistryServer `
        --docker-username=$RegistryUsername `
        --docker-password=$RegistryPassword `
        --docker-email=$Email `
        -n $Namespace

    Write-Info "Проверка созданного секрета..."
    kubectl get secret regcred -n $Namespace

    Write-Step "Секрет Registry успешно создан"
} catch {
    Write-Error-Message "Ошибка при создании секрета: $_"
    exit 1
}

# ===================================================================
# ЭТАП 3: DEPLOYMENT ROLLOUT (0:10-0:20)
# ===================================================================
Write-Step "ЭТАП 3/5: Перезапуск деплойментов"

try {
    Write-Info "Получение списка деплойментов в $Namespace..."
    $deployments = kubectl get deployments -n $Namespace -o name 2>$null

    if ($deployments) {
        foreach ($deploy in $deployments) {
            Write-Info "Перезапуск $deploy..."
            kubectl rollout restart $deploy -n $Namespace
        }

        Write-Info "Ожидание готовности pods (это может занять 2-5 минут)..."
        Start-Sleep -Seconds 10

        Write-Info "Проверка статуса pods..."
        kubectl get pods -n $Namespace

        Write-Info "Проверка events..."
        kubectl get events -n $Namespace --sort-by='.lastTimestamp' | Select-Object -Last 20

    } else {
        Write-Info "Деплойменты не найдены. Возможно, они ещё не созданы через Helm."
    }

    Write-Step "Деплойменты перезапущены"
} catch {
    Write-Error-Message "Ошибка при перезапуске деплойментов: $_"
    # Не выходим, продолжаем проверки
}

# ===================================================================
# ЭТАП 4: LOADBALANCER & SERVICES (0:20-0:25)
# ===================================================================
Write-Step "ЭТАП 4/5: Проверка сервисов и LoadBalancer"

try {
    Write-Info "Получение списка сервисов..."
    kubectl get svc -n $Namespace

    Write-Info "Ожидание назначения EXTERNAL-IP для LoadBalancer..."
    $maxWait = 180  # 3 минуты
    $waited = 0
    $externalIP = $null

    while ($waited -lt $maxWait) {
        $lbService = kubectl get svc -n $Namespace -o json | ConvertFrom-Json | `
            Select-Object -ExpandProperty items | `
            Where-Object { $_.spec.type -eq "LoadBalancer" } | `
            Select-Object -First 1

        if ($lbService -and $lbService.status.loadBalancer.ingress) {
            $externalIP = $lbService.status.loadBalancer.ingress[0].ip
            if ($externalIP -and $externalIP -ne "<pending>") {
                Write-Info "EXTERNAL-IP получен: $externalIP"
                break
            }
        }

        Write-Info "Ожидание... ($waited/$maxWait сек)"
        Start-Sleep -Seconds 10
        $waited += 10
    }

    if (!$externalIP) {
        Write-Info "EXTERNAL-IP ещё не назначен. Проверьте позже."
    }

    Write-Info "Проверка статуса нод..."
    kubectl get nodes

    Write-Step "Проверка сервисов завершена"
} catch {
    Write-Error-Message "Ошибка при проверке сервисов: $_"
}

# ===================================================================
# ЭТАП 5: FINAL CHECKS (0:25-0:30)
# ===================================================================
Write-Step "ЭТАП 5/5: Финальная проверка"

try {
    Write-Info "Все pods:"
    kubectl get pods -n $Namespace

    Write-Info "Все deployments:"
    kubectl get deployments -n $Namespace

    Write-Info "Все cronjobs:"
    kubectl get cronjobs -n $Namespace

    Write-Info "Все services:"
    kubectl get svc -n $Namespace

    Write-Info "Все ingress:"
    kubectl get ingress -n $Namespace 2>$null

    if ($externalIP) {
        Write-Info "Проверка health endpoint..."
        try {
            $health = Invoke-WebRequest -Uri "http://${externalIP}:80/health" -TimeoutSec 5 -UseBasicParsing
            Write-Info "Health check: $($health.StatusCode) $($health.StatusDescription)"
        } catch {
            Write-Info "Health endpoint пока недоступен: $_"
        }
    }

    Write-Step "Финальная проверка завершена"
} catch {
    Write-Error-Message "Ошибка при финальной проверке: $_"
}

# ===================================================================
# SUMMARY
# ===================================================================
Write-ColorOutput Yellow "\n" + "="*70
Write-ColorOutput Yellow "ИТОГОВЫЙ СТАТУС SETUP"
Write-ColorOutput Yellow "="*70

Write-Info "Кластер: $ClusterName"
Write-Info "Namespace: $Namespace"
Write-Info "Registry: $RegistryServer"
if ($externalIP) {
    Write-Info "LoadBalancer IP: $externalIP"
}

Write-ColorOutput Yellow "\nДЛЯ ПРОВЕРКИ DNS:"
Write-Info "nslookup 97k.ru"
Write-Info "nslookup api.97k.ru"

Write-ColorOutput Yellow "\nДЛЯ МОНИТОРИНГА:"
Write-Info "kubectl get pods -n $Namespace -w"
Write-Info "kubectl logs -f deployment/digital-twin-api -n $Namespace"

Write-ColorOutput Green "\n✓ Setup завершён успешно!\n"