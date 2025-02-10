import streamlit.components.v1 as components
import streamlit as st

def custom_select(label, options, key=None):
    # HTML e JavaScript para o select customizado
    select_html = f"""
    <div style="font-family: -apple-system, system-ui, sans-serif;">
        <label style="font-size: 14px; color: rgb(49, 51, 63);">{label}</label>
        <select id="custom-select" style="width: 100%; padding: 8px; margin-top: 4px; 
                border: 1px solid #ccc; border-radius: 4px; background-color: white;
                font-size: 14px; color: rgb(49, 51, 63);">
            {' '.join(f'<option value="{opt}">{opt}</option>' for opt in options)}
        </select>
    </div>
    <script>
        // Impede o teclado virtual de aparecer em dispositivos móveis
        document.getElementById('custom-select').addEventListener('touchstart', function(e) {{
            e.preventDefault();
            this.focus();
        }});
    </script>
    """
    
    # Renderiza o componente HTML
    components.html(select_html, height=70)

