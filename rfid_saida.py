import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from time import sleep
import signal
import sys
import requests
import pika
import datetime

# Configurações de hardware
GPIO.setmode(GPIO.BOARD)
BUZZER_SAIDA = 13
CS_SAIDA = 24  
SERVO_SAIDA_PIN = 12
LED_VERMELHO_SAIDA = 16  
LED_VERDE_SAIDA = 18

GPIO.setup(BUZZER_SAIDA, GPIO.OUT)
GPIO.setup(CS_SAIDA, GPIO.OUT)
GPIO.setup(SERVO_SAIDA_PIN, GPIO.OUT)
GPIO.setup(LED_VERMELHO_SAIDA, GPIO.OUT)
GPIO.setup(LED_VERDE_SAIDA, GPIO.OUT)

# Configuração do PWM para os servos
servoSaida = GPIO.PWM(SERVO_SAIDA_PIN, 50)  # Frequência de 50Hz

def angle_to_percent (angle) :
    if angle > 180 or angle < 0 :
        return False

    start = 4
    end = 12.5
    ratio = (end - start)/180 #Calcul ratio from angle to percent

    angle_as_percent = angle * ratio

    return start + angle_as_percent

servoSaida.start(angle_to_percent(0))  # Inicializa em 0 graus

leitorRFID_saida = SimpleMFRC522()

# URL da API
URL_API = "http://10.1.24.62:5000"
URL_RABBIT = "amqps://uxtpvazt:ug2EvD1w4EuMnAlH2yuDT9E35gwnPU8M@prawn.rmq.cloudamqp.com/uxtpvazt"

def enviar_mensagem_rabbitmq(placa, data_hora_entrada):
    URL=pika.URLParameters(URL_RABBIT)
    connection = pika.BlockingConnection(URL)
    channel = connection.channel()
    channel.queue_declare(queue='estacionamento')

    mensagem = f"Saída: {placa};{data_hora_entrada}"
    channel.basic_publish(exchange='', routing_key='estacionamento', body=mensagem)
    print(f"Mensagem enviada para RabbitMQ: {mensagem}")
    connection.close()

# Funções para o buzzer
def tocar_buzzer(frequencia, duracao, buzzer):
    p = GPIO.PWM(buzzer, frequencia)
    p.start(50)
    sleep(duracao)
    p.stop()

def buzzer_erro(buzzer, ledvermelho):
    tocar_buzzer(200, 0.5, buzzer)
    GPIO.output(ledvermelho, GPIO.HIGH)  # Liga LED vermelho
    sleep(2)  # Aguarda 2 segundos
    GPIO.output(ledvermelho, GPIO.LOW)  # Desliga LED vermelho após 2 segundos

def buzzer_sucesso(buzzer, ledverde):
    tocar_buzzer(1000, 0.5, buzzer)
    GPIO.output(ledverde, GPIO.HIGH)     # Liga LED verde
    sleep(2)  # Aguarda 2 segundos
    GPIO.output(ledverde, GPIO.LOW)  # Desliga LED verde após 2 segundos

# Função para abrir e fechar a cancela
def abrir_cancela(servo):
    servo.ChangeDutyCycle(angle_to_percent(90))  # Ajuste para abrir (aproximadamente 90 graus)
    sleep(5)  # Aguarda 5 segundos para fechar
    servo.ChangeDutyCycle(angle_to_percent(0))  # Para o PWM (cancela fecha)
    sleep(1)  # Aguarda um segundo antes de permitir o próximo movimento

# Função para finalizar o programa
def finalizar_programa(signal, frame):
    print("\nFinalizando o programa...")
    servoSaida.stop()    # Para o PWM do servo de saída
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, finalizar_programa)


def ler_tag(cs_pin, leitor):
    # Ativar CS do leitor desejado
    GPIO.output(cs_pin, GPIO.LOW)
    sleep(0.1)  # Pequeno delay para estabilizar

    # Leitura
    try:
        tag_id, _ = leitor.read()
        return int(tag_id)
    except Exception as e:
        print(f"Erro ao ler o RFID: {e}")
        sleep(0.1)

    return None

def processar_saida(tag):
    response = requests.get(f"{URL_API}/carros/{tag}")
    if response.status_code == 200:
        carro = response.json()
        placa = carro.get('placa')
        if placa:
            buzzer_sucesso(BUZZER_SAIDA, LED_VERDE_SAIDA)  # Sucesso na saída
            abrir_cancela(servoSaida)  # Abre a cancela de saída

            # Enviar dados para RabbitMQ
            data_hora_entrada = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            enviar_mensagem_rabbitmq(placa, data_hora_entrada)
            
            response = requests.post(f"{URL_API}/sair", json={'carro_id': tag})
            if response.status_code == 200:
                print("Saída registrada com sucesso.")
            else:
                print("Erro ao registrar saída.")
                buzzer_erro(BUZZER_SAIDA, LED_VERMELHO_SAIDA)
        else:
            print("ID não reconhecido.")
            buzzer_erro(BUZZER_SAIDA, LED_VERMELHO_SAIDA)
    else:
        print("Erro ao buscar dados do carro.")
        buzzer_erro(BUZZER_SAIDA, LED_VERMELHO_SAIDA)

# Loop principal
try:
    while True:
        print("Aguardando leitura na saída...")
        tagSaida = ler_tag(CS_SAIDA, leitorRFID_saida)
        if tagSaida:
            processar_saida(tagSaida)
        sleep(1)

        

finally:
    GPIO.cleanup()