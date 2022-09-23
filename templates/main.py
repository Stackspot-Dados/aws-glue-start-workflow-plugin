from src import glue_client
from src.utils import utils
import boto3
from datetime import datetime
import logging
import json
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

glue = boto3.client('glue', region_name='sa-east-1')

def get_environment_variable(environment_variable_name): 
    logger.setLevel(logging.INFO) 
    try: 
        logger.info( 
            "INFO: Obtendo valor da variável de ambiente {}" 
            .format(environment_variable_name) 
        ) 
        environment_variable_value = os.environ[environment_variable_name]
       
        return environment_variable_value
    except Exception as e:
         logger.error(e)
         logger.error( 
            "ERROR: A variável de ambiente {} não existe" 
            .format(environment_variable_name) 
        )

def acionar_workflow(workflow_name):
    try:
        logger.info(
            "INFO: Inicializando o workflow (Glue) - Workflow: {}"
            .format(workflow_name)
        )
        response_start_workflow_run = glue.start_workflow_run(
            Name=workflow_name
        )
        return response_start_workflow_run

    except Exception as e:
        logger.error(e)
        logger.error(
            "ERROR: Erro ao inicializar o workflow (Glue) - Workflow: {}"
            .format(workflow_name)
        )


def set_propriedades_execucao_workflow(
        workflow_name,
        workflow_run_id,
        run_properties
        ):
    try:
        logger.info(
            "INFO: Adicionando as propriedades de execução no workflow - \
            Workflow: {} | Run properties: {} "
            .format(workflow_name, run_properties)
        )
        glue.put_workflow_run_properties(
            Name=workflow_name,
            RunId=workflow_run_id,
            RunProperties=run_properties
        )
        return {
            'workflow_name': workflow_name,
            'workflow_run_id': workflow_run_id,
            'run_properties': run_properties
        }
    except Exception as e:
        logger.error(e)
        logger.error(
            "ERROR: Erro na passagem das propriedades para \
            o workflow (Glue) - Workflow: {}".format(workflow_name)
        )

def lambda_handler(event, context):

    list_event = filter_payload_sqs(event)

    for event in list_event:

        if ("/export_info_" not in event['detail']['object']['key']):
            logger.info(
                "INFO: Aguardando a exportação do snapshot \
                para o S3 ser finalizada com sucesso"
            )
            return {
                'message': 'Snapshot não encontrado',
                'statusCode': 404
            }

        logger.info(event)
        WORKFLOW_NAME = utils.get_environment_variable('WORKFLOW_NAME')
        run_properties = create_workflow_run_properties(
            event['detail']['bucket']['name'],
            event['detail']['object']['key'])
        response_start_workflow_run = glue_client\
            .acionar_workflow(WORKFLOW_NAME)
        glue_client.set_propriedades_execucao_workflow(
            WORKFLOW_NAME,
            response_start_workflow_run['RunId'],
            run_properties
        )

        return {
            'workflow': WORKFLOW_NAME,
            'runIdWorkflow': response_start_workflow_run['RunId'],
            'runProperties': run_properties,
            'datetime': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'statusCode': 200
        }


def create_workflow_run_properties(bucket_name, key_object_detail):
    key_object_detail = key_object_detail.split('/')[0:2]
    prefixo_pasta = '/'.join(key_object_detail) + '/'

    DICT_BUCKETS_DBS = utils.get_environment_variable('JSON_DICT_BUCKETS_DBS')

    try:
        logger.info(
            "INFO: Criando as propriedades de execução do workflow (Glue)"
        )
        DICT_BUCKETS_DBS = json.loads(DICT_BUCKETS_DBS)
        data_base_glue = DICT_BUCKETS_DBS[
            '/'.join([bucket_name, key_object_detail[0]]) + '/'
        ]
    except ValueError:
        raise ValueError(
            "ERROR: Erro ao carregar JSON da variável de \
            ambiente DICT_BUCKETS_DBS"
        )
    except KeyError:
        raise KeyError(
            "ERROR: Não foi encontrado o banco de dados associado ao \
            bucket de exportação do snapshot - Bucket: {} | DB: ?"
            .format('/'.join([bucket_name, key_object_detail[0]]) + '/')
        )

    dictionary = {
        'BUCKET_NOME': bucket_name,
        'PREFIXO_PASTA_S3': prefixo_pasta,
        'DATABASE_GLUE': data_base_glue
    }

    logger.info(
        'Propriedades de execução do workflow (Glue): {}'
        .format(dictionary)
    )

    return dictionary


def filter_payload_sqs(event):

    list = []

    if event.get("Records", False):
        logger.info("Origem evento SQS")
        for x in event.get("Records"):
            payload = json.loads(json.loads(x.get('body')).get("Message"))

            list.append(payload)

        return list

    return [event]