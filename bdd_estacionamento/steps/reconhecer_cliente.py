from behave import given, when,then
from estacionamento import *


@given ("o ambiente de reconhecimento foi preparado com sucesso"))
    def given_ambiente_reconhecimento_preparado(context):
        context.configuracao, context.clientes_reconhecidos, context.clientes_autorizados, context.clientes_em_vagas_reservadas, gerador_dados_falsos
    
    assert context.configuracao =! None
    
@
def 