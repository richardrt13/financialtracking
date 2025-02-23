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
