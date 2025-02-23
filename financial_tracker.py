import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import plotly.express as px
import streamlit as st


class FinancialTracker:
    def __init__(self, user_id=None):
        """
        Inicializa o rastreador financeiro com conexão ao MongoDB e carregamento de ativos
        
        Args:
            user_id: ID do usuário atual para filtrar transações
        """
        # Conexão com MongoDB
        self.client = MongoClient(mongo_uri)
        self.db = self.client['financial_tracker']
        self.transactions_collection = self.db['transactions']
        self.investments_collection = self.db['investments']
        self.user_id = user_id
        
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
            'payment_date': None,
            'user_id': self.user_id  # Adiciona user_id à transação
        }
        self.transactions_collection.insert_one(transaction)



    def update_payment_status(self, transaction_id, paid=True):
        """
        Atualiza o status de pagamento de uma transação
        """
        from bson.objectid import ObjectId
        
        # Adiciona verificação de propriedade
        transaction = self.transactions_collection.find_one({
            '_id': ObjectId(transaction_id),
            'user_id': self.user_id
        })
        
        if not transaction:
            raise ValueError("Transação não encontrada ou não pertence ao usuário")
            
        updates = {
            'paid': paid,
            'payment_date': datetime.now() if paid else None
        }
        
        self.transactions_collection.update_one(
            {'_id': ObjectId(transaction_id), 'user_id': self.user_id},
            {'$set': updates}
        )

    def get_transactions(self, year=None):
        """
        Recupera transações, opcionalmente filtradas por ano
        
        Args:
            year (int, optional): Ano para filtrar as transações
            
        Returns:
            pd.DataFrame: DataFrame contendo as transações
        """
        # Base query com filtro de usuário
        query = {'user_id': self.user_id}
        
        # Adiciona filtro de ano se especificado
        if year is not None:
            query['year'] = year
            
        # Recupera transações do MongoDB
        transactions = list(self.transactions_collection.find(query))
        
        # Converte para DataFrame
        df = pd.DataFrame(transactions)
        
        if not df.empty:
            # Converte _id para string no próprio DataFrame
            df['_id'] = df['_id'].astype(str)
            
            # Adiciona colunas faltantes se necessário
            if 'paid' not in df.columns:
                df['paid'] = False
            if 'payment_date' not in df.columns:
                df['payment_date'] = None
                
        return df
    
    def get_transactions_for_display(self, year=None):
        """
        Recupera transações formatadas para exibição na interface
        
        Args:
            year (int, optional): Ano para filtrar as transações
            
        Returns:
            pd.DataFrame: DataFrame formatado para exibição
        """
        # Usa o método existente para obter as transações
        df = self.get_transactions(year)
        
        if not df.empty:
            # Os IDs já estão como strings desde o get_transactions
            # Seleciona apenas as colunas necessárias para exibição
            display_columns = ['_id', 'month', 'year', 'category', 'type', 'value', 
                             'observation', 'paid', 'payment_date']
            df = df[display_columns]
        
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
        """
        from bson.objectid import ObjectId
        
        # Verifica propriedade da transação
        transaction = self.transactions_collection.find_one({
            '_id': ObjectId(transaction_id),
            'user_id': self.user_id
        })
        
        if not transaction:
            raise ValueError("Transação não encontrada ou não pertence ao usuário")
        
        # Remove campos sensíveis dos updates
        updates.pop('_id', None)
        updates.pop('user_id', None)
        
        result = self.transactions_collection.update_one(
            {'_id': ObjectId(transaction_id), 'user_id': self.user_id}, 
            {'$set': updates}
        )
        return result.modified_count > 0
    
    def delete_transaction(self, transaction_id):
        """
        Deleta uma transação específica
        """
        from bson.objectid import ObjectId
        
        # Verifica propriedade antes de deletar
        result = self.transactions_collection.delete_one({
            '_id': ObjectId(transaction_id),
            'user_id': self.user_id
        })
        return result.deleted_count > 0

    def get_transactions_ids(self, year=None):
        """
        Recupera os IDs das transações
        """
        query = {} if year is None else {'year': year}
        transactions = list(self.transactions_collection.find(query, {'_id': 1}))
        return [str(trans['_id']) for trans in transactions]
