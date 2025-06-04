from flask import Flask, request, jsonify
import pdfplumber
import pandas as pd
import os

app = Flask(__name__)

@app.route('/extrair-tabelas', methods=['POST'])
def extrair_tabelas():
    # Diretórios
    pasta_entrada = "entrada_pdfs"
    pasta_saida = "saida_excel"
    # Nome fixo para o PDF de entrada
    nome_entrada = "entrada.pdf"
    caminho_entrada = os.path.join(pasta_entrada, nome_entrada)
    caminho_saida = os.path.join(pasta_saida, "saida.xlsx")
    
    # Cria as pastas se não existirem
    os.makedirs(pasta_entrada, exist_ok=True)
    os.makedirs(pasta_saida, exist_ok=True)

    file = request.files['file']

    # Remove o arquivo anterior se existir
    if os.path.exists(caminho_entrada):
        os.remove(caminho_entrada)

    # Salva sempre como "entrada.pdf"
    file.save(caminho_entrada)
    
    CABECALHO_PADRAO = ["MODELOS", "cm³", "JAN", "FEV", "MAR", "ABR", "TOTAL", "%"]
    todas_as_tabelas = []
    with pdfplumber.open(caminho_entrada) as pdf:
        for pagina in pdf.pages:
            tabelas = pagina.extract_tables()
            for tabela in tabelas:
                if tabela and len(tabela) > 1 and len(tabela[0]) == 8:
                    df = pd.DataFrame(tabela[1:], columns=CABECALHO_PADRAO)
                    todas_as_tabelas.append(df)
    if todas_as_tabelas:
        df_final = pd.concat(todas_as_tabelas, ignore_index=True)
        df_final.to_excel(caminho_saida, index=False)
        return jsonify({"status": "sucesso", "excel": caminho_saida})
    else:
        return jsonify({"status": "erro", "msg": "Nenhuma tabela encontrada"}), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
