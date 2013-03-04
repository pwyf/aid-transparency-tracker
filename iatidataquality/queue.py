import pika
import sys
import time
import json

# FIXME: host= should be in config
def enqueue(queue, args):
    body = json.dumps(args)
    
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=True)
    channel.basic_publish(exchange='',
                          routing_key=queue,
                          body=body,
                          properties=pika.BasicProperties(delivery_mode=2))
    connection.close()

def get_connection(host):
    count = 0.4
    while count < 60:
        try:            
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=host))
            return connection
        except:
            time.sleep(count)
            count *= 1.7
    sys.exit(1)

# FIXME: hostname should be in config
def handle_queue(queue_name, callback_fn):
    try:
        connection = get_connection('localhost')
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(callback_fn, queue=queue_name)
        channel.start_consuming()
    except:
        pass 
    finally:
        connection.close()
