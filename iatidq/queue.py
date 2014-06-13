
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

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

def handle_queue_generator(queue_name):
    try:
        connection = get_connection('localhost')
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)
        channel.basic_qos(prefetch_count=1)
        while True:
            method_frame, properties, body = channel.basic_get(queue_name)
            if not method_frame:
                break
            channel.basic_ack(method_frame.delivery_tag)
            yield body
    finally:
        requeued_messages = channel.cancel()
        channel.close()
        connection.close()

def exhaust_queue(queue, callback_fn):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        while True:
            method_frame, header_frame, body = channel.basic_get(queue)
            if not method_frame:
                break
            callback_fn(body)
            channel.basic_ack(method_frame.delivery_tag)

    finally:
        channel.close()
        connection.close()
