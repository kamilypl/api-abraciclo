import pdfplumber
import pandas as pd
import os

entrada = os.path.join("entrada_pdfs", "entrada.pdf")
saida = os.path.join("saida_excel", "saida.xlsx")

CABECALHO_PADRAO = ["MODELOS", "cm³", "JAN", "FEV", "MAR", "ABR", "TOTAL", "%"]

def extrair_tabelas_pdf():
    todas_as_tabelas = []
    with pdfplumber.open(entrada) as pdf:
        for pagina in pdf.pages:
            tabelas = pagina.extract_tables()
            for tabela in tabelas:
                # Verifica se é tabela válida com 8 colunas
                if tabela and len(tabela) > 1 and len(tabela[0]) == 8:
                    df = pd.DataFrame(tabela[1:], columns=CABECALHO_PADRAO)
                    todas_as_tabelas.append(df)

    if todas_as_tabelas:
        df_final = pd.concat(todas_as_tabelas, ignore_index=True)
        df_final.to_excel(saida, index=False)
        print("Extração reestruturada com sucesso!")
    else:
        print("Nenhuma tabela no formato esperado encontrada.")

if __name__ == "__main__":
    extrair_tabelas_pdf()

