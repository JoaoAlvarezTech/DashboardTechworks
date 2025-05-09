import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import os
import csv
from datetime import datetime, timedelta

st.set_page_config(page_title="Dashboard de Transações - Comparação de Clientes", layout="wide")

st.title("📊 Dashboard de Transações: Comparação de Clientes e Dias")

data_path = "data"
csv_files = glob.glob(os.path.join(data_path, "dados_*.csv"))

all_dfs = []

for file in csv_files:
    try:
        client_name = os.path.basename(file).replace("dados_", "").replace(".csv", "")
        data = []
        with open(file, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader) 
            for row in reader:
                if len(row) == 5: 
                    date, timezone, operation, volume, amount = row
                   
                    try:
                        amount = float(amount.replace(',', ''))  
                    except ValueError:
                        amount = float('nan') 
                    data.append([date, timezone, operation, float(volume), amount])
        
        df = pd.DataFrame(data, columns=["Date", "Timezone", "Operation", "Volume", "Amount"])
        
        
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce", format="%Y-%m-%d")
        df["Client"] = client_name
        
        if df["Date"].isnull().all():
            st.error(f"Erro: Nenhuma data válida em {file}.")
        else:
            all_dfs.append(df)
    except Exception as e:
        st.error(f"Erro ao carregar {file}: {str(e)}")


if all_dfs:
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    
    total_df = combined_df.groupby(["Client", "Date"]).agg({
        "Volume": "sum",
        "Amount": "sum"
    }).reset_index()
    total_df["Operation"] = "Total"
    
    combined_df = pd.concat([combined_df, total_df], ignore_index=True)
    
   
    st.sidebar.header("🔍 Filtros")
    st.sidebar.markdown("**Selecione os parâmetros abaixo para personalizar a visualização:**")
    
    clients = sorted(combined_df["Client"].unique())
    selected_clients = st.sidebar.multiselect(
        "👥 Selecione os Clientes",
        options=clients,
        default=clients,
        help="Escolha um ou mais clientes."
    )
    
    min_date = combined_df["Date"].min().date() if pd.notnull(combined_df["Date"].min()) else datetime.now().date()
    max_date = combined_df["Date"].max().date() if pd.notnull(combined_df["Date"].max()) else datetime.now().date()
    date_range = st.sidebar.date_input(
        "📅 Intervalo de Datas",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
    else:
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[0])
    
    filtered_df = combined_df[
        (combined_df["Client"].isin(selected_clients)) &
        (combined_df["Date"].notna()) &
        (combined_df["Date"] >= start_date) &
        (combined_df["Date"] <= end_date)
    ]
    
   
    st.markdown("### Resumo Geral")
    col1, col2 = st.columns(2)
    total_volume = filtered_df[filtered_df["Operation"] == "Total"]["Volume"].sum()
    total_amount = filtered_df[filtered_df["Operation"] == "Total"]["Amount"].sum()
    col1.metric("Volume Total", f"{total_volume:,.2f}")
    col2.metric("Montante Total", f"R${total_amount:,.2f}" if pd.notnull(total_amount) else "N/A")
    
   
    st.markdown("---")
    st.subheader("Tabela de Transações Detalhada")
    filtered_df_display = filtered_df[["Client", "Date", "Operation", "Volume", "Amount"]].copy()
    filtered_df_display["Volume"] = filtered_df_display["Volume"].apply(lambda x: f"{x:,.2f}")
    filtered_df_display["Amount"] = filtered_df_display["Amount"].apply(lambda x: f"R${x:,.2f}" if pd.notnull(x) else "N/A")
    filtered_df_display["Date"] = filtered_df_display["Date"].dt.strftime("%d/%m/%Y")
    
    st.dataframe(
        filtered_df_display,
        use_container_width=True,
        column_config={
            "Client": st.column_config.TextColumn("Cliente", width="medium"),
            "Date": st.column_config.TextColumn("Data", width="medium"),
            "Operation": st.column_config.TextColumn("Operação", width="medium"),
            "Volume": st.column_config.TextColumn("Volume", width="medium"),
            "Amount": st.column_config.TextColumn("Montante", width="medium")
        },
        hide_index=True
    )
    
   
    st.subheader("Comparação de Volume Total entre Clientes")
    volume_by_client = filtered_df[filtered_df["Operation"] == "Total"].groupby("Client")["Volume"].sum().reset_index()
    fig1 = px.bar(
        volume_by_client,
        x="Client",
        y="Volume",
        title="Volume Total por Cliente",
        color="Client",
        labels={"Volume": "Volume Total", "Client": "Cliente"},
        color_discrete_sequence=px.colors.qualitative.Vivid,
        hover_data={"Volume": ":.2f"}
    )
    fig1.update_traces(hovertemplate="<b>%{x}</b><br>Volume: %{y:,.2f}<extra></extra>")
    fig1.update_layout(
        title_font_size=20,
        title_font_color="#FF4B4B",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="#262730"),
        showlegend=True
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    
    st.markdown("---")
    st.subheader("Evolução do Volume ao Longo do Tempo por Cliente")
    volume_over_time = filtered_df[filtered_df["Operation"] == "Total"]
    fig2 = px.line(
        volume_over_time,
        x="Date",
        y="Volume",
        color="Client",
        title="Evolução do Volume por Cliente",
        labels={"Volume": "Volume Total", "Date": "Data", "Client": "Cliente"},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig2.update_traces(line=dict(width=3), hovertemplate="<b>%{x|%d/%m/%Y}</b><br>Cliente: %{fullData.name}<br>Volume: %{y:,.2f}<extra></extra>")
    fig2.update_layout(
        title_font_size=20,
        title_font_color="#FF4B4B",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="#262730"),
        showlegend=True,
        xaxis_tickformat="%d/%m/%Y"
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    
    st.markdown("---")
    st.subheader("Volume por Operação e Cliente")
    volume_by_operation = filtered_df[filtered_df["Operation"] != "Total"]
    fig3 = px.bar(
        volume_by_operation,
        x="Client",
        y="Volume",
        color="Operation",
        barmode="stack",
        title="Volume por Operação e Cliente",
        labels={"Volume": "Volume", "Client": "Cliente", "Operation": "Operação"},
        color_discrete_sequence=px.colors.qualitative.Set1
    )
    fig3.update_traces(hovertemplate="<b>%{x}</b><br>Operação: %{fullData.name}<br>Volume: %{y:,.2f}<extra></extra>")
    fig3.update_layout(
        title_font_size=20,
        title_font_color="#FF4B4B",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="#262730"),
        showlegend=True
    )
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("Nenhum dado encontrado. Verifique os arquivos em 'data/dados_*.csv'.")
