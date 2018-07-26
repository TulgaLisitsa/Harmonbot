
import atexit
from queue import Queue
from subprocess import Popen, PIPE
import sys
from threading import Thread
from tkinter import BOTH, END, Frame, Text, Tk, ttk

import psutil

class HarmonbotGUI:
	
	def __init__(self, master):
		self.master = master
		master.title("Harmonbot")
		
		self.notebook = ttk.Notebook(master)
		for tab in ("overview", "discord", "discord_listener", "twitch", "telegram"):
			frame = Frame(self.notebook)
			setattr(self, f"{tab}_tab", frame)
			self.notebook.add(frame, text = tab.replace('_', ' ').title())
		self.notebook.pack()
		
		for overview_frame in ("discord", "discord_listener", "twitch", "telegram"):
			frame = Frame(self.overview_tab)
			setattr(self, f"overview_{overview_frame}_frame", frame)
			text = Text(frame)
			setattr(self, f"overview_{overview_frame}_text", text)
			text.pack()
		self.overview_discord_frame.grid(row = 1, column = 1)
		self.overview_discord_listener_frame.grid(row = 2, column = 1)
		self.overview_twitch_frame.grid(row = 1, column = 2)
		self.overview_telegram_frame.grid(row = 2, column = 2)
		
		for tab in ("discord", "discord_listener", "twitch", "telegram"):
			notebook_tab = getattr(self, f"{tab}_tab")
			frame = Frame(notebook_tab)
			setattr(self, f"{tab}_frame", frame)
			frame.pack(expand = True, fill = BOTH)
			text = Text(frame)
			setattr(self, f"{tab}_text", text)
			text.pack(expand = True, fill = BOTH)

if __name__ == "__main__":
	root = Tk()
	root.wm_state("zoomed")  # Maximized window
	harmonbot_gui = HarmonbotGUI(root)
	
	processes = {}
	process_kwargs = {"stdout": PIPE, "stderr": PIPE, "bufsize": 1, "universal_newlines": True}
	processes["discord"] = Popen([sys.executable, "-u", "Harmonbot.py"], cwd = "Discord", **process_kwargs)
	processes["discord_listener"] = Popen(["go", "run", "Harmonbot_Listener.go"], cwd = "Discord", shell = True, **process_kwargs)
	processes["twitch"] = Popen(["pyw", "-3.6", "-u", "Twitch_Harmonbot.py"], cwd = "Twitch", **process_kwargs)
	# TODO: Update to use Python 3.7 executable
	processes["telegram"] = Popen([sys.executable, "-u", "Telegram_Harmonbot.py"], cwd = "Telegram", **process_kwargs)
	
	def enqueue_output(out, queue):
		for line in iter(out.readline, ""):
			queue.put(line)
		out.close()
	
	output_queues = {}
	stdout_threads = {}
	stderr_threads = {}
	for name, process in processes.items():
		output_queue = Queue()
		output_queues[name] = output_queue
		# stdout
		stdout_thread = Thread(target = enqueue_output, args = (process.stdout, output_queue))
		stdout_threads[name] = stdout_thread
		stdout_thread.daemon = True
		stdout_thread.start()
		# stderr
		stderr_thread = Thread(target = enqueue_output, args = (process.stderr, output_queue))
		stderr_threads[name] = stderr_thread
		stderr_thread.daemon = True
		stderr_thread.start()
	
	def process_outputs():
		for name, output_queue in output_queues.items():
			while not output_queue.empty():
				line = output_queue.get_nowait()
				for text_name in (f"overview_{name}_text", f"{name}_text"):
					text = getattr(harmonbot_gui, text_name)
					text.insert(END, line)
		root.after(1, process_outputs)
		# TODO: Check stdout and stderr order
	
	def check_discord_process_ended():
		if processes["discord"].poll() is None:
			root.after(1, check_discord_process_ended)
		else:
			line = "Discord process ended"
			harmonbot_gui.overview_discord_text.insert(END, line)
			harmonbot_gui.discord_text.insert(END, line)
	
	def check_discord_listener_process_ended():
		if processes["discord_listener"].poll() is None:
			root.after(1, check_discord_listener_process_ended)
		else:
			line = "Discord listener process ended"
			harmonbot_gui.overview_discord_listener_text.insert(END, line)
			harmonbot_gui.discord_listener_text.insert(END, line)
	
	def check_twitch_process_ended():
		if processes["twitch"].poll() is None:
			root.after(1, check_twitch_process_ended)
		else:
			line = "Twitch process ended"
			harmonbot_gui.overview_twitch_text.insert(END, line)
			harmonbot_gui.twitch_text.insert(END, line)
	
	def check_telegram_process_ended():
		if processes["telegram"].poll() is None:
			root.after(1, check_telegram_process_ended)
		else:
			line = "Telegram process ended"
			harmonbot_gui.overview_telegram_text.insert(END, line)
			harmonbot_gui.telegram_text.insert(END, line)
	
	for function in (process_outputs, check_discord_process_ended, 
						check_discord_listener_process_ended, check_twitch_process_ended, 
						check_telegram_process_ended):
		root.after(0, function)
	
	def cleanup():
		go_process = psutil.Process(processes["discord_listener"].pid)
		for process in go_process.children(recursive = True):
			process.terminate()
		for process in processes.values():
			process.terminate()
		## root.destroy()
	
	atexit.register(cleanup)
	
	## root.protocol("WM_DELETE_WINDOW", cleanup)
	root.mainloop()

