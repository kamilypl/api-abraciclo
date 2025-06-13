from flask import Flask, request, jsonify
import pdfplumber
import pandas as pd
from io import BytesIO
import re

app = Flask(__name__)

@app.route('/extrair-tabelas', methods=['POST'])
def extrair_tabelas():
    file = request.files['file']
    CABECALHO_PADRAO = ["MODELOS","cm³","JAN","FEV","MAR","ABR","MAI","TOTAL","%"]
    todas_as_tabelas = []

    with pdfplumber.open(BytesIO(file.read())) as pdf:
        for pagina in pdf.pages:
            # 1) Extrai todo o texto pra capturar fabricantes
            linhas = pagina.extract_text().split('\n')
            fabricantes = {
                idx: linha.strip()
                for idx, linha in enumerate(linhas)
                if re.fullmatch(r"[A-Z0-9ÁÉÍÓÚÇ ]+", linha.strip())
                   and linha.strip() not in CABECALHO_PADRAO
            }

            # 2) Extrai *todas* as tabelas da página
            tabelas_brutas = pagina.extract_tables()

            # 3) Filtra só as que realmente têm o header que queremos
            tabelas_válidas = [
                t for t in tabelas_brutas
                if t
                   and t[0]  # primeira linha não vazia
                   and len(t[0]) == len(CABECALHO_PADRAO)
                   and t[0] == CABECALHO_PADRAO
            ]

            # 4) Ordena fabricantes por posição no texto e zip com as tabelas
            makers_ordenados = [fab for _, fab in sorted(fabricantes.items())]

            for fabricante, tabela in zip(makers_ordenados, tabelas_válidas):
                df = pd.DataFrame(tabela[1:], columns=CABECALHO_PADRAO)
                df.insert(0, 'Fabricante', fabricante)
                todas_as_tabelas.append(df)

    if not todas_as_tabelas:
        return jsonify({"status": "erro", "msg": "Nenhuma tabela encontrada"}), 400

    df_final = pd.concat(todas_as_tabelas, ignore_index=True)
    output = BytesIO()
    df_final.to_excel(output, index=False)
    output.seek(0)
    return (
        output.getvalue(),
        200,
        {
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "Content-Disposition": "attachment; filename=saida_com_fabricante.xlsx"
        }
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
