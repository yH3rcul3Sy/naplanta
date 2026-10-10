# Coleta diaria no computador do projeto: Cury e Sousa Araujo nao respondem aos servidores do GitHub.
# Usa uma copia so da automacao (fora do OneDrive), sempre igual ao GitHub: nunca mexe na pasta em que voce trabalha.
# Agendar (uma vez): coleta\local.ps1 -Agendar     Remover: Unregister-ScheduledTask 'NaPlanta coleta local'
param([switch]$Agendar)

if ($Agendar) {
    $acao = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    $quando = New-ScheduledTaskTrigger -Daily -At '12:00'  # depois da coleta do GitHub (06h, que costuma atrasar)
    # StartWhenAvailable: se o PC estava desligado ao meio-dia, roda assim que ligar
    $regras = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2) -RunOnlyIfNetworkAvailable
    Register-ScheduledTask -TaskName 'NaPlanta coleta local' -Action $acao -Trigger $quando -Settings $regras -Force | Out-Null
    'Agendado: todo dia 12:00 (ou ao ligar o PC).'
    return
}

$copia = Join-Path $env:LOCALAPPDATA 'naplanta-coleta'
$log = Join-Path $copia 'coleta-local.log'
function Git { git -C $copia -c user.name=coleta-bot -c user.email=coleta-bot@users.noreply.github.com @args; if ($LASTEXITCODE) { throw "git $args falhou" } }

if (-not (Test-Path $copia)) { git clone -q https://github.com/yH3rcul3Sy/naplanta $copia }
$env:PYTHONIOENCODING = 'utf-8'  # sem console (agendador) o print de acentos quebraria no cp1252
$falhou = $false
Start-Transcript -Path $log -Append | Out-Null
try {
    Git fetch -q origin
    Git checkout -q main
    Git reset -q --hard origin/main  # copia descartavel: parte sempre do que esta publicado
    if (-not (Test-Path "$copia\.venv")) { python -m venv "$copia\.venv" }
    & "$copia\.venv\Scripts\python.exe" -m pip install -q -r "$copia\coleta\requirements.txt"
    & "$copia\.venv\Scripts\python.exe" "$copia\coleta\coletar.py"
    if ($LASTEXITCODE) { throw 'coletar.py falhou' }
    Git add site/dados.json site/mudancas.json site/status.json site/fotos coleta/geo_cache.json coleta/arredores_cache.json
    git -C $copia diff --cached --quiet
    if ($LASTEXITCODE) {
        Git commit -q -m 'Atualiza dados coletados (coleta local)'
        Git pull -q --rebase  # a coleta do GitHub pode ter publicado enquanto esta rodava
        Git push -q origin main
        'publicado'
    } else { 'nada mudou' }
} catch {
    "ERRO: $_"
    git -C $copia rebase --abort 2>$null  # conflito com a coleta do GitHub: fica para amanha, a copia e resetada
    $falhou = $true
} finally {
    Stop-Transcript | Out-Null
}
if ($falhou) { exit 1 }
