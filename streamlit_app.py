import streamlit as st 
import openpyxl
import streamlit.runtime.scriptrunner.magic_funcs
import importlib.metadata
from importlib.metadata import version  
import pandas as pd
import altair as alt
from PIL import Image
from datetime import datetime
import calendar
from calendar import monthrange

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title='DASHBOARD DE ACOMPANHAMENTO DE AÇÕES  ',
    page_icon='./Imagem2.jpg',
    layout='wide',
    initial_sidebar_state='expanded',
    menu_items={
        'Get Help': 'http://www.anatel.gov.br',
        'Report a bug': "http://www.anatel.gov.br",
        'About': "Esse app foi desenvolvido no nosso Curso de Streamlit."
    }
)

#Criando uma variável com a data atual
hoje = datetime.today()
mes_atual = hoje.strftime("%Y-%m")

st.header("Dashboard Experimental de Acompanhamento de Ações")


if "atualiza_df" not in st.session_state:
    st.session_state["atualiza_df"] = 0 #Se for zero, as tabelas auxiliares ainda não foram criadas
botao_form = False

#Criando o dataframe
#Carrega o arquivo com a extração de ações do Fiscaliza
@st.cache_data  #Carrega em cache na máquina do usuário, os dados do dataframe acelerando as consultas 
def busca_df():
    df = pd.read_excel(
         io = arq_excel_1,
         sheet_name="issues",
         engine="openpyxl",
         usecols='A:O',
         nrows = 9000
         )
    #Limpa a coluna com a classe de inspeção de nomes repetidos
    df.loc[df["Classe da Inspeção"].str.contains("Serviço")==True, "Classe da Inspeção" ] = "Serviço"
    df.loc[df["Classe da Inspeção"].str.contains("Técnica")==True, "Classe da Inspeção" ] = "Técnica"
    df.loc[df["Classe da Inspeção"].str.contains("Tributária")==True, "Classe da Inspeção" ] = "Tributária"
    
    return df
#Rotina que carrega a tabela com as capacidades anuais de horas por UD
@st.cache_data  #Carrega em cache na máquina do usuário, os dados do dataframe acelerando as consultas 
def busca_capacidade_df():
    cap_df = pd.read_excel(
         io = arq_excel_1,
         sheet_name="capacidade",
         engine="openpyxl",
         usecols='A:H',
         nrows = 31
         )
    return cap_df    
    
    

#Função que entra com a data atual e retorna a lista de meses entre jan do ano atual até  março do ano seguinte
def periodos(data_atual: datetime):
    data_inicio = datetime(data_atual.year,1,1) #Jan do ano atual
    data_fim = datetime(data_atual.year+1,3,31) #Março do póximo ano
    
    #Obtem lista de meses entre a data de início e a final
    lista_meses = pd.date_range(start=data_inicio,end=data_fim,freq='ME')
    #Converte as datas para string formato "2024-03"
    lista_meses = lista_meses.strftime("%Y-%m")

      
    return lista_meses

#Função que calcula os dias decorridos desde o início da ação até o mês de análise
def dias_exec(data_ini:datetime,data_fim:datetime,mes_ano_ref:str):
     dias_dec = 0
     mes_ano = datetime.strptime(mes_ano_ref,"%Y-%m")
     fim_mes = monthrange(mes_ano.year,mes_ano.month)
     #Monthrange devolve 2 valores: o dia da semana do dia primeiro e o total de dias do mês
     ultimo_dia_do_mes = datetime(mes_ano.year,mes_ano.month,fim_mes[1])
     if ((data_ini > ultimo_dia_do_mes) or
           (data_fim < datetime(mes_ano.year,mes_ano.month,1))): #Se a ação não iniciou ainda ou já terminou
           dias_dec = 0
     else:
            if data_fim < ultimo_dia_do_mes: #Se a ação terminou dentro do mês analisado
              dias_dec = (data_fim - data_ini)
            else:
              dias_dec = (ultimo_dia_do_mes - data_ini)   
     return dias_dec
    
    
#Função que calcula a estimativa de horas executadas acumuladas no mês
# Parêmetros de entrada: mês e ano de referência
# - Data de início, data limite, horas previstas
def horas_exec(mes_ano_ref:str,data_ini:datetime,data_lim:datetime,horas_prev:int):
    #Para obter o úytimo dia de cada mês. Pega o Ano-mês em string, converte para formato datetime
    # e usa a função monthrange
    
    #mes_ano = datetime.strptime(mes_ano_ref,"%Y-%m")
    #fim_mes = monthrange(mes_ano.year,mes_ano.month)
    #Monthrange devolve 2 valores: o dia da semana do dia primeiro e o total de dias do mês
    #ultimo_dia_do_mes = datetime(mes_ano.year,mes_ano.month,fim_mes[1])
    prazo_dias = (data_lim - data_ini)
    prazo_dias = list(map(pd.Timedelta,prazo_dias))
    #Inicializa o vetor com o prazo da ação em dias
    horas_executadas =  prazo_dias
    
       
    #Curva de horas acumuladas = Horas_estimadas*(dias_decorridos/prazo)^2
    for i in range(0, len(data_ini)):
        dias_decorr =  dias_exec(data_ini[i],data_lim[i],mes_ano_ref) 
        dias_decorr = pd.Timedelta(dias_decorr)
        dias_decorr = dias_decorr.days
        prazo_total = prazo_dias[i].days
        #As horas são calculadas como número float com 1 casa decimal
        horas_executadas[i] = round(float(((dias_decorr/prazo_total)**2)*horas_prev[i]),1)
     
    return horas_executadas













    


def cap_mensal(df_ent):
    #Dataframe de capacidade mensal por mes da fiscalização de serviços
    df_cap_mens_s = df_ent["UD"]
    df_cap_mens_s = pd.DataFrame(df_cap_mens_s)
    #Cria coluna com a classe de inspeção
    df_cap_mens_s["Classe da Inspeção"]= "Serviço"
    df_cap_mens_s.rename(columns={'UD': 'Unidade_executante'}, inplace=True) #Renomeia a coluna de unidade executante
    
    #Dataframe de capacidade mensal por mes da fiscalização técnica
    df_cap_mens_t = df_ent["UD"]
    df_cap_mens_t = pd.DataFrame(df_cap_mens_t)
    #Cria coluna com a classe de inspeção
    df_cap_mens_t["Classe da Inspeção"]= "Técnica"
    df_cap_mens_t.rename(columns={'UD': 'Unidade_executante'}, inplace=True) #Renomeia a coluna de unidade executante
    
        
    #Dataframe de capacidade mensal por mes da fiscalização tributaria e outros assuntos
    df_cap_mens_o = df_ent["UD"]
    df_cap_mens_o = pd.DataFrame(df_cap_mens_o)
    #Cria coluna com a classe de inspeção
    df_cap_mens_o["Classe da Inspeção"]= "Tributária"
    df_cap_mens_o.rename(columns={'UD': 'Unidade_executante'}, inplace=True) #Renomeia a coluna de unidade executante
 
    #Cria colunas com os meses de execução
    lista_de_meses = periodos(hoje)
    meses_de_ferias =["1","7","12"]  #Jan, julho e dez
    
    for i in range(0,len(lista_de_meses)):
        
        
        df_cap_mens_s[f"{lista_de_meses[i]}"] = "" #Cria as colunas vazias com os meses
        df_cap_mens_t[f"{lista_de_meses[i]}"] = "" #Cria as colunas vazias com os meses
        df_cap_mens_o[f"{lista_de_meses[i]}"] = "" #Cria as colunas vazias com os meses
        
        #Preenche cada linha com a capacidade em horas daquele mês.
        #Se for mês de férias a capacidade de horas é reduzida pela metade
        mes = lista_de_meses[i]   #string
        mes = datetime.strptime(mes,"%Y-%m") #converte para formato de tempo
        mes = mes.month #obtém o mês
        mes = str(mes) #converte de volta para string para procurar na lista de meses de férias
        
        if mes in meses_de_ferias:  #metade da capacidade de horas nas férias
              df_cap_mens_s[f"{lista_de_meses[i]}"] = round(((df_ent["CapS"]/12))/2,1)
              df_cap_mens_t[f"{lista_de_meses[i]}"] = round(((df_ent["CapT"]/12))/2,1)
              df_cap_mens_o[f"{lista_de_meses[i]}"] = round(((df_ent["CapO"]/12))/2,1)
        else:
              df_cap_mens_s[f"{lista_de_meses[i]}"] = round((df_ent["CapS"]/12),1)
              df_cap_mens_t[f"{lista_de_meses[i]}"] = round((df_ent["CapT"]/12),1)
              df_cap_mens_o[f"{lista_de_meses[i]}"] = round((df_ent["CapO"]/12),1)
     
      
    return df_cap_mens_s, df_cap_mens_t, df_cap_mens_o 







def cria_tabelas_auxiliares(df):
    #Comandos que só precisam sem executados uma vez por arquivo excel carregado com o dataframe
    
    #Cria uma coluna com a quantidade de dias remanescentes até a data limite da ação
    df["Dias_Remanescentes"]=  df["Data limite"] - hoje
    df["Dias_Remanescentes"]= (df["Dias_Remanescentes"].dt.days) + 1

    #Cria uma coluna com a quantidade de dias decorridos até a data de hoje
    df["Dias_Decorridos"]=  hoje - df["Data de início"] 
    df["Dias_Decorridos"]= (df["Dias_Decorridos"].dt.days)

    #Cria uma coluna com o prazo total em dias
    df["Prazo_em_Dias"]=  df["Data limite"] - df["Data de início"] 
    df["Prazo_em_Dias"]= (df["Prazo_em_Dias"].dt.days)

    #Cria uma coluna com o estimativa de horas executadas
    #Curva de horas acumuladas = Horas_estimadas*(dias_decorridos/prazo)^2
    df["Horas_Executadas_Estimadas"] = (hoje - df["Data de início"])
    df["Horas_Executadas_Estimadas"] = df["Horas_Executadas_Estimadas"].dt.days
    df["Horas_Executadas_Estimadas"] = (df["Horas_Executadas_Estimadas"])/(df["Prazo_em_Dias"])
    df["Horas_Executadas_Estimadas"] = pow(df["Horas_Executadas_Estimadas"],2)*df["Total de horas"]

    
    #Cria o dataframe com as estimativas de horas executadas acumuladas no mês, desde o início por ação
    #df_horas_exec = horas_executadas(df)[0]


    #Cria o dataframe com as horas estimadas executadas dentro do mês por ação
    #df_horas_exec_mes = horas_executadas(df)[1]
    

    lista_de_meses = periodos(hoje)    #Cria lista com os meses do ano atual até março do ano seguinte
 
        
    #Cria uma coluna no dataframe com o mês da data limite da ação
    df["Mes_Ano"]=df["Data limite"].dt.to_period("M") #Data com tipo datetime
    df["Mes_Ano_String"]=df["Mes_Ano"].astype(str) #converte para string as datas para facilitar os filtros
            
    #Cria coluna com a GR ou UO executante da ação
    df["Unidade_executante"]=df["Título"].str.split('_').str[1]  #Separa o título pelo caracter "_" e pega o segundo pedaço
        
    st.session_state["df"] = df #Armazena o dataframe principal no session state para ser usado fora dessa rotina
    df = st.session_state["df"]  
           
    if "df_horas" not in st.session_state:
        st.session_state["df_horas"] = True #Se for zero, as tabelas auxiliares ainda não foram criadas            
        df_horas = horas_executadas(df)
        st.session_state["df_horas_exec"] = df_horas[0]
        st.session_state["df_horas_exec_mes"] = df_horas[1]
        st.session_state["df_exec_acum"] = df_horas[2]            
            

    #Cria o dataframe com as estimativas de horas executadas acumuladas no mês, desde o início por ação
    df_horas_exec = st.session_state["df_horas_exec"] 
                
    #Cria o dataframe com as horas estimadas executadas dentro do mês por ação
    df_horas_exec_mes = st.session_state["df_horas_exec_mes"]
    #Cria o dataframe com as horas estimadas executadas acumuladas até aquele mês
    df_exec_acum = st.session_state["df_exec_acum"] 
        
    #Cria o dataframe com as horas estimadas executadas dentro do mês por ação agrupando por Unidade executante e classe de inspeção
    df_horas_exec_mes_UD = df_horas_exec_mes
    df_horas_exec_mes_UD.drop(["Data de início","Data limite"],axis=1,inplace=True) #Remove esses campos para não dar erro no group by
    df_horas_exec_mes_UD = df_horas_exec_mes_UD.groupby(["Unidade_executante","Classe da Inspeção","Situação"]).agg('sum')
    df_horas_exec_mes_UD = df_horas_exec_mes_UD.reset_index()  #Transforma o objeto tipo "GROUPBY" para um dataframe comum
    df_horas_exec_mes_UD.drop(["Título","Total de horas previstas"],axis=1,inplace=True)
    #Reordenando as colunas de meses para linhas
    df_horas_exec_mes_UD = pd.melt(df_horas_exec_mes_UD, id_vars=["Unidade_executante","Classe da Inspeção","Situação"], value_vars=lista_de_meses,var_name="Mes_execucao",value_name='CargaH_Mes')

    if "df_horas_exec_mes_UD" not in st.session_state:
        st.session_state["df_horas_exec_mes_UD"] = df_horas_exec_mes_UD


    #Cria o dataframe com as horas estimadas executadas acumuladas até aquele mês agrupando por Unidade executante e classe de inspeção
    df_exec_acum_UD = df_exec_acum.groupby(["Unidade_executante","Classe da Inspeção","Situação"]).agg('sum')
    df_exec_acum_UD = df_exec_acum_UD.reset_index()  #Transforma o objeto tipo "GROUPBY" para um dataframe comum

    df_exec_acum_UD.drop(["Título","Total de horas previstas"],axis=1,inplace=True)
    #Reordenando as colunas de meses para linhas
    df_exec_acum_UD = pd.melt(df_exec_acum_UD, id_vars=["Unidade_executante","Classe da Inspeção","Situação"], value_vars=lista_de_meses,var_name="Mes_execucao",value_name='CargaH_Mes_Acum')


    if "df_exec_acum_UD" not in st.session_state:
        st.session_state["df_exec_acum_UD"] = df_exec_acum_UD

    #Carrega tabela com capacidades anuais de horas por UD
    if "df_cap" not in st.session_state:
        st.session_state["df_cap"] = True #Se for zero, as tabelas auxiliares ainda não foram criadas            
        df_cap = busca_capacidade_df()
        st.session_state["df_cap_mens_s"] =  cap_mensal(df_cap)[0]
        st.session_state["df_cap_mens_t"] =  cap_mensal(df_cap)[1]
        st.session_state["df_cap_mens_o"] = cap_mensal(df_cap)[2]
    
     
    #Cria tabela com as capacidades mensais de horas por UD
    df_cap_mens_s = st.session_state["df_cap_mens_s"] 
    df_cap_mens_t = st.session_state["df_cap_mens_t"]
    df_cap_mens_o = st.session_state["df_cap_mens_o"]

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
  
    


#Criando um dataframe com as horas de execução acumuladas (carga) estimadas por mês para cada ação
def horas_executadas(df_ent):
    #df_exec - dataframe com as horas executadas estimadas ACUMULADAS até aquele mês
    df_exec = df_ent["Título"]
    df_exec = pd.DataFrame(df_exec)
    
    df_exec["Situação"] = df_ent["Situação"]
    df_exec["Classe da Inspeção"] = df_ent["Classe da Inspeção"]
    
    #Cria colunas com data de início e final
    df_exec["Data de início"] = df_ent["Data de início"]
    df_exec["Data limite"] = df_ent["Data limite"]
    
    
    #Cria uma coluna com o prazo total em dias de cada ação
    df_exec["Prazo_em_Dias"]=  df_ent["Data limite"] - df_ent["Data de início"] 
    df_exec["Prazo_em_Dias"]= (df_exec["Prazo_em_Dias"].dt.days)

    
    #Cria coluna com o total de horas previstas por ação
    df_exec["Total de horas previstas"] = df_ent["Total de horas"]
        
    #Cria coluna com a GR ou UO executante da ação
    df_exec["Unidade_executante"]=df_ent["Título"].str.split('_').str[1]  #Separa o título pelo caracter "_" e pega o segundo pedaço
    
    #Cria colunas com os meses de execução
    lista_de_meses = periodos(hoje)
    
    #df_exec_no_mes - dataframe com as horas executadas estimadas DENTRO DAQUELE mês
    #É calculado como a diferença entre as horas acumuladas deste mês e as horas 
    #acumuladas do mês anterior
    df_exec_no_mes = df_ent["Título"]
    df_exec_no_mes = pd.DataFrame(df_exec_no_mes)
    df_exec_no_mes["Situação"] = df_ent["Situação"]
    df_exec_no_mes["Classe da Inspeção"] = df_ent["Classe da Inspeção"]
    df_exec_no_mes["Data de início"] = df_ent["Data de início"]
    df_exec_no_mes["Data limite"] = df_ent["Data limite"]
    df_exec_no_mes["Total de horas previstas"] = df_ent["Total de horas"]
    df_exec_no_mes["Unidade_executante"] = df_exec["Unidade_executante"]
    
    #df_exec_acum - dataframe com as horas executadas estimadas acumuladas ao longo dos meses.
    #É calculado somando as horas executadas no mês atual com as executadas no mês anterior
    # do dataframe df_exec_no_mes
    df_exec_acum = df_ent["Título"]
    df_exec_acum = pd.DataFrame(df_exec_acum)
    df_exec_acum["Situação"] = df_ent["Situação"]
    df_exec_acum["Classe da Inspeção"] = df_ent["Classe da Inspeção"]
    df_exec_acum["Total de horas previstas"] = df_ent["Total de horas"]
    df_exec_acum["Unidade_executante"] = df_exec["Unidade_executante"]    
    
       
    
    for i in range(0,len(lista_de_meses)):
        df_exec[f"{lista_de_meses[i]}"] = "" #Cria as colunas vazias com os meses
        df_exec_no_mes[f"{lista_de_meses[i]}"] = "" #Cria as colunas vazias com os meses
        #Preenche cada linha com as horas executadas até aquele mês
        df_exec[f"{lista_de_meses[i]}"] = horas_exec(f"{lista_de_meses[i]}",df_exec["Data de início"] ,df_exec["Data limite"] ,df_exec["Total de horas previstas"])
        
        if i==0:
            df_exec_no_mes[f"{lista_de_meses[i]}"] = df_exec[f"{lista_de_meses[i]}"]
            
           
        else:
            df_exec_no_mes[f"{lista_de_meses[i]}"] = df_exec[f"{lista_de_meses[i]}"] - df_exec[f"{lista_de_meses[i-1]}"]
            
        #Preenche com zero as horas do mês atual, se a ação terminou no mês anterior
        df_exec_no_mes.loc[df_exec_no_mes[f"{lista_de_meses[i]}"] < 0,f"{lista_de_meses[i]}" ] = 0 
        
        if i==0:
            df_exec_acum[f"{lista_de_meses[i]}"] = df_exec_no_mes[f"{lista_de_meses[i]}"]
        else:
            df_exec_acum[f"{lista_de_meses[i]}"] = df_exec_no_mes[f"{lista_de_meses[i]}"] + df_exec_acum[f"{lista_de_meses[i-1]}"] 
           
    return df_exec, df_exec_no_mes, df_exec_acum






      
def cria_tabelas_dos_graficos():    
    #Cria as tabelas com os dados usados nos gráficos
        # Tabelas para criação dos gráficos
    # Horas por classe de inspeção: serviço, técnica, tributário
    
    df = st.session_state["df"]  
    
    
    
    tab1_horas_previstas = df.loc[(df["Situação"].isin(fStatus)
                                   )&(
                                       df["Classe da Inspeção"].isin(fClasseAcao))&(
                                           df["Unidade_executante"].isin(fUnidade_Executante)
                                       )]
    tab1_horas_previstas.sort_values(by=["Data limite"],ascending=False)
    #Removendo as colunas que não são necessárias para os gráficos
    tab1_horas_previstas = tab1_horas_previstas.loc[:, ['Título', 'Situação','Data limite','Classe da Inspeção',"Mes_Ano","Mes_Ano_String","Total de horas"]]
    
    st.session_state["tab1_horas_previstas"] = tab1_horas_previstas
    
    
           
    #Tabela para o gráfico de horas de execução acumuladas
    
    df_horas_exec = st.session_state["df_horas_exec"]
    
    tab2_horas_exec =df_horas_exec.loc[(df_horas_exec["Situação"].isin(fStatus))&(df_horas_exec["Classe da Inspeção"].isin(fClasseAcao))&(df_horas_exec["Unidade_executante"].isin(fUnidade_Executante))]
    colunas_tab2_horas_exec = list(tab2_horas_exec) #Lista com os nomes das colunas da tabela
    colunas_tab2_horas_exec.remove("Título") #Remove o nome da coluna título da ação da lista de nomes das colunas
    #Transforma a tabela de horas executadas agrupando as colunas de mês-ano
    lista_de_meses = periodos(hoje) #Lista com os meses de jan do ano atual até março do próximo ano
    lista_col_tab_horas_exec = ["Título","Situação","Classe da Inspeção", "Data de início", "Data limite", "Prazo_em_Dias", "Total de horas previstas","Unidade_executante"]
                
    tab2_horas_exec = pd.melt(tab2_horas_exec, id_vars=lista_col_tab_horas_exec, value_vars=lista_de_meses,var_name="Mes_execucao",value_name='Horas_exec_acum_mes')
    tab2_horas_exec = tab2_horas_exec.loc[tab2_horas_exec["Horas_exec_acum_mes"]>0]
    
    st.session_state["tab2_horas_exec"] = tab2_horas_exec
    
    #Tabelas com as capacidades mensais de horas por UD
    
    df_cap_mens_s = st.session_state["df_cap_mens_s"]
    df_cap_mens_t = st.session_state["df_cap_mens_t"]
    df_cap_mens_o = st.session_state["df_cap_mens_o"]
    
    df_exec_acum_UD = st.session_state["df_exec_acum_UD"] 
    df_horas_exec_mes_UD = st.session_state["df_horas_exec_mes_UD"]
    
    #Criando tabelas com as horas executadas por mês, agrupadas por UD, mas só com a situação
    #conforme filtrado no menu lateral
    
   
    df_exec_acum_UD_agrupada_situacao = df_exec_acum_UD.loc[(df_exec_acum_UD["Situação"].isin(fStatus))]
    df_exec_acum_UD_agrupada_situacao = df_exec_acum_UD_agrupada_situacao.groupby(["Unidade_executante","Classe da Inspeção","Mes_execucao"]).agg('sum')
    #A coluna de situação é removida para poder juntar com a tabela de capcidade por UD por mês,
    #que não pode ser separada pela situação da ação.
    df_exec_acum_UD_agrupada_situacao.drop(['Situação'],axis=1,inplace=True,errors='ignore' )
    
    st.session_state["df_exec_acum_UD_agrupada_situacao"] = df_exec_acum_UD_agrupada_situacao
    
    #Fazendo o mesmo com a tabela de horas executadas dentro de cada mês
    df_horas_exec_mes_UD_agrupada_situacao = df_horas_exec_mes_UD.loc[(df_exec_acum_UD["Situação"].isin(fStatus))]
    df_horas_exec_mes_UD_agrupada_situacao = df_horas_exec_mes_UD_agrupada_situacao.groupby(["Unidade_executante","Classe da Inspeção","Mes_execucao"]).agg('sum')
    df_horas_exec_mes_UD_agrupada_situacao.drop(["Situação"],axis=1,inplace=True,errors='ignore')
  

    tab3_cap_horas_mensais_s = df_cap_mens_s
    lista_col_tab_cap_mensal = ["Unidade_executante","Classe da Inspeção"]
    tab3_cap_horas_mensais_s = pd.melt(tab3_cap_horas_mensais_s, id_vars=lista_col_tab_cap_mensal, value_vars=lista_de_meses,var_name="Mes_execucao",value_name='CapH_Mes')
    
    tab3_cap_horas_mensais_t = df_cap_mens_t
    tab3_cap_horas_mensais_t = pd.melt(tab3_cap_horas_mensais_t, id_vars=lista_col_tab_cap_mensal, value_vars=lista_de_meses,var_name="Mes_execucao",value_name='CapH_Mes')
    
    tab3_cap_horas_mensais_o = df_cap_mens_o
    tab3_cap_horas_mensais_o = pd.melt(tab3_cap_horas_mensais_o, id_vars=lista_col_tab_cap_mensal, value_vars=lista_de_meses,var_name="Mes_execucao",value_name='CapH_Mes')

    #Juntando as tabelas de capacidade mensal de horas de execução por mês e Unidade executante
    tab3_cap_horas_mensais_ud = pd.concat([tab3_cap_horas_mensais_s,tab3_cap_horas_mensais_t,tab3_cap_horas_mensais_o],axis=0) #junta uma tabela em cima da outra 
    #Criando coluna com a capacidade acumulada de horas
     
    tab3_cap_horas_mensais_ud['Cap_H_Mes_Acum'] = tab3_cap_horas_mensais_ud.groupby(['Unidade_executante',"Classe da Inspeção"])['CapH_Mes'].cumsum()
    lista_campos_tab3_cap_horas_mensais_ud = list(tab3_cap_horas_mensais_ud)
    
     
    #Juntar lado a lado a df_exec_acum_UD_agrupada_situacao (coluna CargaH_Mes_Acum) com a tab3_cap_horas_mensais_ud
    tab3_cap_horas_mensais_ud = tab3_cap_horas_mensais_ud.merge(df_exec_acum_UD_agrupada_situacao,on=["Unidade_executante","Classe da Inspeção","Mes_execucao"],how="outer")
    
    #Juntar lado a lado a df_horas_exec_mes_UD_agrupada_situacao (coluna CargaH_Mes) com a tab3_cap_horas_mensais_ud
    tab3_cap_horas_mensais_ud = tab3_cap_horas_mensais_ud.merge(df_horas_exec_mes_UD_agrupada_situacao,on=["Unidade_executante","Classe da Inspeção","Mes_execucao"],how="outer")
    #Adicionando uma segunda coluna de classe de inspeção para facilitar agrupamento de cores no gráfico
    tab3_cap_horas_mensais_ud["Classe da Inspeção 2"]=(tab3_cap_horas_mensais_ud["Classe da Inspeção"] + "_2")
    
    #Adicionando coluna auxiliar para calcular a carga e capacidade de horas do mês atual em diante
    #A coluna tem a quantidade de meses futuros a contar do mês atual
    tab3_cap_horas_mensais_ud["Mes_execucao_2"] = pd.to_datetime(tab3_cap_horas_mensais_ud["Mes_execucao"])
    tab3_cap_horas_mensais_ud["Mes_atual"] = hoje
    tab3_cap_horas_mensais_ud["Qtd_Meses_Futuros"] = tab3_cap_horas_mensais_ud["Mes_execucao_2"].dt.to_period('M').astype(int) - tab3_cap_horas_mensais_ud["Mes_atual"].dt.to_period('M').astype('int64')
    tab3_cap_horas_mensais_ud.drop(["Mes_execucao_2","Mes_atual"],axis=1,inplace=True,errors='ignore') 
    
    
    st.session_state["tab3_cap_horas_mensais_ud"] = tab3_cap_horas_mensais_ud
    
    
    #Criando uma versão filtrada da tabela tab3_cap_horas_mensais_ud para fazer o gráfico
    tab3_cap_horas_mensais_ud_filtrada =tab3_cap_horas_mensais_ud.loc[(tab3_cap_horas_mensais_ud["Classe da Inspeção"].isin(fClasseAcao))&(tab3_cap_horas_mensais_ud["Unidade_executante"].isin(fUnidade_Executante))]
    
    #Criando uma coluna com a carga de horas acumlada e a capacidade de horas acumuladas
    #contadas a partir do mês atual e para os meses futuros
    tab3_cap_horas_mensais_ud_filtrada.sort_values(by=["Mes_execucao"], ascending=True)
    tab3_cap_horas_mensais_ud_filtrada["Grupo"]= tab3_cap_horas_mensais_ud_filtrada["Unidade_executante"] + "_" + tab3_cap_horas_mensais_ud_filtrada["Classe da Inspeção"]
    tab3_cap_horas_mensais_ud_filtrada["Cap_H_Mes_Acum_Futuros"] = tab3_cap_horas_mensais_ud_filtrada['CapH_Mes'].where(tab3_cap_horas_mensais_ud_filtrada['Qtd_Meses_Futuros'] >= 0, 0).groupby(tab3_cap_horas_mensais_ud_filtrada['Grupo']).cumsum()
    
    tab3_cap_horas_mensais_ud_filtrada.sort_values(by=["Mes_execucao"], ascending=True)
    tab3_cap_horas_mensais_ud_filtrada["CargaH_Mes_Acum_Futuros"] = tab3_cap_horas_mensais_ud_filtrada['CargaH_Mes'].where(tab3_cap_horas_mensais_ud_filtrada['Qtd_Meses_Futuros'] >= 0, 0).groupby(tab3_cap_horas_mensais_ud_filtrada['Grupo']).cumsum()

 
    st.session_state["tab3_cap_horas_mensais_ud_filtrada"] = tab3_cap_horas_mensais_ud_filtrada
    
    
    
    
    
    


#-----------------------
#ROTINAS DE GRÁFICOS
#-----------------------

def graf_total_horas_venc_mes(tab_horas_previstas,cor_grafico,altura_grafico,u_execs):
# Gráfico 1 - Total de horas somadas das ações, por classe de inspeção, por mês de data limite
 titulo1 = alt.TitleParams(f"TOTAL DE HORAS POR MÊS DE VENCIMENTO DAS AÇÕES'",
     subtitle=[f"Unidades Executantes: {u_execs}",
               f"Status das ações: {fStatus}"])
       
 graf1_vencimento_por_mes = alt.Chart(tab_horas_previstas).mark_bar(
    color= cor_grafico,
    cornerRadiusTopLeft=9,
    cornerRadiusTopRight=9,
    ).encode(
    x = alt.X("Classe da Inspeção",type="nominal"),
    y = alt.Y('sum(Total de horas)',title="Soma do Total de Horas Previstas por Mês e Classe de Inspeção"),
    column=alt.Column('Mes_Ano_String',title="Ano e Mês de Vencimento das Ações",type="nominal",header=alt.Header(orient='top')),
    color= "Classe da Inspeção",
    tooltip=[ alt.Tooltip("Mes_Ano_String", title="Ano/Mês de Vencimento") , 
            alt.Tooltip("sum(Total de horas)",title="Soma do Total de Horas"),"Classe da Inspeção",
            alt.Tooltip("count(Título)",title="Quantidade de Ações")]
    ).properties(height=altura_grafico, width=80, title=titulo1
    ).configure_axis(grid=False).configure_view(strokeWidth=0)
 rot1_mes_ano = graf1_vencimento_por_mes.mark_text(radius=210, size=14).encode(text='Mes_Ano')
 rot1_horas = graf1_vencimento_por_mes.mark_text(radius=210, size=14).encode(text='sum(Total de horas)')

 st.altair_chart(graf1_vencimento_por_mes,use_container_width=False)


def graf_qtd_acoes_venc_mes(tab_horas_previstas,cor_grafico,altura_grafico,u_execs):
# Gráfico 2 - Quantidade de ações por classe de inspeção, por mês de data limite
    titulo2 = alt.TitleParams(f"QUANTIDADE DE AÇÕES POR MÊS DE VENCIMEMTO",
     subtitle=[f"Unidades Executantes: {u_execs}",
               f"Status das ações: {fStatus}"])
    graf2_qtd_acoes_por_mes_vencimento = alt.Chart(tab_horas_previstas).mark_bar(
        color= cor_grafico,
        cornerRadiusTopLeft=9,
        cornerRadiusTopRight=9,
    ).encode(
        x = alt.X("Classe da Inspeção", type="nominal",),
        y = alt.Y("count(Título)",title="Quantidade de Ações"), #Qtd de ações vencendo em cada mês
        column=alt.Column('Mes_Ano_String',title="Ano e Mês de Vencimento das Ações",type="nominal",header=alt.Header(orient='top')),
        color= "Classe da Inspeção",
        tooltip=[ alt.Tooltip("Mes_Ano_String", title="Ano/Mês de Vencimento") ,
                alt.Tooltip("sum(Total de horas)",title="Soma do Total de Horas"),"Classe da Inspeção",
                alt.Tooltip("count(Título)",title="Quantidade de Ações")]
    ).properties(height=altura_grafico, width=80, title=titulo2
    ).configure_axis(grid=False
    ).configure_view(strokeWidth=0    )

    st.altair_chart(graf2_qtd_acoes_por_mes_vencimento,use_container_width=False)

     
def graf_cap_vs_carga_no_mes_por_UD (tab_cap_horas_mensais_ud,cor_grafico,altura_grafico,u_execs,classe_insp):
#Gráfico comparando a capacidade em horas em cada mês versus a carga de horas de execução estimadas para cada mês
     titulo4 = alt.TitleParams(f"CAPACIDADE E CARGA MENSAIS.",
     subtitle=[f"Unidades Executantes: {u_execs}", 
            f"Status das ações: {fStatus}",    
            "Gráfico comparando a capacidade em horas em cada mês versus a carga de horas de execução estimadas para cada mês"])
    
     base = alt.Chart(tab_cap_horas_mensais_ud).encode(x="Classe da Inspeção:N")
     #Gráfico da capacidade de horas por mês
     larg_coluna = 20
     graf_cap_mes = base.mark_bar(
        color= cor_grafico,
        cornerRadiusTopLeft=9,
        cornerRadiusTopRight=9,
        ).encode(
        y = alt.Y("sum(CapH_Mes)",title="Capacidade de Horas"),
        color="Classe da Inspeção:N",
        tooltip=[ alt.Tooltip("Mes_execucao", title="Ano/Mês de Execução"),  
                  alt.Tooltip("sum(CapH_Mes)",title="Cap Mensal (Horas)",format= ".2f"),
                  "Classe da Inspeção",   
                ]
      #  column= 'Mes_execucao:N'
     ).properties(
        width=alt.Step(larg_coluna)  # controls width of bar.
     ) 
        
     #Gráfico da carga de horas por mês
     graf_carga_mes = base.mark_circle(opacity=0.99, filled=True,stroke = "black",strokeWidth=2).encode(
        y = alt.Y("sum(CargaH_Mes)",title="Carga Mensal (Horas)"),
        size="sum(CargaH_Mes)",
        color="Classe da Inspeção",
        tooltip=[ alt.Tooltip("Mes_execucao", title="Ano/Mês de Execução"),  
                  alt.Tooltip("sum(CargaH_Mes)",title="Carga Mensal (Horas)",format= ".2f"),
                               "Classe da Inspeção"]
        )    
   
  
     chart = alt.layer(graf_cap_mes, graf_carga_mes, data=tab_cap_horas_mensais_ud).facet(
        column="Mes_execucao:N"
     ).properties(title=titulo4)  
        
     st.altair_chart(chart, theme=None, use_container_width=True)    
    

     
def graf_cap_vs_carga_acum_mes_por_UD (tab_cap_horas_mensais_ud,cor_grafico,altura_grafico,u_execs,classe_insp):
#Gráfico comparando a capacidade em horas em cada mês versus a carga de horas de execução estimadas para cada mês
     titulo4 = alt.TitleParams(f"CAPACIDADE E CARGA ACUMULADAS ATÉ CADA MÊS.",
     subtitle=[f"Unidades Executantes: {u_execs}", 
               f"Status das ações: {fStatus}",    
            "Gráfico comparando os valores acumulados até cada mês da capacidade em horas e da carga de horas de execução estimadas"])
    
     base = alt.Chart(tab_cap_horas_mensais_ud).encode(x="Classe da Inspeção:N")
     #Gráfico da capacidade de horas por mês
     larg_coluna = 20
     graf_cap_mes = base.mark_bar(
        color= cor_grafico,
        cornerRadiusTopLeft=9,
        cornerRadiusTopRight=9,
        ).encode(
        y = alt.Y("sum(Cap_H_Mes_Acum)",title="Capacidade Acumulada de Horas"),
        color="Classe da Inspeção:N",
        tooltip=[ alt.Tooltip("Mes_execucao", title="Ano/Mês de Execução"),  
                  alt.Tooltip("sum(Cap_H_Mes_Acum)",title="Cap Acum Mensal (Horas)",format= ".2f"),
                  "Classe da Inspeção",   
                ]
      #  column= 'Mes_execucao:N'
     ).properties(
        width=alt.Step(larg_coluna)  # controls width of bar.
     ) 
        
     #Gráfico da carga de horas por mês
     graf_carga_mes = base.mark_circle(opacity=0.99, filled=True,stroke = "black",strokeWidth=2).encode(
        y = alt.Y("sum(CargaH_Mes_Acum)",title="Carga Acumulada Mensal (Horas)"),
        size="sum(CargaH_Mes_Acum)",
        color="Classe da Inspeção",
        tooltip=[ alt.Tooltip("Mes_execucao", title="Ano/Mês de Execução"),  
                  alt.Tooltip("sum(CargaH_Mes_Acum)",title="Carga Acum Mensal (Horas)",format= ".2f"),
                                "Classe da Inspeção"]
        )    
   
  
     chart = alt.layer(graf_cap_mes, graf_carga_mes, data=tab_cap_horas_mensais_ud).facet(
        column="Mes_execucao:N"
     ).properties(title=titulo4)  
        
     st.altair_chart(chart, theme=None, use_container_width=True)    
    



     
def graf_cap_vs_carga_acum_meses_futuros_UD (tab_cap_horas_mensais_ud,cor_grafico,altura_grafico,u_execs,classe_insp):
#Gráfico comparando as capacidades acumuladas em horas até cada mês das horas de carga versus horas de capacidade.
#Aqui só aparece do mês atual em diante 
     #Só inclui os dados que vão desde o mês atual até o mês máximo da base de dados (março do ano seguinte)
     tab_cap_horas_mensais_ud = tab_cap_horas_mensais_ud.loc[tab_cap_horas_mensais_ud["Qtd_Meses_Futuros"]>=0]
     titulo4 = alt.TitleParams(f"CAPACIDADE E CARGA ACUMULADAS - DO MÊS ATUAL EM DIANTE.",
     subtitle=[f"Unidades Executantes: {u_execs}", 
               f"Status das ações: {fStatus}",    
            "Gráfico comparando os valores acumulados até cada mês da capacidade em horas e da carga de horas de execução estimadas",
            "OBS: DO MÊS ATUAL EM DIANTE."])
    
     base = alt.Chart(tab_cap_horas_mensais_ud).encode(x="Classe da Inspeção:N")
     #Gráfico da capacidade de horas por mês
     larg_coluna = 20
     graf_cap_mes = base.mark_bar(
        color= cor_grafico,
        cornerRadiusTopLeft=9,
        cornerRadiusTopRight=9,
        ).encode(
        y = alt.Y("sum(Cap_H_Mes_Acum_Futuros)",title="Capacidade Acumulada de Horas - MESES FUTUROS"),
        color="Classe da Inspeção:N",
        tooltip=[ alt.Tooltip("Mes_execucao", title="Ano/Mês de Execução"),  
                  alt.Tooltip("sum(Cap_H_Mes_Acum_Futuros)",title="Cap Acum Mensal (Horas)",format= ".2f"),
                  "Classe da Inspeção",   
                ]
      #  column= 'Mes_execucao:N'
     ).properties(
        width=alt.Step(larg_coluna)  # controls width of bar.
     ) 
        
     #Gráfico da carga de horas por mês
     graf_carga_mes = base.mark_circle(opacity=0.99, filled=True,stroke = "black",strokeWidth=2).encode(
        y = alt.Y("sum(CargaH_Mes_Acum_Futuros)",title="Carga Acumulada Mensal (Horas)"),
        size="sum(CargaH_Mes_Acum)",
        color="Classe da Inspeção",
        tooltip=[ alt.Tooltip("Mes_execucao", title="Ano/Mês de Execução"),  
                  alt.Tooltip("sum(CargaH_Mes_Acum_Futuros)",title="Carga Acum Mensal (Horas)",format= ".2f"),
                                "Classe da Inspeção"]
        )    
     
     chart = alt.layer(graf_cap_mes, graf_carga_mes, data=tab_cap_horas_mensais_ud).facet(
         column="Mes_execucao:N").properties(title=titulo4)  
        
     st.altair_chart(chart, theme=None, use_container_width=True)    
    

      
      
#------------------------

    
    
#------------------------





#-----------------
#ROTINA PRINCIPAL
#-----------------
def mostra_dados_filtrados():
    #Função que é chamada após clicar no botão de submeter no formulário                   
    
    lista_de_meses = periodos(hoje) 
    
    df_horas_exec =  st.session_state["df_horas_exec"]    
    df_cap_mens_s =  st.session_state["df_cap_mens_s"]  
    df_cap_mens_t =  st.session_state["df_cap_mens_t"]  
    df_cap_mens_o =  st.session_state["df_cap_mens_o"]  
    df_exec_acum_UD = st.session_state["df_exec_acum_UD"] 
    df_horas_exec_mes_UD = st.session_state["df_horas_exec_mes_UD"]
    
    
    cria_tabelas_dos_graficos()
    
        
    
    #Filtra o dataframe carregado do arquivo com as opções selecionadas na barra lateral
    df_filtrado = df.query("Situação == @fStatus & Mes_Ano_String==@fMesAno & `Classe da Inspeção`==@fClasseAcao & Unidade_executante == @fUnidade_Executante") #query a ser avaliada. @ usada para referenciar variáveis do código

    #Cria o dataset depois de filtradas as linhas e colunas
    df_exibido = df_filtrado.filter(items=selecao_colunas)
    #Cria as tabelas usadas nos gráficos
    
              
  
    
    if  arq_excel_1 != None:
         #Cartão mostrando a quantidade de ações selecionadas pelos filtros
         st.write('**AÇÕES SELECIONADAS:**')
         st.info(f"Quantidade de ações selecionadas na tabela: {len(df_exibido)}")
         st.info(f"Status das ações selecionadas: {fStatus}")

         #Mostra na tela o dataset depois de filtradas as linhas e colunas
         df_exibido    
         
         
         #GRÁFICOS   
         #Definições gerais dos gráficos
         cor_grafico = '#9DD1F1'
         altura_grafico=500

         if todas > 0: #Se todas as UD´s nforem selecionadas para exibição dos dados
                u_execs = todas_UDs
         else:
                u_execs = fUnidade_Executante
              
                
         tab2_horas_exec = st.session_state["tab2_horas_exec"]
         tab3_cap_horas_mensais_ud_filtrada = st.session_state["tab3_cap_horas_mensais_ud_filtrada"]
         
         # Gráfico 1 - Total de horas somadas das ações, por classe de inspeção, por mês de data limite
         tab1_horas_previstas = st.session_state["tab1_horas_previstas"]
         graf_total_horas_venc_mes(tab1_horas_previstas,cor_grafico,altura_grafico,u_execs)
          
         # Gráfico 2 - Quantidade de ações por classe de inspeção, por mês de data limite
         graf_qtd_acoes_venc_mes(tab1_horas_previstas,cor_grafico,altura_grafico,u_execs)
         
      
         #Gráfico 4 - Comparação, mês a mês da carga demandada de horas versus a capacidade de horas naquele mes
         graf_cap_vs_carga_no_mes_por_UD (tab3_cap_horas_mensais_ud_filtrada,cor_grafico,altura_grafico,u_execs,fClasseAcao)
         
         #Gráfico 5 - Comparação dos valores acumulados ao longo dos meses
         #da carga demandada acumulada em horas versus a capacidade acumulada em horas
         graf_cap_vs_carga_acum_mes_por_UD (tab3_cap_horas_mensais_ud_filtrada,cor_grafico,altura_grafico,u_execs,fClasseAcao)
        
         #Gráfico 6 - comparando as capacidades acumuladas em horas até cada mês das horas de carga versus horas de capacidade.
         #Aqui só aparece do mês atual em diante 
         graf_cap_vs_carga_acum_meses_futuros_UD (tab3_cap_horas_mensais_ud_filtrada,cor_grafico,altura_grafico,u_execs,fClasseAcao)

  
#Criando o Sidebar com os filtros


with st.sidebar:
    #atualiza_df = 0  #Se for zero, as tabelas auxiliares ainda não foram criadas
    #botao_form = False
    #Carrega o logotipo
    logo_teste = Image.open('./Imagem1.jpg')
    st.image(logo_teste, width=300)
    st.subheader('MENU - AÇÕES DE FISCALIZAÇÃO')
    

    #Botão para carregar o arquivo excel com os dados
    arq_excel_1 = st.file_uploader(
    "Escolha o arquivo Excel: ", 
    type=["xlsx"],
    accept_multiple_files=False      #Carrega só um arquivo
    )
    if  arq_excel_1 == None:
        #Apaga todo as informações do session_state
        # Delete all the items in Session state
        for key in st.session_state.keys():
            del st.session_state[key]
            
        #Inicializando os valores no session state:    
        if "atualiza_df" not in st.session_state:
            st.session_state["atualiza_df"] = 0
        if "df" not in st.session_state:    
            st.session_state["df"] = pd.DataFrame() #Esvazia os dataframes toda vez que se carrega um novo aqruivo excel
    #Só carrega os menus de filtros caso tenha sido carregado algum arquivo excel antes
    if  arq_excel_1 != None:
        df = st.session_state["df"]    
        if  st.session_state["atualiza_df"] == 0: #Só cria as tabelas auxiliares uma única vez, quando um novo arquivo excel é carregado.
            df = busca_df()            
            cria_tabelas_auxiliares(df)
            df = st.session_state["df"]  
            st.session_state["atualiza_df"] = st.session_state["atualiza_df"] +1 

        #Listas com os campos da tabela para uso nos menus de seleção
        lista_mes_ano = pd.Series(df["Mes_Ano"].unique()).sort_values()
        lista_mes_ano = lista_mes_ano.dropna()  #Remove valores ausentes
        lista_mes_ano_string = lista_mes_ano.astype(str) #converte para string
                
        #Cria lista com as classes de ações    
        lista_classe_acoes = df["Classe da Inspeção"].unique()

        #Cria lista com os status das ações
        lista_situacao = df["Situação"].unique()
        lista_situacao = sorted(lista_situacao)  #ordena por ordem alfabética
        lista_situacao_agrupada = ["ABERTAS","ENCERRADAS","TODAS"]
        lista_situacao_abertas = ["Aguardando conferência","Devolvida ao Centralizador", "Em andamento", 
                                "Em planejamento", "Horas Alocadas", "Rascunho"]
        lista_situacao_encerradas = ["Aguardando aprovação","Concluída"]
        lista_situacao_todas = ["Aguardando aprovação",
                                "Aguardando conferência",
                                "Cancelada", "Concluída", 
                                "Devolvida ao Centralizador", "Em andamento", 
                                "Em planejamento", "Horas Alocadas", "Rascunho","Transferida"]
        

        #Cria lista com os as GRé e UO´s executantes das ações
        lista_executantes = df["Unidade_executante"].unique()
        lista_executantes = sorted(lista_executantes) #ordena por ordem alfabética
        lista_executantes.append("TODAS")
        
        #Criação do formulário. Os dados só são atualizados após
        #clicar no botão de submeter
    
        with st.form("Formulário: selecione as opções abaixo e clique em ´Enviar´:"):
            
            st.write("GRÁFICOS e TABELA:")
            #Filtro do status da ação
            fStatus = st.selectbox("Status das Ações:",
                                        lista_situacao_agrupada,
                                        index=0  #Valor default da lista
            ) #como default deixa todos pré-selecionados
            if fStatus == "ABERTAS":
                fStatus = lista_situacao_abertas
            elif fStatus == "ENCERRADAS":   
                    fStatus = lista_situacao_encerradas
            else:
                fStatus = lista_situacao_todas    
                    
            #Filtro da classe da ação: técnica, serviços, tributária:
            fClasseAcao =st.multiselect("Classe das Ações:",
                        options=lista_classe_acoes,
                        default=["Serviço","Técnica","Tributária"]        
            )
            #Filtro da unidade executante:
            fUnidade_Executante =st.multiselect("Unidades Executantes:",
                            options=lista_executantes,
                            default=["TODAS"]        
            )
            st.divider()
            st.write("TABELA:")            
            #Filtro das colunas exibidas
            todas_UDs = "TODAS" #variável para selecionar todas as unidades executantes
            todas = fUnidade_Executante.count(todas_UDs)
            if todas > 0: #Se todas as UD´s nforem selecionadas para exibição dos dados
                fUnidade_Executante = lista_executantes
                fUnidade_Executante.remove("TODAS")
            #Filtro do mês/ano da data limite
            fMesAno = st.multiselect("Mês/Ano da Data Limite da Ação:",
                options=lista_mes_ano_string,
                default= mes_atual #Como default mostra o mês atual        
                )
            if fMesAno == []:
                fMesAno = lista_mes_ano_string.to_list()  #Se deixar a data em branco, busca de todas as datas
            #Adiciona na sidebar a seleção de colunas a exibir
            selecao_colunas = st.multiselect(
                            "Selecione as colunas para exibição:",
                            options = sorted(list(df)),
                            default=["Título","Situação","Subtema","Data limite","Descrição","Classe da Inspeção"]
                            )
                            
            #Chama a rotina principal com os dados filtrados a partir das seleções
            botao_form = st.form_submit_button("Enviar")
if botao_form:  #só submete os parâmetros do filtro depois de clicar o botão
    st.session_state["atualiza_df"] = st.session_state["atualiza_df"] +1
    mostra_dados_filtrados() #chama a função que mostra os dados preenchidos
           
           
