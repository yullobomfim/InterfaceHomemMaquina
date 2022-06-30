#Importando as bibiliotecas
import face_recognition
import secrets
import random
import faker
import simpy
import json

FOTOS_MOTORISTAS = [
                "/home/yullo/dev/ifba/IHM/estacionamento/faces/ayrton1.jpeg",
                "/home/yullo/dev/ifba/IHM/estacionamento/faces/ayrton2.jpeg",
                "/home/yullo/dev/ifba/IHM/estacionamento/faces/ayrton3.jpeg",
                "/home/yullo/dev/ifba/IHM/estacionamento/faces/roberto1.jpeg",
                "/home/yullo/dev/ifba/IHM/estacionamento/faces/roberto2.jpeg",
                "/home/yullo/dev/ifba/IHM/estacionamento/faces/roberto3.jpeg", 
                "/home/yullo/dev/ifba/IHM/estacionamento/faces/zeca1.jpeg",
                "/home/yullo/dev/ifba/IHM/estacionamento/faces/zeca2.jpeg",
                "/home/yullo/dev/ifba/IHM/estacionamento/faces/zeca3.jpeg",                
                "/home/yullo/dev/ifba/IHM/estacionamento/faces/rubinho1.jpeg",
                "/home/yullo/dev/ifba/IHM/estacionamento/faces/rubinho2.jpeg",
                "/home/yullo/dev/ifba/IHM/estacionamento/faces/rubinho3.jpeg"                
]
ARQUIVO_CONFIGURACAO = "/home/yullo/dev/ifba/IHM/estacionamento/configuracao.json"

PROBABILIDADE_A1 = 6
PROBABILIDADE_A2 = 36
PROBABILIDADE_A3 = 6
PROBABILIDADE_B1 = 9
PROBABILIDADE_B2 = 1
PROBABILIDADE_B3 = 3

PROBABILIDADE_DE_SER_AUTORIZADO = 30
PROBABILIDADE_DE_SER_LIBERADO = 100 - PROBABILIDADE_DE_SER_AUTORIZADO
PROBABILIDADE_NECESSIDADE_DE_VAGA = 5
PROBABILIDADE_DE_LIBERACAO_DA_VAGA = 30

CAPACIDADE_MAXIMA_ESTACIONAMENTO = 5

TEMPO_ENTRE_CLIENTES = 150
TEMPO_RECONHECIMENTO_AUTORIZACAO = 60
TEMPO_VERIFICACAO_DISPONIBILIDADE_VAGAS = 60
TEMPO_LIBERACAO_CLIENTE = 90
TEMPO_LIBERACAO_VAGAS = 500

#Preparando o ambiente de reconhecimento
def preparar():
    configuracao = None
    with open(ARQUIVO_CONFIGURACAO, "r") as arquivo_configuracao:
        configuracao = json.load(arquivo_configuracao)
        if configuracao:
            print("--------------------------------------------------------------------------")
            print("----------------ESTACIONAMENTO DIGITAL INTELIGENTE-----------------------")
            print("--------------------------------------------------------------------------")
            print("Arquivos de configuração carregados")
            print("versão da simulação:", configuracao["versao"])
            print("--------------------------------------------------------------------------")

    clientes_reconhecidos = {}
    clientes_autorizados = {}
    clientes_em_vagas_reservadas = {}
    gerador_dados_falsos = faker.Faker(locale="pt_BR")

    total_vagas = {
        "A1": (random.randint(1, 100) <= PROBABILIDADE_A1),
        "A2": (random.randint(1, 100) <= PROBABILIDADE_A2),
        "A3": (random.randint(1, 100) <= PROBABILIDADE_A3),
        "B1": (random.randint(1, 100) <= PROBABILIDADE_B1),
        "B2": (random.randint(1, 100) <= PROBABILIDADE_B2),
        "B3": (random.randint(1, 100) <= PROBABILIDADE_B3)
    }

    return configuracao, clientes_reconhecidos, clientes_autorizados, clientes_em_vagas_reservadas, gerador_dados_falsos

# Simulando o reconhecimento de cliente e um motorista
def simular_estacionamento():
    motorista = {
        "foto": random.choice(FOTOS_MOTORISTAS),
        "cliente": None
    }

    return motorista

def reconhecer_cliente(motorista):

    print("iniciando o reconhecimento de motoristas...")
    foto_motorista = face_recognition.load_image_file(motorista["foto"])
    encoding_foto_motorista = face_recognition.face_encodings(foto_motorista)[0]

    reconhecido = False
    for cliente in configuracao["clientes"]:
        fotos_banco = cliente["fotos"]
        total_reconhecimentos = 0

        for foto in fotos_banco:
            foto_banco = face_recognition.load_image_file(foto)
            encoding_foto_banco = face_recognition.face_encodings(foto_banco)[0]

            foto_reconhecida = face_recognition.compare_faces([encoding_foto_motorista], encoding_foto_banco)[0]
            if foto_reconhecida:
                total_reconhecimentos += 1

        if total_reconhecimentos/len(fotos_banco) > 0.7:
            reconhecido = True

            motorista["cliente"] = {}
            motorista["cliente"]["nome"] = gerador_dados_falsos.name()
            motorista["cliente"]["mensalista"] = random.randint(1, 100)
            motorista["cliente"]["status"] = gerador_dados_falsos.address()
            motorista["cliente"]["vagas"] = random.choice(["A1", "A2", "A3", "B1", "B2", "B3"])

    return reconhecido, motorista

def imprimir_cliente(cliente):
    print("*****************************************************************************")
    print("nome:", cliente["cliente"]["nome"])
    print("tipo de vagas:", cliente["cliente"]["vagas"])
    print("*****************************************************************************")

def reconhecer_motorista(env):

    while True:
        print("--------------------------------------------------------------------------")
        print("reconhecendo um cliente ", env.now)
        
        motorista = simular_estacionamento()
        reconhecido, cliente = reconhecer_cliente(motorista)
        if reconhecido:
            id_atendimento = secrets.token_hex(nbytes=16).upper()
            clientes_reconhecidos[id_atendimento] = cliente
            print("--------------------------------------------------------------------------")
            print("um cliente foi reconhecido, imprimindo vagas...")
            print("--------------------------------------------------------------------------")
            imprimir_cliente(cliente)
        else:
            print("--------------------------------------------------------------------------")
            print("não foi reconhecido um cliente")
            print("--------------------------------------------------------------------------")

        yield env.timeout(TEMPO_ENTRE_CLIENTES)


def identificar_autorizacao(env):

    while True:
        if len(clientes_reconhecidos):
            print("--------------------------------------------------------------------------")
            print("verificando situacao de autorizacao ", env.now)
            total_clientes_autorizados = 0
            for id_atendimento, cliente in list(clientes_reconhecidos.items()):
                autorizacao_reconhecida = (random.randint(1, 100) <= PROBABILIDADE_DE_SER_AUTORIZADO)
                if autorizacao_reconhecida:
                    cliente["mensalista"] = False
                    clientes_autorizados[id_atendimento] = cliente
                    clientes_reconhecidos.pop(id_atendimento)
                    print("--------------------------------------------------------------------------")
                    print("cliente", cliente["cliente"]["nome"], "em situacao de autorizacao")
                    print("--------------------------------------------------------------------------")
                    total_clientes_autorizados += 1

            timeout = 1
            if total_clientes_autorizados > 0:
                timeout = total_clientes_autorizados * TEMPO_RECONHECIMENTO_AUTORIZACAO

            yield env.timeout(timeout)
        else:
            yield env.timeout(1)

def liberar_cliente(env):

    while True:
        if len(clientes_reconhecidos):
            print("--------------------------------------------------------------------------")
            print("verificando liberacao de cliente ", env.now)
            total_liberacoes = 0
            for id_atendimento, cliente in list(clientes_reconhecidos.items()):
                cliente_liberado = (random.randint(1, 100) <= PROBABILIDADE_DE_SER_LIBERADO)
                if cliente_liberado:
                    print("--------------------------------------------------------------------------")
                    print("cliente", cliente["cliente"]["nome"], "sendo liberado")
                    print("--------------------------------------------------------------------------")
                    clientes_reconhecidos.pop(id_atendimento)

                    total_liberacoes += 1

            timeout = 1
            if total_liberacoes > 0:
                timeout = total_liberacoes * TEMPO_LIBERACAO_CLIENTE

            yield env.timeout(timeout)
        else:
            yield env.timeout(1)

def disponibilizar_vagas(env):

    while True:
        if len(clientes_autorizados):
            print("--------------------------------------------------------------------------")
            print("verificando disponibilidade de vagas ", env.now)
            
            total_verificacoes_vagas = 0
            for cliente in clientes_autorizados.values():
                if not cliente["mensalista"]:
                    tipo_vagas = cliente["cliente"]["vagas"]
                    tem_vagas = total_vagas[tipo_vagas]
                    if tem_vagas:
                        print("--------------------------------------------------------------------------")
                        print("tem vagas do tipo", tipo_vagas, "para o cliente", cliente["cliente"]["nome"])
                    else:
                        print("--------------------------------------------------------------------------")
                        print("não tem vagas do tipo", tipo_vagas, "para o cliente", cliente["cliente"]["nome"])
                    cliente["mensalista"] = True
                    total_verificacoes_vagas += 1

            timeout = 1
            if total_verificacoes_vagas > 0:
                timeout = total_verificacoes_vagas * TEMPO_VERIFICACAO_DISPONIBILIDADE_VAGAS

            yield env.timeout(timeout)
        else:
            yield env.timeout(1)


def reservar_vaga(env):

    while True:
        if len(clientes_autorizados):
            print("verificando disponibilidade de Vagas para os clientes", env.now)

            if len(clientes_em_vagas_reservadas) == CAPACIDADE_MAXIMA_ESTACIONAMENTO:
                print("não há vagas")

                yield env.timeout(1)
            else:
                total_clientes_em_vagas_reservadas = 0
                for id_atendimento, cliente in list(clientes_autorizados.items()):
                    necessita_vagas = (random.randint(1, 100) <= PROBABILIDADE_NECESSIDADE_DE_VAGA)
                    if necessita_vagas:
                        clientes_em_vagas_reservadas[id_atendimento] = cliente
                        clientes_autorizados.pop(id_atendimento)

                        print("cliente", cliente["cliente"]["nome"], "necessita de Vagas")

                        total_clientes_em_vagas_reservadas += 1

                timeout = 1
                if total_clientes_em_vagas_reservadas > 0:
                    timeout = total_clientes_em_vagas_reservadas * TEMPO_RECONHECIMENTO_AUTORIZACAO

                yield env.timeout(timeout)
        else:
            yield env.timeout(1)


def liberar_vaga(env):

    while True:
        if len(clientes_em_vagas_reservadas):
            print("verificando liberacao de Vagas em ciclo/tempo", env.now)

            total_liberacoes_vagas = 0
            for id_atendimento, cliente in list(clientes_em_vagas_reservadas.items()):
                liberar_vaga = (random.randint(1, 100) <= PROBABILIDADE_DE_LIBERACAO_DA_VAGA)

                if liberar_vaga:
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                    print("O cliente", cliente["cliente"]["nome"], "está deixando o estacionamento e liberando da Vaga")
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                    clientes_em_vagas_reservadas.pop(id_atendimento)
                    total_liberacoes_vagas += 1

            timeout = 1
            if total_liberacoes_vagas > 0:
                timeout = total_liberacoes_vagas * TEMPO_LIBERACAO_VAGAS 
            yield env.timeout(timeout)
        else:
            yield env.timeout(1)
