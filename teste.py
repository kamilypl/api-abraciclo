from flask import Flask, request, jsonify
import pdfplumber
import pandas as pd
from io import BytesIO

app = Flask(__name__)

@app.route('/extrair-tabelas', methods=['POST'])
def extrair_tabelas():
    file = request.files['file']
    # O segredo aqui: trabalhar com BytesIO
    CABECALHO_PADRAO = ["MODELOS", "cm³", "JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET","OUT", "NOV", "DEZ", "TOTAL", "%"]
    todas_as_tabelas = []
    with pdfplumber.open(BytesIO(file.read())) as pdf:
        for pagina in pdf.pages:
            tabelas = pagina.extract_tables()
            for tabela in tabelas:
                if tabela and len(tabela) > 1 and len(tabela[0]) == 16:
                    df = pd.DataFrame(tabela[1:], columns=CABECALHO_PADRAO)
                    todas_as_tabelas.append(df)
    if todas_as_tabelas:
        df_final = pd.concat(todas_as_tabelas, ignore_index=True)
        # Agora vamos devolver o Excel direto como resposta, sem salvar no disco!
        output = BytesIO()
        df_final.to_excel(output, index=False)
        output.seek(0)
        return (
            output.getvalue(),  # Binário do arquivo
            200,
            {
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "Content-Disposition": "attachment; filename=saida.xlsx"
            }
        )
    else:
        return jsonify({"status": "erro", "msg": "Nenhuma tabela encontrada"}), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
