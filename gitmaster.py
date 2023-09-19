import openai
import requests
import base64
import re
import tkinter as tk
from tkinter import simpledialog, messagebox, Text, Scrollbar

# Set up OpenAI API key
openai.api_key = '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'

class GitHubRepoPlugin:

    def __init__(self, token):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def parse_link(self, link):
        parts = link.split("/")
        owner = parts[-2]
        repo = parts[-1]
        return owner, repo

    def fetch_repo_data(self, owner, repo):
        # Update the URL format
        url = f"{self.base_url}/{owner}/{repo}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return f"Error fetching repository data: {e}"

    def fetch_repo_files(self, owner, repo):
        url = f"{self.base_url}/repos/{owner}/{repo}/contents"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return [item["name"] for item in response.json()]
        except requests.RequestException as e:
            return f"Error fetching repository files: {e}"

    def fetch_file_content(self, owner, repo, filename):
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{filename}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            encoded_content = response.json()["content"]
            return base64.b64decode(encoded_content).decode('utf-8')
        except requests.RequestException as e:
            return f"Error fetching file content: {e}"

    def query(self, message):
        link, question = self.parse_message(message)
        owner, repo = self.parse_link(link)
        if not question:
            data = self.fetch_repo_data(owner, repo)
            if isinstance(data, dict):
                return f"Repository {data['name']} has {data['stargazers_count']} stars, {data['forks_count']} forks, and its description is: {data['description']}."
            else:
                return data
        elif "files" in question or "contents" in question:
            files = self.fetch_repo_files(owner, repo)
            if isinstance(files, list):
                return f"Files in the repository: {', '.join(files)}"
            else:
                return files
        elif "content" in question:
            filename = question.split("content of")[-1].strip()
            content = self.fetch_file_content(owner, repo, filename)
            return f"Content of {filename}: {content}"
        else:
            return "I'm not sure how to answer that question."

    def parse_message(self, message):
        link_pattern = r'https://github.com/[\w-]+/[\w-]+'
        link_match = re.search(link_pattern, message)
        link = link_match.group(0) if link_match else None
        question = message.replace(link, '').strip() if link else message
        return link, question


import requests

import requests

def chat_with_gpt(message, conversation_history="", temperature=0.7, max_tokens=150):
    plugin = GitHubRepoPlugin("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")
    try:
        plugin_response = plugin.query(message)
        conversation_history += f"User: {message}\nAgent: {plugin_response}\n"
        conversation_payload = {
            "messages": [{"role": "user", "content": conversation_history}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        headers = {
            "Authorization": f"Bearer {openai.api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post("https://api.openai.com/v2/completions", headers=headers, json=conversation_payload)
        response_data = response.json()
        
        # Check for errors in the response
        if 'error' in response_data:
            return response_data['error']['message'], conversation_history
        
        assistant_response = response_data['choices'][0]['message']['content']
        conversation_history += f"Assistant: {assistant_response}\n"
        return assistant_response, conversation_history
    except Exception as e:
        return str(e), conversation_history



class ChatGPTGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("gitmaster GitHub Plugin")

        self.conversation_history = ""
        self.temperature = 0.7
        self.max_tokens = 300

        self.text_widget = Text(root, wrap=tk.WORD, state=tk.DISABLED)
        self.text_widget.pack(expand=1, fill=tk.BOTH, padx=10, pady=10)

        self.scrollbar = Scrollbar(root, command=self.text_widget.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_widget.config(yscrollcommand=self.scrollbar.set)

        self.entry = tk.Entry(root, width=50)
        self.entry.pack(pady=10)
        self.entry.bind('<Return>', self.send_message)

        self.button = tk.Button(root, text="Send", command=self.send_message)
        self.button.pack(pady=10)

        self.menu = tk.Menu(root)
        root.config(menu=self.menu)

        self.settings_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label="Settings", menu=self.settings_menu)
        self.settings_menu.add_command(label="Modify Agent", command=self.modify_agent)

    def send_message(self, event=None):
        user_message = self.entry.get()
        if user_message:
            response, self.conversation_history = chat_with_gpt(user_message, self.conversation_history, self.temperature, self.max_tokens)
            self.display_message(f"User: {user_message}\nAgent: {response}\n")
            self.entry.delete(0, tk.END)

    def display_message(self, message):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)

    def modify_agent(self):
        def apply_changes():
            self.temperature = temperature_slider.get()
            self.max_tokens = int(max_tokens_entry.get())
            modify_window.destroy()
            messagebox.showinfo("Info", f"Agent modified with temperature: {self.temperature} and max tokens: {self.max_tokens}")

        modify_window = tk.Toplevel(self.root)
        modify_window.title("Modify Agent Parameters")

        # Temperature
        temperature_label = tk.Label(modify_window, text="Temperature:")
        temperature_label.pack(pady=10)

        temperature_slider = tk.Scale(modify_window, from_=0.0, to=10.0, resolution=0.01, orient=tk.HORIZONTAL)
        temperature_slider.set(self.temperature)
        temperature_slider.pack(pady=10)

        # Max Tokens
        max_tokens_label = tk.Label(modify_window, text="Max Tokens:")
        max_tokens_label.pack(pady=10)

        max_tokens_entry = tk.Entry(modify_window)
        max_tokens_entry.insert(0, str(self.max_tokens))
        max_tokens_entry.pack(pady=10)

        apply_button = tk.Button(modify_window, text="Apply", command=apply_changes)
        apply_button.pack(pady=10)

root = tk.Tk()
gui = ChatGPTGUI(root)
root.mainloop()