import React, { useState, useRef, useEffect } from "react";

export default function ChatWidget({ wsUrl, restUrl }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const ws = useRef(null);

  useEffect(() => {
    if (wsUrl) {
      ws.current = new WebSocket(wsUrl);
      ws.current.onmessage = (evt) => {
        const data = JSON.parse(evt.data);
        setMessages((ms) => [...ms, { text: data.message || data.response, user: "bot" }]);
      };
      return () => ws.current && ws.current.close();
    }
  }, [wsUrl]);

  const send = () => {
    if (!input.trim()) return;

    if (ws.current && ws.current.readyState === 1) {
      ws.current.send(JSON.stringify({ message: input }));
    } else if (restUrl) {
      fetch(restUrl, {
        method: "POST",
        body: JSON.stringify({ message: input }),
        headers: { "Content-Type": "application/json" },
      })
        .then((res) => res.json())
        .then((data) =>
          setMessages((ms) => [...ms, { text: data.response || data.message, user: "bot" }])
        )
        .catch((err) => console.error("Error:", err));
    }
    setMessages((ms) => [...ms, { text: input, user: "user" }]);
    setInput("");
  };

  return (
    <div className="p-4 max-w-md mx-auto">
      <div className="bg-white h-64 overflow-y-auto shadow rounded mb-2 p-2">
        {messages.map((msg, i) => (
          <div key={i} className={msg.user === "user" ? "text-right" : ""}>
            <span
              className={
                msg.user === "user"
                  ? "inline-block bg-blue-200 px-2 py-1 rounded m-1"
                  : "inline-block bg-gray-200 px-2 py-1 rounded m-1"
              }
            >
              {msg.text}
            </span>
          </div>
        ))}
      </div>
      <div className="flex">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && send()}
          className="flex-1 border rounded px-2 py-1"
          placeholder="Type a message..."
        />
        <button
          onClick={send}
          className="bg-blue-500 text-white rounded px-4 py-1 ml-2 hover:bg-blue-600"
        >
          Send
        </button>
      </div>
    </div>
  );
}

