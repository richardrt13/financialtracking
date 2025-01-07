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

mongo_uri = "mongodb+srv://richardrt13:QtZ9CnSP6dv93hlh@stockidea.isx8swk.mongodb.net/?retryWrites=true&w=majority&appName=StockIdea"

class FinancialAdvisor:
    def __init__(self, transactions_df: pd.DataFrame):
        """
        Inicializa o conselheiro financeiro com dados de transações
        
        Args:
            transactions_df (pd.DataFrame): DataFrame com transações financeiras
        """
        self.transactions_df = transactions_df
        
        # Inicializa gerador de texto com Gemini 1.5 Flash
        try:
            genai.configure(api_key=st.secrets["api_key"])
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        except Exception as e:
            # Fallback se a configuração falhar
            st.warning(f"Não foi possível configurar o modelo Gemini: {e}")
            self.model = None
    
    def analyze_financial_health(self) -> dict:
        if self.transactions_df.empty:
            return {}
        
        # Expanded monthly summary
        monthly_summary = self.transactions_df.groupby(['month', 'type'])['value'].sum().unstack(fill_value=0)
        
        
        # Advanced metrics calculation
        metrics = {
            'total_revenue': monthly_summary.get('Receita', pd.Series(0)).sum(),
            'total_expenses': monthly_summary.get('Despesa', pd.Series(0)).sum(),
            'total_investments': monthly_summary.get('Investimento', pd.Series(0)).sum(),
            'net_cashflow': monthly_summary.get('Receita', pd.Series(0)).sum() - 
                            monthly_summary.get('Despesa', pd.Series(0)).sum(),
            
            # New advanced metrics
            'average_monthly_revenue': monthly_summary.get('Receita', pd.Series(0)).mean(),
            'average_monthly_expenses': monthly_summary.get('Despesa', pd.Series(0)).mean(),
            'investment_ratio': monthly_summary.get('Investimento', pd.Series(0)).sum() / 
                                max(monthly_summary.get('Receita', pd.Series(0)).sum(), 1) * 100,
            'expense_to_income_ratio': monthly_summary.get('Despesa', pd.Series(0)).sum() / 
                                        max(monthly_summary.get('Receita', pd.Series(0)).sum(), 1) * 100,
            'revenue_volatility': monthly_summary.get('Receita', pd.Series(0)).std() / 
                                   max(monthly_summary.get('Receita', pd.Series(0)).mean(), 1) * 100
        }
        
        return metrics
        
    
    def generate_contextual_tips(self) -> list:
        metrics = self.analyze_financial_health()
        
        tips = []
        
        # Investment Analysis
        if metrics['investment_ratio'] < 10:
            tips.append("🚨 Seu percentual de investimentos está muito baixo. Recomenda-se investir pelo menos 10-20% da renda.")
        elif metrics['investment_ratio'] > 30:
            tips.append("💡 Você está investindo muito! Verifique se não está comprometendo sua liquidez.")
        
        # Expense Management
        if metrics['expense_to_income_ratio'] > 70:
            tips.append("⚠️ Suas despesas consomem mais de 70% da sua renda. É crucial cortar gastos e aumentar a eficiência financeira.")
        elif metrics['expense_to_income_ratio'] > 50:
            tips.append("🔍 Suas despesas estão próximas de 50% da renda. Faça uma revisão detalhada dos gastos.")
        
        # Revenue Stability
        if metrics['revenue_volatility'] > 30:
            tips.append("📊 Sua renda apresenta alta variabilidade. Considere fontes de renda mais estáveis ou criar um fundo de emergência.")
        
        # Savings and Emergency Fund
        if metrics['net_cashflow'] < 0:
            tips.append("🐖 Você está gastando mais do que ganha. Priorize a criação de um orçamento e corte de despesas não essenciais.")
        else:
            savings_rate = metrics['net_cashflow'] / max(metrics['total_revenue'], 1) * 100
            if savings_rate < 10:
                tips.append("💰 Sua taxa de poupança está baixa. Tente economizar pelo menos 10-20% da renda.")
        
        # Advanced AI-powered tips (if text generator available)
        if st.button("Dica do HeroAI"):
            if self.model and tips:
                try:
                    context = " ".join(tips)
                    response = self.model.generate_content(f"Considerando esta análise financeira detalhada: {context}. Dê uma dica personalizada de gestão financeira em até 3 linhas.")
                    ai_tip = response.text.strip()
                    tips.append(f"🤖 HeroAI: {ai_tip}")
                except Exception as e:
                    st.warning(f"Geração de dica de IA avançada falhou: {e}")
            
        return tips[:5]
        
        # Backup tips
        if not tips:
            tips = [
                "💡 Seu perfil financeiro parece estável. Continue monitorando e ajustando seu orçamento.",
                "🏦 Considere diversificar suas fontes de renda e investimentos.",
                "📈 Mantenha um registro detalhado e faça revisões periódicas."
            ]
        
        return tips[:5]

class FinancialTracker:
    def __init__(self):
        """
        Inicializa o rastreador financeiro com conexão ao MongoDB e carregamento de ativos
        """
        # Conexão com MongoDB
        mongo_uri = "mongodb+srv://richardrt13:QtZ9CnSP6dv93hlh@stockidea.isx8swk.mongodb.net/?retryWrites=true&w=majority&appName=StockIdea"
        self.client = MongoClient(mongo_uri)
        
        # Nome do banco de dados e coleção
        self.db = self.client['financial_tracker']
        self.transactions_collection = self.db['transactions']
        self.investments_collection = self.db['investments']
        
        # Carregar ativos
        self.stock_tickers = self.load_stock_tickers()
        
        # CDI rates (example values, should be updated with real data)
        self.cdi_rates = {
            '2023': 0.1375,  # 13.75%
            '2024': 0.1150   # 11.50%
        }

    
    def add_transaction(self, month, year, category, type, value):
        """
        Adiciona uma nova transação ao MongoDB
        """
        transaction = {
            'month': month,
            'year': year,
            'category': category,
            'type': type,
            'value': float(value),
            'created_at': datetime.now()
        }
        self.transactions_collection.insert_one(transaction)
    
    def get_transactions(self, year=None):
        """
        Recupera transações, opcionalmente filtradas por ano
        """
        query = {} if year is None else {'year': year}
        transactions = list(self.transactions_collection.find(query))
        
        df = pd.DataFrame(transactions)
        
        # Remover o campo '_id' do MongoDB para processamento
        if not df.empty:
            df = df.drop(columns=['_id', 'created_at'])
        
        return df
    
    def financial_analysis(self, df):
        """
        Análise financeira consolidada com tratamento de dados
        """
        if df.empty:
            return pd.DataFrame()
        
        # Garante que todos os meses estejam presentes
        meses_ordem = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                       'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        
        # Agrupa por mês e tipo, preenchendo com zero para meses sem transações
        summary = df.groupby(['month', 'type'])['value'].sum().unstack(fill_value=0)
        
        # Reordena os meses
        summary = summary.reindex(meses_ordem)
        
        # Calcula Net (preenchendo com zero se não existir)
        summary['Receita'] = summary.get('Receita', pd.Series([0]*12, index=meses_ordem))
        summary['Despesa'] = summary.get('Despesa', pd.Series([0]*12, index=meses_ordem))
        summary['Net'] = summary['Receita'] - summary['Despesa']
    
        return summary

    # Função de plotagem atualizada na interface Streamlit
    def plot_financial_analysis(self, analysis):
        """
        Cria gráfico de análise financeira com tratamento de dados
        """
        # Prepara dados para plotagem
        plot_data = analysis.reset_index()
        
        # Cria figura
        fig = px.bar(plot_data, 
                     x='month', 
                     y=['Receita', 'Despesa', 'Net'],
                     title=f"Resumo Financeiro",
                     labels={'value': 'Valor', 'month': 'Mês', 'variable': 'Tipo'},
                     barmode='group')
        
        # Personaliza layout
        fig.update_layout(
            xaxis_title='Mês',
            yaxis_title='Valor (R$)',
            legend_title='Tipo de Transação'
        )
        
        return fig
        # Adicione estes métodos à classe FinancialTracker
    def get_transaction_by_id(self, transaction_id):
        """
        Recupera uma transação específica pelo seu ID
        """
        from bson.objectid import ObjectId
        
        transaction = self.transactions_collection.find_one({'_id': ObjectId(transaction_id)})
        return transaction
    
    def update_transaction(self, transaction_id, updates):
        """
        Atualiza uma transação existente
        
        Args:
            transaction_id (str): ID da transação no MongoDB
            updates (dict): Dicionário com campos a serem atualizados
        """
        from bson.objectid import ObjectId
        
        # Remove o ID se estiver presente nos updates para evitar erro
        updates.pop('_id', None)
        
        # Atualiza a transação
        result = self.transactions_collection.update_one(
            {'_id': ObjectId(transaction_id)}, 
            {'$set': updates}
        )
        return result.modified_count > 0
    
    def delete_transaction(self, transaction_id):
        """
        Deleta uma transação específica
        
        Args:
            transaction_id (str): ID da transação no MongoDB
        """
        from bson.objectid import ObjectId
        
        result = self.transactions_collection.delete_one({'_id': ObjectId(transaction_id)})
        return result.deleted_count > 0

    def get_transactions_ids(self, year=None):
        """
        Recupera os IDs das transações
        """
        query = {} if year is None else {'year': year}
        transactions = list(self.transactions_collection.find(query, {'_id': 1}))
        return [str(trans['_id']) for trans in transactions]
        
    def load_stock_tickers(self):
        """
        Carrega tickers de ativos de um repositório GitHub
        """
        try:
            df = pd.read_csv('https://raw.githubusercontent.com/richardrt13/Data-Science-Portifolio/main/ativos.csv')
            return df['Ticker'].tolist()
        except Exception as e:
            st.warning(f"Erro ao carregar ativos: {e}")
            return []
    
    def track_stock_investment(self, ticker, quantity, purchase_price, purchase_date):
        """
        Rastreia o desempenho de um investimento em ações
        """
        try:
            stock = yf.Ticker(f"{ticker}.SA")
            
            # Obtém o preço atual
            current_price = stock.history(period="1d")['Close'][0]
            
            # Calcula performance
            total_purchase_value = quantity * purchase_price
            total_current_value = quantity * current_price
            performance_percentage = ((current_price - purchase_price) / purchase_price) * 100
            
            # Salva o investimento no MongoDB
            investment = {
                'ticker': ticker,
                'type': 'Renda Variável',
                'quantity': quantity,
                'purchase_price': purchase_price,
                'purchase_date': purchase_date,
                'current_price': current_price,
                'total_purchase_value': total_purchase_value,
                'total_current_value': total_current_value,
                'performance_percentage': performance_percentage,
                'created_at': datetime.now()
            }
            
            # Insere no MongoDB
            self.investments_collection.insert_one(investment)
            
            return investment
        
        except Exception as e:
            st.error(f"Erro ao rastrear ativo {ticker}: {e}")
            return None
    
    def track_fixed_income_investment(self, investment_type, initial_investment, investment_date, cdi_percentage):
        """
        Rastreia investimentos de renda fixa baseado no CDI
        """
        current_date = datetime.now()
        investment_datetime = pd.to_datetime(investment_date)
        
        # Calcula duração do investimento
        duration_days = (current_date - investment_datetime).days
        duration_years = duration_days / 365.25
        
        # Obtém a taxa CDI apropriada
        year = str(investment_datetime.year)
        base_cdi_rate = self.cdi_rates.get(year, 0.11)  # Padrão 11% se não houver taxa específica
        
        # Calcula retorno
        investment_return = initial_investment * ((1 + base_cdi_rate * cdi_percentage) ** duration_years - 1)
        
        # Salva o investimento no MongoDB
        investment = {
            'investment_type': investment_type,
            'type': 'Renda Fixa',
            'initial_investment': initial_investment,
            'investment_date': investment_date,
            'cdi_percentage': cdi_percentage,
            'total_current_value': initial_investment + investment_return,
            'total_return': investment_return,
            'return_percentage': (investment_return / initial_investment) * 100,
            'created_at': datetime.now()
        }
        
        # Insere no MongoDB
        self.investments_collection.insert_one(investment)
        
        return investment
    
    def get_investments(self, year=None):
        """
        Recupera investimentos, opcionalmente filtrados por ano
        """
        query = {} if year is None else {'investment_date__year': year}
        investments = list(self.investments_collection.find(query))
        
        df = pd.DataFrame(investments)
        
        # Remove o campo '_id' do MongoDB para processamento
        if not df.empty:
            df = df.drop(columns=['_id', 'created_at'])
        
        return df

    # Método para atualizar a coleção de investimentos
    def update_investment(self, investment_id, updates):
        """
        Atualiza um investimento existente
        """
        from bson.objectid import ObjectId
        
        # Remove o ID se estiver presente nos updates para evitar erro
        updates.pop('_id', None)
        
        # Atualiza o investimento
        result = self.investments_collection.update_one(
            {'_id': ObjectId(investment_id)}, 
            {'$set': updates}
        )
        return result.modified_count > 0
    
    def delete_investment(self, investment_id):
        """
        Deleta um investimento específico
        """
        from bson.objectid import ObjectId
        
        result = self.investments_collection.delete_one({'_id': ObjectId(investment_id)})
        return result.deleted_count > 0


class InvestmentTracker:
    def __init__(self):
        # Load stock tickers
        self.stock_tickers = self.load_stock_tickers()
        
        # CDI rates (example values, should be updated with real data)
        self.cdi_rates = {
            '2023': 0.1375,  # 13.75%
            '2024': 0.1150   # 11.50%
        }
    
    def load_stock_tickers(self):
        """
        Load stock tickers from GitHub repository
        """
        try:
            url = "https://raw.githubusercontent.com/richardrt13/Data-Science-Portifolio/main/ativos.csv"
            df = pd.read_csv(url)
            return df['ticker'].tolist()
        except Exception as e:
            st.error(f"Erro ao carregar ativos: {e}")
            return []
    
    def track_stock_investment(self, ticker, quantity, purchase_price, purchase_date):
        """
        Track stock investment performance
        """
        try:
            stock = yf.Ticker(f"{ticker}.SA")
            
            # Get current price
            current_price = stock.history(period="1d")['Close'][0]
            
            # Calculate performance
            total_purchase_value = quantity * purchase_price
            total_current_value = quantity * current_price
            performance_percentage = ((current_price - purchase_price) / purchase_price) * 100
            
            return {
                'ticker': ticker,
                'quantity': quantity,
                'purchase_price': purchase_price,
                'purchase_date': purchase_date,
                'current_price': current_price,
                'total_purchase_value': total_purchase_value,
                'total_current_value': total_current_value,
                'performance_percentage': performance_percentage
            }
        except Exception as e:
            st.error(f"Erro ao rastrear ativo {ticker}: {e}")
            return None
    
    def track_fixed_income_investment(self, investment_type, initial_investment, investment_date, cdi_percentage):
        """
        Track fixed-income investment performance based on CDI
        """
        current_date = datetime.now()
        investment_datetime = pd.to_datetime(investment_date)
        
        # Calculate investment duration
        duration_days = (current_date - investment_datetime).days
        duration_years = duration_days / 365.25
        
        # Get appropriate CDI rate
        year = str(investment_datetime.year)
        base_cdi_rate = self.cdi_rates.get(year, 0.11)  # Default to 11% if no specific rate
        
        # Calculate return
        investment_return = initial_investment * ((1 + base_cdi_rate * cdi_percentage) ** duration_years - 1)
        
        return {
            'investment_type': investment_type,
            'initial_investment': initial_investment,
            'investment_date': investment_date,
            'cdi_percentage': cdi_percentage,
            'total_current_value': initial_investment + investment_return,
            'total_return': investment_return,
            'return_percentage': (investment_return / initial_investment) * 100
        }
        
def investment_tracking_interface(tracker):
    """
    Interface Streamlit para rastreamento de investimentos
    """
    st.header("📈 Registro de Investimentos")
    
    investment_type = st.selectbox("Tipo de Investimento", 
                                   ["Renda Variável", "Renda Fixa"])
    
    if investment_type == "Renda Variável":
        col1, col2 = st.columns(2)
        with col1:
            ticker = st.selectbox("Ativo", tracker.stock_tickers)
            quantity = st.number_input("Quantidade", min_value=1)
            purchase_price = st.number_input("Preço de Compra", min_value=0.01, format="%.2f")
        
        with col2:
            purchase_date = st.date_input("Data de Compra", datetime.now())
        
        if st.button("Rastrear Investimento em Ações"):
            result = tracker.track_stock_investment(ticker, quantity, purchase_price, purchase_date)
            if result:
                st.success("Investimento registrado com sucesso!")
                st.json(result)
    
    else:  # Renda Fixa
        col1, col2 = st.columns(2)
        
        with col1:
            investment_name = st.selectbox("Tipo de Investimento", 
                ["Tesouro Direto", "CDB", "LCI", "LCA", "CRI", "CRA"])
            initial_investment = st.number_input("Valor Inicial", min_value=0.01, format="%.2f")
            
        with col2:
            investment_date = st.date_input("Data do Investimento", datetime.now())
            cdi_percentage = st.number_input("% do CDI", min_value=0.0, max_value=200.0, value=100.0, format="%.2f")
        
        if st.button("Rastrear Investimento de Renda Fixa"):
            result = tracker.track_fixed_income_investment(
                investment_name, initial_investment, investment_date, cdi_percentage/100
            )
            if result:
                st.success("Investimento registrado com sucesso!")
                st.json(result)
    
    

def check_mongodb_connection():
    """
    Verifica a conexão com o MongoDB
    """
    try:
        client = MongoClient(mongo_uri)
        client.admin.command('ismaster')
        st.success("Conexão com MongoDB estabelecida com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro de conexão com MongoDB: {e}")
        st.warning("Verifique sua connection string e configurações de rede.")
        return False

def main():
    """
    Função principal do aplicativo Streamlit
    """
    st.title("🏦 Gestor Financeiro Inteligente")
    
    # Inicializa o rastreador financeiro
    tracker = FinancialTracker()
    
    # Menu de navegação
    menu = ["Lançamentos", "Análise Financeira", "Dicas Financeiras", 
            "Gerenciar Transações", "Registro de Investimentos", "Gerenciar Investimentos"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Lançamentos":
      st.subheader("📝 Registrar Transações")
    
      col1, col2 = st.columns(2)

      with col2:
          year = st.number_input("Ano", min_value=2020, max_value=2030, value=datetime.now().year)
          type_transaction = st.selectbox("Tipo", ['Receita', 'Despesa', 'Investimento'])
          repeat_months = st.number_input("Repetir por quantos meses?", min_value=1, max_value=36, value=1)
    
      with col1:
          month = st.selectbox("Mês", 
            ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
             'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'])
        
          if type_transaction == 'Receita':
              category = st.selectbox("Categoria", 
                ['Salário', 'Outros'])
            
          elif type_transaction == 'Despesa': 
              category = st.selectbox("Categoria", 
                ['Cartão', 'Internet', 'Tv a Cabo', 'Manutenção do carro', 'Combustível', 'Gás','Financiamento', 
                 'Aluguel', 'Condomínio', 'Mercado', 'Cursos', 'Anuidade'])

          elif type_transaction == 'Investimento': 
              category = st.selectbox("Categoria", 
                ['Renda Fixa', 'Renda Variável'])

    
      value = st.number_input("Valor", min_value=0.0, format="%.2f")
    
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
                  value=value
              )
            
            # Avança para o próximo mês
              current_month_index += 1
              if current_month_index >= 12:
                  current_month_index = 0
                  current_year += 1
        
          st.success(f"Transação adicionada com sucesso para {repeat_months} meses!")
    
    
    elif choice == "Análise Financeira":
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
        df_transactions = tracker.get_transactions(selected_year)
        
        if selected_month != 'Todos':
            df_transactions = df_transactions[df_transactions['month'] == selected_month]
        
        if not df_transactions.empty:
            # Sumário de métricas
            st.subheader("Resumo Financeiro")
            
            col1, col2 = st.columns(2)
            
            with col1:
                total_receita = df_transactions[df_transactions['type'] == 'Receita']['value'].sum()
                st.metric(label="Total Receitas", value=f"R$ {total_receita:.2f}")
                total_despesa = df_transactions[df_transactions['type'] == 'Despesa']['value'].sum()
                st.metric(label="Total Despesas",
                          value=f"R$ {total_despesa:.2f}",
                          delta_color="inverse",
                          delta=f"{(total_despesa/max(total_receita, 1)*100):.2f}%")

            with col2:
                total_investimento = df_transactions[df_transactions['type'] == 'Investimento']['value'].sum()
                st.metric(label="Total Investimentos", 
                          value=f"R$ {total_investimento:.2f}",
                          delta_color="inverse",
                          delta=f"{(total_investimento/max(total_receita, 1)*100):.2f}%")
                saldo_liquido = total_receita - total_despesa - total_investimento
                st.metric(label="Saldo Líquido", 
                          value=f"R$ {saldo_liquido:.2f}", 
                          delta=f"{(saldo_liquido/max(total_receita, 1)*100):.2f}%")
            
            # Opção para mostrar gráfico
            if st.checkbox("Mostrar Gráfico Detalhado"):
                analysis = tracker.financial_analysis(df_transactions)
                fig = tracker.plot_financial_analysis(analysis)
                st.plotly_chart(fig)
            
            # Detalhamento por categoria
            st.subheader("Detalhamento por Categoria")
            
            categoria_summary = df_transactions.groupby(['type', 'category'])['value'].sum().reset_index()
            st.dataframe(categoria_summary.style.format({'value': 'R$ {:.2f}'}))
            
        else:
            st.warning("Nenhuma transação registrada para o período selecionado")
    
    elif choice == "Dicas Financeiras":
        st.subheader("💡 Dicas de Otimização")
        
        # Recupera transações
        df_transactions = tracker.get_transactions()
        df_transactions 
        
        if not df_transactions.empty:
            # Gera dicas contextuais
            advisor = FinancialAdvisor(df_transactions)
            tips = advisor.generate_contextual_tips()
            
            for i, tip in enumerate(tips, 1):
                st.write(f"{i}. {tip}")
        else:
            st.warning("Adicione algumas transações para receber dicas personalizadas.")
            
    elif choice == "Registro de Investimentos":
        investment_tracking_interface(tracker)
    
    elif choice == "Gerenciar Investimentos":
        manage_investments_interface(tracker)

    elif choice == "Gerenciar Transações":
      st.subheader("📋 Gerenciar Transações")
    
    # Seleção de ano para visualização
      selected_year = st.selectbox("Selecione o Ano", 
          list(range(datetime.now().year, 2019, -1)))
    
    # Recupera transações do ano selecionado
      df_transactions = tracker.get_transactions(selected_year)
    
      if not df_transactions.empty:
        # Adiciona coluna de ID para referência
          df_transactions['_id'] = tracker.get_transactions_ids(selected_year)
        
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
                          st.experimental_rerun()
                  else:
                      st.warning("Nenhuma transação selecionada para exclusão.")
      else:
          st.warning("Nenhuma transação encontrada para o ano selecionado")

if __name__ == "__main__":
    # Verifica conexão com MongoDB
    if check_mongodb_connection():
        main()


