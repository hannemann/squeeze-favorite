#!/usr/bin/env python

import sys
import socket
import time
import urllib
import getopt


class SqueezeFavorite(object):

    def __init__(self, host, port_no):
        """ initialize """
        self.host = host
        self.port = port_no if port_no is not None else 9090
        self.players = {}
        self.favorites = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __enter__(self):
        self.socket.connect((self.host, self.port))
        self.get_players()
        self.get_favorites()
        return self

    def print_list(self):
        print "\n\tPlayers:"
        for name in self.players:
            print "\t\t" + name

        print "\n\tFavorites:"
        for name in self.favorites:
            print "\t\t" + name

    def start_favorite(self, player_name, favorite_name):
        try:
            payload = "{} favorites playlist play item_id:{}\n".format(
                self.players[player_name], self.favorites[favorite_name]
            )
            self.socket.send(payload)
        except KeyError:
            print "Player '{}' or favorite '{}' not available".format(player_name, favorite)

    def get_players(self):
        payload = "players 0 9999\n"
        self.socket.send(payload)
        start = time.time()
        while 1:
            data = self.socket.recv(4096)
            if data or time.time() - start > 10:
                break
        if data:
            self.parse_players(data)

    def get_favorites(self):
        payload = "favorites items 0 9999\n"
        self.socket.send(payload)
        start = time.time()
        while 1:
            data = self.socket.recv(4096)
            if data or time.time() - start > 10:
                break
        if data:
            self.parse_favorites(data)

    def shuffle_playlist(self, player_name):
        payload = "{} playlist shuffle ?\n".format(self.players[player_name])
        self.socket.send(payload)
        start = time.time()
        while 1:
            data = self.socket.recv(4096)
            if data or time.time() - start > 10:
                break
        if data:
            shuffled = int(data.split(' ')[-1:][0]) > 0
            payload = "{} playlist shuffle {}\n".format(self.players[player_name], 0 if shuffled is True else 1)
            self.socket.send(payload)

    def parse_players(self, data):
        data = data.split(' ')[5:]
        start = 0
        length = 14
        stop = start + length
        while stop <= len(data):
            row = data[start:stop]
            current = {}
            for i in row:
                key, value = urllib.unquote(i).split(':', 1)
                current[key] = value
            self.players[current['name']] = current['playerid']
            start = stop
            stop += length

    def parse_favorites(self, data):
        data = data.split(' ')[5:-1]
        start = 0
        length = 5
        stop = start + length
        while stop <= len(data):
            row = data[start:stop]
            current = {}
            for i in row:
                key, value = urllib.unquote(i).split(':', 1)
                current[key] = value
            self.favorites[current['name']] = current['id']
            start = stop
            stop += length

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.socket.close()


def usage():
    """ print help message """
    print '\n\tStart a LMS favorite via command line\n'
    print '\n\tUsage:\n'
    print '\t\t-h\tHelp'
    print '\t\t-l\tGet list of available players and favorites'
    print '\t\t-s\tServer address (ip or hostname)'
    print '\t\t-p\tPort (default 9090)'
    print '\t\t-r\tPlayer name'
    print '\t\t-f\tFavorite name'
    print '\t\t-t\ttoggle shuffle'
    print '\n'


if __name__ == "__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:p:r:f:hlt", ["help"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    server = None
    port = None
    player = None
    favorite = None
    get_list = False
    shuffle = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        if opt == '-s':
            server = arg
        if opt == '-p':
            try:
                port = int(arg)
            except ValueError:
                usage()
                sys.exit(1)
        if opt == '-r':
            player = arg
        if opt == '-f':
            favorite = arg
        if opt == '-l':
            get_list = True
        if opt == '-t':
            shuffle = True

    if server is None:
        usage()
        sys.exit(2)

    with SqueezeFavorite(server, port) as squeeze:
        if get_list is True:
            squeeze.print_list()
        elif player and favorite:
            squeeze.start_favorite(player, favorite)
        elif player and shuffle is not None:
            squeeze.shuffle_playlist(player)
        else:
            usage()
            sys.exit(2)
