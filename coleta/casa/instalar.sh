#!/usr/bin/env bash
# Instala ou atualiza a coleta em casa (docs/agendamento.md): Python 3.12, runner do GitHub e servicos do systemd.
# Tudo fica em .casa/ (fora do git); o systemd guarda so links para la. Rodar de novo e seguro.
# Requer gh logado (gh auth login) e uv em ~/.local/bin.
set -euo pipefail
PATH=$HOME/.local/bin:$PATH
RAIZ=$(cd "$(dirname "$0")/../.." && pwd)
CASA=$RAIZ/.casa
REPO=yH3rcul3Sy/naplanta
RUNNER=2.338.1  # o runner se atualiza sozinho depois de registrado

mkdir -p "$CASA/systemd" "$CASA/runner"
[ -x "$CASA/venv/bin/pip" ] || uv venv --seed --python 3.12 "$CASA/venv"
if [ ! -f "$CASA/runner/.runner" ]; then
  curl -sSfL "https://github.com/actions/runner/releases/download/v$RUNNER/actions-runner-linux-x64-$RUNNER.tar.gz" | tar xz -C "$CASA/runner"
  "$CASA/runner/config.sh" --unattended --url "https://github.com/$REPO" --name casa-danilo --labels casa --work _work --replace \
    --token "$(gh api -X POST "repos/$REPO/actions/runners/registration-token" -q .token)"
fi
# PATH dos jobs: o venv primeiro, para "python" e "pip" serem os do 3.12
echo "$CASA/venv/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin" > "$CASA/runner/.path"

for u in "$RAIZ"/coleta/casa/naplanta-*; do
  sed "s|@CASA@|$CASA|g" "$u" > "$CASA/systemd/$(basename "$u")"
done
systemctl --user link --force "$CASA"/systemd/naplanta-*
systemctl --user daemon-reload
systemctl --user enable --now naplanta-runner.service naplanta-coleta.timer
systemctl --user restart naplanta-runner.service  # pega um .path novo
