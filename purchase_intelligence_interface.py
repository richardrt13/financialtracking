import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from financial_advisor import FinancialAdvisor, tracker

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
