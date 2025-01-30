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

mongo_uri = st.secrets["mongo_uri"]

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
    
    # Investment Analysis (0-30%)
        if metrics['investment_ratio'] < 10:
            tips.append("🚨 Seu percentual de investimentos está muito baixo. Recomenda-se investir pelo menos 10-20% da renda.")
        elif 10 <= metrics['investment_ratio'] <= 20:
            tips.append("✅ Ótimo! Você está investindo dentro da faixa recomendada (10-20%). Continue com o bom trabalho!")
        elif 20 < metrics['investment_ratio'] <= 30:
            tips.append("👍 Você está investindo acima da média! Apenas certifique-se de manter uma reserva de emergência.")
        else:
            tips.append("💡 Você está investindo muito! Verifique se não está comprometendo sua liquidez.")

        # Expense Management (0-100%)
        if metrics['expense_to_income_ratio'] > 70:
            tips.append("⚠️ Suas despesas consomem mais de 70% da sua renda. É crucial cortar gastos.")
        elif 50 < metrics['expense_to_income_ratio'] <= 70:
            tips.append("🔍 Suas despesas estão entre 50-70% da renda. Busque reduzir gastos não essenciais.")
        elif 30 <= metrics['expense_to_income_ratio'] <= 50:
            tips.append("✅ Suas despesas estão em um bom patamar, entre 30-50% da renda.")
        else:
            tips.append("💫 Parabéns! Suas despesas estão muito bem controladas, abaixo de 30% da renda.")
    
    # Revenue Stability
        if metrics['revenue_volatility'] > 30:
            tips.append("📊 Sua renda apresenta alta variabilidade. Considere um fundo de emergência maior.")
        elif 15 < metrics['revenue_volatility'] <= 30:
            tips.append("📈 Sua renda tem variação moderada. Mantenha uma reserva de emergência adequada.")
        else:
            tips.append("💪 Sua renda é bastante estável. Continue mantendo uma reserva de segurança.")
    
    # Savings Analysis
        if metrics['net_cashflow'] < 0:
            tips.append("🐖 Atenção: você está gastando mais do que ganha. Revise seu orçamento.")
        else:
            savings_rate = metrics['net_cashflow'] / max(metrics['total_revenue'], 1) * 100
            if savings_rate < 10:
                tips.append("💰 Sua taxa de poupança está abaixo de 10%. Tente aumentar suas economias.")
            elif 10 <= savings_rate <= 20:
                tips.append("🎯 Boa taxa de poupança, entre 10-20%! Continue economizando.")
            else:
                tips.append("🌟 Excelente! Sua taxa de poupança está acima de 20%.")
    
    # AI-powered tip (if available)
        if st.button("Dica do HeroAI") and self.model and tips:
            try:
                context = " ".join(tips)
                response = self.model.generate_content(
                    f"Considerando esta análise financeira: {context}. "
                    "Dê uma dica personalizada de gestão financeira em até 3 linhas."
                )
                tips.append(f"🤖 HeroAI: {response.text.strip()}")
            except Exception:
                pass
    
        return tips[:5]
        
class FinancialTracker:
    def __init__(self):
        """
        Inicializa o rastreador financeiro com conexão ao MongoDB e carregamento de ativos
        """
        # Conexão com MongoDB
        self.client = MongoClient(mongo_uri)
        
        # Nome do banco de dados e coleção
        self.db = self.client['financial_tracker']
        self.transactions_collection = self.db['transactions']
        self.investments_collection = self.db['investments']
        
    def add_transaction(self, month, year, category, type, value, observation=''):
        """
        Adiciona uma nova transação ao MongoDB com status de pagamento e observação
        """
        transaction = {
            'month': month,
            'year': year,
            'category': category,
            'type': type,
            'value': float(value),
            'observation': observation,
            'created_at': datetime.now(),
            'paid': False,
            'payment_date': None
        }
        self.transactions_collection.insert_one(transaction)


    def update_payment_status(self, transaction_id, paid=True):
        """
        Atualiza o status de pagamento de uma transação
        """
        from bson.objectid import ObjectId
        
        updates = {
            'paid': paid,
            'payment_date': datetime.now() if paid else None
        }
        
        self.transactions_collection.update_one(
            {'_id': ObjectId(transaction_id)},
            {'$set': updates}
        )
        
    def get_transactions(self, year=None):
        """
        Recupera transações, opcionalmente filtradas por ano
        """
        query = {} if year is None else {'year': year}
        transactions = list(self.transactions_collection.find(query))
        
        df = pd.DataFrame(transactions)
        
        if not df.empty:
            # Remove o campo '_id' do MongoDB mas mantém como índice
            df['_id'] = df['_id'].astype(str)
            # Garante que o campo paid existe
            if 'paid' not in df.columns:
                df['paid'] = False
            if 'payment_date' not in df.columns:
                df['payment_date'] = None
                
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

        
def purchase_intelligence_interface(tracker):
    """
    Interface aprimorada para consultoria financeira inteligente e planejamento de compras
    """
    st.subheader("🧠 Consultor Financeiro Inteligente")
    
    # Recupera transações para análise
    current_year = datetime.now().year
    df_transactions = tracker.get_transactions(current_year)
    
    if not df_transactions.empty:
        # Cria o conselheiro financeiro
        advisor = FinancialAdvisor(df_transactions)
        metrics = advisor.analyze_financial_health()
        
        # Calcula métricas mensais corretas
        monthly_summary = df_transactions.groupby(['month', 'type'])['value'].sum().unstack(fill_value=0)
        
        # Calcula médias mensais reais
        monthly_revenue = monthly_summary.get('Receita', pd.Series([0])).mean()
        monthly_expenses = monthly_summary.get('Despesa', pd.Series([0])).mean()
        monthly_investments = monthly_summary.get('Investimento', pd.Series([0])).mean()
        monthly_savings = monthly_revenue - monthly_expenses - monthly_investments
        
        # Obtém dados do mês atual
        current_month = datetime.now().strftime('%B')  # Gets month name
        months_pt = {
            'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
            'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
            'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
            'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
        }
        current_month_pt = months_pt[current_month]
        
        current_month_data = monthly_summary.loc[current_month_pt] if current_month_pt in monthly_summary.index else pd.Series({'Receita': 0, 'Despesa': 0, 'Investimento': 0})
        
        # Seção 1: Visão Geral Financeira
        st.write("### 📊 Sua Situação Financeira")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            expense_ratio = (monthly_expenses / monthly_revenue * 100) if monthly_revenue > 0 else 0
            st.metric(
                "Saúde Financeira",
                f"{100 - expense_ratio:.1f}%",
                help="Porcentagem da sua renda média mensal que não está comprometida com despesas"
            )
        with col2:
            # Mostra tanto a reserva média quanto a atual
            st.metric(
                "Reserva Mensal Média",
                f"R$ {monthly_savings:.2f}",
                delta=f"R$ {(current_month_data.get('Receita', 0) - current_month_data.get('Despesa', 0) - current_month_data.get('Investimento', 0)) - monthly_savings:.2f} este mês",
                help="Valor médio que sobra por mês após despesas e investimentos"
            )
        with col3:
            investment_ratio = (monthly_investments / monthly_revenue * 100) if monthly_revenue > 0 else 0
            st.metric(
                "Taxa de Investimento",
                f"{investment_ratio:.1f}%",
                help="Porcentagem média da sua renda destinada a investimentos"
            )
        
        
        # Seção 2: Planejamento de Compra
        st.write("### 🛍️ Planejamento de Compra")
        
        col1, col2 = st.columns(2)
        with col1:
            purchase_value = st.number_input("Valor do Item (R$)", min_value=0.01, format="%.2f")
            purchase_priority = st.select_slider(
                "Prioridade da Compra",
                options=["Baixa", "Média", "Alta", "Essencial"],
                value="Média"
            )
        
        with col2:
            purchase_type = st.selectbox(
                "Tipo de Compra",
                ["Única", "Recorrente"],
                help="Compra única ou despesa recorrente mensal?"
            )
            if purchase_type == "Recorrente":
                duration_months = st.number_input("Duração (meses)", min_value=1, max_value=60, value=12)
        
        # Seção 3: Análise de Viabilidade
        if st.button("Analisar Viabilidade"):
            st.write("### 📈 Análise de Viabilidade")
            
            # Define limites com base na prioridade
            priority_limits = {
                "Baixa": 0.05,  # 5% da renda
                "Média": 0.15,  # 15% da renda
                "Alta": 0.25,   # 25% da renda
                "Essencial": 0.35  # 35% da renda
            }
            
            max_recommended = monthly_revenue * priority_limits[purchase_priority]
            
            # Analisa diferentes cenários
            scenarios = []
            
            # Cenário 1: Compra à vista
            current_month_savings = (current_month_data.get('Receita', 0) - 
                                   current_month_data.get('Despesa', 0) - 
                                   current_month_data.get('Investimento', 0))
            
            if purchase_value <= current_month_savings:
                scenarios.append({
                    "tipo": "À Vista",
                    "viabilidade": "Alta",
                    "impacto": "Baixo",
                    "descricao": f"Você pode fazer a compra à vista este mês, usando {(purchase_value/current_month_savings)*100:.1f}% da sua reserva atual de {current_month_savings:.2f}."
                })
            elif purchase_value <= monthly_savings * 2:
                scenarios.append({
                    "tipo": "À Vista com Planejamento",
                    "viabilidade": "Média",
                    "impacto": "Médio",
                    "descricao": f"Você pode fazer a compra à vista em 2 meses, economizando {purchase_value/2:.2f} por mês."
                })
            
            # Cenário 2: Parcelamento
            max_installment = monthly_savings * 0.3  # Máximo 30% da reserva mensal
            recommended_installments = min(12, max(1, int(np.ceil(purchase_value / max_installment))))
            
            if recommended_installments <= 12:
                installment_value = purchase_value / recommended_installments
                scenarios.append({
                    "tipo": "Parcelado",
                    "viabilidade": "Média" if recommended_installments <= 6 else "Baixa",
                    "impacto": "Médio",
                    "descricao": f"Parcelamento em {recommended_installments}x de R$ {installment_value:.2f}, comprometendo {(installment_value/monthly_savings)*100:.1f}% da sua reserva média mensal."
                })
            
            # Cenário 3: Economia programada
            months_to_save = int(np.ceil(purchase_value / (monthly_savings * 0.3)))
            if months_to_save <= 12:
                scenarios.append({
                    "tipo": "Economia Programada",
                    "viabilidade": "Alta",
                    "impacto": "Baixo",
                    "descricao": f"Economize R$ {purchase_value/months_to_save:.2f} por mês durante {months_to_save} meses para realizar a compra à vista."
                })
            
            # Exibe recomendações
            st.write("#### 💡 Cenários Recomendados")
            
            for scenario in scenarios:
                with st.expander(f"{scenario['tipo']} - Viabilidade {scenario['viabilidade']}"):
                    st.write(scenario['descricao'])
                    
                    if scenario['tipo'] == "Parcelado":
                        # Adiciona simulação de juros
                        st.write("##### Simulação com Juros")
                        juros = st.slider("Taxa de Juros Mensal (%)", 0.0, 5.0, 2.0, 0.1)
                        valor_final = purchase_value * (1 + juros/100) ** recommended_installments
                        parcela_com_juros = valor_final / recommended_installments
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Valor Final", f"R$ {valor_final:.2f}")
                            st.metric("Custo dos Juros", f"R$ {(valor_final - purchase_value):.2f}")
                        with col2:
                            st.metric("Parcela sem Juros", f"R$ {installment_value:.2f}")
                            st.metric("Parcela com Juros", f"R$ {parcela_com_juros:.2f}")
            
            # Alertas e Recomendações
            st.write("#### ⚠️ Alertas e Considerações")
            
            alerts = []
            if purchase_value > max_recommended:
                alerts.append(f"O valor da compra representa {(purchase_value/monthly_revenue)*100:.1f}% da sua renda mensal média, acima do recomendado ({priority_limits[purchase_priority]*100}%) para sua prioridade.")
            
            if expense_ratio > 70:
                alerts.append("Suas despesas médias já estão acima do recomendado (70% da renda). Considere adiar compras não essenciais.")
            
            if investment_ratio < 10:
                alerts.append("Sua taxa média de investimento está abaixo do recomendado (10%). Considere priorizar investimentos.")
            
            
            # Solicita recomendação do modelo de IA
            if advisor.model:
                try:
                    context = (
                        f"Valor da compra: R$ {purchase_value}, "
                        f"Prioridade: {purchase_priority}, "
                        f"Renda mensal média: R$ {monthly_revenue:.2f}, "
                       # f"Reserva mensal média: R$ {monthly_savings:.2f}, "
                        f"Reserva atual: R$ {current_month_savings:.2f}, "
                        f"Comprometimento atual: {expense_ratio:.1f}%, "
                        f"Taxa de investimento: {investment_ratio:.1f}%"
                    )
                    
                    response = advisor.model.generate_content(
                        f"Analise esta situação financeira: {context}. "
                        "Dê uma recomendação estratégica e personalizada sobre a melhor forma de proceder com esta compra, "
                        "considerando a diferença entre a reserva média e atual, o impacto no orçamento, prioridades financeiras e saúde financeira de longo prazo. "
                        "A resposta deve ser objetiva e prática, em até 4 linhas."
                    )
                    st.info(f"🤖 Recomendação Estratégica: {response.text.strip()}")
                except Exception as e:
                    st.error(f"Erro ao gerar recomendação: {e}")
    else:
        st.warning("Adicione algumas transações para receber recomendações personalizadas.")

                    
    
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
            "Gerenciar Transações", "Inteligência de Compra"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Lançamentos":
        st.subheader("📝 Registrar Transações")
        
        col1, col2 = st.columns(2)
        
        with col1:
            year = st.number_input("Ano", min_value=2020, max_value=2030, value=datetime.now().year)
            month = st.selectbox("Mês", 
                ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'])
            
            # Primeiro seleciona o tipo
            type_transaction = st.selectbox("Tipo", ['Receita', 'Despesa', 'Investimento'])
            
            # Depois seleciona a categoria baseada no tipo
            if type_transaction == 'Receita':
                category = st.selectbox("Categoria", 
                    ['Salário - 1ª Parcela', 'Salário - 2ª Parcela', '13º Salário', 'Férias', 'Outros'])
            elif type_transaction == 'Despesa':
                category = st.selectbox("Categoria", 
                    ['Cartão', 'Internet', 'Tv a Cabo', 'Manutenção do carro', 'Combustível', 'Gás',
                     'Financiamento', 'Aluguel', 'Condomínio', 'Mercado', 'Cursos', 'Anuidade'])
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
            
            # Tabela detalhada com status de pagamento
            st.subheader("Detalhamento de Transações")
            
            # Prepara dados para exibição
            display_df = df_transactions[['month', 'category', 'type', 'value', 'paid']].copy()
            
            # Adiciona ícones para status de pagamento
            def format_payment_status(row):
                #if row['type'] != 'Despesa':
                    #return "N/A"
                return "✅" if row['paid'] else "⏳"
            
            display_df['Status'] = display_df.apply(format_payment_status, axis=1)
            
            # Remove coluna 'paid' da exibição
            display_df = display_df.drop('paid', axis=1)
            
            # Exibe tabela com formatação condicional
            st.dataframe(
                display_df.style.format({'value': 'R$ {:.2f}'})
                         .map(lambda x: 'color: green' if x == '✅' else 'color: orange',
                                 subset=['Status'])
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
