# Coleta diaria no computador do projeto: Cury e Sousa Araujo nao respondem aos servidores do GitHub.
# Usa uma copia so da automacao (fora do OneDrive), sempre igual ao GitHub: nunca mexe na pasta em que voce trabalha.
# Agendar (uma vez): coleta\local.ps1 -Agendar     Remover: Unregister-ScheduledTask 'NaPlanta coleta local'
param([switch]$Agendar)

if ($Agendar) {
    $acao = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    $quando = New-ScheduledTaskTrigger -Daily -At '12:00'  # depois da coleta do GitHub (06h, que costuma atrasar)
    # StartWhenAvailable: se o PC estava desligado ao meio-dia, roda assim que ligar
    $regras = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 4) -RunOnlyIfNetworkAvailable
    Register-ScheduledTask -TaskName 'NaPlanta coleta local' -Action $acao -Trigger $quando -Settings $regras -Force | Out-Null
    'Agendado: todo dia 12:00 (ou ao ligar o PC).'
    return
}

$copia = Join-Path $env:LOCALAPPDATA 'naplanta-coleta'
$log = Join-Path $copia 'coleta-local.log'
function GitBot { git.exe -C $copia -c user.name=coleta-bot -c user.email=coleta-bot@users.noreply.github.com @args; if ($LASTEXITCODE) { throw "git $args falhou" } }

# copia corrompida (PC desligado no meio de um git, por exemplo): guarda a pasta quebrada e clona de novo
if ((Test-Path $copia) -and -not (git.exe -C $copia rev-parse --verify -q HEAD 2>$null)) {
    Rename-Item $copia "$copia-quebrada-$(Get-Date -Format yyyyMMddHHmm)"
}
if (-not (Test-Path $copia)) { git.exe clone -q https://github.com/yH3rcul3Sy/naplanta $copia }
$env:PYTHONIOENCODING = 'utf-8'  # sem console (agendador) o print de acentos quebraria no cp1252
$falhou = $false
Start-Transcript -Path $log -Append | Out-Null
try {
    GitBot fetch -q origin
    GitBot checkout -q main
    GitBot reset -q --hard origin/main  # copia descartavel: parte sempre do que esta publicado
    if (-not (Test-Path "$copia\.venv")) { python -m venv "$copia\.venv" }
    & "$copia\.venv\Scripts\python.exe" -m pip install -q -r "$copia\coleta\requirements.txt"
    & "$copia\.venv\Scripts\python.exe" "$copia\coleta\coletar.py"
    if ($LASTEXITCODE) { throw 'coletar.py falhou' }
    $dados = 'site/dados.json', 'site/mudancas.json', 'site/status.json', 'site/fotos', 'coleta/cache'
    GitBot add @dados
    git -C $copia diff --cached --quiet
    if ($LASTEXITCODE) {
        GitBot commit -q -m 'Atualiza dados coletados (coleta local)'
        git -C $copia pull -q --rebase  # a coleta do GitHub pode ter publicado enquanto esta rodava
        if ($LASTEXITCODE) {
            # conflito nos dados: esta coleta (com todas as fontes) prevalece. Parte da main atual e grava so os
            # arquivos de dados, para nunca desfazer codigo que chegou no meio
            git -C $copia rebase --abort
            GitBot reset -q origin/main
            GitBot add @dados
            GitBot commit -q -m 'Atualiza dados coletados (coleta local)'
        }
        GitBot push -q origin main
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
