import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
from datetime import datetime
import os
import numpy as np
import google.generativeai as genai 

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
        
    def predict_monthly_debt(self, month: str) -> float:
        """
        Prevê dívidas para um mês específico
        
        Args:
            month (str): Mês para previsão
        
        Returns:
            float: Valor projetado de dívidas
        """
        month_data = self.transactions_df[self.transactions_df['month'] == month]
        expenses = month_data[month_data['type'] == 'Despesa']['value'].sum()
        return expenses
    
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
        Inicializa a conexão com o MongoDB
        """
        # Usando variável de ambiente para a connection string
        mongo_uri = "mongodb+srv://richardrt13:QtZ9CnSP6dv93hlh@stockidea.isx8swk.mongodb.net/?retryWrites=true&w=majority&appName=StockIdea"
        self.client = MongoClient(mongo_uri)
        
        # Nome do banco de dados e coleção
        self.db = self.client['financial_tracker']
        self.transactions_collection = self.db['transactions']
    
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
    menu = ["Lançamentos", "Análise Financeira", "Dicas Financeiras", "Gerenciar Transações"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Lançamentos":
        st.subheader("📝 Registrar Transações")
        
        col1, col2 = st.columns(2)

        with col2:
            year = st.number_input("Ano", min_value=2020, max_value=2030, value=datetime.now().year)
            type_transaction = st.selectbox("Tipo", ['Receita', 'Despesa', 'Investimento'])
        
        with col1:
            month = st.selectbox("Mês", 
                ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'])
            
            if type_transaction == 'Receita':
                category = st.selectbox("Categoria", 
                    ['Salário', 'Outros'])
                
            elif type_transaction == 'Despesa': 
                category = st.selectbox("Categoria", 
                    ['Cartão', 'Internet', 'Tv a Cabo', 'Manutenção do carro', 'Combustível', 'Financiamento', 
                     'Aluguel', 'Condomínio', 'Mercado'])

            elif type_transaction == 'Investimento': 
                category = st.selectbox("Categoria", 
                    ['Renda Fixa', 'Renda Variável'])

        
        value = st.number_input("Valor", min_value=0.0, format="%.2f")
        
        if st.button("Adicionar Transação"):
            tracker.add_transaction(month, year, category, type_transaction, value)
            st.success("Transação adicionada com sucesso!")
    
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
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_receita = df_transactions[df_transactions['type'] == 'Receita']['value'].sum()
            st.metric(label="Total Receitas", value=f"R$ {total_receita:.2f}")
        
        with col2:
            total_despesa = df_transactions[df_transactions['type'] == 'Despesa']['value'].sum()
            st.metric(label="Total Despesas", value=f"R$ {total_despesa:.2f}")
        
        with col3:
            saldo_liquido = total_receita - total_despesa
            st.metric(label="Saldo Líquido", 
                      value=f"R$ {saldo_liquido:.2f}", 
                      delta_color="inverse",
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
            
            # Exibe tabela editável
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
                    )
                },
                disabled=["year", "created_at"],
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
                # Coluna para exclusão de transações
                transaction_to_delete = st.selectbox(
                    "🗑️ Selecione Transação para Excluir", 
                    df_transactions['_id'].tolist()
                )
                
                if st.button("Excluir Transação Selecionada"):
                    try:
                        if tracker.delete_transaction(transaction_to_delete):
                            st.success(f"Transação {transaction_to_delete} excluída!")
                            # Atualiza a página para refletir a exclusão
                            st.experimental_rerun()
                        else:
                            st.error("Falha ao excluir transação")
                    except Exception as e:
                        st.error(f"Erro ao excluir transação: {e}")
        else:
            st.warning("Nenhuma transação encontrada para o ano selecionado")

if __name__ == "__main__":
    # Verifica conexão com MongoDB
    if check_mongodb_connection():
        main()


