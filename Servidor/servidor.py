#!/usr/bin/env python
from __future__ import print_function
import threading
import time
from xmlrpclib import ServerProxy, Binary
from SimpleXMLRPCServer import SimpleXMLRPCServer,SimpleXMLRPCRequestHandler
import SocketServer
from os import stat,walk
from ast import literal_eval

class AsyncXMLRPCServer(SocketServer.ThreadingMixIn,SimpleXMLRPCServer): pass

centralServerDir = "http://localhost:8000"
serverDir = "http://localhost:8121"
nameFileStatics = "statistics.txt"
messages = [ "1. Libros en descarga.",
			 "2. Libros descargados.",
			 "3. Estadisticas de clientes." ]
currentDownloads = {}

def cargarListaLibros():
	libros = []
	for root,dir,file in walk("Repositorio"):
		for f in file:
			libros.append(f.split('.')[0])
	return libros

def ComprobarLibro(libro):
	print("comprobando libro...")
	for aux in server.libros:
		if (aux == libro):
			return True
	return False

def tamLibro(libro):
	ruta = "Repositorio/" + libro + ".pdf"
	print(ruta)
	return stat(ruta).st_size

def bajarDatos(username, libro, tamfragmento, fragmento, centinela):
	if (not username in currentDownloads):
		currentDownloads[username] = []
	currentDownloads[username].append(libro)	
	print("Enviando libro...")
	ruta = "Repositorio/" + libro + ".pdf"
	file = open(ruta, "rb")
	file.read(tamfragmento * (fragmento - 1))
	if (centinela):
		aux = file.read()
	else:
		aux = file.read(tamfragmento)
	file.close()
	return Binary(aux)

def ListaLibros():
	return server.libros

def actReportes(option, clientName, bookName):
	# REGION CRITICA
	file = open(nameFileStatics, 'r')
	statistics = file.readlines()
	books      = literal_eval(statistics[0])
	clients    = literal_eval(statistics[1])
	file.close()
	if (option == 0):
		currentDownloads[clientName].remove(bookName)
		if (not currentDownloads[clientName]):
			del currentDownloads[clientName]
		if not (bookName in books):
			books[bookName] = 0
		books[bookName] = books[bookName] + 1
		try:
			centralServer = ServerProxy(centralServerDir)
			centralServer.actReportes(0, serverDir, bookName)
		except:
			print("No se logro establecer conexion con el servidor central.")
	else:
		if not (clientName in clients):
			clients[clientName] = 0
		clients[clientName] = clients[clientName] + 1
	file = open(nameFileStatics, 'w')
	file.write(str(books)   + '\n')
	file.write(str(clients) + '\n')
	file.close()
	return "ACK"

class DownloadServer(threading.Thread):
	def run(self):
		server = AsyncXMLRPCServer(("localhost", 8121), SimpleXMLRPCRequestHandler)
		server.register_function(ComprobarLibro,    "ComprobarLibro")
		server.register_function(bajarDatos, "bajarDatos")
		server.register_function(ListaLibros,    "ListaLibros")
		server.register_function(tamLibro,     "tamLibro")
		server.register_function(actReportes, "actReportes")
		server.serve_forever()

class Server:
	def __init__(self, central = centralServerDir, server = serverDir):
		self.proxy = ServerProxy(centralServerDir)
		self.proxy.registerServer(serverDir)
		self.downloadServer = DownloadServer()
		self.downloadServer.start()
		self.libros = cargarListaLibros()

	def printBooks(self):
		print("Los libros disponibles son: ")
		for book in self.libros:
			print(book)

	# Muestra las estadisticas segun la opcion elegida
	def showStatistics(self, option):
		if (option == '1'):
			for client in currentDownloads:
				print(client)
				for book in currentDownloads[client]:
					print("\t" + book)
		else:
			file = open(nameFileStatics, 'r')
			statistics  = file.readlines()
			data = literal_eval(statistics[int(option)-2])
			elements = [(data[name], name) for name in data]
			elements.sort(reverse = True)
			x = 1
			for val, name in elements:
				print(str(x) + ". " + name + ": " + str(val))
				x = x+1
			print()
			file.close()

	def run(self):
		while (True):
			print("Elija un opcion: ")
			for message in messages:
				print(message)
			print()
			option = raw_input()
			if ( not (option == '1' or option == '2' or option == '3')):
				print("Opcion invalida")
				continue
			if  (option == '1'):
				self.showStatistics(option)
			else:
				self.showStatistics(option)

if __name__ == '__main__':
	server = Server()
	server.run()