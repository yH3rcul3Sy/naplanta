"""Caso de uso: a coleta diaria. Orquestra fontes, regras do dominio e servicos de infra; nao conhece HTML nem caminhos."""
from datetime import datetime
from naplanta.config import FUSO, SITE
from naplanta.dominio.empreendimento import campos_sumidos, etapa, limpo, problemas, tipo
from naplanta.dominio.mudancas import COLETAS_PARA_ACEITAR_QUEDA, comparar, historico_recente, quedas
from naplanta.fontes import FONTES
from naplanta.infra import arredores, fotos, geo, repositorio


class ColetaIncompleta(RuntimeError):
    def __init__(self, mensagem, seguidas):
        super().__init__(mensagem)
        self.seguidas = seguidas


def nome(fonte):
    return fonte.__name__.rsplit('.', 1)[-1]  # 'naplanta.fontes.helbor' -> 'helbor', como aparece nos logs


def rotulo(fonte, lista):
    return getattr(fonte, 'ROTULO', None) or (lista[0]['construtora'] if lista else nome(fonte))


def hoje():
    return datetime.now(FUSO).date().isoformat()


def validos(fonte):
    """Empreendimentos da fonte limpos, validados e com etapa e tipo padronizados."""
    novos = []
    for e in map(limpo, fonte.coletar()):
        if ruins := problemas(e, fonte.BASE):
            if {'nome', 'fonte'} & set(ruins):  # sem nome ou link de origem nao da para mostrar
                print(f'{nome(fonte)}: descartado, campos invalidos {ruins}: {str(e)[:150]}')
                continue
            print(f"{nome(fonte)}: {e['fonte']} com campos invalidos {ruins} -> ficam vazios")
            e.update(dict.fromkeys(ruins))
        e['etapa'] = etapa(e['etapa'])
        e['tipo'] = tipo(e.pop('texto'))
        if e['etapa']:  # descarta "100% vendido" e etapas desconhecidas
            novos.append(e)
    return novos


def conferir_volume(fonte, novos, velhos, status_antes):
    """Devolve quantas coletas seguidas veio com queda (0 = normal); levanta excecao se a coleta parece ter falhado."""
    if getattr(fonte, 'VAZIO_OK', False):  # o cadastro pelo site pode estar vazio ou perder itens de proposito
        return 0
    if not novos:  # site que bloqueia o servidor responde "vazio" em vez de dar erro
        raise RuntimeError('nenhum empreendimento retornado (site fora do ar ou bloqueando o acesso)')
    seguidas = quedas(len(novos), len(velhos), status_antes.get('quedas', 0))
    if 0 < seguidas < COLETAS_PARA_ACEITAR_QUEDA:
        raise ColetaIncompleta(f'so {len(novos)} de {len(velhos)} (coleta incompleta)', seguidas)
    if seguidas:
        print(f'{nome(fonte)}: queda para {len(novos)} repetida em {seguidas} coletas seguidas -> aceita como real')
    return seguidas


def enriquecer(dados):
    for e in dados:
        e.pop('plantas', None)  # o site nao usa; so pesa no download
    geo.no_predio(dados)
    arredores.completar(dados)
    fotos.completar(dados)


def executar():
    dia = hoje()
    anteriores, historico, status_antes = repositorio.ler(dia)
    dados, eventos, fontes = [], [], []
    for f in FONTES:
        velhos = [e for e in anteriores if e.get('fonte', '').startswith(f.BASE)]
        antes = status_antes.get(f.BASE, {})
        try:
            novos = validos(f)
            conferir_volume(f, novos, velhos, antes)
        except Exception as erro:  # mantem os dados da ultima coleta dessa fonte
            seguidas = getattr(erro, 'seguidas', 0)
            print(f'falha em {nome(f)}: {erro} -> mantendo {len(velhos)} da coleta anterior')
            dados += [geo.completar(limpo(e)) for e in velhos]
            fontes.append({'site': f.BASE, 'construtora': rotulo(f, velhos), 'total': len(velhos),
                           'ok': False, 'erro': str(erro), 'atualizada': antes.get('atualizada'),
                           **({'quedas': seguidas} if seguidas else {})})
            # aviso na aba Actions: fonte parada nao derruba a coleta, mas precisa ser vista
            print(f"::warning::{nome(f)} sem atualizar desde {antes.get('atualizada')}: {erro}")
            continue
        print(f'{nome(f)}: {len(novos)} coletados')
        eventos += comparar(velhos, novos, dia)
        dados += [geo.completar(e) for e in novos]
        # comparado depois do geo, que tambem completa cidade e posicao dos dois lados
        if sumidos := campos_sumidos(velhos, novos):
            print(f"::warning::{nome(f)}: campos {sumidos} sumiram da maioria dos empreendimentos (o site pode ter mudado)")
        fontes.append({'site': f.BASE, 'construtora': rotulo(f, novos), 'total': len(novos), 'ok': True, 'atualizada': dia,
                       **({'sumidos': sumidos} if sumidos else {})})
    enriquecer(dados)
    historico['eventos'] = historico_recente(eventos + historico['eventos'], dia)
    repositorio.gravar(dados, historico, {'coleta': datetime.now(FUSO).isoformat(timespec='minutes'), 'fontes': fontes})
    print(len(dados), 'empreendimentos,', len(eventos), 'mudancas hoje ->', SITE)
