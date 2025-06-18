# fix_openapi.py (Versão Final Simplificada)
import argparse
import json
import yaml
import sys
import logging
from pathlib import Path
from openapi_processor import OpenApiProcessor # Continua usando nosso processador avançado

def main():
    """Função principal para orquestrar a correção do OpenAPI."""
    parser = argparse.ArgumentParser(
        description="Ferramenta para corrigir e enriquecer especificações OpenAPI a partir de um dicionário consolidado."
    )
    # Argumentos apontam para arquivos específicos, com padrões inteligentes
    parser.add_argument('-i', '--input', default='openapi.yaml',
                        help='Caminho para o arquivo OpenAPI de entrada. Padrão: openapi.yaml')
    parser.add_argument('-d', '--dictionary', default='dictionary.json',
                        help='Caminho para o arquivo de dicionário JSON consolidado. Padrão: dictionary.json')
    parser.add_argument('-c', '--config', default='config.yaml',
                        help='Caminho para o arquivo de configuração. Padrão: config.yaml')
    parser.add_argument('-o', '--output', default='dist/openapi.fixed.yaml',
                        help='Caminho completo para o arquivo de saída. Padrão: dist/openapi.fixed.yaml')
    args = parser.parse_args()

    # Configuração inicial do logging
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    try:
        # 1. Carregar o arquivo de configuração
        logging.info(f"Carregando configuração de '{args.config}'...")
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 2. Carregar o dicionário de tradução consolidado
        logging.info(f"Carregando dicionário de '{args.dictionary}'...")
        with open(args.dictionary, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        logging.info(f"Total de {len(translations)} chaves de tradução carregadas.")

        # 3. Carregar o arquivo OpenAPI base
        logging.info(f"Carregando OpenAPI base de '{args.input}'...")
        with open(args.input, 'r', encoding='utf-8') as f:
            openapi_data = yaml.safe_load(f)

        # 4. Processar os dados com a classe que já temos
        processor = OpenApiProcessor(openapi_data, config, translations)
        fixed_data = processor.run()

        # 5. Salvar o resultado
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True) # Garante que o diretório de saída exista

        # Reordenar as chaves para um output padrão e mais limpo
        ORDER = ['openapi', 'info', 'servers', 'security', 'tags', 'paths', 'components']
        reordered_data = {k: fixed_data.get(k) for k in ORDER if k in fixed_data}
        reordered_data.update({k: v for k, v in fixed_data.items() if k not in reordered_data})

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(reordered_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False, width=120)

        print("\n" + "="*50)
        print(f"✅ Arquivo final gerado com sucesso em: {output_path}")
        print("="*50)
        print(processor.get_report())

    except FileNotFoundError as e:
        logging.error(f"ARQUIVO NÃO ENCONTRADO: {e}. Verifique o caminho ou use os argumentos --input, --dictionary, --config.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Ocorreu um erro inesperado: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
