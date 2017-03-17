import subprocess
from time import sleep
import socket
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DETACHED_PROCESS = 0x00000008

class UDPFileEventHandler(FileSystemEventHandler):
	def __init__(self, ip, port):
		self.dest = (ip, port)
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	def on_any_event(self, event):
		if event.is_directory:
			self.sock.sendto('{} directory: {}'.format(event.event_type, event.src_path), self.dest)
		else:
			self.sock.sendto('{} : {}'.format(event.event_type, event.src_path), self.dest)



def watch_files(locs, ip, port):
	for l in locs:
		fileEvtHandler = UDPFileEventHandler(ip, port)
		observer = Observer()
		observer.schedule(fileEvtHandler, l, recursive=True)
		observer.start()


def watch(ip, port, locs):
	if len(locs) > 0:
		watch_files(locs, ip ,port)

	cmd = 'wmic process get caption,executablepath,processid'.split(' ')
	procs = set(subprocess.check_output(cmd, creationflags=DETACHED_PROCESS).split('\n'))
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	while True:
		sleep(10)
		new_procs = set(subprocess.check_output(cmd).split('\n'))
		# diff of last set of processes vs this set (only which ones are new though)
		added = [' '.join(p.split()) + ' ' for p in new_procs - procs]
		if len(added) > 0:
			added_with_users = []
			# get extra information not available from wmic like Username
			for a in added:
				if not a.startswith('WMIC.exe'):
					extra_info = ' '.join(subprocess.check_output(['tasklist' ,'/v','/nh', '/fi', 'pid eq {}'.format(a.split()[-1])], creationflags=DETACHED_PROCESS).split())
					added_with_users.append(a + extra_info if not extra_info.startswith('INFO') else a)
			# send to listening udp port
			sock.sendto('\n'.join(added_with_users), (ip, port))



		procs = new_procs

if __name__=='__main__':
	if len(sys.argv) < 3:
		f = open('info.log')
		f.write('need args <ip> <port> [<comma list of places to watch>]')
		f.close()
	elif len(sys.argv) == 3:
		ip = sys.argv[1]
		port = int(sys.argv[2])
		watch(ip, port, [])
	else:
		ip = sys.argv[1]
		port = int(sys.argv[2])
		watch(ip, port, sys.argv[3].split(','))