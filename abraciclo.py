from flask import Flask, request, jsonify
import pdfplumber
import pandas as pd
from io import BytesIO
import re

app = Flask(__name__)

@app.route('/extrair-tabelas', methods=['POST'])
def extrair_tabelas():
    # 1. Recebe o PDF enviado em memória
    file = request.files['file']

    # 2. Define o cabeçalho fixo de 9 colunas (incluindo MAI)
    CABECALHO_PADRAO = ["MODELOS", "cm³", "JAN", "FEV", "MAR", "ABR", "MAI", "TOTAL", "%"]
    todas_as_tabelas = []

    # 3. Abre o PDF em BytesIO (sem tocar no disco)
    with pdfplumber.open(BytesIO(file.read())) as pdf:
        for pagina in pdf.pages:
            # 4. Extrai todo o texto da página e quebra em linhas
            linhas = pagina.extract_text().split('\n')

            # 5. Detecta fabricantes: linhas em maiúsculas que não são o cabeçalho
            fabricantes = {
                idx: linha.strip()
                for idx, linha in enumerate(linhas)
                if re.fullmatch(r"[A-Z0-9ÁÉÍÓÚÇ ]+", linha.strip())
                   and linha.strip() not in CABECALHO_PADRAO
            }

            # 6. Extrai todas as tabelas brutas da página
            tabelas_brutas = pagina.extract_tables()

            # 7. Filtra só as tabelas cujo primeiro row == nosso cabeçalho
            tabelas_validas = [
                t for t in tabelas_brutas
                if t and t[0] == CABECALHO_PADRAO
            ]

            # 8. Ordena fabricantes pela posição no texto e associa a cada tabela
            makers_ordenados = [fab for _, fab in sorted(fabricantes.items())]
            for fabricante, tabela in zip(makers_ordenados, tabelas_validas):
                # 9. Constrói o DataFrame e insere a coluna ‘Fabricante’
                df = pd.DataFrame(tabela[1:], columns=CABECALHO_PADRAO)
                df.insert(0, 'Fabricante', fabricante)
                todas_as_tabelas.append(df)

    # 10. Se não encontrou nada, retorna erro
    if not todas_as_tabelas:
        return jsonify({"status": "erro", "msg": "Nenhuma tabela encontrada"}), 400

    # 11. Concatena todos os DataFrames e gera o Excel em memória
    df_final = pd.concat(todas_as_tabelas, ignore_index=True)
    output = BytesIO()
    df_final.to_excel(output, index=False)
    output.seek(0)

    # 12. Envia o binário do Excel como attachment
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
