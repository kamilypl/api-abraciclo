from flask import Flask, request, jsonify
import pdfplumber
import pandas as pd
import os

app = Flask(__name__)

@app.route('/extrair-tabelas', methods=['POST'])
def extrair_tabelas():
    file = request.files['file']
    entrada = os.path.join("entrada_pdfs", file.filename)
    saida = os.path.join("saida_excel", "saida.xlsx")
    file.save(entrada)
    
    CABECALHO_PADRAO = ["MODELOS", "cm³", "JAN", "FEV", "MAR", "ABR", "TOTAL", "%"]
    todas_as_tabelas = []
    with pdfplumber.open(entrada) as pdf:
        for pagina in pdf.pages:
            tabelas = pagina.extract_tables()
            for tabela in tabelas:
                if tabela and len(tabela) > 1 and len(tabela[0]) == 8:
                    df = pd.DataFrame(tabela[1:], columns=CABECALHO_PADRAO)
                    todas_as_tabelas.append(df)
    if todas_as_tabelas:
        df_final = pd.concat(todas_as_tabelas, ignore_index=True)
        df_final.to_excel(saida, index=False)
        return jsonify({"status": "sucesso", "excel": saida})
    else:
        return jsonify({"status": "erro", "msg": "Nenhuma tabela encontrada"}), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
