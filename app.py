import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
from datetime import datetime
import os
from transformers import pipeline
import numpy as np

mongo_uri = "mongodb+srv://richardrt13:QtZ9CnSP6dv93hlh@stockidea.isx8swk.mongodb.net/?retryWrites=true&w=majority&appName=StockIdea"

class FinancialAdvisor:
    def __init__(self, transactions_df: pd.DataFrame):
        """
        Inicializa o conselheiro financeiro com dados de transações
        
        Args:
            transactions_df (pd.DataFrame): DataFrame com transações financeiras
        """
        self.transactions_df = transactions_df
        
        # Inicializa gerador de texto (opcional, pode ser substituído)
        try:
            self.text_generator = pipeline('text-generation', model='gpt2')
        except:
            self.text_generator = None
    
    def analyze_financial_health(self) -> dict:
        """
        Analisa a saúde financeira com métricas importantes
        
        Returns:
            Dict com métricas financeiras
        """
        if self.transactions_df.empty:
            return {}
        
        # Agrupa por mês e tipo de transação
        monthly_summary = self.transactions_df.groupby(['month', 'type'])['value'].sum().unstack()
        
        # Calcula métricas
        metrics = {
            'total_revenue': monthly_summary.get('Receita', pd.Series(0, index=monthly_summary.index)).sum(),
            'total_expenses': monthly_summary.get('Despesa', pd.Series(0, index=monthly_summary.index)).sum(),
            'total_investments': monthly_summary.get('Investimento', pd.Series(0, index=monthly_summary.index)).sum(),
            'net_cashflow': monthly_summary.get('Receita', pd.Series(0, index=monthly_summary.index)).sum() - 
                            monthly_summary.get('Despesa', pd.Series(0, index=monthly_summary.index)).sum()
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
        """
        Gera dicas financeiras contextuais baseadas na análise de dados
        
        Returns:
            List[str]: Dicas financeiras personalizadas
        """
        metrics = self.analyze_financial_health()
        tips = []
        
        # Análise de receita vs despesas
        if metrics.get('net_cashflow', 0) < 0:
            tips.append("🚨 Suas despesas estão superando suas receitas. Considere um corte de gastos.")
        
        # Análise de investimentos
        investment_ratio = metrics.get('total_investments', 0) / max(metrics.get('total_revenue', 1), 1)
        if investment_ratio < 0.1:
            tips.append("💡 Seu percentual de investimentos está baixo. Tente investir pelo menos 10% da sua renda.")
        
        # Previsão de dívidas mensais
        for month in ['Janeiro', 'Fevereiro', 'Março']:
            predicted_debt = self.predict_monthly_debt(month)
            if predicted_debt > metrics.get('total_revenue', 0) * 0.5:
                tips.append(f"⚠️ Sua previsão de despesas para {month} está muito alta (mais de 50% da sua receita).")
                tips.append(f"🐖 Recomendo criar uma estratégia de economia nos meses anteriores para cobrir as despesas de {month}.")
        
        # Geração avançada de dicas com IA (se modelo disponível)
        if self.text_generator and len(tips) > 0:
            try:
                context = " ".join(tips)
                ai_tip = self.text_generator(
                    f"Considerando estas situações financeiras: {context}. Dê uma dica financeira concisa:", 
                    max_length=100
                )[0]['generated_text']
                tips.append(f"🤖 Dica de IA: {ai_tip}")
            except:
                pass
        
        # Dicas genéricas de backup
        if not tips:
            tips = [
                "💰 Mantenha um registro detalhado de suas finanças.",
                "🏦 Crie uma reserva de emergência equivalente a 3-6 meses de despesas.",
                "📊 Revise seus gastos mensalmente e ajuste seu orçamento."
            ]
        
        return tips[:5]  # Limita para 5 dicas

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
        
        with col1:
            month = st.selectbox("Mês", 
                ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'])
            
            category = st.text_input("Categoria (ex: Salário, Alimentação)")
        
        with col2:
            year = st.number_input("Ano", min_value=2020, max_value=2030, value=datetime.now().year)
            type_transaction = st.selectbox("Tipo", ['Receita', 'Despesa', 'Investimento'])
        
        value = st.number_input("Valor", min_value=0.0, format="%.2f")
        
        if st.button("Adicionar Transação"):
            tracker.add_transaction(month, year, category, type_transaction, value)
            st.success("Transação adicionada com sucesso!")
    
    elif choice == "Análise Financeira":
        st.subheader("📊 Consolidado Financeiro")
        
        # Seleção de ano para análise
        selected_year = st.selectbox("Selecione o Ano", 
            list(range(datetime.now().year, 2019, -1)))
        
        df_transactions = tracker.get_transactions(selected_year)
        
        if not df_transactions.empty:
            analysis = tracker.financial_analysis(df_transactions)
            
            if not analysis.empty:
                # Nova função de plotage
                fig = tracker.plot_financial_analysis(analysis)
                st.plotly_chart(fig)
                
                # Adiciona tabela de resumo
                st.dataframe(analysis)
            else:
                st.warning("Sem dados para análise")
        else:
            st.warning("Nenhuma transação registrada")
    
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


