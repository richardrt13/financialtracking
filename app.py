import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
from datetime import datetime
import os
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import google.generativeai as genai 
import requests
from dotenv import load_dotenv
from auth_manager import AuthManager
from custom_select import custom_select
from financial_advisor import FinancialAdvisor
from financial_tracker import FinancialTracker
from purchase_intelligence_interface import purchase_intelligence_interface
from login_page import login_page

mongo_uri = st.secrets["mongo_uri"]
                    
    
def check_mongodb_connection():
    """
    Verifica a conexão com o MongoDB
    """
    try:
        client = MongoClient(mongo_uri)
        client.admin.command('ismaster')
        #st.success("Conexão com MongoDB estabelecida com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro de conexão com MongoDB: {e}")
        st.warning("Verifique sua connection string e configurações de rede.")
        return False

# def login_page():
#     """Render login page"""
#     st.title("🔐 Login")
    
#     # Initialize auth manager
#     auth_manager = AuthManager(st.secrets["mongo_uri"])
    
#     # Check if already logged in
#     current_user = auth_manager.get_current_user()
#     if current_user:
#         st.success(f"Você já está logado como {current_user['name']}!")
#         if st.button("Sair"):
#             auth_manager.logout_user()
#             st.rerun()
#         return True
    
#     # Login/Register tabs
#     tab1, tab2 = st.tabs(["Login", "Cadastro"])
    
#     with tab1:
#         with st.form("login_form"):
#             email = st.text_input("Email")
#             password = st.text_input("Senha", type="password")
#             remember_me = st.checkbox("Lembrar-me neste dispositivo", 
#                                     help="Ninguém merece fazer login toda hora, né?!")
            
#             # Adiciona mensagem sobre usuário legado
#             if email == "admin@example.com":
#                 st.info("Use este login para acessar os dados existentes.")
                
#             submitted = st.form_submit_button("Entrar")
            
#             if submitted:
#                 success, result = auth_manager.login_user(email, password, remember_me)
#                 if success:
#                     st.session_state['token'] = result
#                     st.success("Login realizado com sucesso!")
#                     st.rerun()
#                 else:
#                     st.error(result)
    
#     with tab2:
#         with st.form("register_form"):
#             name = st.text_input("Nome")
#             email = st.text_input("Email")
#             password = st.text_input("Senha", type="password")
#             password_confirm = st.text_input("Confirme a senha", type="password")
#             submitted = st.form_submit_button("Cadastrar")
            
#             if submitted:
#                 if password != password_confirm:
#                     st.error("As senhas não conferem!")
#                 elif not name:
#                     st.error("Nome é obrigatório!")
#                 else:
#                     success, result = auth_manager.register_user(email, password, name)
#                     if success:
#                         st.success("Cadastro realizado com sucesso! Faça login para continuar.")
#                     else:
#                         st.error(result)

def main():
    """
    Função principal do aplicativo Streamlit
    """
    # Initialize auth manager
    auth_manager = AuthManager(st.secrets["mongo_uri"])
    
    # Check if user is logged in
    if 'token' not in st.session_state:
        # Only show login page if not logged in
        login_page()
        return
        
    # Get current user
    current_user = auth_manager.get_current_user()
    if not current_user:
        st.error("Erro de autenticação")
        # Clear invalid token
        if 'token' in st.session_state:
            del st.session_state['token']
        st.rerun()
        return
        
    # Display welcome message
    st.sidebar.write(f"👤 Olá, {current_user['name']}!")
    if st.sidebar.button("Logout"):
        auth_manager.logout_user()
        st.rerun()
    
    # Initialize the financial tracker with user context
    tracker = FinancialTracker(user_id=str(current_user['_id']))
    
    # Menu de navegação
    menu = ["Análise Financeira", "Dicas Financeiras", 
            "Gerenciar Transações", "Inteligência de Compra"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    st.title("🏦 Gestor Financeiro Inteligente")

    
    if choice == "Análise Financeira":
        st.subheader("📊 Consolidado Financeiro")
        
        # Filtros mais flexíveis
        col1, col2 = st.columns(2)
        
        with col1:
            current_year = datetime.now().year 
            options = [current_year, current_year + 1] + list(range(current_year - 1, 2019, -1)) 
            selected_year = st.selectbox("Ano", options)
        
        with col2:
            selected_month = st.selectbox("Mês", 
                ['Todos'] + 
                ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'])
        
        # Recupera transações com filtros
        df_transactions = tracker.get_transactions_for_display(selected_year)
        
        if selected_month != 'Todos':
            df_transactions = df_transactions[df_transactions['month'] == selected_month]
        
        if not df_transactions.empty:
            # Sumário de métricas
            st.subheader("Resumo Financeiro")
            
            # Métricas de pagamentos
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_receita = df_transactions[df_transactions['type'] == 'Receita']['value'].sum()
                st.metric(label="Total Receitas", value=f"R$ {total_receita:.2f}")
                
            with col2:
                total_despesa = df_transactions[df_transactions['type'] == 'Despesa']['value'].sum()
                paid_expenses = df_transactions[(df_transactions['type'] == 'Despesa') & 
                                             (df_transactions['paid'])]['value'].sum()
                pending_expenses = total_despesa - paid_expenses
                
                st.metric(label="Total Despesas",
                         value=f"R$ {total_despesa:.2f}",
                         delta=f"R$ {pending_expenses:.2f} pendente",
                         delta_color="inverse")
                
            with col3:
                payment_ratio = (paid_expenses / total_despesa * 100) if total_despesa > 0 else 0
                st.metric(label="Compromissos Cumpridos",
                         value=f"{payment_ratio:.1f}%",
                         delta=f"{100-payment_ratio:.1f}% pendente")
                
            col4, col5 = st.columns(2)

            with col4:
                total_investimento = df_transactions[df_transactions['type'] == 'Investimento']['value'].sum()
                paid_investimento = df_transactions[(df_transactions['type'] == 'Investimento') & 
                                             (df_transactions['paid'])]['value'].sum()
                pending_investimento = total_investimento - paid_investimento
                
                st.metric(label="Total Investimentos",
                         value=f"R$ {total_investimento:.2f}",
                         delta=f"R$ {pending_investimento:.2f} pendente",
                         delta_color="inverse")

            with col5:
                saldo_livre = total_receita - total_despesa - total_investimento
                delta_saldo = f"Positivo" if saldo_livre >= 0 else "Negativo"
                delta_color = "normal" if saldo_livre >= 0 else "inverse"
    
                st.metric(label="Saldo Livre",
                          value=f"R$ {saldo_livre:.2f}",
                          delta=delta_saldo,
                          delta_color=delta_color)

            with st.expander("➕ Adicionar Nova Transação"):
                col1, col2 = st.columns(2)
        
                with col1:
                    year = st.number_input("Ano", min_value=2020, max_value=2030, value=datetime.now().year)

                    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                          'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

                    mes_atual = datetime.now().month - 1


                    month = st.selectbox("Mês", meses, index=mes_atual)
                    #month = st.selectbox("Mês", 
                    #    ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                      #   'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'])
        
                    
                    # Primeiro seleciona o tipo
                    type_transaction = st.selectbox("Tipo", ['Receita', 'Despesa', 'Investimento'])
                    
                    # Depois seleciona a categoria baseada no tipo
                    if type_transaction == 'Receita':
                        category = st.selectbox("Categoria", 
                            ['Salário - 1ª Parcela', 'Salário - 2ª Parcela', '13º Salário', 'Férias', 'Outros'])
                    elif type_transaction == 'Despesa':
                        category = st.selectbox("Categoria", 
                            ['Cartão', 'Internet', 'Tv a Cabo', 'Manutenção do carro', 'Combustível', 'Gás',
                             'Financiamento', 'Aluguel', 'Condomínio', 'Mercado', 'Cursos', 'Anuidade', 'Outros'])
                    else:  # Investimento
                        category = st.selectbox("Categoria", 
                            ['Renda Fixa', 'Renda Variável'])
                
                with col2:
                    value = st.number_input("Valor", min_value=0.0, format="%.2f")
                    repeat_months = st.number_input("Repetir por quantos meses?", min_value=1, max_value=36, value=1)
                    
                    # Campo para observações
                    observation = st.text_area("Observações", 
                        placeholder="Ex: Pagamento adiantado, Despesa extra, Bônus especial...")
                
                if st.button("Adicionar Transação"):
                    current_month_index = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                                       'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'].index(month)
                    current_year = year
                    
                    for i in range(repeat_months):
                        tracker.add_transaction(
                            month=['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                                 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][current_month_index],
                            year=current_year,
                            category=category,
                            type=type_transaction,
                            value=value,
                            observation=observation
                        )
                        
                        # Avança para o próximo mês
                        current_month_index += 1
                        if current_month_index >= 12:
                            current_month_index = 0
                            current_year += 1
                    
                    st.success(f"Transação adicionada com sucesso para {repeat_months} meses!")
            
            # Tabela detalhada com status de pagamento
            st.subheader("Detalhamento de Transações")
            
            # Prepara dados para exibição
            display_df = df_transactions[['month', 'category', 'type', 'observation', 'value', 'paid']].copy()
            
            # Adiciona ícones para status de pagamento
            def format_payment_status(row):
                #if row['type'] != 'Despesa':
                    #return "N/A"
                return "✅" if row['paid'] else "⏳"
            
            display_df['Status'] = display_df.apply(format_payment_status, axis=1)
            
            # Remove coluna 'paid' da exibição
            display_df = display_df.drop('paid', axis=1)

            st.dataframe(
                display_df.style.format({'value': 'R$ {:.2f}'})
                .map(lambda x: 'color: green' if x == '✅' else 'color: orange', subset=['Status'])
            )
            
            if st.checkbox("Gerenciar Status de Compromissos"):
                st.subheader("Atualizar Status de Compromissos")
            
                unpaid_transactions = df_transactions[
                    (df_transactions['paid'].fillna(False) == False)
                ][['_id', 'month', 'category', 'type', 'value', 'paid']]
            
                if not unpaid_transactions.empty:
                    for _, row in unpaid_transactions.iterrows():
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
                        with col1:
                            st.write(f"{row['month']} - {row['category']}")
                        with col2:
                            st.write(f"{row['type']}")  # Adicionado o tipo
                        with col3:
                            st.write(f"R$ {row['value']:.2f}")
                        with col4:
                            button_text = {
                                'Receita': '✅ Marcar como Recebido',
                                'Despesa': '✅ Marcar como Pago',
                                'Investimento': '✅ Marcar como Realizado'
                            }.get(row['type'], '✅ Marcar como Concluído')
            
                            if st.button(button_text, key=row['_id']):
                                tracker.update_payment_status(row['_id'])
                                st.success(f"{row['type']} marcado como concluído!")
                                st.rerun()
                else:
                    st.info("Não há movimentações pendentes no período selecionado! 🎉")

            
    elif choice == "Dicas Financeiras":
        st.subheader("💡 Dicas de Otimização")
        
        # Recupera transações
        df_transactions = tracker.get_transactions()
        
        
        if not df_transactions.empty:
            # Gera dicas contextuais
            advisor = FinancialAdvisor(df_transactions)
            
            tips = advisor.generate_contextual_tips()
            
            
            for i, tip in enumerate(tips, 1):
                st.write(f"{i}. {tip}")
        else:
            st.warning("Adicione algumas transações para receber dicas personalizadas.")

    elif choice == "Gerenciar Transações":
      st.subheader("📋 Gerenciar Transações")
    
    # Seleção de ano para visualização
      selected_year = st.selectbox("Selecione o Ano", 
          list(range(datetime.now().year, 2019, -1)))
    
    # Recupera transações do ano selecionado
      df_transactions = tracker.get_transactions_for_display(selected_year)
    
      if not df_transactions.empty:
        # Adiciona coluna de ID para referência
          df_transactions = tracker.get_transactions_for_display(selected_year)
        
        # Adiciona uma coluna de seleção (checkboxes) para exclusão
          df_transactions['Selecionar'] = False  # Coluna inicializada como False
        
        # Exibe tabela editável com checkboxes
          edited_df = st.data_editor(
              df_transactions, 
              column_config={
                  '_id': st.column_config.TextColumn("ID", disabled=True),
                  'month': st.column_config.SelectboxColumn(
                      "Mês", 
                      options=['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                             'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
                  ),
                  'type': st.column_config.SelectboxColumn(
                      "Tipo", 
                      options=['Receita', 'Despesa', 'Investimento']
                  ),
                  'Selecionar': st.column_config.CheckboxColumn("Selecionar para Excluir")  # Checkbox para seleção
              },
              disabled=["year", "created_at", "_id"],  # Desabilita edição de campos sensíveis
              num_rows="dynamic"
          )
        
        # Botões de ação
          col1, col2 = st.columns(2)
        
          with col1:
              if st.button("💾 Salvar Alterações"):
                # Processa alterações
                  for index, row in edited_df.iterrows():
                    # Verifica se a linha foi modificada
                      original_row = df_transactions.iloc[index]
                    
                    # Prepara dicionário de atualizações
                      updates = {}
                      for col in ['month', 'category', 'type', 'value']:
                          if row[col] != original_row[col]:
                              updates[col] = row[col]
                    
                    # Atualiza se houver mudanças
                      if updates:
                          try:
                              tracker.update_transaction(row['_id'], updates)
                              st.success(f"Transação {row['_id']} atualizada!")
                          except Exception as e:
                              st.error(f"Erro ao atualizar transação: {e}")
        
          with col2:
            # Exclusão de transações selecionadas
              if st.button("🗑️ Excluir Transações Selecionadas"):
                # Filtra as transações marcadas para exclusão
                  transactions_to_delete = edited_df[edited_df['Selecionar']]['_id'].tolist()
                
                  if transactions_to_delete:
                      success_count = 0
                      for transaction_id in transactions_to_delete:
                          try:
                              if tracker.delete_transaction(transaction_id):
                                  success_count += 1
                              else:
                                  st.error(f"Falha ao excluir transação {transaction_id}")
                          except Exception as e:
                              st.error(f"Erro ao excluir transação {transaction_id}: {e}")
                    
                      if success_count > 0:
                          st.success(f"{success_count} transações excluídas com sucesso!")
                        # Atualiza a página para refletir a exclusão
                          st.rerun()
                  else:
                      st.warning("Nenhuma transação selecionada para exclusão.")
      else:
          st.warning("Nenhuma transação encontrada para o ano selecionado")

    elif choice == "Inteligência de Compra":
        purchase_intelligence_interface(tracker)
    
if __name__ == "__main__":
    # Verifica conexão com MongoDB
    if check_mongodb_connection():
        main()
