#!/usr/bin/env bash
# Bateria completa de verificacoes, sobre o checkout atual. A mesma lista roda no workflow "testes"
# (push e pull request) e no job "publicar", sobre o commit exato que vai ao ar.
# Requer Linux (actionlint) e as dependencias de coleta/requirements.txt + ruff.
set -euo pipefail
cd "$(dirname "$0")/../.."

echo "::group::actionlint (workflows)"
versao=1.7.12
sha256=8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8  # actionlint_1.7.12_linux_amd64.tar.gz
curl -sSfLo /tmp/al.tgz "https://github.com/rhysd/actionlint/releases/download/v${versao}/actionlint_${versao}_linux_amd64.tar.gz"
echo "${sha256}  /tmp/al.tgz" | sha256sum -c -
tar -xzf /tmp/al.tgz -C /tmp actionlint
/tmp/actionlint -shellcheck= -pyflakes= -color  # so estrutura, expressoes e contextos dos workflows
echo "::endgroup::"

echo "::group::ruff (erros reais e caracteres invisiveis no codigo)"
ruff check coleta --select E9,F,PLE25 --output-format github
echo "::endgroup::"

echo "::group::autotestes das regras (assert dentro dos modulos)"
(cd coleta && python -c "import coletar, paginas, alerta, alertas, agendamento, naplanta.publicacao.paginas, naplanta.app.alertas; print('autotestes ok')")
echo "::endgroup::"

echo "::group::leitura dos coletores contra paginas gravadas"
python coleta/testes/testar.py
echo "::endgroup::"

echo "::group::dados publicados"
python coleta/testes/validar_dados.py
echo "::endgroup::"

echo "::group::sintaxe do JavaScript do site"
for f in $(git ls-files 'site/js/*.js' 'site/js/**/*.js' | grep -v vendor); do
  cp "$f" /tmp/x.mjs && node --check /tmp/x.mjs || { echo "::error file=$f::erro de sintaxe"; exit 1; }
done
echo "::endgroup::"
echo "bateria completa: ok ($(git rev-parse --short HEAD))"
