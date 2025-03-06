import os
import re
from typing import Dict, List
from flask import Flask, render_template, request, jsonify, session

# -------------------------------
# Vault access code
# -------------------------------
class Vault:
    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        self.notes = self._load_notes()

    def _load_notes(self) -> Dict[str, str]:
        """Load all notes from the vault directory."""
        notes = {}
        for file in os.listdir(self.vault_path):
            if file.endswith(".md"):  # Assuming markdown notes
                file_path = os.path.join(self.vault_path, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    notes[file] = f.read()
        return notes

    def get_note_content(self, note_name: str) -> str:
        """Retrieve the content of a specific note."""
        return self.notes.get(note_name + ".md", "Note not found.")

    def extract_links(self, content: str) -> List[str]:
        """Extract linked notes from the given content."""
        return re.findall(r'\[\[(.*?)\]\]', content)

    def resolve_links(self, note_name: str) -> Dict[str, str]:
        """Retrieve content of linked notes."""
        content = self.get_note_content(note_name)
        links = self.extract_links(content)
        linked_notes = {link: self.get_note_content(link) for link in links}
        return linked_notes

    def search_notes(self, query: str) -> List[str]:
        """Search for notes containing the query."""
        return [name for name, content in self.notes.items() if query.lower() in content.lower()]

# -------------------------------
# Flask app configuration
# -------------------------------
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production

# Initialize the vault (change the path to your actual vault location)
vault_path = "path/to/vault"  # Update this with your vault directory path
vault = Vault(vault_path)

# Ensure chat history exists in session
@app.before_request
def ensure_chat_history():
    if 'chat_history' not in session:
        session['chat_history'] = []

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/send', methods=['POST'])
def send_message():
    user_message = request.form.get('message')
    chat_history = session.get('chat_history', [])

    # Save the user message to the chat history
    chat_history.append({'role': 'user', 'message': user_message})

    # Process the user message to generate a response.
    # Here we support two commands:
    # - "note: <note_name>" to retrieve a note
    # - "search: <query>" to search for notes containing a query
    if user_message.lower().startswith("note:"):
        note_name = user_message[5:].strip()
        note_content = vault.get_note_content(note_name)
        response_message = f"Content of note '{note_name}':\n{note_content}"
    elif user_message.lower().startswith("search:"):
        query = user_message[7:].strip()
        results = vault.search_notes(query)
        if results:
            response_message = "Notes matching your query: " + ", ".join(results)
        else:
            response_message = "No notes found matching your query."
    else:
        response_message = ("I'm not sure how to handle that. Try using the commands:\n"
                            "- 'note: <note_name>' to get a specific note\n"
                            "- 'search: <query>' to search your vault notes.")

    # Save the assistant response to the chat history
    chat_history.append({'role': 'assistant', 'message': response_message})
    session['chat_history'] = chat_history

    return jsonify({'response': response_message, 'chat_history': chat_history})

if __name__ == '__main__':
    app.run(debug=True)
