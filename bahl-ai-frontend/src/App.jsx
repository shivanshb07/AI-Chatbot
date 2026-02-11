import { useEffect, useState, useRef } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import "./App.css";

const API = "http://127.0.0.1:5000";

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentId, setCurrentId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadChats = async () => {
    const res = await axios.get(`${API}/conversations`);
    setConversations(res.data);
  };

  const createChat = async () => {
    const res = await axios.post(`${API}/new-chat`);
    setCurrentId(res.data.conversationId);
    setMessages([]);
    loadChats();
  };

  const loadConversation = async (id) => {
    const res = await axios.get(`${API}/conversation/${id}`);
    setCurrentId(id);
    setMessages(res.data.messages);
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    let activeId = currentId;

    if (!activeId) {
      const res = await axios.post(`${API}/new-chat`);
      activeId = res.data.conversationId;
      setCurrentId(activeId);
      loadChats();
    }

    const userMessage = { role: "user", content: input };
    setMessages(prev => [...prev, userMessage]);

    const res = await axios.post(`${API}/chat`, {
      message: input,
      conversationId: activeId,
    });

    setMessages(prev => [
      ...prev,
      { role: "bot", content: res.data.reply }
    ]);

    setInput("");
  };

  const deleteChat = async (id) => {
    await axios.delete(`${API}/conversation/${id}`);

    if (id === currentId) {
      setCurrentId(null);
      setMessages([]);
    }

    loadChats();
  };

  const renameChat = async (id) => {
    const newTitle = prompt("Rename chat:");
    if (!newTitle) return;

    await axios.put(`${API}/conversation/${id}/rename`, {
      title: newTitle
    });

    loadChats();
  };

  useEffect(() => {
    loadChats();
  }, []);

  return (
    <div className="app">
      <div className="sidebar">
        <div className="logo">Bahl AI</div>

        <button className="new-chat" onClick={createChat}>
          + New Chat
        </button>

        <div className="chat-list">
          {conversations.map(chat => (
            <div
              key={chat.id}
              className={`chat-item ${chat.id === currentId ? "active" : ""}`}
              onClick={() => loadConversation(chat.id)}
            >
              <span className="chat-title">
                {chat.title}
              </span>

              <div
                className="actions"
                onClick={(e) => e.stopPropagation()}
              >
                <button onClick={() => renameChat(chat.id)}>✏</button>
                <button onClick={() => deleteChat(chat.id)}>🗑</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="main">
        <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
          <ReactMarkdown
  remarkPlugins={[remarkGfm]}
  components={{
    code({ inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || "");
      return !inline && match ? (
        <SyntaxHighlighter
          style={vscDarkPlus}
          language={match[1]}
          PreTag="div"
          {...props}
        >
          {String(children).replace(/\n$/, "")}
        </SyntaxHighlighter>
      ) : (
        <code className="inline-code" {...props}>
          {children}
        </code>
      );
    },
  }}
>
  {m.content}
</ReactMarkdown>

      </div>
))}

          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Message Bahl AI..."
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default App;