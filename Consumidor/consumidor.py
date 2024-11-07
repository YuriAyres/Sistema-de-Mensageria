import pika
from flask import Flask, render_template, jsonify
import threading

app = Flask(__name__)

mensagens = []

# Conexão com o RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('10.1.24.62'))
channel = connection.channel()
channel.queue_declare(queue='estacionamento')

# Função para processar as mensagens e adicionar na lista
def callback(ch, method, properties, body):
    mensagem = body.decode()
    print(f"Mensagem recebida: {mensagem}")
    
    # Adiciona a mensagem na lista
    mensagens.append(mensagem)

    # Salvando a mensagem no arquivo txt
    with open("registro_estacionamento.txt", "a") as file:
        file.write(mensagem + "\n")

# Consumindo mensagens da fila
channel.basic_consume(queue='estacionamento', on_message_callback=callback, auto_ack=True)

# Função para rodar o consumidor em uma thread separada
def start_consuming():
    print('Aguardando mensagens...')
    channel.start_consuming()

# Rota para a página principal
@app.route('/')
def index():
    return render_template('index.html', mensagens=mensagens)

# Rota para obter as mensagens em formato JSON
@app.route('/mensagens')
def get_mensagens():
    return jsonify(mensagens)

if __name__ == "__main__":
    # Rodar o consumidor em uma thread separada
    thread = threading.Thread(target=start_consuming)
    thread.start()

    # Rodar o servidor Flask
    app.run(host='localhost', port=5000)