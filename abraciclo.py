from flask import Flask, request, jsonify
import pdfplumber
import pandas as pd
from io import BytesIO
import re

app = Flask(__name__)

@app.route('/extrair-tabelas', methods=['POST'])
def extrair_tabelas():
    file = request.files['file']
    CABECALHO_PADRAO = ["MODELOS", "cm³", "JAN", "FEV", "MAR", "ABR", "MAI", "TOTAL", "%"]
    todas_as_tabelas = []

    with pdfplumber.open(BytesIO(file.read())) as pdf:
        for pagina in pdf.pages:
            # 1. Leia todo o texto para capturar fabricantes
            linhas = pagina.extract_text().split('\n')
            fabricantes = {}
            for idx, linha in enumerate(linhas):
                text = linha.strip()
                # Se for todo maiúsculas (e não for o próprio cabeçalho):
                if re.fullmatch(r"[A-Z0-9ÁÉÍÓÚÇ ]+", text) and text not in CABECALHO_PADRAO:
                    fabricantes[idx] = text

            # 2. Extraia as tabelas
            tabelas = pagina.extract_tables()
            # Encontrar onde cada tabela “começa” no texto
            # Para simplificar, achamos o índice da linha de cabeçalho em linhas[]
            starts = [i for i, l in enumerate(linhas)
                      if l.strip().split() == CABECALHO_PADRAO]

            # Zip garante que o primeiro cabeçalho “captura” a primeira tabela, e assim por diante
            for start_idx, tabela in zip(starts, tabelas):
                df = pd.DataFrame(tabela[1:], columns=CABECALHO_PADRAO)
                # 3. Achar o fabricante mais próximo acima do cabeçalho
                prev_idxs = [i for i in fabricantes if i < start_idx]
                maker_idx = max(prev_idxs) if prev_idxs else None
                fabricante_corrente = fabricantes.get(maker_idx, "DESCONHECIDO")
                # 4. Adicionar coluna
                df.insert(0, 'Fabricante', fabricante_corrente)
                todas_as_tabelas.append(df)

    if todas_as_tabelas:
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
    else:
        return jsonify({"status": "erro", "msg": "Nenhuma tabela encontrada"}), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
