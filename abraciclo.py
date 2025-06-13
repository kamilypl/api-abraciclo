from flask import Flask, request, jsonify
import pdfplumber
import pandas as pd
from io import BytesIO
import re

app = Flask(__name__)

def normaliza(linha):
    # Deixa tudo minúsculo, sem espaços nas pontas e troca '³' por '3'
    return [str(col).strip().lower().replace('³', '3') for col in linha]

@app.route('/extrair-tabelas', methods=['POST'])
def extrair_tabelas():
    file = request.files['file']
    CABECALHO_PADRAO = ["MODELOS", "cm³", "JAN", "FEV", "MAR", "ABR", "MAI", "TOTAL", "%"]
    todas_as_tabelas = []

    with pdfplumber.open(BytesIO(file.read())) as pdf:
        for pagina in pdf.pages:
            linhas = pagina.extract_text().split('\n')

            # Encontra linhas em maiúsculas (potenciais fabricantes)
            fabricantes = {
                idx: linha.strip()
                for idx, linha in enumerate(linhas)
                if re.fullmatch(r"[A-Z0-9ÁÉÍÓÚÇ ]+", linha.strip())
                   and linha.strip() not in CABECALHO_PADRAO
            }

            tabelas_brutas = pagina.extract_tables()

            tabelas_validas = []
            for tabela in tabelas_brutas:
                if tabela and len(tabela[0]) == 9 and normaliza(tabela[0]) == normaliza(CABECALHO_PADRAO):
                    tabelas_validas.append(tabela)
                # Debug opcional: veja o que está vindo do PDF!
                # print("CABEÇALHO EXTRAÍDO:", tabela[0])

            makers_ordenados = [fab for _, fab in sorted(fabricantes.items())]
            for fabricante, tabela in zip(makers_ordenados, tabelas_validas):
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
