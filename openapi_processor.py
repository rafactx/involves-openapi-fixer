# openapi_processor.py (Versão Definitiva e Corrigida)
import re
import logging
import random
from copy import deepcopy
from faker import Faker

class OpenApiProcessor:
    def __init__(self, openapi_data, config, translations):
        self.data = deepcopy(openapi_data)
        self.config = config
        self.translations = translations
        self.fake = Faker('pt_BR')
        # [CORREÇÃO] Nomes das chaves de estatísticas 100% padronizados
        self.stats = {
            "i18n_translated": 0,
            "operationId_fixed": 0,
            "params_enhanced": 0,
            "examples_added": 0,
            "schemas_renamed": 0,
            "params_centralized": 0,
            "req_bodies_centralized": 0,
            "global_headers_added": 0
        }
        self.seen_operation_ids = set()

    def run(self):
        logging.info("Iniciando o processo de correção do OpenAPI...")
        self._apply_config_rules()
        self._rename_invalid_component_names()
        self._centralize_components()
        self._process_paths()
        self._recursive_translate(self.data)
        self._cleanup_temp_fields(self.data)
        logging.info("Processo finalizado com sucesso.")
        return self.data

    def get_report(self):
        # [CORREÇÃO] Usando as chaves padronizadas
        report = "--- Relatório de Correções ---\n"
        report += f"Descrições (i18n) traduzidas: {self.stats['i18n_translated']}\n"
        report += f"Operation IDs corrigidos: {self.stats['operationId_fixed']}\n"
        report += f"Parâmetros aprimorados: {self.stats['params_enhanced']}\n"
        report += f"Exemplos de resposta gerados: {self.stats['examples_added']}\n"
        report += f"Propriedades de schema renomeadas: {self.stats['schemas_renamed']}\n"
        report += f"Parâmetros centralizados: {self.stats['params_centralized']}\n"
        report += f"Request Bodies centralizados: {self.stats['req_bodies_centralized']}\n"
        report += f"Operações com Headers Globais: {self.stats['global_headers_added']}\n"
        report += "------------------------------"
        return report

    def _apply_config_rules(self):
        logging.info("Aplicando regras do arquivo de configuração...")
        self.data.update(self.config.get('metadata', {}))
        components = self.data.setdefault('components', {})
        components.setdefault('schemas', {}).update(self.config.get('common_schemas', {}))
        components.setdefault('responses', {}).update(self.config.get('default_error_responses', {}))
        components.setdefault('securitySchemes', {}).update(self.config.get('security_schemes', {}))
        self.data['security'] = [{'BasicAuth': []}]
        if 'tags' in self.data and 'tag_map' in self.config:
            tag_map = self.config['tag_map']
            self.data['tags'] = [tag_map.get(tag.get('name'), tag) for tag in self.data['tags'] if tag.get('name') in tag_map]
            self.data['tags'].sort(key=lambda x: x['name'])

    def _rename_invalid_component_names(self):
        logging.info("Padronizando nomes de componentes...")
        if 'schemas' in self.data.get('components', {}):
            schemas = self.data['components']['schemas']
            new_schemas, rename_map = {}, {}
            for name, schema_def in schemas.items():
                new_name = re.sub(r'[^A-Za-z0-9_.-]', '', name.replace(' ', ''))
                if name != new_name:
                    rename_map[f'#/components/schemas/{name}'] = f'#/components/schemas/{new_name}'
                new_schemas[new_name] = schema_def
            self.data['components']['schemas'] = new_schemas
            if rename_map:
                self._update_all_refs(self.data, rename_map)

    def _update_all_refs(self, item, rename_map):
        if isinstance(item, dict):
            for key, value in item.items():
                if key == '$ref' and value in rename_map:
                    item[key] = rename_map[value]
                else:
                    self._update_all_refs(value, rename_map)
        elif isinstance(item, list):
            for i in item:
                self._update_all_refs(i, rename_map)

    def _centralize_components(self):
        logging.info("Centralizando componentes reutilizáveis...")
        params_config = self.config.get('global_parameters', {})
        self.data.setdefault('components', {}).setdefault('parameters', {}).update(params_config)

    def _process_paths(self):
        if 'paths' not in self.data: return
        for path_item in self.data.get('paths', {}).values():
            self._enhance_parameters(path_item) # Aprimora parâmetros a nível de path
            for method, operation in path_item.items():
                if isinstance(operation, dict):
                    self._fix_operation_id(method, operation)
                    self._apply_global_parameters(operation)
                    self._enhance_parameters(operation) # Aprimora parâmetros a nível de operação
                    self._add_default_responses(operation)
                    self._add_response_examples(operation)

    def _add_default_responses(self, operation):
        responses = operation.setdefault('responses', {})
        has_success = any(str(k).startswith('2') for k in responses)
        if not has_success and 'default' not in responses:
            responses['204'] = {'description': 'Operação bem-sucedida, sem conteúdo de retorno.'}
        for name in self.config.get('default_error_responses', {}).keys():
            code_map = {"badrequest": "400", "unauthorized": "401", "forbidden": "403", "notfound": "404"}
            code = code_map.get(name.lower(), "500")
            if code not in responses:
                responses[code] = {'$ref': f'#/components/responses/{name}'}

    def _enhance_parameters(self, item_with_params):
        for param in item_with_params.get('parameters', []):
            if isinstance(param, dict) and '$ref' not in param:
                if 'description' not in param:
                    param['description'] = '⚠️ Descrição ausente.'
                    self.stats['params_enhanced'] += 1

    def _generate_example_from_schema(self, schema, seen_refs=None):
        seen_refs = seen_refs or set()
        if schema.get('$ref'):
            ref_path = schema['$ref']
            if ref_path in seen_refs: return None
            seen_refs.add(ref_path)
            target_schema = self._dereference_schema(ref_path)
            return self._generate_example_from_schema(target_schema, seen_refs) if target_schema else {}
        if 'enum' in schema and schema['enum']: return random.choice(schema['enum'])

        schema_type = schema.get('type')
        prop_name = schema.get('x-prop-name', '')

        if schema_type == 'object':
            example = {}
            for name, prop in schema.get('properties', {}).items():
                prop['x-prop-name'] = name
                example[name] = self._generate_example_from_schema(prop, seen_refs)
            return example
        elif schema_type == 'array':
            return [self._generate_example_from_schema(schema.get('items', {}), seen_refs)]
        elif schema_type == 'string':
            if 'email' in prop_name: return self.fake.email()
            if prop_name == 'name': return self.fake.name()
            if 'description' in prop_name: return self.fake.sentence(nb_words=5)
            if schema.get('format') == 'date-time': return self.fake.iso8601()
            if schema.get('format') == 'date': return self.fake.date()
            return self.fake.word()
        elif schema_type == 'integer':
            min_val, max_val = schema.get('minimum', 1), schema.get('maximum', 999)
            if min_val > max_val: max_val = min_val + 100
            return self.fake.random_int(min=min_val, max=max_val)
        elif schema_type == 'boolean': return self.fake.boolean()
        return None

    def _dereference_schema(self, ref):
        parts = ref.strip('#/').split('/')
        node = self.data
        try:
            for part in parts: node = node.get(part)
            return node if node else None
        except (KeyError, TypeError): return None

    def _add_response_examples(self, operation):
        for code, response in operation.get('responses', {}).items():
            if str(code).startswith('2') and 'content' in response:
                content = response.get('content', {}).get('application/json')
                if content and 'schema' in content and 'example' not in content:
                    content['example'] = self._generate_example_from_schema(content['schema'])
                    self.stats['examples_added'] += 1

    def _recursive_translate(self, item):
        if isinstance(item, dict):
            for key, value in item.items():
                if key in ['description', 'summary'] and isinstance(value, str) and value.startswith('api.doc.'):
                    item[key] = self.translations.get(value, f"⚠️ {value}")
                    self.stats["i18n_translated"] += 1
                else: self._recursive_translate(value)
        elif isinstance(item, list):
            for i in item: self._recursive_translate(i)

    def _cleanup_temp_fields(self, item):
        if isinstance(item, dict):
            for key in list(item.keys()):
                if key.startswith('x-'): del item[key]
                else: self._cleanup_temp_fields(item[key])
        elif isinstance(item, list):
            for sub_item in item: self._cleanup_temp_fields(sub_item)

    def _fix_operation_id(self, method, operation):
        if not operation.get('operationId'):
            operation['operationId'] = f"{method}_operation_{self.fake.uri_path().replace('/', '')}"
            self.stats["operationId_fixed"] += 1

    def _apply_global_parameters(self, operation):
        params_config = self.config.get('global_parameters', {})
        if not params_config: return
        operation.setdefault('parameters', [])
        added_to_op = False
        for param_name in params_config:
            param_ref = f'#/components/parameters/{param_name}'
            if not any(p.get('$ref') == param_ref for p in operation.get('parameters', []) if isinstance(p, dict)):
                operation['parameters'].insert(0, {'$ref': param_ref})
                added_to_op = True
        if added_to_op: self.stats['global_headers_added'] += 1
