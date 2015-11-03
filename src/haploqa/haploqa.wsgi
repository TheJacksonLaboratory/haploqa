from haploqa.haploqaapp import app as application
import socket

application.config['SERVER_NAME'] = socket.getfqdn()
