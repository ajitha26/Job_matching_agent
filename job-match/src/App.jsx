import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [scrapeLoading, setScrapeLoading] = useState(false);

  // Send chat message
  const sendMessage = async () => {
    if (!input.trim()) return;

    const newMessages = [...messages, { role: 'user', content: input }];
    setMessages(newMessages);
    setInput('');
    setChatLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/chat/', {
        messages: newMessages,
      });
      setMessages([...newMessages, { role: 'agent', content: response.data.reply }]);
    } catch (error) {
      setMessages([
        ...newMessages,
        { role: 'agent', content: 'Sorry, something went wrong.' },
      ]);
    }
    setChatLoading(false);
  };

  // Handle Enter key for chat input
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Trigger scraping internships
  const handleScrape = async () => {
    setScrapeLoading(true);
    try {
      await axios.post('http://localhost:8000/scrape_and_store/');
      alert('Scraping complete');
    } catch (error) {
      alert('Scraping failed');
    }
    setScrapeLoading(false);
  };

  return (
    <div className="p-8 max-w-2xl mx-auto flex flex-col h-screen">
      <h1 className="text-2xl font-bold mb-4">Chat with Job Matching Agent</h1>

      <button
        onClick={handleScrape}
        disabled={scrapeLoading}
        className="mb-4 px-4 py-2 bg-green-600 text-white rounded disabled:opacity-50"
      >
        {scrapeLoading ? 'Scraping...' : 'Scrape Internships'}
      </button>

      <div className="flex-grow overflow-y-auto border rounded p-4 mb-4" style={{ minHeight: 300 }}>
        {messages.length === 0 && <p className="text-gray-500">Start the conversation...</p>}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`mb-3 p-2 rounded max-w-xs ${
              msg.role === 'user' ? 'bg-blue-500 text-white self-end' : 'bg-gray-200 self-start'
            }`}
            style={{ alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start' }}
          >
            <strong>{msg.role === 'user' ? 'You' : 'Agent'}:</strong> {msg.content}
          </div>
        ))}
        {chatLoading && <p className="text-gray-500">Agent is typing...</p>}
      </div>

      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={3}
        className="border rounded p-2 mb-2 resize-none"
        placeholder="Type your message and press Enter to send..."
      />

      <button
        onClick={sendMessage}
        disabled={chatLoading || !input.trim()}
        className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
      >
        Send
      </button>
    </div>
  );
}

export default App;
