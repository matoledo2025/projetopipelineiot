import streamlit as st
import pandas as pd
import clickhouse_connect
import plotly.express as px

# Conexão com o ClickHouse
client = clickhouse_connect.get_client(
    host='localhost',
    port=8123,
    username='dashboard',
    password='senha',
    database='data_warehouse'
)

# Query base para buscar dados, incluindo consumo_horas_mes e qtd_canais_assistidos
QUERY_BASE = """
SELECT
    f.id_visita,
    u.nome AS usuario,
    u.cidade,
    p.descricao AS pagina,
    t.data_assinatura AS data,
    t.dia_semana,
    t.consumo_horas_mes,
    t.qtd_canais_assistidos,
    f.duracao AS duracao_min
FROM
    fato_visita AS f
JOIN dim_usuario AS u ON f.id_usuario = u.id_usuario
JOIN dim_pagina AS p ON f.id_pagina = p.id_pagina
JOIN dim_tempo AS t ON f.id_tempo = t.id_tempo
"""

# Função para carregar dados
def load_data():
    result = client.query(QUERY_BASE)
    df = pd.DataFrame(result.result_rows, columns=result.column_names)
    # Garantir que a coluna de datas é datetime
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    return df

# Título do dashboard
st.title('Dashboard de Visitas')

# Carrega os dados
df = load_data()

# Sidebar: filtros
cidades = st.sidebar.multiselect(
    "Cidade", options=sorted(df['cidade'].unique()), default=sorted(df['cidade'].unique()))
paginas = st.sidebar.multiselect(
    "Página", options=sorted(df['pagina'].unique()), default=sorted(df['pagina'].unique()))
datas = st.sidebar.date_input(
    "Período", value=(df['data'].min(), df['data'].max()), min_value=df['data'].min(), max_value=df['data'].max())

# Filtra os dados
df_filtrado = df[
    df['cidade'].isin(cidades) &
    df['pagina'].isin(paginas)
]

if datas is not None and len(datas) == 2:
    df_filtrado = df_filtrado[
        (df_filtrado['data'] >= pd.to_datetime(datas[0])) &
        (df_filtrado['data'] <= pd.to_datetime(datas[1]))
    ]

# Exibir dados filtrados
st.dataframe(df_filtrado)

# Estatísticas resumidas
st.markdown('### Estatísticas resumidas')
st.write(f"Total de Visitas selecionadas: {len(df_filtrado)}")
st.write(f"Duração Média das visitas: {df_filtrado['duracao_min'].mean():.1f} minutos")
st.write(f"Consumo Médio de Horas/Mês: {df_filtrado['consumo_horas_mes'].mean():.1f} horas")
st.write(f"Média de Canais Assistidos: {df_filtrado['qtd_canais_assistidos'].mean():.1f}")

# Gráfico de visitas por dia
st.markdown("### Visitas por dia")
if df_filtrado.empty:
    st.info("Sem dados para os filtros selecionados")
else:
    daily = df_filtrado.groupby(df_filtrado['data'].dt.date).size()
    fig = px.bar(
        x=daily.index,
        y=daily.values,
        labels={'x': 'Data', 'y': 'Visitas'},
        title='Visitas por dia'
    )
    st.plotly_chart(fig, use_container_width=True)
