import pika

# Conexão com o RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declara a mesma fila usada pelo produtor
channel.queue_declare(queue='estacionamento')

# Função para processar as mensagens e salvar no arquivo
def callback(ch, method, properties, body):
    mensagem = body.decode()
    print(f"Mensagem recebida: {mensagem}")
    
    # Salvando a mensagem no arquivo txt
    with open("registro_estacionamento.txt", "a") as file:
        file.write(mensagem + "\n")

# Consumindo mensagens da fila
channel.basic_consume(queue='estacionamento', on_message_callback=callback, auto_ack=True)

print('Aguardando mensagens...')
channel.start_consuming()