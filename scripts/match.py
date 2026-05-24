import pandas as pd
import re

# =============================================================
# SCRIPT DE MATCH — PROGRAMA DE MENTORIA
# =============================================================
# Finalidade: Cruza padrinhos (veteranos) com calouros com base
# em critérios de afinidade e disponibilidade.
#
# Pesos de pontuação:
# - Turno: 200 pts
# - Gênero: 80 pts
# - Cidade: 4 pts
# - Prouni: 2 pts
# - Trabalho: 1 pt
# - Proximidade de idade ≤2 anos: 8 pts / ≤5 anos: 4 pts
#
# Para rodar:
#   1. Coloca veteranos_limpo.csv e calouros_limpo.csv em scripts/
#   2. python scripts/match.py
# =============================================================

ARQUIVO_VETERANOS = 'scripts/veteranos_limpo.csv'
ARQUIVO_CALOUROS  = 'scripts/calouros_limpo.csv'
ARQUIVO_SAIDA     = 'scripts/matches_resultado.xlsx'


def carregar_dados(caminho_arquivo, tipo):
    try:
        df = pd.read_csv(caminho_arquivo)
        df[f'{tipo}_id'] = range(len(df))
        if 'idade' in df.columns:
            df['idade'] = pd.to_numeric(df['idade'], errors='coerce')
            df.dropna(subset=['idade'], inplace=True)
            df['idade'] = df['idade'].astype(int)
        print(f"Arquivo '{caminho_arquivo}' carregado com {len(df)} {tipo}(s).")
        return df
    except FileNotFoundError:
        print(f"ERRO: '{caminho_arquivo}' não encontrado!")
        return None


def calcular_pontuacao(veterano, calouro):
    pontuacao = 0
    pesos = {
        'turno':   200,
        'genero':   80,
        'cidade':    4,
        'prouni':    2,
        'trabalho':  1,
    }
    for criterio, peso in pesos.items():
        if veterano[criterio] == calouro[criterio]:
            pontuacao += peso

    diferenca_idade = abs(veterano['idade'] - calouro['idade'])
    if diferenca_idade <= 2:
        pontuacao += 8
    elif diferenca_idade <= 5:
        pontuacao += 4

    return pontuacao


def rodar_match(veteranos_df, calouros_df):
    todos_os_pares = []
    for _, veterano in veteranos_df.iterrows():
        for _, calouro in calouros_df.iterrows():
            score = calcular_pontuacao(veterano, calouro)
            todos_os_pares.append({
                'pontuacao':        score,
                'veterano_id':      veterano['veterano_id'],
                'veterano_nome':    veterano['nome'],
                'calouro_id':       calouro['calouro_id'],
                'calouro_nome':     calouro['nome'],
                'calouro_telefone': calouro['telefone'],
            })
    todos_os_pares.sort(key=lambda x: x['pontuacao'], reverse=True)

    matches = {vid: [] for vid in veteranos_df['veterano_id']}
    calouros_atribuidos = set()
    turnos = set(veteranos_df['turno'].unique()) | set(calouros_df['turno'].unique())

    for turno in turnos:
        vets_do_turno = veteranos_df[
            veteranos_df['turno'] == turno
        ]['veterano_id'].tolist()

        if not vets_do_turno:
            print(f"Aviso: calouros no turno {turno} sem padrinho disponível.")
            continue

        print(f"Distribuindo calouros para o turno: {turno}...")

        while True:
            alocacoes_nesta_rodada = 0
            for v_id in vets_do_turno:
                opcoes = [
                    p for p in todos_os_pares
                    if p['veterano_id'] == v_id
                    and p['calouro_id'] not in calouros_atribuidos
                    and calouros_df.loc[
                        calouros_df['calouro_id'] == p['calouro_id'], 'turno'
                    ].values[0] == turno
                ]
                if opcoes:
                    match = opcoes[0]
                    matches[v_id].append(match)
                    calouros_atribuidos.add(match['calouro_id'])
                    alocacoes_nesta_rodada += 1
            if alocacoes_nesta_rodada == 0:
                break

    print(f"\nMatch concluído! Total alocados: {len(calouros_atribuidos)}")
    return matches


def exportar_resultado(matches, veteranos_df):
    resultados = []
    for veterano_id, calouros_list in sorted(matches.items()):
        veterano_nome = veteranos_df.loc[veterano_id, 'nome']
        if not calouros_list:
            resultados.append({
                'Veterano':               veterano_nome,
                'Quantidade de Calouros': 0,
                'Calouro':                'NENHUM CALOURO ATRIBUÍDO',
                'Telefone do Calouro':    '',
                'Pontuação do Match':     0,
            })
        else:
            calouros_list.sort(key=lambda x: x['pontuacao'], reverse=True)
            for match_info in calouros_list:
                resultados.append({
                    'Veterano':               veterano_nome,
                    'Quantidade de Calouros': len(calouros_list),
                    'Calouro':                match_info['calouro_nome'],
                    'Telefone do Calouro':    match_info['calouro_telefone'],
                    'Pontuação do Match':     match_info['pontuacao'],
                })

    df = pd.DataFrame(resultados)
    df.to_excel(ARQUIVO_SAIDA, index=False, sheet_name='Resultados do Match')
    print(f"Resultados salvos em '{ARQUIVO_SAIDA}'.")


def limpar_csv(arquivo_entrada, arquivo_saida, tipo):
    colunas = [
        "timestamp", "user", "nome", "idade", "matricula",
        "telefone", "turno", "genero", "cidade", "prouni", "trabalho"
    ]
    df = pd.read_csv(arquivo_entrada, header=None, names=colunas,
                     skiprows=1, engine='python')

    df.drop(columns=['timestamp', 'user', 'extra'],
            inplace=True, errors='ignore')
    df.drop_duplicates(subset=['matricula'], keep='first', inplace=True)

    def extrair_idade(texto):
        numeros = re.findall(r'\d+', str(texto))
        return int(numeros[0]) if numeros else None

    def padronizar_sim_nao(texto):
        t = str(texto).strip().lower()
        if t.startswith('sim'):                                    return 'Sim'
        if t.startswith('não') or t.startswith('nao') or t == 'nan': return 'Não'
        return str(texto).strip()

    def padronizar_cidade(texto):
        return 'Sim' if str(texto).strip().lower() == 'sim' else 'Não'

    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip()

    df['turno']    = df['turno'].str.title()
    df['genero']   = df['genero'].str.title()
    df['prouni']   = df['prouni'].apply(padronizar_sim_nao)
    df['trabalho'] = df['trabalho'].apply(padronizar_sim_nao)
    df['cidade']   = df['cidade'].apply(padronizar_cidade)
    df['idade']    = df['idade'].apply(extrair_idade)
    df.dropna(subset=['idade'], inplace=True)
    df['idade']    = df['idade'].astype(int)

    colunas_finais = [
        'nome', 'turno', 'genero', 'idade',
        'cidade', 'prouni', 'trabalho', 'telefone'
    ]
    df[colunas_finais].to_csv(arquivo_saida, index=False, encoding='utf-8-sig')
    print(f"Limpeza concluída! '{arquivo_saida}' com {len(df)} {tipo}(s) únicos.")


if __name__ == "__main__":
    # 1. Limpa os CSVs brutos (descomenta se precisar)
    # limpar_csv("scripts/veteranos.csv",  "scripts/veteranos_limpo.csv",  "veterano")
    # limpar_csv("scripts/calouros.csv",   "scripts/calouros_limpo.csv",   "calouro")

    # 2. Carrega os dados limpos
    veteranos_df = carregar_dados(ARQUIVO_VETERANOS, 'veterano')
    calouros_df  = carregar_dados(ARQUIVO_CALOUROS,  'calouro')

    if veteranos_df is None or calouros_df is None:
        print("Arquivos não encontrados. Abortando.")
    else:
        matches = rodar_match(veteranos_df, calouros_df)
        exportar_resultado(matches, veteranos_df)
